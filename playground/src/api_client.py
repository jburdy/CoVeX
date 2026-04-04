"""
Client HTTP minimal pour appeler l'API backend CoVeX depuis le playground.

Usage:
- Module importe par `playground/src/playground.py` pour charger les profils et lancer
  `POST /analyze`.
- Reutilise par les tests playground pour simuler et verifier les echanges HTTP.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, cast
from urllib import error, request


DEFAULT_API_TIMEOUT_SEC = 120


@dataclass(frozen=True)
class AnalyzeResult:
    score: int
    decision: str
    justification: str
    profile_used: str
    latency_sec: float | None = None
    model_used: str | None = None
    covered_elements: tuple[str, ...] = ()
    missing_elements: tuple[str, ...] = ()
    extractions: tuple[dict, ...] = ()


class ApiClientError(RuntimeError):
    def __init__(
        self, message: str, *, status_code: int | None = None, raw_message: str | None = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.raw_message = raw_message


class ApiClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        timeout_sec: float = DEFAULT_API_TIMEOUT_SEC,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_sec = timeout_sec

    def analyze(
        self,
        *,
        text: str,
        profile_id: str,
        inference_engine: str | None = None,
    ) -> AnalyzeResult:
        body: dict[str, Any] = {"text": text, "profile_id": profile_id}
        if inference_engine:
            body["inference_engine"] = inference_engine

        payload = self._request_json("POST", "/analyze", body)
        return AnalyzeResult(
            score=payload.get("score", 0),
            decision=payload.get("decision", "KO"),
            justification=payload.get("justification", ""),
            profile_used=payload.get("profile_used", profile_id),
            latency_sec=payload.get("latency_sec"),
            model_used=payload.get("model_used"),
            covered_elements=tuple(payload.get("covered_elements", [])),
            missing_elements=tuple(payload.get("missing_elements", [])),
            extractions=tuple(payload.get("extractions", [])),
        )

    def _request(self, method: str, path: str, body: dict | None = None) -> object:
        url = f"{self._base_url}{path}"
        data = json.dumps(body).encode("utf-8") if body else None
        headers = {"Content-Type": "application/json"} if body else {}
        req = request.Request(url, method=method, headers=headers, data=data)
        try:
            with request.urlopen(req, timeout=self._timeout_sec) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise ApiClientError(
                f"API {method} failed for {path}",
                status_code=exc.code,
                raw_message=_extract_http_error_message(exc),
            ) from exc
        except Exception as exc:
            raise ApiClientError(
                f"API {method} failed for {path}",
                raw_message=_extract_request_error_message(exc),
            ) from exc

    def _request_json(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        return cast(Any, self._request(method, path, body))


def _extract_http_error_message(exc: error.HTTPError) -> str | None:
    try:
        payload = json.loads(exc.read().decode("utf-8"))
    except Exception:
        return None

    detail = payload.get("detail")
    if isinstance(detail, str) and detail.strip():
        return detail.strip()
    return None


def _extract_request_error_message(exc: Exception) -> str | None:
    message = str(exc).strip()
    if not message:
        return None

    lowered = message.lower()
    if "timed out" in lowered or "timeout" in lowered:
        return "Le playground a attendu trop peu longtemps la reponse du backend local. Reessayez."

    return message
