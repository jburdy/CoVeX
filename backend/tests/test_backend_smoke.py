"""
Verifie que le backend FastAPI demarre et expose le payload de sante attendu.

Controle aussi que l'etat applicatif reste minimal au demarrage.
"""

from fastapi.testclient import TestClient

from main import app


def test_backend_starts_and_returns_bootstrap_status() -> None:
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "covex-backend-bootstrap"}


def test_bootstrap_is_stateless() -> None:
    forbidden_state_keys = {"db", "database", "cache", "redis", "session"}
    existing_state = set(vars(app.state).keys())

    assert forbidden_state_keys.isdisjoint(existing_state)
