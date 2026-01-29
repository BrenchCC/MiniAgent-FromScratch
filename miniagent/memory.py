import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional


from dataclasses import dataclass, field

logger = logging.getLogger("MiniAgent Memory")


def _get_memory_dir() -> Path:
    """
    Get memory directory from environment variable or use default location
    """
    memory_dir = Path(os.environ.get("MINIAGENT_HOME", ".miniagent")).expanduser() / "memory"
    memory_dir.mkdir(parents = True, exist_ok = True)
    return memory_dir


def _generate_timestamped_filename() -> str:
    """
    Generate timestamped filename in format: YYYYMMDD_HHMM.json
    """
    return datetime.now().strftime("%Y%m%d_%H%M.json")


def _list_memory_files() -> List[Path]:
    """
    List all memory files in memory directory sorted by creation time (oldest to newest)
    """
    memory_dir = _get_memory_dir()
    memory_files = sorted(
        [f for f in memory_dir.glob("*.json") if f.name != "memory.json"],
        key = lambda x: x.stat().st_ctime
    )
    return memory_files


def _manage_memory_files(max_files: int = 8) -> None:
    """
    Manage memory files: keep only the most recent `max_files` files
    """
    memory_files = _list_memory_files()
    if len(memory_files) > max_files:
        files_to_delete = memory_files[:len(memory_files) - max_files]
        for file in files_to_delete:
            try:
                file.unlink()
                logger.info(f"Deleted old memory file: {file}")
            except Exception:
                logger.exception(f"Failed to delete old memory file: {file}")


def _default_memory_path() -> Path:
    """
    Get default memory path with timestamped filename
    """
    memory_dir = _get_memory_dir()
    _manage_memory_files()
    return memory_dir / _generate_timestamped_filename()


def _get_memory_path_by_index(index: int) -> Optional[Path]:
    """
    Get memory file path by index (1-based). 1 = most recent, 2 = second most recent, etc.
    Returns None if index is out of range.
    """
    memory_files = _list_memory_files()
    if 1 <= index <= len(memory_files):
        return memory_files[-index]
    return None


@dataclass
class Memory:
    """
    Memory class for MiniAgent
    """
    path: Path = field(default_factory = _default_memory_path)
    preferences: Dict[str, Any] = field(default_factory = dict)
    facts: Dict[str, Any] = field(default_factory = dict)
    messages: List[Dict[str, str]] = field(default_factory = list)
    max_messages: int = 40

    @classmethod
    def from_index(cls, index: int) -> "Memory":
        """
        Create a Memory instance from a conversation index (1-based).
        If index is out of range or file not found, creates a new memory.
        """
        path = _get_memory_path_by_index(index)
        if path:
            logger.info(f"Loading memory from: {path}")
            return cls(path = path)
        logger.warning(f"Memory index {index} not found, creating new memory")
        return cls()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding = "utf-8"))
            self.preferences = data.get("preferences", {}) or {}
            self.facts = data.get("facts", {}) or {}
            self.messages = data.get("messages", []) or []
        except Exception:
            logger.exception("Failed to load memory")

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents = True, exist_ok = True)
            payload = {
                "updated_at": int(time.time()),
                "preferences": self.preferences,
                "facts": self.facts,
                "messages": self.messages[-self.max_messages :],
            }
            self.path.write_text(
                json.dumps(payload, ensure_ascii = False, indent = 2),
                encoding = "utf-8"
            )
        except Exception:
            logger.exception("Failed to save memory")

    def set_preference(self, key: str, value: Any) -> None:
        self.preferences[key] = value
        self.save()

    def set_fact(self, key: str, value: Any) -> None:
        self.facts[key] = value
        self.save()

    def push(self, role: str, content: str) -> None:
        if not content:
            return
        self.messages.append({"role": role, "content": content})
        self.messages = self.messages[-self.max_messages :]
        self.save()

    def context(self) -> str:
        """Generate a compact memory context string for the LLM."""
        parts: List[str] = []
        if self.preferences:
            prefs = ", ".join(f"{k}={v}" for k, v in sorted(self.preferences.items()))
            parts.append(f"User preferences: {prefs}")
        if self.facts:
            facts = ", ".join(f"{k}={v}" for k, v in sorted(self.facts.items()))
            parts.append(f"User facts: {facts}")
        if self.messages:
            recent = self.messages[-10:]
            convo = "\n".join(f"{m['role']}: {m['content']}" for m in recent)
            parts.append("Recent conversation:\n" + convo)
        return "\n\n".join(parts).strip()
