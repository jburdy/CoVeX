"""
Utilitaires partages pour demarrer, verifier et arreter le backend CoVeX.

Usage:
- Module importe par `tools/validation/api_smoke.py` et `tools/evaluation/run_dataset_evaluation.py`.
- Centralise le lancement `uvicorn`, l'attente de disponibilite et l'arret du processus backend.
"""

from __future__ import annotations

import json
import signal
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib import request

ROOT_DIR = Path(__file__).resolve().parents[2]
BASE_URL = "http://127.0.0.1:8000"


def is_backend_ready(*, base_url: str = BASE_URL) -> bool:
    """Retourne True si le backend repond a `GET /` avec un statut sain."""
    try:
        req = request.Request(f"{base_url}/", method="GET")
        with request.urlopen(req, timeout=2) as response:  # nosec B310
            payload = json.loads(response.read().decode("utf-8"))
            return response.status == 200 and payload.get("status") == "ok"
    except Exception:
        return False


def start_backend(
    *,
    root_dir: Path = ROOT_DIR,
    stdout: Any = subprocess.DEVNULL,
    stderr: Any = subprocess.STDOUT,
) -> subprocess.Popen[str]:
    """Demarre le backend via `uv run ... uvicorn` et retourne le processus."""
    cmd = [
        "uv",
        "run",
        "--project",
        "backend",
        "uvicorn",
        "main:app",
        "--app-dir",
        "backend/src",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]
    return subprocess.Popen(
        cmd,
        cwd=str(root_dir),
        stdout=stdout,
        stderr=stderr,
        text=True,
        bufsize=1,
    )


def wait_backend_ready(
    process: subprocess.Popen[str],
    *,
    timeout_sec: float = 30.0,
    base_url: str = BASE_URL,
) -> None:
    """Attend que le backend reponde ou echoue si `timeout_sec` est depasse."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Backend process exited before becoming ready")
        if is_backend_ready(base_url=base_url):
            return
        time.sleep(0.3)
    raise RuntimeError("Backend not ready within timeout")


def stop_backend(
    process: subprocess.Popen[str],
    *,
    graceful_timeout: float = 8.0,
    kill_timeout: float = 3.0,
) -> None:
    """Arrete le backend avec SIGINT puis SIGKILL si necessaire."""
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=graceful_timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=kill_timeout)
