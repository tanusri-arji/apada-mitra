content = r'''"""
Official IMD/NDMA Common Alerting Protocol (CAP) Alert Feed Adapter.
Ingests real-time administrative-level weather and flash-flood warning evidence
from the authoritative public RSS/XML feed.
"""
import logging
import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

from app.adapters.base import DataSourceAdapter
from app.models.domain import NormalizedEnvironmentObservation, DataSourceState, DataQualityLevel
from app.models.imd import (
    IMDWarning,
    IMDStatus,
    IMDVillageWarningResponse,
    IMDDistrictWarningResponse,
)

logger = logging.getLogger(__name__)

CAP_FEED_URL = "https://cap-sources.s3.amazonaws.com/in-imd-en/rss.xml"
CACHE_TTL_SECONDS = 300  # 5 minutes cache TTL

# Known APADA MITRA monitored geographic entities
MONITORED_DISTRICTS = {
    "chamoli": ("Chamoli", "Uttarakhand"),
    "rudraprayag": ("Rudraprayag", "Uttarakhand"),
    "mandi": ("Mandi", "Himachal Pradesh"),
    "wayanad": ("Wayanad", "Kerala"),
    "pithoragarh": ("Pithoragarh", "Uttarakhand"),
    "uttarkashi": ("Uttarkashi", "Uttarakhand"),
    "tehri": ("Tehri Garhwal", "Uttarakhand"),
}

MONITORED_STATES = {
    "uttarakhand": "Uttarakhand",
    "himachal pradesh": "Himachal Pradesh",
    "kerala": "Kerala",
    "madhya pradesh": "Madhya Pradesh",
    "odisha": "Odisha",
    "jharkhand": "Jharkhand",
    "chhattisgarh": "Chhattisgarh",
    "uttar pradesh": "Uttar Pradesh",
}


class IMDCAPAdapter(DataSourceAdapter):
    """
    Adapter for official IMD/NDMA CAP RSS/XML alert feed.
    Provides authoritative macro warning evidence at district/subdivision level.
    """

    def __init__(self, feed_url: str = CAP_FEED_URL, timeout_seconds: float = 4.0):
        self._feed_url = feed_url
        self._timeout = timeout_seconds
        self._cached_warnings: List[IMDWarning] = []
        self._last_fetch_time: Optional[datetime] = None
        self._last_successful_fetch: Optional[datetime] = None
        self._last_error: Optional[str] = None
        self._last_data_state: str = "UNAVAILABLE"

    @property
    def name(self) -> str:
        return "IMD/NDMA CAP Alert Feed"

    @property
    def source_type(self) -> str:
        return "OFFICIAL_CAP_FEED"

    def fetch(self, latitude: float = 0.0, longitude: float = 0.0) -> Optional[Dict[str, Any]]:
        """
        Fetches live CAP RSS/XML from the official feed.
        Returns raw dictionary with feed data, or None if unreachable.
        """
        now = datetime.now(timezone.utc)

        # Check if cached data is still fresh within TTL
        if (
            self._cached_warnings
            and self._last_fetch_time
            and (now - self._last_fetch_time).total_seconds() < CACHE_TTL_SECONDS
        ):
            return {
                "raw_xml": None,
                "warnings": self._cached_warnings,
                "data_state": self._last_data_state,
                "cached": True,
            }

        req = urllib.request.Request(
            self._feed_url,
            headers={"User-Agent": "APADA-MITRA-Disaster-Intelligence/1.0 (Government Alert Ingestion)"},
        )

        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                if resp.status == 200:
                    raw_xml = resp.read().decode("utf-8", errors="replace")
                    self._last_fetch_time = now
                    self._last_successful_fetch = now
                    self._last_error = None
                    self._last_data_state = "REAL_LIVE_OFFICIAL"
                    parsed = self.parse_feed_xml(raw_xml, data_state="REAL_LIVE_OFFICIAL")
                    self._cached_warnings = parsed
                    return {
                        "raw_xml": raw_xml,
                        "warnings": parsed,
                        "data_state": "REAL_LIVE_OFFICIAL",
                        "cached": False,
                    }
                else:
                    self._last_error = f"HTTP {resp.status}"
        except urllib.error.HTTPError as e:
            logger.warning(f"IMD CAP HTTP error: {e.code} - {e.reason}")
            self._last_error = f"HTTP {e.code}: {e.reason}"
        except urllib.error.URLError as e:
            logger.warning(f"IMD CAP connection error: {e.reason}")
            self._last_error = f"Network Error: {e.reason}"
        except Exception as e:
            logger.warning(f"IMD CAP fetch exception: {e}")
            self._last_error = str(e)

        # On failure, fall back to cached warnings if available
        self._last_fetch_time = now
        if self._cached_warnings:
            self._last_data_state = "CACHED_OFFICIAL"
            # Update data_state on existing warnings
            for w in self._cached_warnings:
                w.data_state = "CACHED_OFFICIAL"
            return {
                "raw_xml": None,
                "warnings": self._cached_warnings,
                "data_state": "CACHED_OFFICIAL",
                "cached": True,
            }

        self._last_data_state = "UNAVAILABLE"
        return None

    def parse_feed_xml(self, xml_content: str, data_state: str = "REAL_LIVE_OFFICIAL") -> List[IMDWarning]:
        """
        Parses RSS XML or standalone CAP alert XML into normalized IMDWarning list.
        Safe against malformed XML and missing tags.
        """
        if not xml_content or not xml_content.strip():
            return []

        warnings: List[IMDWarning] = []
        retrieved_at = datetime.now(timezone.utc).isoformat()

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.warning(f"XML parse error in IMD CAP feed: {e}")
            self._last_error = f"Malformed XML: {e}"
            return []

        # Case 1: RSS 2.0 Feed containing multiple <item> tags
        if root.tag == "rss" or root.tag.endswith("rss"):
            channel = root.find("channel")
            items = channel.findall("item") if channel is not None else root.findall(".//item")

            for item in items:
                warning = self._parse_rss_item(item, retrieved_at, data_state)
                if warning:
                    warnings.append(warning)

        # Case 2: Standalone CAP 1.2 <alert> document
        elif "alert" in root.tag.lower():
            warning = self._parse_cap_alert(root, retrieved_at, data_state, self._feed_url)
            if warning:
                warnings.append(warning)

        return warnings

    def _parse_rss_item(self, item: ET.Element, retrieved_at: str, data_state: str) -> Optional[IMDWarning]:
        """Extracts an IMDWarning from an RSS item."""
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        guid = (item.findtext("guid") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()

        warning_id = guid or link or f"IMD-ALERT-{abs(hash(title + desc))}"
        
        # Match geographic scope from title and description
        districts, states, scope = self._match_geography(f"{title} {desc}")

        # Derive event and severity heuristics from title/desc if full CAP XML is not nested
        event = title if title else "Weather Warning"
        severity = "Severe" if ("extremely" in title.lower() or "extreme" in desc.lower()) else "Moderate"

        return IMDWarning(
            warning_id=warning_id,
            source="IMD/NDMA CAP",
            source_url=link or self._feed_url,
            issued_at=pub_date or retrieved_at,
            effective_at=pub_date,
            expires_at=None,
            event=event,
            severity=severity,
            urgency="Expected",
            certainty="Likely",
            headline=title,
            description=desc,
            area_description=", ".join(states + districts) if (states or districts) else "Regional",
            affected_districts=districts,
            affected_states=states,
            instruction=None,
            status="Actual",
            retrieved_at=retrieved_at,
            data_state=data_state,
            scope=scope,
        )

    def _parse_cap_alert(
        self, root: ET.Element, retrieved_at: str, data_state: str, source_url: str
    ) -> Optional[IMDWarning]:
        """Extracts an IMDWarning from a standard OASIS CAP 1.2 <alert> element."""
        # Strip namespace for robust tag matching
        def strip_ns(tag: str) -> str:
            return tag.split("}")[-1] if "}" in tag else tag

        identifier = ""
        sent = ""
        status = "Actual"

        for child in root:
            tag = strip_ns(child.tag).lower()
            if tag == "identifier":
                identifier = (child.text or "").strip()
            elif tag == "sent":
                sent = (child.text or "").strip()
            elif tag == "status":
                status = (child.text or "").strip()

        # Look for <info> block
        info_elem = None
        for child in root:
            if strip_ns(child.tag).lower() == "info":
                info_elem = child
                break

        event = None
        urgency = None
        severity = None
        certainty = None
        headline = None
        description = None
        instruction = None
        onset = None
        expires = None
        area_desc = None

        if info_elem is not None:
            for child in info_elem:
                tag = strip_ns(child.tag).lower()
                if tag == "event":
                    event = (child.text or "").strip()
                elif tag == "urgency":
                    urgency = (child.text or "").strip()
                elif tag == "severity":
                    severity = (child.text or "").strip()
                elif tag == "certainty":
                    certainty = (child.text or "").strip()
                elif tag == "headline":
                    headline = (child.text or "").strip()
                elif tag == "description":
                    description = (child.text or "").strip()
                elif tag == "instruction":
                    instruction = (child.text or "").strip()
                elif tag == "onset":
                    onset = (child.text or "").strip()
                elif tag == "expires":
                    expires = (child.text or "").strip()
                elif tag == "area":
                    for area_child in child:
                        if strip_ns(area_child.tag).lower() == "areadesc":
                            area_desc = (area_child.text or "").strip()

        text_for_matching = f"{headline or ''} {description or ''} {area_desc or ''} {event or ''}"
        districts, states, scope = self._match_geography(text_for_matching)

        return IMDWarning(
            warning_id=identifier or f"CAP-{abs(hash(source_url + (headline or '')))}",
            source="IMD/NDMA CAP",
            source_url=source_url,
            issued_at=sent or retrieved_at,
            effective_at=onset or sent,
            expires_at=expires,
            event=event or headline or "Weather Hazard",
            severity=severity or "Moderate",
            urgency=urgency or "Expected",
            certainty=certainty or "Likely",
            headline=headline or event or "IMD Warning",
            description=description,
            area_description=area_desc or ", ".join(states + districts),
            affected_districts=districts,
            affected_states=states,
            instruction=instruction,
            status=status,
            retrieved_at=retrieved_at,
            data_state=data_state,
            scope=scope,
        )

    def _match_geography(self, text: str) -> Tuple[List[str], List[str], str]:
        """
        Matches text against known districts and states using word boundaries.
        Returns (matched_districts, matched_states, scope).
        """
        if not text:
            return [], [], "UNMATCHED"

        matched_districts: List[str] = []
        matched_states: List[str] = []
        lower_text = text.lower()

        # 1. District Matching
        for key, (dist_name, state_name) in MONITORED_DISTRICTS.items():
            if re.search(r"\b" + re.escape(key) + r"\b", lower_text):
                if dist_name not in matched_districts:
                    matched_districts.append(dist_name)
                if state_name not in matched_states:
                    matched_states.append(state_name)

        # 2. State/Subdivision Matching
        for key, state_name in MONITORED_STATES.items():
            if re.search(r"\b" + re.escape(key) + r"\b", lower_text):
                if state_name not in matched_states:
                    matched_states.append(state_name)

        # Scope classification
        if matched_districts:
            scope = "DISTRICT"
        elif matched_states:
            scope = "SUBDIVISION"
        else:
            scope = "UNMATCHED"

        return matched_districts, matched_states, scope

    def get_status(self) -> IMDStatus:
        """Returns the current ingestion status metadata."""
        # Ensure at least one fetch has been attempted
        self.fetch()
        now_iso = datetime.now(timezone.utc).isoformat()
        last_succ = self._last_successful_fetch.isoformat() if self._last_successful_fetch else None

        active_count = len(self._cached_warnings)
        return IMDStatus(
            source="IMD/NDMA CAP",
            source_url=self._feed_url,
            data_state=self._last_data_state,
            last_successful_fetch=last_succ,
            retrieved_at=now_iso,
            warning_count=len(self._cached_warnings),
            active_warning_count=active_count,
            coverage="India administrative warnings (District/Subdivision level)",
            error=self._last_error,
        )

    def get_all_warnings(self) -> List[IMDWarning]:
        """Returns all currently parsed warnings."""
        self.fetch()
        return self._cached_warnings

    def get_warning_by_id(self, warning_id: str) -> Optional[IMDWarning]:
        """Returns a single warning matching warning_id or None."""
        self.fetch()
        for w in self._cached_warnings:
            if w.warning_id == warning_id or warning_id in w.warning_id:
                return w
        return None

    def get_warnings_for_district(self, district_name: str) -> IMDDistrictWarningResponse:
        """Returns warnings covering a specified district."""
        self.fetch()
        dist_lower = district_name.lower().strip()
        matched: List[IMDWarning] = []

        for w in self._cached_warnings:
            # Match directly in affected_districts or in full text
            in_districts = any(dist_lower in d.lower() for d in w.affected_districts)
            in_text = dist_lower in (w.headline or "").lower() or dist_lower in (w.description or "").lower()
            if in_districts or in_text:
                matched.append(w)

        return IMDDistrictWarningResponse(
            district=district_name,
            data_state=self._last_data_state,
            has_active_warning=len(matched) > 0,
            warnings=matched,
            evidence_context=f"Official IMD/NDMA warning for {district_name} district.",
        )

    def get_warnings_for_village(
        self, village_id: str, village_name: str, district: str, state: str = "Uttarakhand"
    ) -> IMDVillageWarningResponse:
        """
        Returns official warning evidence applicable to the village's district.
        Clearly labels the scope as DISTRICT-level contextual evidence.
        """
        self.fetch()
        dist_lower = district.lower().strip()
        state_lower = state.lower().strip()
        matched: List[IMDWarning] = []

        for w in self._cached_warnings:
            # Match district or state
            in_districts = any(dist_lower in d.lower() for d in w.affected_districts)
            in_states = any(state_lower in s.lower() for s in w.affected_states)
            in_text = (
                dist_lower in (w.headline or "").lower()
                or dist_lower in (w.description or "").lower()
                or state_lower in (w.description or "").lower()
            )
            if in_districts or (in_states and not w.affected_districts) or in_text:
                matched.append(w)

        return IMDVillageWarningResponse(
            village_id=village_id,
            village_name=village_name,
            district=district,
            state=state,
            data_state=self._last_data_state,
            has_active_warning=len(matched) > 0,
            warnings=matched,
            evidence_context=(
                f"Official IMD/NDMA warning covers {district} district. "
                "APADA MITRA uses this as macro-regional evidence fused with 30m terrain physics for village assessment."
            ),
        )

    def normalize(
        self, raw_payload: Dict[str, Any], latitude: float, longitude: float
    ) -> NormalizedEnvironmentObservation:
        """
        Normalizes CAP observation state into NormalizedEnvironmentObservation.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        return NormalizedEnvironmentObservation(
            latitude=latitude,
            longitude=longitude,
            observation_timestamp=now_iso,
            current_rainfall_mm_hr=None,
            forecast_rainfall_24h_mm=None,
            soil_saturation_pct=None,
            river_water_level_m=None,
            discharge_cumecs=None,
            source_name=self.name,
            source_type=self.source_type,
            source_timestamp=now_iso,
            data_state=(
                DataSourceState.LIVE if self._last_data_state == "REAL_LIVE_OFFICIAL" else DataSourceState.CACHED
            ),
            quality_status=DataQualityLevel.GOOD if self._cached_warnings else DataQualityLevel.WARNING,
            freshness_seconds=0.0,
            missing_fields=[],
            validation_warnings=[],
        )


# Singleton instance for application use
imd_cap_adapter_instance = IMDCAPAdapter()
'''

with open('app/adapters/imd_cap_adapter.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('app/adapters/imd_cap_adapter.py' + " restored successfully, length:", len(content))
