"""
MyCoder Skills Manager
Načítá a spravuje externí skilly (OpenAI Codex style) ze složky skills/.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Skill:
    """Reprezentace jednoho načteného skillu."""

    name: str
    description: str
    command: str
    icon: str = "🔧"
    version: str = "1.0.0"
    author: str = "Unknown"
    path: Optional[Path] = None


class SkillManager:
    """Spravuje načítání a přístup k skills."""

    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, Skill] = {}
        self._load_skills()

    def _load_skills(self) -> None:
        """Prohledá skills_dir a načte všechny platné skill.json soubory."""
        self.skills.clear()
        if not self.skills_dir.exists():
            logger.debug(f"Skills directory {self.skills_dir} does not exist.")
            return

        # Procházení podadresářů
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            json_path = skill_dir / "skill.json"
            if not json_path.exists():
                continue

            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))

                # Validace povinných polí
                if not all(k in data for k in ("name", "description", "command")):
                    logger.warning(
                        f"Skipping invalid skill in {skill_dir}: missing fields"
                    )
                    continue

                skill = Skill(
                    name=data["name"],
                    description=data["description"],
                    command=data["command"],
                    icon=data.get("icon", "🔧"),
                    version=data.get("version", "1.0.0"),
                    author=data.get("author", "Unknown"),
                    path=skill_dir,
                )

                self.skills[skill.name] = skill
                logger.info(f"Loaded skill: {skill.name}")

            except json.JSONDecodeError as e:
                logger.error(f"Error parsing {json_path}: {e}")
            except Exception as e:
                logger.error(f"Error loading skill from {skill_dir}: {e}")

    def get_skill(self, name: str) -> Optional[Skill]:
        """Vrátí skill podle jména."""
        return self.skills.get(name)

    def list_skills(self) -> List[Skill]:
        """Vrátí seznam všech načtených skillů."""
        return list(self.skills.values())

    def reload(self) -> None:
        """Znovu načte všechny skilly."""
        self._load_skills()
