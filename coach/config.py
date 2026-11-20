import os
from dataclasses import dataclass, field
from pathlib import Path


def _env_flag(name):
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def ai_enabled_from_env():
    return bool(
        os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("ANTHROPIC_AUTH_TOKEN")
        or _env_flag("COACH_AI_ENABLED")
    )


@dataclass
class Config:
    base_dir: Path
    host: str = "127.0.0.1"
    port: int = 5050
    max_upload_mb: int = 25
    pending_ttl_hours: int = 24
    timezone: str = "Asia/Ho_Chi_Minh"
    ai_model: str = field(default_factory=lambda: os.environ.get("COACH_AI_MODEL", "claude-opus-5-5"))
    ai_enabled: bool = field(default_factory=ai_enabled_from_env)

    def __post_init__(self):
        self.base_dir = Path(self.base_dir).resolve()

    @property
    def data_dir(self):
        return self.base_dir / "data"

    @property
    def plans_dir(self):
        return self.base_dir / "plans"

    @property
    def uploads_dir(self):
        return self.base_dir / "uploads"

    @property
    def backup_dir(self):
        return self.base_dir / "data_backup"

    @property
    def max_upload_bytes(self):
        return self.max_upload_mb * 1024 * 1024
