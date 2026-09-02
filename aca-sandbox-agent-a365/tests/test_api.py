from fastapi.testclient import TestClient

from app.main import create_app


def test_health_and_browser_make_mode_clear(settings):
    with TestClient(create_app(settings)) as client:
        health = client.get("/health")
        auth_config = client.get("/api/auth/config")
        page = client.get("/")
        docs = client.get("/docs")

    assert health.status_code == 200
    assert health.json() == {
        "status": "ok",
        "mode": "offline",
        "live_integrations_ready": False,
    }
    assert page.status_code == 200
    assert docs.status_code == 404
    assert "OFFLINE FIXTURE MODE" in page.text
    assert auth_config.status_code == 200
    assert auth_config.json() == {
        "enabled": False,
        "tenant_id": None,
        "spa_client_id": None,
        "authority": None,
        "api_audience": None,
        "api_scope": None,
        "msal_browser_cdn_url": None,
    }
