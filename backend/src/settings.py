"""
Infrastructure transversale du backend: chargement de `.env` et configuration des logs.

Usage:
- Module importe par `backend/src/main.py` au demarrage de l'API.
- Reutilise par `backend/src/analysis.py` et `backend/src/inference.py` pour acceder aux logs
  applicatifs et a l'environnement du projet.
"""

from __future__ import annotations

import logging
import os
from datetime import date
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from pathlib import Path

TRACE_LOGGER_NAME = "covex.prompt_trace"
APP_LOGGER_NAME = "covex.app"
PROMPT_TRACE_ENABLED_ENV = "COVEX_PROMPT_TRACE_ENABLED"
APP_ENV_ENV = "APP_ENV"
PRODUCTION_ENV = "production"

_LOGGING_CONFIGURED = False
_ENV_LOADED = False
_ENV_PATH: Path | None = None

logger = logging.getLogger(__name__)


def ensure_project_env_loaded() -> Path | None:
    global _ENV_LOADED, _ENV_PATH

    if _ENV_LOADED:
        return _ENV_PATH

    env_path = _find_project_env_file()
    if env_path is None:
        _ENV_LOADED = True
        logger.info("No .env file found in project parents")
        return None

    loaded_count = 0
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if (
            (value.startswith('"') and value.endswith('"'))
            or (value.startswith("'") and value.endswith("'"))
        ) and len(value) >= 2:
            value = value[1:-1]

        if key not in os.environ:
            os.environ[key] = value
            loaded_count += 1

    _ENV_LOADED = True
    _ENV_PATH = env_path
    logger.info("Loaded environment variables from %s (count=%d)", env_path, loaded_count)
    return env_path


def get_loaded_env_path() -> Path | None:
    return _ENV_PATH


def _find_project_env_file() -> Path | None:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / ".env"
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def configure_logging() -> None:
    global _LOGGING_CONFIGURED

    if _LOGGING_CONFIGURED:
        return

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )
    _configure_prompt_trace_logger(level=level)
    _configure_app_logger(level=level)
    logger.info(
        "Prompt trace logging enabled=%s (app_env=%s, env_flag=%s)",
        should_emit_prompt_trace(),
        get_app_env(),
        is_prompt_trace_enabled(),
    )

    _LOGGING_CONFIGURED = True


def _configure_prompt_trace_logger(*, level: int) -> None:
    trace_logger = logging.getLogger(TRACE_LOGGER_NAME)
    trace_logger.handlers.clear()
    trace_logger.setLevel(level)
    trace_logger.propagate = False


def is_prompt_trace_enabled() -> bool:
    return _read_bool_env(PROMPT_TRACE_ENABLED_ENV, default=True)


def get_app_env() -> str:
    raw_value = os.getenv(APP_ENV_ENV, "development").strip().lower()
    return raw_value or "development"


def should_emit_prompt_trace() -> bool:
    if get_app_env() != PRODUCTION_ENV:
        return True
    return is_prompt_trace_enabled()


def get_prompt_trace_logger(
    *, profile_name: str | None, inference_engine_name: str | None
) -> logging.Logger:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    today = date.today().strftime("%y-%m-%d")
    profile_slug = _slugify_log_component(profile_name or "inline-prompt")
    inference_engine_slug = _slugify_log_component(inference_engine_name or "unknown-brain-engine")
    logger_name = f"{TRACE_LOGGER_NAME}.{inference_engine_slug}.{profile_slug}.{today}"
    trace_logger = logging.getLogger(logger_name)
    expected_path = _project_root() / "logs" / f"bee-{today}-{inference_engine_slug}-{profile_slug}.log"

    if getattr(trace_logger, "_covex_prompt_trace_path", None) == str(expected_path):
        trace_logger.setLevel(level)
        return trace_logger

    trace_logger.handlers.clear()
    trace_logger.setLevel(level)
    trace_logger.propagate = False

    logs_dir = expected_path.parent
    logs_dir.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        expected_path,
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", "%Y-%m-%d %H:%M:%S"))
    trace_logger.addHandler(handler)
    setattr(trace_logger, "_covex_prompt_trace_path", str(expected_path))
    return trace_logger


def _configure_app_logger(*, level: int) -> None:
    app_logger = logging.getLogger(APP_LOGGER_NAME)
    app_logger.handlers.clear()
    app_logger.setLevel(level)
    app_logger.propagate = False

    stream_handler = StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    )
    app_logger.addHandler(stream_handler)

    logs_dir = _project_root() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        logs_dir / f"app-{date.today().isoformat()}.log",
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    )
    app_logger.addHandler(handler)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _read_bool_env(name: str, *, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _slugify_log_component(value: str) -> str:
    slug = "".join(
        character if character.isalnum() or character in {"-", "_"} else "-"
        for character in value.strip().lower()
    )
    slug = "-".join(part for part in slug.split("-") if part)
    return slug or "inline-prompt"
