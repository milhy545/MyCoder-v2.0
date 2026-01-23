"""
MyCoder Chat Interface - FastAPI Backend
Mini-orchestrator pro routing na HAS a LLM Server
"""

import json
import logging
import os
from pathlib import Path

import httpx
from debug_utils import setup_debug_logging, timing_decorator
from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from router import MiniOrchestrator

# Logging setup
setup_debug_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MyCoder Chat - J.A.R.V.I.S.",
    description="Lightweight chat interface s mini-orchestrací",
    version="1.0.0",
)

# Configuration
HAS_URL = os.getenv("HAS_URL", "http://192.168.0.58:8020")
LLM_SERVER_URL = os.getenv("LLM_SERVER_URL", "http://llm-server.local:8000")
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000"
).split(",")
AUTH_TOKEN = os.getenv("MYCODER_AUTH_TOKEN", "")  # If empty, auth is disabled

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = MiniOrchestrator()

# Mount frontend
frontend_path = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


@app.get("/")
async def get_chat():
    """Vrátí chat UI"""
    html_path = frontend_path / "index.html"
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "has_url": HAS_URL, "llm_server_url": LLM_SERVER_URL}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket pro real-time chat"""
    await websocket.accept()
    logger.info("New WebSocket connection established")

    try:
        while True:
            # Přijmi zprávu od uživatele
            user_message = await websocket.receive_text()
            logger.info(f"Received message: {user_message[:100]}...")

            # Mini-orchestrace: rozhodnutí kam poslat
            routing = orchestrator.route_request(user_message)
            logger.info(f"Routing decision: {routing}")

            # Pošli routing info uživateli (pro transparentnost)
            await websocket.send_json({"type": "routing_info", "routing": routing})

            # Zavolej příslušný backend
            try:
                if routing["target"] == "has":
                    response = await call_has(user_message, routing)
                elif routing["target"] == "llm_server":
                    response = await call_llm_server(user_message, routing)
                else:
                    response = {
                        "content": f"❌ Unknown target: {routing['target']}",
                        "metadata": {},
                    }

                # Pošli odpověď uživateli
                await websocket.send_json(
                    {
                        "type": "response",
                        "content": response.get("content", "Prázdná odpověď"),
                        "metadata": response.get("metadata", {}),
                    }
                )

            except Exception as e:
                logger.error(f"Error processing request: {e}")
                await websocket.send_json(
                    {
                        "type": "error",
                        "content": f"❌ Chyba při zpracování: {str(e)}",
                        "metadata": {"error": str(e)},
                    }
                )

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


@timing_decorator
async def call_has(message: str, routing: dict) -> dict:
    """Zavolá HAS Mega-Coordinator"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "message": message,
                "service": routing["service"],
                "mode": routing["mode"],
                "model": routing.get("model", "auto"),
            }

            logger.info(f"Calling HAS: {HAS_URL}/mcp")
            response = await client.post(f"{HAS_URL}/mcp", json=payload)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"HAS error: {response.status_code} - {response.text}")
                return {
                    "content": f"❌ HAS vrátil chybu: {response.status_code}",
                    "metadata": {"error": response.text},
                }

    except httpx.ConnectError:
        logger.error(f"Cannot connect to HAS at {HAS_URL}")
        return {
            "content": f"❌ Nelze se připojit k HAS ({HAS_URL}). Zkontroluj že server běží.",
            "metadata": {"error": "connection_refused"},
        }
    except Exception as e:
        logger.error(f"HAS call failed: {e}")
        return {
            "content": f"❌ Chyba při volání HAS: {str(e)}",
            "metadata": {"error": str(e)},
        }


@timing_decorator
async def call_llm_server(message: str, routing: dict) -> dict:
    """Zavolá LLM Server pro heavy tasks"""
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            payload = {
                "message": message,
                "service": routing["service"],
                "mode": routing["mode"],
            }

            logger.info(f"Calling LLM Server: {LLM_SERVER_URL}/process")
            response = await client.post(f"{LLM_SERVER_URL}/process", json=payload)

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "content": f"❌ LLM Server error: {response.status_code}",
                    "metadata": {"error": response.text},
                }

    except httpx.ConnectError:
        return {
            "content": f"❌ LLM Server nedostupný ({LLM_SERVER_URL})",
            "metadata": {"error": "connection_refused"},
        }
    except Exception as e:
        logger.error(f"LLM Server call failed: {e}")
        return {
            "content": f"❌ Chyba LLM Server: {str(e)}",
            "metadata": {"error": str(e)},
        }


# ========== DEBUG ENDPOINTS ==========


@app.get("/debug/routing/{message}")
async def debug_routing(message: str):
    """Debug endpoint pro testování routing logiky"""
    routing = orchestrator.route_request(message)
    return {
        "message": message,
        "routing_decision": routing,
        "patterns_matched": orchestrator._debug_get_matched_patterns(message),
    }


@app.get("/debug/logs")
async def get_logs(lines: int = 100):
    """Vrátí posledních N řádků z logu"""
    try:
        with open("mycoder_chat.log", "r") as f:
            all_lines = f.readlines()
            return {"total_lines": len(all_lines), "last_lines": all_lines[-lines:]}
    except FileNotFoundError:
        return {"error": "Log file not found"}


@app.get("/debug/stats")
async def get_stats():
    """Statistiky routingu"""
    return {
        "total_requests": orchestrator.total_requests,
        "routing_breakdown": orchestrator.routing_stats,
        "error_count": 0,
    }


@app.post("/debug/test-has")
async def test_has_connection():
    """Test spojení s HAS"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{HAS_URL}/health")
            return {
                "status": "connected",
                "has_response": (
                    response.json() if response.status_code == 200 else None
                ),
                "status_code": response.status_code,
            }
    except Exception:
        logger.exception("HAS health check failed")
        return {"status": "failed", "error": "HAS health check failed"}


@app.post("/debug/test-llm-server")
async def test_llm_connection():
    """Test spojení s LLM Server"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{LLM_SERVER_URL}/health")
            return {
                "status": "connected",
                "llm_response": (
                    response.json() if response.status_code == 200 else None
                ),
                "status_code": response.status_code,
            }
    except Exception:
        logger.exception("LLM server health check failed")
        return {"status": "failed", "error": "LLM server health check failed"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
