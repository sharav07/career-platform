"""Tests for the Privacy page, footer link, and consent-gated analytics."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.routes import templates


def make_client(tmp_path: Path) -> TestClient:
    seed = Path(__file__).parent / "fixtures" / "resume_fixture.json"
    return TestClient(create_app(tmp_path / "missing.db", seed))


@pytest.fixture
def analytics_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(templates.env.globals, "ga_measurement_id", "")


@pytest.fixture
def analytics_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(templates.env.globals, "ga_measurement_id", "G-TEST123456")


def test_privacy_page_loads(tmp_path: Path, analytics_off: None) -> None:
    response = make_client(tmp_path).get("/privacy")

    assert response.status_code == 200
    assert "How this site handles your data" in response.text


def test_footer_links_to_privacy_page(tmp_path: Path, analytics_off: None) -> None:
    response = make_client(tmp_path).get("/")

    # The database is missing in this test, so the page is degraded (503) but still has the footer.
    assert response.status_code == 503
    assert 'href="http://testserver/privacy"' in response.text or 'href="/privacy"' in response.text


def test_analytics_off_sends_nothing_to_google(tmp_path: Path, analytics_off: None) -> None:
    client = make_client(tmp_path)
    page = client.get("/").text
    privacy = client.get("/privacy").text

    assert "googletagmanager" not in page
    assert "consent-banner" not in page
    assert "analytics.js" not in page
    assert "does not currently use analytics" in privacy


def test_analytics_on_shows_banner_but_never_inlines_google_script(
    tmp_path: Path, analytics_on: None
) -> None:
    page = make_client(tmp_path).get("/").text

    assert 'data-ga-id="G-TEST123456"' in page
    assert 'id="consent-banner"' in page
    assert 'id="consent-accept"' in page
    assert 'id="consent-decline"' in page
    assert 'id="consent-reopen"' in page
    # The Google script may only be added by analytics.js after the visitor accepts.
    assert "googletagmanager" not in page
    assert page.count("analytics.js") == 1


def test_privacy_page_describes_analytics_when_on(tmp_path: Path, analytics_on: None) -> None:
    privacy = make_client(tmp_path).get("/privacy").text

    assert "Google Analytics" in privacy
    assert "Nothing is sent to Google" in privacy
    assert "Privacy choices" in privacy


def test_analytics_script_is_served_and_gates_on_consent(tmp_path: Path) -> None:
    response = make_client(tmp_path).get("/static/analytics.js")

    assert response.status_code == 200
    script = response.text
    # The Google URL appears only inside the loader that runs after Accept.
    assert script.count("googletagmanager.com/gtag/js") == 1
    assert 'saveChoice("granted")' in script
    assert 'saveChoice("denied")' in script


def test_footer_shows_hosting_note(tmp_path: Path, analytics_off: None) -> None:
    response = make_client(tmp_path).get("/")

    assert "Served from Railway with PostgreSQL." in response.text
