"""
Debug utility nástroje
"""
import logging
import time
from functools import wraps
from typing import Any, Callable
import json


# Enhanced logging formatter
class ColoredFormatter(logging.Formatter):
    """Barevný formatter pro lepší čitelnost logů"""

    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_debug_logging(log_file: str = "mycoder_chat.log"):
    """Nastaví pokročilé logování"""

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # Console handler s barvami
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter(
        '%(levelname)s | %(name)s | %(message)s'
    )
    console_handler.setFormatter(console_formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger


def timing_decorator(func: Callable) -> Callable:
    """Decorator pro měření času funkcí"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        logging.getLogger(func.__module__).debug(
            f"{func.__name__} took {duration:.3f}s"
        )
        return result

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        logging.getLogger(func.__module__).debug(
            f"{func.__name__} took {duration:.3f}s"
        )
        return result

    # Detekuj jestli je funkce async
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def log_request_response(logger: logging.Logger):
    """Decorator pro logování request/response"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Log request
            logger.debug(f"REQUEST to {func.__name__}")
            logger.debug(f"Args: {args}")
            logger.debug(f"Kwargs: {kwargs}")

            try:
                result = await func(*args, **kwargs)

                # Log response
                logger.debug(f"RESPONSE from {func.__name__}")
                if isinstance(result, dict):
                    logger.debug(f"Response: {json.dumps(result, indent=2)}")
                else:
                    logger.debug(f"Response: {result}")

                return result

            except Exception as e:
                logger.error(f"ERROR in {func.__name__}: {e}")
                raise

        return wrapper
    return decorator
