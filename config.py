from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


LOGGER = logging.getLogger(__name__)
SLOT_COUNT = 5


@dataclass(slots=True)
class ReactionSlot:
    index: int
    enabled: bool = True
    user_id: int | None = None
    role_id: int | None = None
    emoji_id: int | None = None
    emoji_name: str | None = None

    @property
    def is_configured(self) -> bool:
        return self.user_id is not None and (
            self.emoji_id is not None or bool(self.emoji_name)
        )

    @property
    def emoji_display(self) -> str:
        if self.emoji_id is not None and self.emoji_name:
            return f"<:{self.emoji_name}:{self.emoji_id}>"
        if self.emoji_id is not None:
            return str(self.emoji_id)
        if self.emoji_name:
            return self.emoji_name
        return "Not set"

    @property
    def status_label(self) -> str:
        return "ENABLED" if self.enabled else "DISABLED"


@dataclass(slots=True)
class AppConfig:
    token: str
    log_level: str
    slots: list[ReactionSlot] = field(default_factory=list)
    env_path: Path = Path(".env")

    def get_slot(self, slot_number: int) -> ReactionSlot:
        return self.slots[slot_number - 1]


class ConfigError(ValueError):
    """Raised when the environment file is invalid."""


def load_config(env_path: str | Path = ".env") -> AppConfig:
    env_file = Path(env_path)
    load_dotenv(dotenv_path=env_file, override=False)

    token = os.getenv("DISCORD_USER_TOKEN", "").strip()
    if not token:
        raise ConfigError("DISCORD_USER_TOKEN is required.")

    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO"
    slots = [_load_slot(index) for index in range(1, SLOT_COUNT + 1)]

    return AppConfig(
        token=token,
        log_level=log_level,
        slots=slots,
        env_path=env_file,
    )


def save_enabled_state(config: AppConfig, slot_number: int) -> None:
    env_path = config.env_path
    slot = config.get_slot(slot_number)
    key = f"SLOT_ENABLED_{slot_number}"
    lines = []

    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    updated = False
    output: list[str] = []
    for line in lines:
        if line.startswith(f"{key}="):
            output.append(f"{key}={str(slot.enabled).lower()}")
            updated = True
        else:
            output.append(line)

    if not updated:
        output.append(f"{key}={str(slot.enabled).lower()}")

    env_path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
    LOGGER.info("Persisted %s=%s to %s", key, slot.enabled, env_path)


def _load_slot(index: int) -> ReactionSlot:
    enabled = _parse_bool(os.getenv(f"SLOT_ENABLED_{index}", "true"), default=True)
    user_id = _parse_optional_int(os.getenv(f"TARGET_USER_ID_{index}"))
    role_id = _parse_optional_int(os.getenv(f"ROLE_ID_{index}"))
    emoji_id = _parse_optional_int(os.getenv(f"EMOJI_ID_{index}"))
    emoji_name = _clean(os.getenv(f"EMOJI_NAME_{index}"))

    return ReactionSlot(
        index=index,
        enabled=enabled,
        user_id=user_id,
        role_id=role_id,
        emoji_id=emoji_id,
        emoji_name=emoji_name,
    )


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off", ""}:
        return False
    raise ConfigError(f"Invalid boolean value: {value!r}")


def _parse_optional_int(value: str | None) -> int | None:
    cleaned = _clean(value)
    if cleaned is None:
        return None
    try:
        parsed = int(cleaned)
    except ValueError as exc:
        raise ConfigError(f"Invalid integer value: {value!r}") from exc
    if parsed <= 0:
        raise ConfigError(f"Expected a positive integer, got: {value!r}")
    return parsed


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None