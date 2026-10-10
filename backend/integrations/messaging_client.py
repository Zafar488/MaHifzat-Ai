"""No production messaging provider is configured. Demo never sends live traffic."""
from datetime import datetime, timezone
import uuid
from backend.config import settings


class MessagingClient:
    def __init__(self, *args, **kwargs):
        self._sent_messages = []

    async def send_sms(self, phone, message, priority="normal"):
        return self._simulate("sms", phone)

    async def send_whatsapp(self, phone, message, priority="normal"):
        return self._simulate("whatsapp", phone)

    def _simulate(self, channel, phone):
        result = {"message_id": "demo_" + uuid.uuid4().hex if settings.DEMO_MODE else None, "channel": channel, "recipient": phone, "status": "simulated" if settings.DEMO_MODE else "unavailable", "simulated": settings.DEMO_MODE, "sent_at": None, "recorded_at": datetime.now(timezone.utc).isoformat(), "reason": "No provider acknowledgment or delivery receipt"}
        self._sent_messages.append(result)
        return result

    async def send_emergency_alert(self, recipients, alert_data):
        return [await self.send_sms(p, alert_data.get("message", ""), "emergency") for p in recipients]

    async def get_delivery_status(self, message_id):
        return next((r for r in self._sent_messages if r["message_id"] == message_id and message_id is not None), {"message_id": message_id, "status": "unknown"})

    async def send_reminder(self, phone, reminder_type, details):
        return await self.send_sms(phone, reminder_type)
