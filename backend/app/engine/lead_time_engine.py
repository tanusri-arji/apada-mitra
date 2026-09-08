"""
Operational Lead-Time & Evacuation Window Engine for APADA MITRA.
Calculates actionable evacuation lead times, community mobilization requirements,
and safety margins to support emergency operational decisions.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.models.domain import ScenarioType, DataSourceState, DataQualityStatus
from app.models.lead_time import (
    VillageLeadTimeDetail,
    LeadTimeDecisionStatus,
    LeadTimeDataState,
)
from app.data_pipeline import pipeline_instance
from app.engine.risk_engine import calculate_flash_flood_risk
from app.engine.shelter_engine import recommend_safest_shelter

# ==============================================================================
# CONFIGURATION CONSTANTS (All thresholds & parameters consolidated in one block)
# ==============================================================================
DEFAULT_PREPARATION_TIME_MINUTES: float = 25.0    # Standard community mobilization & vulnerable alert duration
SAFE_SAFETY_MARGIN_MINUTES: float = 60.0          # Minimum surplus margin required for SAFE evacuation status
CRITICAL_ACTION_RISK_THRESHOLD: float = 75.0      # Multi-hazard risk score triggering immediate evacuation
HIGH_ACTION_RISK_THRESHOLD: float = 50.0          # Multi-hazard risk score triggering high alert & staging
MAX_OPERATIONAL_FORECAST_WINDOW_MINUTES: float = 720.0  # 12-hour maximum operational forecasting window
FALLBACK_TRAVEL_TIME_MINUTES: float = 35.0        # Default mountain travel time when routing cannot resolve


class LeadTimeEngine:
    """
    Central operational lead-time calculation engine.
    Estimates actionable evacuation windows from live/forecast hydro-meteorological data,
    Dijkstra road routing travel times, and community mobilization parameters.
    """

    def calculate_village_lead_time(
        self,
        village_data: Dict[str, Any],
        scenario: ScenarioType = ScenarioType.HEAVY_RAIN,
        force_offline: bool = False,
        custom_forecast_rainfall: Optional[float] = None,
        custom_current_rainfall: Optional[float] = None,
        force_missing_forecast: bool = False,
    ) -> VillageLeadTimeDetail:
        """
        Computes operational evacuation lead time and safety margin for a specific village.
        """
        village_id = village_data.get("id", "UNKNOWN")
        village_name = village_data.get("name", "Unknown Village")
        now_iso = datetime.now(timezone.utc).isoformat()
        assumptions: List[str] = []

        # 1. Geographic Coordinate Validation
        try:
            lat = float(village_data.get("latitude", 0.0))
            lon = float(village_data.get("longitude", 0.0))
        except (ValueError, TypeError):
            lat, lon = 999.0, 999.0

        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0) or abs(lat) > 89.0 or abs(lon) > 179.0:
            return VillageLeadTimeDetail(
                village_id=village_id,
                village_name=village_name,
                calculated_at=now_iso,
                current_risk_score=0.0,
                current_risk_level="UNKNOWN",
                hazard_escalation_estimate_minutes=None,
                evacuation_time_minutes=0.0,
                preparation_time_minutes=DEFAULT_PREPARATION_TIME_MINUTES,
                total_required_time_minutes=DEFAULT_PREPARATION_TIME_MINUTES,
                available_lead_time_minutes=None,
                safety_margin_minutes=None,
                decision_status=LeadTimeDecisionStatus.UNKNOWN,
                confidence=0.0,
                calculation_method="INVALID_GEOGRAPHIC_COORDINATES",
                data_state=LeadTimeDataState.UNKNOWN,
                assumptions=["Coordinates are out of physical geographic bounds."],
            )

        # 2. Environmental Observation & Risk Feature Snapshot
        obs = pipeline_instance.get_normalized_observation(
            latitude=lat,
            longitude=lon,
            location_key=village_id,
            scenario=scenario,
            force_offline=force_offline,
        )

        snapshot = pipeline_instance.convert_to_risk_feature_snapshot(
            obs=obs,
            village_static_data=village_data,
            scenario=scenario,
        )

        if custom_current_rainfall is not None:
            snapshot["current_rainfall"] = custom_current_rainfall
        if custom_forecast_rainfall is not None:
            snapshot["forecast_rainfall"] = custom_forecast_rainfall
        if force_missing_forecast:
            snapshot["forecast_rainfall"] = None
            snapshot["feature_statuses"]["forecast_rainfall"] = DataQualityStatus.MISSING

        # 3. Multi-Hazard Risk Computation
        risk_res = calculate_flash_flood_risk(snapshot)
        current_risk_score = risk_res["flash_flood_risk_score"]
        current_risk_level = risk_res["risk_level"].value

        # 4. Evacuation Travel Time via Hazard-Aware Routing Engine
        preparation_time = DEFAULT_PREPARATION_TIME_MINUTES
        assumptions.append(f"Standard community mobilization time: {preparation_time:.0f} minutes.")

        route_accessible = True
        try:
            shelter_rec = recommend_safest_shelter(village_id=village_id, scenario=scenario)
            travel_time = float(shelter_rec.route.estimated_travel_time_mins)
            dest_name = shelter_rec.recommended_shelter.name
            assumptions.append(
                f"Destination shelter: {dest_name} via {shelter_rec.route.total_distance_km:.1f}km route "
                f"(Dijkstra travel time: {travel_time:.0f} mins, Route Safety: {shelter_rec.route.route_safety_score:.0f}%)."
            )
        except Exception as e:
            route_accessible = False
            travel_time = FALLBACK_TRAVEL_TIME_MINUTES
            assumptions.append(
                f"No fully safe open route to designated relief shelters ({e}). "
                f"Fallback estimate of {travel_time:.0f} mins applied; vertical evacuation/shelter-in-place advised."
            )

        total_required_time = round(preparation_time + travel_time, 1)

        # 5. Lead Time & Hazard Escalation Estimation
        forecast_val = snapshot.get("forecast_rainfall")
        curr_rf_val = snapshot.get("current_rainfall", 0.0) or 0.0
        fc_status = snapshot.get("feature_statuses", {}).get("forecast_rainfall", DataQualityStatus.OK)

        # Check for missing/unknown forecast
        if forecast_val is None or fc_status == DataQualityStatus.MISSING or force_missing_forecast:
            available_lead_time = None
            hazard_escalation_mins = None
            safety_margin = None
            decision_status = LeadTimeDecisionStatus.UNKNOWN
            calc_method = "UNKNOWN — INSUFFICIENT OR MISSING FORECAST DATA"
            data_state = LeadTimeDataState.UNKNOWN
            confidence = max(10.0, risk_res["confidence"] - 35.0)
            assumptions.append(
                "Forecast precipitation data is missing or unverified. Scientific lead-time estimate cannot be derived."
            )
        else:
            calc_method = "OPERATIONAL_THRESHOLD_CROSSING_ESTIMATE"
            
            # Map Data State
            if obs.data_state in [DataSourceState.LIVE, DataSourceState.LIVE_IOT_SENSOR, DataSourceState.LIVE_EXTERNAL_API]:
                data_state = LeadTimeDataState.ESTIMATED_FROM_LIVE_DATA
            elif obs.data_state == DataSourceState.CACHED:
                data_state = LeadTimeDataState.CACHED
            else:
                data_state = LeadTimeDataState.OFFLINE_DEMO

            confidence = risk_res["confidence"]
            if data_state == LeadTimeDataState.OFFLINE_DEMO:
                confidence = max(10.0, confidence - 15.0)
            if not route_accessible:
                confidence = max(10.0, confidence - 15.0)

            # Operational Time-to-Threshold Logic
            if current_risk_score >= CRITICAL_ACTION_RISK_THRESHOLD:
                # Critical condition already active
                hazard_escalation_mins = 0.0
                available_lead_time = 0.0
                assumptions.append("Current multi-hazard risk is at or above the CRITICAL action threshold (>=75.0). Immediate action required.")
            elif current_risk_score >= HIGH_ACTION_RISK_THRESHOLD:
                # High risk active (50 to 74.99): compute time to reach 75.0 based on rainfall intensity
                hourly_intensity = max(10.0, curr_rf_val)
                score_delta = CRITICAL_ACTION_RISK_THRESHOLD - current_risk_score
                # Escalation minutes proportional to remaining points over intensity factor
                escalate_mins = round(max(15.0, (score_delta / (hourly_intensity * 0.45)) * 60.0), 1)
                hazard_escalation_mins = min(MAX_OPERATIONAL_FORECAST_WINDOW_MINUTES, escalate_mins)
                available_lead_time = hazard_escalation_mins
                assumptions.append(
                    f"Hazard is approaching critical threshold ({current_risk_score:.1f}/100). "
                    f"Estimated escalation window to >=75.0 is {available_lead_time:.0f} mins based on {curr_rf_val:.1f} mm/h rain."
                )
            else:
                # Moderate/Low risk (<50): ample buffer under current forecast
                if forecast_val > 150.0:
                    hazard_escalation_mins = 240.0  # 4 hours
                else:
                    hazard_escalation_mins = 360.0  # 6 hours
                available_lead_time = hazard_escalation_mins
                assumptions.append(
                    f"Current risk is within manageable bounds ({current_risk_score:.1f}/100). "
                    f"Estimated operational window before potential threshold breach is {available_lead_time:.0f} mins."
                )

            # Compute Safety Margin
            safety_margin = round(available_lead_time - total_required_time, 1)

            # Determine Decision Status
            if not route_accessible:
                decision_status = LeadTimeDecisionStatus.INSUFFICIENT
            elif safety_margin >= SAFE_SAFETY_MARGIN_MINUTES:
                decision_status = LeadTimeDecisionStatus.SAFE
            elif safety_margin >= 0.0:
                decision_status = LeadTimeDecisionStatus.TIGHT
            else:
                decision_status = LeadTimeDecisionStatus.INSUFFICIENT

        # Mandatory Operational Disclaimer
        assumptions.append(
            "DISCLAIMER: This calculation provides operational emergency evacuation decision-support based on "
            "meteorological thresholds, mobilization buffers, and road graph travel times. It is NOT an exact hydrodynamic "
            "flood-wave propagation model."
        )

        return VillageLeadTimeDetail(
            village_id=village_id,
            village_name=village_name,
            calculated_at=now_iso,
            current_risk_score=current_risk_score,
            current_risk_level=current_risk_level,
            hazard_escalation_estimate_minutes=hazard_escalation_mins,
            evacuation_time_minutes=travel_time,
            preparation_time_minutes=preparation_time,
            total_required_time_minutes=total_required_time,
            available_lead_time_minutes=available_lead_time,
            safety_margin_minutes=safety_margin,
            decision_status=decision_status,
            confidence=round(confidence, 1),
            calculation_method=calc_method,
            data_state=data_state,
            assumptions=assumptions,
        )


# Global Singleton Lead-Time Engine Instance
lead_time_engine_instance = LeadTimeEngine()
