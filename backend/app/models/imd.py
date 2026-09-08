"""
Pydantic Domain Models for IMD/NDMA Common Alerting Protocol (CAP) Integration.
Provides structured types for official government weather and flood alert evidence.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class IMDWarning(BaseModel):
    """
    Normalized representation of an official IMD/NDMA CAP warning.
    """
    warning_id: str = Field(..., description="Unique CAP alert identifier or GUID")
    source: str = Field(default="IMD/NDMA CAP", description="Authoritative warning provider")
    source_url: str = Field(..., description="URL of the CAP feed or individual alert document")
    issued_at: Optional[str] = Field(None, description="ISO timestamp when alert was issued/sent")
    effective_at: Optional[str] = Field(None, description="ISO timestamp when alert takes effect (onset)")
    expires_at: Optional[str] = Field(None, description="ISO timestamp when alert expires")
    event: Optional[str] = Field(None, description="Event title or hazard type (e.g. Extremely heavy rainfall)")
    severity: Optional[str] = Field(None, description="CAP severity level (Extreme, Severe, Moderate, Minor)")
    urgency: Optional[str] = Field(None, description="CAP urgency level (Immediate, Expected, Future, Past)")
    certainty: Optional[str] = Field(None, description="CAP certainty level (Observed, Likely, Possible, Unlikely)")
    headline: Optional[str] = Field(None, description="Brief summary headline of the warning")
    description: Optional[str] = Field(None, description="Detailed hazard advisory and meteorological summary")
    area_description: Optional[str] = Field(None, description="Affected geographic area description")
    affected_districts: List[str] = Field(default_factory=list, description="Districts matched in the warning")
    affected_states: List[str] = Field(default_factory=list, description="States or subdivisions matched")
    instruction: Optional[str] = Field(None, description="Recommended actions or safety directives from IMD")
    status: Optional[str] = Field(default="Actual", description="CAP message status (Actual, Exercise, Test)")
    retrieved_at: str = Field(..., description="ISO timestamp when APADA MITRA retrieved this warning")
    data_state: str = Field(
        default="REAL_LIVE_OFFICIAL",
        description="Provenance state: REAL_LIVE_OFFICIAL, CACHED_OFFICIAL, or UNAVAILABLE"
    )
    scope: str = Field(
        default="UNMATCHED",
        description="Geographic scope: DISTRICT, SUBDIVISION, STATE, or UNMATCHED"
    )


class IMDStatus(BaseModel):
    """
    Status of the IMD/NDMA CAP alert ingestion pipeline.
    """
    source: str = Field(default="IMD/NDMA CAP", description="Warning provider name")
    source_url: str = Field(
        default="https://cap-sources.s3.amazonaws.com/in-imd-en/rss.xml",
        description="Source feed URL"
    )
    data_state: str = Field(..., description="REAL_LIVE_OFFICIAL, CACHED_OFFICIAL, or UNAVAILABLE")
    last_successful_fetch: Optional[str] = Field(None, description="ISO timestamp of last successful retrieval")
    retrieved_at: str = Field(..., description="ISO timestamp of current status check")
    warning_count: int = Field(default=0, description="Total warnings parsed in current snapshot")
    active_warning_count: int = Field(default=0, description="Active unexpired warnings count")
    coverage: str = Field(
        default="India administrative warnings (District/Subdivision level)",
        description="Geographic coverage description"
    )
    error: Optional[str] = Field(None, description="Error message if fetch or parsing failed")


class IMDVillageWarningResponse(BaseModel):
    """
    Response model for village-level IMD warning queries.
    Clarifies that the warning is an authoritative district-level contextual evidence layer.
    """
    village_id: str = Field(..., description="Village identifier (e.g. VIL-001)")
    village_name: str = Field(..., description="Village name")
    district: str = Field(..., description="District name (e.g. Chamoli)")
    state: str = Field(..., description="State or sub-division name (e.g. Uttarakhand)")
    data_state: str = Field(..., description="REAL_LIVE_OFFICIAL, CACHED_OFFICIAL, or UNAVAILABLE")
    has_active_warning: bool = Field(default=False, description="True if any active warning covers this district")
    warnings: List[IMDWarning] = Field(default_factory=list, description="Applicable official warnings")
    evidence_context: str = Field(
        default="IMD official warnings provide district/subdivision contextual evidence. APADA MITRA combines this with 30m terrain physics for village decision support.",
        description="Methodological disclaimer on geographic resolution and multi-source fusion"
    )


class IMDDistrictWarningResponse(BaseModel):
    """
    Response model for district-level IMD warning queries.
    """
    district: str = Field(..., description="District name")
    data_state: str = Field(..., description="REAL_LIVE_OFFICIAL, CACHED_OFFICIAL, or UNAVAILABLE")
    has_active_warning: bool = Field(default=False)
    warnings: List[IMDWarning] = Field(default_factory=list)
    evidence_context: str = Field(
        default="Official IMD/NDMA warning at district/subdivision level.",
        description="Contextual note"
    )
