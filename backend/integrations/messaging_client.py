"""Messaging client — Twilio/WhatsApp API stub."""
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.config import settings
import uuid


class MessagingClient:
    """Client for SMS and WhatsApp notifications."""

    def __init__(self, base_url: str = None, timeout: float = 3.0):
        self.base_url = base_url or settings.MESSAGING_API_URL
        self.timeout = timeout
        self._sent_messages = []  # In-memory log for testing

    async def send_sms(self, phone: str, message: str, priority: str = "normal") -> Dict[str, Any]:
        """Send SMS message. Returns delivery status."""
        msg_id = f"sms_{uuid.uuid4().hex[:8]}"
        result = {
            "message_id": msg_id,
            "channel": "sms",
            "recipient": phone,
            "status": "delivered",  # STUB: always succeeds
            "sent_at": datetime.utcnow().isoformat(),
            "priority": priority,
        }
        self._sent_messages.append(result)
        return result

    async def send_whatsapp(self, phone: str, message: str, priority: str = "normal") -> Dict[str, Any]:
        """Send WhatsApp message."""
        msg_id = f"wa_{uuid.uuid4().hex[:8]}"
        result = {
            "message_id": msg_id,
            "channel": "whatsapp",
            "recipient": phone,
            "status": "delivered",
            "sent_at": datetime.utcnow().isoformat(),
            "priority": priority,
        }
        self._sent_messages.append(result)
        return result

    async def send_emergency_alert(self, recipients: List[str], alert_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Send emergency alerts to multiple recipients.

        Uses alert_data["message"] as the alert text when provided (e.g. an
        LLM-generated message); otherwise falls back to the default template.
        """
        results = []
        message = alert_data.get("message") or (
            f"EMERGENCY ALERT: Patient {alert_data.get('patient_id', 'unknown')} - "
            f"{alert_data.get('reason', 'Critical condition')}. Immediate action required."
        )
        for phone in recipients:
            result = await self.send_sms(phone, message, priority="emergency")
            results.append(result)
        return results

    async def get_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """Check delivery status of a sent message."""
        for msg in self._sent_messages:
            if msg["message_id"] == message_id:
                return msg
        return {"message_id": message_id, "status": "unknown"}

    async def send_reminder(self, phone: str, reminder_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Send ANC reminder (appointment, medication, etc.)."""
        templates = {
            "appointment": "Reminder: Your antenatal checkup is scheduled for {date}. Please visit {facility}.",
            "medication": "Reminder: Please take your {medicine} as prescribed.",
            "followup": "Your health worker will visit you on {date}. Please be available.",
        }
        template = templates.get(reminder_type, "Reminder from MaaHifazat AI health system.")
        message = template.format(**details) if details else template
        return await self.send_sms(phone, message, priority="normal")
