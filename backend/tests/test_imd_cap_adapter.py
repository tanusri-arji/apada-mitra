"""
Automated Test Suite for Official IMD/NDMA CAP Alert Ingestion Adapter.
Covers XML parsing, network error resilience, caching, geographic matching,
data provenance states, and API endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.adapters.imd_cap_adapter import IMDCAPAdapter
from app.models.imd import IMDWarning, IMDStatus

SAMPLE_VALID_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Latest alerts from India Meteorological Department</title>
    <link>https://cap-sources.s3.amazonaws.com/in-imd-en/rss.xml</link>
    <item>
      <title>Extremely heavy rainfall warning for Chamoli and Rudraprayag</title>
      <link>https://cap-sources.s3.amazonaws.com/in-imd-en/2026-09-03-01.xml</link>
      <description>Heavy to very heavy rainfall likely over Chamoli district of Uttarakhand.</description>
      <guid>urn:oid:2.49.0.1.356.0.2026.9.3.1</guid>
      <pubDate>Thu, 03 Sep 2026 07:21:21 +0000</pubDate>
    </item>
    <item>
      <title>Heavy rainfall warning for Mandi district</title>
      <link>https://cap-sources.s3.amazonaws.com/in-imd-en/2026-09-03-02.xml</link>
      <description>Moderate to heavy rain expected in Mandi, Himachal Pradesh.</description>
      <guid>urn:oid:2.49.0.1.356.0.2026.9.3.2</guid>
      <pubDate>Thu, 03 Sep 2026 07:19:24 +0000</pubDate>
    </item>
  </channel>
</rss>
"""

SAMPLE_STANDALONE_CAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<cap:alert xmlns:cap="urn:oasis:names:tc:emergency:cap:1.2">
  <cap:identifier>urn:oid:2.49.0.1.356.0.2026.9.3.7.21.21</cap:identifier>
  <cap:sender>rainfallnwfc@gmail.com</cap:sender>
  <cap:sent>2026-09-03T12:51:21+05:30</cap:sent>
  <cap:status>Actual</cap:status>
  <cap:msgType>Alert</cap:msgType>
  <cap:scope>Public</cap:scope>
  <cap:info>
    <cap:language>en</cap:language>
    <cap:category>Met</cap:category>
    <cap:event>Extremely heavy rainfall</cap:event>
    <cap:urgency>Expected</cap:urgency>
    <cap:severity>Severe</cap:severity>
    <cap:certainty>Likely</cap:certainty>
    <cap:onset>2026-09-03T07:00:00+05:30</cap:onset>
    <cap:expires>2026-09-04T07:00:00+05:30</cap:expires>
    <cap:headline>Heavy to extremely heavy rainfall over Chamoli</cap:headline>
    <cap:description>Extremely heavy rainfall over Chamoli, Uttarakhand.</cap:description>
    <cap:instruction>Avoid low lying areas and road underpasses.</cap:instruction>
    <cap:area>
      <cap:areaDesc>Chamoli, Uttarakhand</cap:areaDesc>
    </cap:area>
  </cap:info>
</cap:alert>
"""

SAMPLE_UNMATCHED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Isolated rain in coastal region</title>
      <link>https://cap-sources.s3.amazonaws.com/in-imd-en/2026-09-03-99.xml</link>
      <description>Scattered showers across Lakshadweep islands.</description>
      <guid>urn:oid:2.49.0.1.356.0.2026.9.3.99</guid>
      <pubDate>Thu, 03 Sep 2026 08:00:00 +0000</pubDate>
    </item>
  </channel>
</rss>
"""


@pytest.fixture
def test_client():
    return TestClient(app)


def test_valid_rss_xml_parsing():
    adapter = IMDCAPAdapter()
    warnings = adapter.parse_feed_xml(SAMPLE_VALID_RSS_XML, data_state="REAL_LIVE_OFFICIAL")
    assert len(warnings) == 2
    assert warnings[0].warning_id == "urn:oid:2.49.0.1.356.0.2026.9.3.1"
    assert "Chamoli" in warnings[0].affected_districts
    assert "Uttarakhand" in warnings[0].affected_states
    assert warnings[0].scope == "DISTRICT"
    assert warnings[0].data_state == "REAL_LIVE_OFFICIAL"

    assert warnings[1].warning_id == "urn:oid:2.49.0.1.356.0.2026.9.3.2"
    assert "Mandi" in warnings[1].affected_districts
    assert "Himachal Pradesh" in warnings[1].affected_states


def test_standalone_cap_xml_parsing():
    adapter = IMDCAPAdapter()
    warnings = adapter.parse_feed_xml(SAMPLE_STANDALONE_CAP_XML, data_state="REAL_LIVE_OFFICIAL")
    assert len(warnings) == 1
    w = warnings[0]
    assert w.warning_id == "urn:oid:2.49.0.1.356.0.2026.9.3.7.21.21"
    assert w.event == "Extremely heavy rainfall"
    assert w.severity == "Severe"
    assert "Chamoli" in w.affected_districts
    assert w.instruction == "Avoid low lying areas and road underpasses."
    assert w.scope == "DISTRICT"


def test_malformed_xml_handling():
    adapter = IMDCAPAdapter()
    malformed = "<rss><channel><item><title>Unclosed"
    warnings = adapter.parse_feed_xml(malformed, data_state="REAL_LIVE_OFFICIAL")
    assert warnings == []
    assert adapter._last_error is not None
    assert "Malformed XML" in adapter._last_error


def test_empty_feed_handling():
    adapter = IMDCAPAdapter()
    warnings = adapter.parse_feed_xml("", data_state="REAL_LIVE_OFFICIAL")
    assert warnings == []


def test_unmatched_geography_scope():
    adapter = IMDCAPAdapter()
    warnings = adapter.parse_feed_xml(SAMPLE_UNMATCHED_XML, data_state="REAL_LIVE_OFFICIAL")
    assert len(warnings) == 1
    assert warnings[0].scope == "UNMATCHED"
    assert len(warnings[0].affected_districts) == 0


def test_live_provenance_on_success():
    adapter = IMDCAPAdapter()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = SAMPLE_VALID_RSS_XML.encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = adapter.fetch()
        assert res is not None
        assert res["data_state"] == "REAL_LIVE_OFFICIAL"
        assert len(res["warnings"]) == 2

        status = adapter.get_status()
        assert status.data_state == "REAL_LIVE_OFFICIAL"
        assert status.warning_count == 2
        assert status.error is None


def test_cached_provenance_on_network_failure():
    adapter = IMDCAPAdapter()
    # Populate cache first
    adapter._cached_warnings = adapter.parse_feed_xml(SAMPLE_VALID_RSS_XML, data_state="REAL_LIVE_OFFICIAL")
    adapter._last_fetch_time = None  # Force re-fetch

    # Simulate network failure
    with patch("urllib.request.urlopen", side_effect=Exception("Connection timed out")):
        res = adapter.fetch()
        assert res is not None
        assert res["data_state"] == "CACHED_OFFICIAL"
        assert res["cached"] is True
        assert len(res["warnings"]) == 2

        status = adapter.get_status()
        assert status.data_state == "CACHED_OFFICIAL"
        assert "Connection timed out" in (status.error or "")


def test_unavailable_state_when_uninitialized_and_network_fails():
    adapter = IMDCAPAdapter()
    adapter._cached_warnings = []
    adapter._last_fetch_time = None

    with patch("urllib.request.urlopen", side_effect=Exception("Host unreachable")):
        res = adapter.fetch()
        assert res is None
        status = adapter.get_status()
        assert status.data_state == "UNAVAILABLE"
        assert status.warning_count == 0


def test_village_warning_lookup():
    adapter = IMDCAPAdapter()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = SAMPLE_VALID_RSS_XML.encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    with patch("urllib.request.urlopen", return_value=mock_resp):
        # Chamoli village
        res = adapter.get_warnings_for_village(
            village_id="VIL-001",
            village_name="Pipalkoti",
            district="Chamoli",
            state="Uttarakhand"
        )
        assert res.village_id == "VIL-001"
        assert res.district == "Chamoli"
        assert res.has_active_warning is True
        assert len(res.warnings) >= 1
        assert "macro-regional evidence" in res.evidence_context

        # Unaffected district
        res_unaffected = adapter.get_warnings_for_village(
            village_id="VIL-999",
            village_name="Test Village",
            district="Wayanad",
            state="Kerala"
        )
        assert res_unaffected.has_active_warning is False


def test_api_imd_status_endpoint(test_client):
    response = test_client.get("/api/imd/status")
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "IMD/NDMA CAP"
    assert data["source_url"] == "https://cap-sources.s3.amazonaws.com/in-imd-en/rss.xml"
    assert data["data_state"] in ["REAL_LIVE_OFFICIAL", "CACHED_OFFICIAL", "UNAVAILABLE"]
    assert "coverage" in data


def test_api_imd_warnings_endpoint(test_client):
    response = test_client.get("/api/imd/warnings")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_imd_villages_endpoint(test_client):
    response = test_client.get("/api/imd/villages/VIL-001")
    assert response.status_code == 200
    data = response.json()
    assert data["village_id"] == "VIL-001"
    assert data["village_name"] == "Pipalkoti"
    assert "evidence_context" in data
    assert "warnings" in data



def test_api_imd_districts_endpoint(test_client):
    response = test_client.get("/api/imd/districts/Chamoli")
    assert response.status_code == 200
    data = response.json()
    assert data["district"] == "Chamoli"
    assert "evidence_context" in data
