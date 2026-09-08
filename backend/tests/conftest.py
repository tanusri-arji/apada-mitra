"""
Pytest configuration for APADA MITRA backend tests.
Ensures deterministic, fast test execution without hanging on external API network delays.
"""
import pytest
import urllib.request
import urllib.error


@pytest.fixture(autouse=True)
def fast_external_requests(monkeypatch):
    """
    Patches urllib.request.urlopen during test execution to ensure fast, deterministic tests.
    External public APIs (Open-Meteo, Open-Elevation, IMD CAP) immediately raise URLError
    to trigger adapter/pipeline fallback instantly (0ms) unless explicitly mocked by individual unit tests.
    """
    orig_urlopen = urllib.request.urlopen

    def fast_urlopen(req, *args, **kwargs):
        url = req.fullurl if isinstance(req, urllib.request.Request) else str(req)

        # Bypass external network calls instantly during automated test runs
        if any(domain in url for domain in ["api.open-meteo.com", "open-elevation", "ndma.gov.in", "s3.amazonaws.com"]):
            raise urllib.error.URLError("Fast test network bypass - trigger fallback")

        return orig_urlopen(req, *args, **kwargs)

    monkeypatch.setattr(urllib.request, "urlopen", fast_urlopen)
