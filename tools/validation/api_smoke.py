#!/usr/bin/env python3
"""
Lance un smoke test HTTP du backend CoVeX avec quelques appels representatifs.

Execution depuis la racine du projet:
- `uv run --project backend python tools/validation/api_smoke.py`
- `--brain-engine` force un moteur envoye dans tous les `POST /analyze`.
- `--startup-timeout` change le delai d'attente du backend si le script doit le demarrer.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import TextIO
from urllib import error, request

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.validation.backend_runner import (
    BASE_URL,
    is_backend_ready,
    start_backend,
    stop_backend,
    wait_backend_ready,
)

LOGS_DIR = ROOT_DIR / "logs"

RESET = "\033[0m"
BLUE = "\033[34m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BOLD = "\033[1m"

ANALYZE_CASES = [
    (
        "tickets_support_it",
        "Ticket: erreur 0x80070005 sur poste Windows 11, utilisateur Marc Dupont, urgence haute.",
    ),
    (
        "demandes_devis_construction",
        "Demande devis: extension maison 45 m2, budget 120000 EUR, delai souhaite septembre 2026, plans fournis par l'architecte.",
    ),
    (
        "rapports_chantier",
        "Rapport chantier Residence Atlas: avancement 60%, incident retard livraison beton, prochaine etape pose charpente lundi prochain.",
    ),
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke test du backend CoVeX avec backend reel."
    )
    parser.add_argument(
        "--brain-engine",
        default=None,
        help="Force un inference_engine pour tous les POST /analyze (ex: remote_google_gemini25_flash).",
    )
    parser.add_argument(
        "--startup-timeout",
        type=float,
        default=30.0,
        help="Timeout de demarrage du backend en secondes.",
    )
    return parser.parse_args()


def _colorize(color: str, icon: str, message: str) -> str:
    return f"{color}{icon} {message}{RESET}"


def _print_info(message: str) -> None:
    print(_colorize(BLUE, "[i]", message))


def _print_success(message: str) -> None:
    print(_colorize(GREEN, "[OK]", message))


def _print_warning(message: str) -> None:
    print(_colorize(YELLOW, "[!]", message))


def _print_error(message: str) -> None:
    print(_colorize(RED, "[KO]", message))


def _backend_log_path() -> Path:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return LOGS_DIR / f"api_smoke_backend_{timestamp}.log"


def _start_backend_with_log() -> tuple[subprocess.Popen[str], Path, TextIO]:
    log_path = _backend_log_path()
    log_handle = log_path.open("w", encoding="utf-8")
    backend = start_backend(stdout=log_handle, stderr=subprocess.STDOUT)
    return backend, log_path, log_handle


def _request_json(
    method: str, path: str, body: dict[str, object] | None = None
) -> tuple[int, dict]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = request.Request(
        f"{BASE_URL}{path}",
        method=method,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=20) as response:  # nosec B310
            raw_payload = response.read().decode("utf-8")
            payload = json.loads(raw_payload) if raw_payload else {}
            if not isinstance(payload, dict):
                raise RuntimeError(
                    f"Unexpected JSON payload for {method} {path}: {payload!r}"
                )
            return response.status, payload
    except error.HTTPError as exc:
        raw_payload = exc.read().decode("utf-8")
        payload = json.loads(raw_payload) if raw_payload else {}
        if not isinstance(payload, dict):
            payload = {"detail": raw_payload}
        return exc.code, payload



def _assert_root() -> None:
    status, payload = _request_json("GET", "/")
    assert status == 200, payload
    assert payload.get("status") == "ok", payload


def _build_analyze_payload(
    *, profile_id: str, text: str, inference_engine: str | None
) -> dict[str, object]:
    payload: dict[str, object] = {"text": text, "profile_id": profile_id}
    if inference_engine is not None:
        payload["inference_engine"] = inference_engine
    return payload


def _assert_analyze(
    profile_id: str, text: str, *, inference_engine: str | None
) -> None:
    status, payload = _request_json(
        "POST",
        "/analyze",
        _build_analyze_payload(
            profile_id=profile_id, text=text, inference_engine=inference_engine
        ),
    )
    assert status == 200, payload
    assert payload.get("profile_used") == profile_id, payload
    assert payload.get("decision") in {"KO", "PARTIEL", "OK"}, payload
    assert isinstance(payload.get("score"), int), payload
    assert isinstance(payload.get("justification"), str), payload
    assert isinstance(payload.get("model_used"), str), payload


def _assert_missing_prompt_rejected() -> None:
    status, payload = _request_json(
        "POST",
        "/analyze",
        {"text": "Ticket IT: erreur BSOD sur poste Windows 11"},
    )
    assert status == 400, payload
    detail = str(payload.get("detail", ""))
    assert (
        "contexte" in detail.lower()
        or "profile_id" in detail.lower()
        or "requete invalide" in detail.lower()
    ), payload


def _assert_unknown_prompt_rejected() -> None:
    status, payload = _request_json(
        "POST",
        "/analyze",
        {"text": "Texte de test", "profile_id": "inexistant"},
    )
    assert status == 404, payload
    assert "introuvable" in str(payload.get("detail", "")).lower(), payload


def _read_backend_output_tail(
    log_path: Path, *, max_lines: int = 60
) -> tuple[str, int, int]:
    if not log_path.exists():
        return "", 0, 0
    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return "", 0, 0

    if not lines:
        return "", 0, 0

    tail_lines = lines[-max_lines:]
    return "\n".join(tail_lines), len(tail_lines), len(lines)


def main() -> int:
    args = _parse_args()
    engine_label = args.brain_engine or "profile-default"
    print(f"{BOLD}CoVeX API smoke test{RESET}")
    _print_info(f"inference_engine={engine_label}")

    backend: subprocess.Popen[str] | None = None
    backend_log_path: Path | None = None
    backend_log_handle: TextIO | None = None
    backend_started_by_script = False

    if is_backend_ready():
        _print_info("Using existing backend on http://127.0.0.1:8000")
    else:
        _print_info("Starting backend on http://127.0.0.1:8000")
        backend, backend_log_path, backend_log_handle = _start_backend_with_log()
        backend_started_by_script = True
        _print_info(f"Backend log file: {backend_log_path}")

    try:
        if backend is not None:
            wait_backend_ready(backend, timeout_sec=args.startup_timeout)
        else:
            _assert_root()

        _assert_root()
        _print_success("GET /")

        for profile_id, text in ANALYZE_CASES:
            _assert_analyze(profile_id, text, inference_engine=args.brain_engine)
            _print_success(f"POST /analyze [{profile_id}] via {engine_label}")

        _assert_missing_prompt_rejected()
        _print_success("POST /analyze rejects missing profile_id")

        _assert_unknown_prompt_rejected()
        _print_success("POST /analyze rejects unknown profile_id")
        _print_info(f"App logs: {LOGS_DIR}")
        return 0
    except Exception as exc:
        _print_error(str(exc))
        return 1
    finally:
        if backend_started_by_script and backend is not None:
            stop_backend(backend)

        if backend_log_handle is not None and not backend_log_handle.closed:
            backend_log_handle.flush()
            backend_log_handle.close()

        backend_output = ""
        displayed_lines = 0
        total_lines = 0
        if backend_log_path is not None:
            backend_output, displayed_lines, total_lines = _read_backend_output_tail(
                backend_log_path
            )
            backend_output = backend_output.strip()

        if backend_output:
            if displayed_lines < total_lines:
                _print_warning(
                    f"Backend output (last {displayed_lines}/{total_lines} lines):"
                )
            else:
                _print_warning("Backend output:")
            print(backend_output)


if __name__ == "__main__":
    raise SystemExit(main())
