"""
Verifie que les erreurs backend sont journalisees et exposees au playground.

Controle les erreurs metier, les indisponibilites d'inference et les erreurs de validation HTTP.
"""

from __future__ import annotations

import io
import logging

from fastapi.testclient import TestClient

import analysis
from analysis_profiles_config import AnalysisProfileRuntime
from main import create_app


def _capture_app_console(monkeypatch) -> io.StringIO:
    stream = io.StringIO()
    app_logger = logging.getLogger("covex.app")
    for handler in app_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            monkeypatch.setattr(handler, "stream", stream)
    return stream


def _stub_context() -> analysis.ResolvedAnalysisContext:
    return analysis.ResolvedAnalysisContext(
        profile=AnalysisProfileRuntime(
            profile_id="profil-test",
            prompt_text="Prompt",
            criterion_ids=["critere-a"],
            criterion_weights={"critere-a": 1.0},
            le_few_shot=[],
            inference_engine_key="engine-from-profile",
        ),
        inference_engine_key="engine-journalise",
    )


def test_post_analyze_returns_not_found_with_logged_warning(monkeypatch) -> None:
    client = TestClient(create_app())
    console_stream = _capture_app_console(monkeypatch)

    def stub_analyze_text(**_kwargs: object) -> analysis.AnalysisResult:
        raise analysis.ProfileNotFoundError("Profil introuvable: profil-test")

    monkeypatch.setattr(analysis, "_resolve_analysis_context", lambda **_kwargs: _stub_context())
    monkeypatch.setattr(analysis, "analyze_text", stub_analyze_text)

    response = client.post("/analyze", json={"text": "Bonjour", "profile_id": "profil-test"})
    console_output = console_stream.getvalue()

    assert response.status_code == 404
    assert response.json() == {"detail": "Profil introuvable: profil-test"}
    assert "Analyze rejected: Profil introuvable: profil-test" in console_output


def test_post_analyze_returns_service_unavailable_with_logged_warning(monkeypatch) -> None:
    client = TestClient(create_app())
    console_stream = _capture_app_console(monkeypatch)

    def stub_analyze_text(**_kwargs: object) -> analysis.AnalysisResult:
        raise analysis.AnalysisServiceUnavailableError("Inference unavailable")

    monkeypatch.setattr(analysis, "_resolve_analysis_context", lambda **_kwargs: _stub_context())
    monkeypatch.setattr(analysis, "analyze_text", stub_analyze_text)

    response = client.post("/analyze", json={"text": "Bonjour", "profile_id": "profil-test"})
    console_output = console_stream.getvalue()

    assert response.status_code == 503
    assert response.json() == {"detail": "Inference unavailable"}
    assert "Analyze unavailable: Inference unavailable" in console_output


def test_post_analyze_logs_request_validation_errors(monkeypatch) -> None:
    client = TestClient(create_app())
    console_stream = _capture_app_console(monkeypatch)

    response = client.post("/analyze", json={"text": "Bonjour"})
    console_output = console_stream.getvalue()

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Requete invalide: verifiez les champs obligatoires et leur format."
    }
    assert "Request validation failed for POST /analyze" in console_output


def test_post_analyze_logs_caller_profile_and_engine(monkeypatch) -> None:
    client = TestClient(create_app())
    console_stream = _capture_app_console(monkeypatch)

    def stub_resolve_analysis_context(**_kwargs: object) -> analysis.ResolvedAnalysisContext:
        return _stub_context()

    def stub_analyze_text(**_kwargs: object) -> analysis.AnalysisResult:
        return analysis.AnalysisResult(
            score=100,
            decision="OK",
            justification="Completude satisfaisante.",
            profile_used="profil-test",
        )

    monkeypatch.setattr(analysis, "_resolve_analysis_context", stub_resolve_analysis_context)
    monkeypatch.setattr(analysis, "analyze_text", stub_analyze_text)

    response = client.post(
        "/analyze",
        json={"text": "Bonjour", "profile_id": "profil-test"},
        headers={"x-forwarded-for": "203.0.113.10, 10.0.0.5"},
    )
    console_output = console_stream.getvalue()

    assert response.status_code == 200
    assert (
        "Analyze request: caller=203.0.113.10 profile=profil-test inference_engine=engine-journalise"
        in console_output
    )
