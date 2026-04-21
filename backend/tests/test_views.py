from backend.app.views import build_root_html


def test_build_root_html_contains_api_hook() -> None:
    html = build_root_html()
    assert "Hello World" in html
    assert 'id="load-api"' in html
    assert "/api/hello" in html
