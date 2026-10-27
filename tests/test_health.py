"""Health, error envelope, correlation id, and OpenAPI tests."""

from __future__ import annotations

from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from silent_cinema.deps import get_database
from sqlalchemy.exc import SQLAlchemyError


class Echo(BaseModel):
    name: str


class HealthyDatabase:
    def ping(self) -> None:
        return None


class BrokenDatabase:
    def ping(self) -> None:
        raise SQLAlchemyError("connection refused")


def _install_probe_routes(app: FastAPI) -> None:
    @app.post("/api/v1/_test/echo")
    def echo(payload: Echo) -> Echo:
        return payload

    @app.get("/api/v1/_test/boom")
    def boom() -> None:
        raise RuntimeError("internal detail that must never reach the client")


def test_liveness_returns_version(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}
    UUID(response.headers["X-Request-ID"])


def test_request_id_is_preserved_when_safe(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "client-request-123"})
    assert response.headers["X-Request-ID"] == "client-request-123"


def test_invalid_request_id_is_replaced(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "bad id with spaces"})
    generated = response.headers["X-Request-ID"]
    assert generated != "bad id with spaces"
    UUID(generated)


def test_readiness_reports_ok(client: TestClient, app: FastAPI) -> None:
    app.dependency_overrides[get_database] = lambda: HealthyDatabase()
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}


def test_readiness_returns_503_when_database_fails(client: TestClient, app: FastAPI) -> None:
    app.dependency_overrides[get_database] = lambda: BrokenDatabase()
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "database": "unavailable"}
    UUID(response.headers["X-Request-ID"])


def test_unknown_route_uses_error_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "Resource not found."
    assert body["error"]["details"] == []
    assert body["error"]["request_id"] == response.headers["X-Request-ID"]


def test_method_not_allowed_uses_error_envelope(client: TestClient) -> None:
    response = client.post("/api/v1/health")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_validation_error_uses_error_envelope(app: FastAPI) -> None:
    _install_probe_routes(app)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/api/v1/_test/echo", json={"unexpected": True})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"]


def test_malformed_json_returns_400(app: FastAPI) -> None:
    _install_probe_routes(app)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/v1/_test/echo",
            content=b'{"name": ',
            headers={"Content-Type": "application/json"},
        )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "bad_request"


def test_unhandled_error_is_safe(app: FastAPI) -> None:
    _install_probe_routes(app)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/v1/_test/boom")
    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "internal_error"
    assert body["error"]["message"] == "An internal error occurred."
    assert "internal detail" not in response.text
    assert "Traceback" not in response.text


def test_openapi_is_served(client: TestClient) -> None:
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["version"] == "0.1.0"
    assert "/api/v1/health" in schema["paths"]
    assert "/api/v1/health/ready" in schema["paths"]
    assert "HealthResponse" in schema["components"]["schemas"]
    assert "ReadinessResponse" in schema["components"]["schemas"]
    assert "ErrorEnvelope" in schema["components"]["schemas"]


@pytest.mark.parametrize("path", ["/api/v1/health", "/api/v1/health/ready"])
def test_health_paths_are_documented(client: TestClient, path: str) -> None:
    schema = client.get("/api/v1/openapi.json").json()
    assert path in schema["paths"]
