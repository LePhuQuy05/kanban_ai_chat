from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_root_returns_html() -> None:
    client = TestClient(create_app())
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Frontend build not found" in response.text


def test_hello_api_returns_message() -> None:
    client = TestClient(create_app())
    response = client.get("/api/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from FastAPI"}
