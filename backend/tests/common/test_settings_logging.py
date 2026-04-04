"""
Verifie la configuration de journalisation exposee par `settings`.

Controle le nommage des fichiers de traces et l'attachement du handler de rotation.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import settings


class _FixedDate:
    @staticmethod
    def today() -> date:
        return date(2026, 3, 7)


def test_get_prompt_trace_logger_uses_profile_and_date_in_filename(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "date", _FixedDate)
    monkeypatch.setattr(settings, "_project_root", lambda: tmp_path)

    trace_logger = settings.get_prompt_trace_logger(
        profile_name="KYC Premium / V2",
        inference_engine_name="local_qwen35",
    )

    assert len(trace_logger.handlers) == 1
    handler = trace_logger.handlers[0]
    assert Path(handler.baseFilename).name == "bee-26-03-07-local_qwen35-kyc-premium-v2.log"


def test_prompt_trace_logging_flag_can_disable_trace_files(monkeypatch) -> None:
    monkeypatch.setenv("COVEX_PROMPT_TRACE_ENABLED", "false")
    monkeypatch.setenv("APP_ENV", "production")

    assert settings.is_prompt_trace_enabled() is False
    assert settings.should_emit_prompt_trace() is False


def test_non_production_always_emits_prompt_trace(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("COVEX_PROMPT_TRACE_ENABLED", "false")

    assert settings.should_emit_prompt_trace() is True
