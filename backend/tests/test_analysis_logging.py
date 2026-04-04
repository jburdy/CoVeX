"""
Verifie la creation des logs bee pour les analyses hors production.

Controle que la trace bee est forcee tant que `APP_ENV` n'est pas `production`.
"""

from __future__ import annotations

import importlib
from pathlib import Path

analysis = importlib.import_module("analysis")
settings = importlib.import_module("settings")


class _StubInferenceAdapter:
    def infer(self, **kwargs: object) -> dict[str, object]:
        return {
            "covered_elements": ["article"],
            "missing_elements": ["quantite_explicite"],
            "latency_sec": 0.25,
            "model_used": "stub-model",
            "extractions": [{"criterion_id": "article", "text": "ecran"}],
            "trace": {
                "inference_engine_type": "remote",
                "endpoint": "https://example.test/v1/chat/completions",
                "model": "stub-model",
                "coverage_item_prompt": "Criteres de test",
                "llm_instruction_sent": "Instruction envoyee au modele",
                "raw_inference_engine_response_keys": ["choices", "usage"],
                "raw_inference_engine_response": {"id": "resp_123"},
                "visualization_html": {
                    "available": True,
                    "path": "artifacts/langextract_html/example.html",
                },
                "llm_response_received": {
                    "covered_elements": ["article"],
                    "missing_elements": ["quantite_explicite"],
                    "coverage_ratio": 0.25,
                },
                "extraction_result": [{"criterion_id": "article", "text": "ecran"}],
            },
        }


def test_analyze_text_writes_bee_log_outside_production(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("COVEX_PROMPT_TRACE_ENABLED", "false")
    monkeypatch.setattr(settings, "_project_root", lambda: tmp_path)

    result = analysis.analyze_text(
        text="Demande d'achat d'un ecran 27 pouces, quantite 1.",
        profile_id="demandes_achat",
        inference_adapter=_StubInferenceAdapter(),
    )

    assert result.profile_used == "demandes_achat"

    bee_logs = list(
        (tmp_path / "logs").glob("bee-*-remote_groq_llama31_8b_instant-demandes_achat.log")
    )
    assert len(bee_logs) == 1

    content = bee_logs[0].read_text(encoding="utf-8")

    assert "=== Analyze Exchange Start" in content
    assert "analysis_profile: demandes_achat" in content
    assert "inference_engine_type: remote" in content
    assert "raw_inference_engine_response_keys:" in content
    assert '"choices"' in content
    assert "visualization_html:" in content
    assert "artifacts/langextract_html/example.html" in content
    assert "llm_response_received:" in content
    assert '"coverage_ratio": 0.25' in content
    assert "extraction_result:" in content
    assert '"criterion_id": "article"' in content
    assert "normalized_analysis_summary:" in content
    assert '"model_used": "stub-model"' in content
    assert "=== Analyze Exchange End ===" in content


def test_analyze_text_can_skip_bee_log_in_production(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("COVEX_PROMPT_TRACE_ENABLED", "false")
    monkeypatch.setattr(settings, "_project_root", lambda: tmp_path)

    analysis.analyze_text(
        text="Demande d'achat d'un ecran 27 pouces, quantite 1.",
        profile_id="demandes_achat",
        inference_adapter=_StubInferenceAdapter(),
    )

    assert not list((tmp_path / "logs").glob("bee-*.log"))
