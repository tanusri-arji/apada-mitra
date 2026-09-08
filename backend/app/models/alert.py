"""
Feature 11: Real-Time Multi-Hazard Alert Generation & Notification Intelligence Models.
Defines schemas for multi-hazard alerts, severity classifications, multilingual messages,
delivery statuses, lifecycle state transitions, and auditable alert records.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertLifecycleState(str, Enum):
    NEW = "NEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"


class HazardType(str, Enum):
    FLASH_FLOOD = "FLASH_FLOOD"
    LANDSLIDE = "LANDSLIDE"
    RIVER_LEVEL = "RIVER_LEVEL"
    HEAVY_RAINFALL = "HEAVY_RAINFALL"
    ROAD_ACCESS = "ROAD_ACCESS"
    SHELTER_SAFETY = "SHELTER_SAFETY"
    MULTI_HAZARD = "MULTI_HAZARD"


class DeliveryStatus(str, Enum):
    NOT_DELIVERED = "NOT_DELIVERED"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    PENDING = "PENDING"


class DeliveryMode(str, Enum):
    SIMULATION = "SIMULATION"
    LOCAL_DASHBOARD = "LOCAL_DASHBOARD"
    SMS_SIMULATION = "SMS_SIMULATION"
    EMAIL_SIMULATION = "EMAIL_SIMULATION"
    EXTERNAL_PROVIDER_UNAVAILABLE = "EXTERNAL_PROVIDER_UNAVAILABLE"


class AlertDataState(str, Enum):
    REAL_LIVE_INPUT = "REAL_LIVE_INPUT"
    ESTIMATED_FROM_LIVE_DATA = "ESTIMATED_FROM_LIVE_DATA"
    CACHED = "CACHED"
    OFFLINE_DEMO = "OFFLINE_DEMO"
    UNKNOWN = "UNKNOWN"


class MultilingualAlertText(BaseModel):
    """
    Equivalent structured disaster alert messages in 5 regional/official languages
    specifically suited for Uttarakhand Himalayan terrain and communities.
    """
    en: str = Field(..., description="English alert notification (Officials, Responders, Technical, Tourists)")
    hi: str = Field(..., description="Hindi (हिन्दी) alert notification (Broad Emergency Communication)")
    garhwali: str = Field(..., description="Garhwali (गढ़वाली) alert notification (Local Garhwal Communities)")
    kumaoni: str = Field(..., description="Kumaoni (कुमाऊँनी) alert notification (Uttarakhand Regional Support)")
    nepali: str = Field(..., description="Nepali (नेपाली) alert notification (Nepali-speaking Communities & Workers)")
    gar: Optional[str] = Field(None, description="Garhwali short alias")
    kum: Optional[str] = Field(None, description="Kumaoni short alias")
    ne: Optional[str] = Field(None, description="Nepali short alias")


class AlertAuditRecord(BaseModel):
    """
    Audit trail entry for tracking alert lifecycle events.
    """
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    alert_id: str
    village_id: str
    action: str = Field(..., description="Event action, e.g. ALERT_GENERATED, ACKNOWLEDGED, ESCALATED, RESOLVED")
    previous_state: Optional[str] = None
    new_state: str
    reason: str
    actor: str = Field("SYSTEM", description="Actor performing action (SYSTEM or Operator ID)")
    source: str = Field("APADA_MITRA_ALERT_ENGINE", description="Originating subsystem")


class MultiHazardAlertRecord(BaseModel):
    """
    Complete Multi-Hazard Alert Object with full situational awareness.
    """
    alert_id: str = Field(..., description="Unique alert identifier")
    village_id: str
    village_name: str
    generated_at: str
    severity: AlertSeverity
    lifecycle_state: AlertLifecycleState = Field(AlertLifecycleState.NEW)
    primary_hazard: HazardType
    secondary_hazards: List[HazardType] = Field(default_factory=list)
    hazards_detected: List[HazardType] = Field(default_factory=list)
    risk_score: float = Field(..., ge=0.0, le=100.0)
    risk_level: str
    reason: str
    key_contributing_factors: List[str] = Field(default_factory=list)
    recommended_action: str
    evacuation_required: bool
    
    # Evacuation & Shelter Context (Features 6, 9, 10)
    selected_shelter_id: Optional[str] = None
    selected_shelter_name: Optional[str] = None
    route_summary: Optional[str] = None
    lead_time: Optional[Dict[str, Any]] = None
    evacuation_context: Optional[Dict[str, Any]] = None
    
    # Provenance & Delivery
    confidence: float = Field(100.0, ge=0.0, le=100.0)
    data_state: AlertDataState = Field(AlertDataState.OFFLINE_DEMO)
    delivery_status: DeliveryStatus = Field(DeliveryStatus.NOT_DELIVERED)
    delivery_mode: DeliveryMode = Field(DeliveryMode.SIMULATION)
    messages: MultilingualAlertText
    associated_incident_id: Optional[str] = None
    fingerprint: str = Field(..., description="Deterministic fingerprint for deduplication")


class AlertStatusResponse(BaseModel):
    """
    Summary status of the Alert Generation and Notification Subsystem.
    """
    total_alerts_count: int
    active_alerts_count: int
    acknowledged_count: int
    escalated_count: int
    resolved_count: int
    delivery_mode: DeliveryMode
    provider_status: str
    supported_languages: List[str]
    disclaimer: str


class AlertDeliveryStatusResponse(BaseModel):
    """
    Honest delivery status breakdown for an alert.
    """
    alert_id: str
    delivery_status: DeliveryStatus
    delivery_mode: DeliveryMode
    channels: Dict[str, str]
    explanation: str
    disclaimer: str
