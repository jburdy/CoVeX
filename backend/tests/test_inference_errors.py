"""Verifie les messages d'erreur d'inference exposes par l'API backend."""

import importlib
from pathlib import Path

import langextract as lx
from langextract.providers.ollama import OllamaLanguageModel

inference = importlib.import_module("inference")
BrainEngineConfig = inference.BrainEngineConfig
CoVeXOllamaLanguageModel = inference.CoVeXOllamaLanguageModel
_save_visualization_html = inference._save_visualization_html
_describe_inference_failure = inference._describe_inference_failure
_normalize_openai_base_url = inference._normalize_openai_base_url
_resolve_engine_credential = inference._resolve_engine_credential


def test_describe_inference_failure_includes_timeout_details_for_local_ollama() -> None:
    engine = BrainEngineConfig(
        type="local",
        model="qwen3.5:9b",
        base_url="http://127.0.0.1:11434",
        timeout_sec=120,
    )

    message = _describe_inference_failure(
        engine,
        RuntimeError("Ollama API error: Ollama Model timed out (timeout=120, num_threads=None)"),
    )

    assert "local:qwen3.5:9b" in message
    assert "120 s" in message
    assert "timed out" in message


def test_describe_inference_failure_suggests_pulling_missing_ollama_model() -> None:
    engine = BrainEngineConfig(
        type="local",
        model="qwen3.5:9b",
        base_url="http://127.0.0.1:11434",
    )

    message = _describe_inference_failure(
        engine,
        RuntimeError("Can't find Ollama qwen3.5:9b. Try: ollama run qwen3.5:9b"),
    )

    assert "introuvable" in message
    assert "ollama run qwen3.5:9b" in message


def test_covex_ollama_model_uses_thinking_field_when_response_is_empty(monkeypatch) -> None:
    model = CoVeXOllamaLanguageModel(model_id="qwen3.5:9b")

    def stub_query(self, *_args, **_kwargs):
        del self
        return {"response": "", "thinking": '{"extractions": []}'}

    monkeypatch.setattr(OllamaLanguageModel, "_ollama_query", stub_query)

    response = model._ollama_query(prompt="Bonjour")

    assert response["response"] == '{"extractions": []}'


def test_resolve_engine_credential_supports_covex_google_alias(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("COVEX_GOOGLE_API_KEY", "google-secret")
    engine = BrainEngineConfig(
        type="remote",
        model="gemini-2.5-flash",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        auth_env_var="GOOGLE_API_KEY",
    )

    credential = _resolve_engine_credential(engine)

    assert credential == "google-secret"


def test_normalize_openai_base_url_adds_openrouter_api_suffix() -> None:
    assert _normalize_openai_base_url("https://openrouter.ai") == "https://openrouter.ai/api/v1"
    assert (
        _normalize_openai_base_url("https://openrouter.ai/api/v1") == "https://openrouter.ai/api/v1"
    )


def test_save_visualization_html_writes_langextract_artifact(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(_save_visualization_html.__globals__, "_project_root", lambda: tmp_path)
    doc = lx.data.AnnotatedDocument(
        text="Demande d'achat d'un ecran 27 pouces.",
        extractions=[
            lx.data.Extraction(
                extraction_class="covered_criterion",
                extraction_text="ecran 27 pouces",
                char_interval=lx.data.CharInterval(start_pos=19, end_pos=35),
                attributes={"criterion_id": "article"},
            )
        ],
    )

    artifact_path = _save_visualization_html(
        doc=doc,
        analysis_profile_name="demandes_achat",
        inference_engine_key="remote_groq_llama31_8b_instant",
    )

    assert artifact_path is not None
    assert artifact_path.parent == tmp_path / "artifacts" / "langextract_html"
    assert artifact_path.exists()

    content = artifact_path.read_text(encoding="utf-8")

    assert "ecran 27 pouces" in content
    assert "lx-animated-wrapper" in content
