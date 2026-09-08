"""
Feature 11: Notification Provider Adapter Interface & Simulation Provider for APADA MITRA.
Provides extensible notification architecture with zero external service dependencies.
Strictly enforces simulation delivery status (never falsely claims real SMS/WhatsApp/broadcast delivery).
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.models.alert import (
    MultiHazardAlertRecord,
    DeliveryStatus,
    DeliveryMode,
    AlertDeliveryStatusResponse,
)


class NotificationProvider(ABC):
    """
    Abstract interface for emergency notification providers (e.g. Government SMS Gateways, CAP-CP, Simulation).
    """

    @abstractmethod
    def prepare_alert_payload(self, alert: MultiHazardAlertRecord) -> Dict[str, Any]:
        """Prepares channel payloads without sending."""
        pass

    @abstractmethod
    def get_delivery_status(self, alert: MultiHazardAlertRecord) -> AlertDeliveryStatusResponse:
        """Returns delivery status for the given alert."""
        pass


class SimulationNotificationProvider(NotificationProvider):
    """
    Zero-cost local simulation provider.
    Prepares SMS, email, and dashboard payloads for testing and local display.
    Guarantees honest NOT_DELIVERED external status.
    """

    def __init__(self):
        self.provider_name = "APADA_MITRA_LOCAL_SIMULATION_GATEWAY"

    def prepare_alert_payload(self, alert: MultiHazardAlertRecord) -> Dict[str, Any]:
        """
        Formats structured alert messages for multiple simulated communication channels.
        """
        sms_preview_en = f"APADA MITRA ALERT [{alert.severity.value}]: {alert.village_name} - {alert.primary_hazard.value}. Action: {alert.recommended_action}. Shelter: {alert.selected_shelter_name or 'N/A'}"
        sms_preview_hi = f"आपदा मित्र चेतावनी [{alert.severity.value}]: {alert.village_name} - {alert.primary_hazard.value}। कार्रवाई: {alert.recommended_action}।"
        sms_preview_gar = f"आपदा मित्र चेतावनी [{alert.severity.value}]: {alert.village_name} - {alert.primary_hazard.value}। सुरक्षित ठौर: {alert.selected_shelter_name or 'N/A'}।"
        sms_preview_kum = f"आपदा मित्र चेतावनी [{alert.severity.value}]: {alert.village_name} - {alert.primary_hazard.value}। सुरक्षित थान: {alert.selected_shelter_name or 'N/A'}।"
        sms_preview_ne = f"आपदा मित्र चेतावनी [{alert.severity.value}]: {alert.village_name} - {alert.primary_hazard.value}। सुरक्षित आश्रय: {alert.selected_shelter_name or 'N/A'}।"

        return {
            "sms_payload": {
                "en": sms_preview_en[:160],
                "hi": sms_preview_hi[:160],
                "garhwali": sms_preview_gar[:160],
                "kumaoni": sms_preview_kum[:160],
                "nepali": sms_preview_ne[:160],
                "char_length_en": len(sms_preview_en[:160]),
            },
            "dashboard_payload": {
                "title": f"{alert.severity.value} Multi-Hazard Alert: {alert.village_name}",
                "severity": alert.severity.value,
                "primary_hazard": alert.primary_hazard.value,
                "recommended_action": alert.recommended_action,
                "generated_at": alert.generated_at,
            },
            "email_payload": {
                "subject": f"URGENT: {alert.severity.value} Hazard Alert for {alert.village_name}",
                "body": alert.messages.en,
            },
        }

    def get_delivery_status(self, alert: MultiHazardAlertRecord) -> AlertDeliveryStatusResponse:
        """
        Returns transparent simulation delivery status.
        """
        return AlertDeliveryStatusResponse(
            alert_id=alert.alert_id,
            delivery_status=DeliveryStatus.NOT_DELIVERED,
            delivery_mode=DeliveryMode.SIMULATION,
            channels={
                "local_dashboard": "LOCAL_DISPLAY_READY",
                "sms_gateway": "SIMULATION_ONLY (No external paid provider configured)",
                "whatsapp_gateway": "EXTERNAL_PROVIDER_UNAVAILABLE",
                "government_cap_broadcast": "GATEWAY_UNCONFIGURED",
            },
            explanation="Alert generated and prepared successfully in local memory. External public SMS / WhatsApp broadcasts remain simulated until authorized telecom gateway credentials are provided.",
            disclaimer="APADA MITRA decision support system generates automated warnings for emergency operation centers. Final public broadcast authorization remains with State Disaster Management Authorities.",
        )


simulation_notification_provider_instance = SimulationNotificationProvider()
