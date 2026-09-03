"""Alert routes — send SMS/WhatsApp/emergency alerts and check delivery status."""
import uuid
from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.api.auth import get_current_user
from backend.integrations import MessagingClient
from backend.schemas.auth import TokenPayload

router = APIRouter(prefix="/alerts", tags=["alerts"])

# ---------------------------------------------------------------------------
# In-memory alert store for status lookup
# ---------------------------------------------------------------------------

_alert_store: Dict[str, Dict] = {}

# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class SendAlertRequest(BaseModel):
    recipient: str
    message: str
    channel: str = "sms"          # sms | whatsapp | emergency
    patient_id: Optional[str] = None
    priority: str = "normal"


class AlertResponse(BaseModel):
    alert_id: str
    message_id: str
    channel: str
    recipient: str
    status: str
    sent_at: str
    patient_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/send", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def send_alert(
    request: SendAlertRequest,
    current_user: TokenPayload = Depends(get_current_user),
):
    """
    Send an alert via SMS, WhatsApp, or emergency broadcast.
    Requires an authenticated user.
    """
    client = MessagingClient()
    channel = request.channel.lower()

    try:
        if channel == "sms":
            result = await client.send_sms(
                phone=request.recipient,
                message=request.message,
                priority=request.priority,
            )
        elif channel == "whatsapp":
            result = await client.send_whatsapp(
                phone=request.recipient,
                message=request.message,
                priority=request.priority,
            )
        elif channel == "emergency":
            results = await client.send_emergency_alert(
                recipients=[request.recipient],
                alert_data={
                    "patient_id": request.patient_id or "unknown",
                    "reason": request.message,
                },
            )
            result = results[0] if results else {}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown channel '{channel}'. Use: sms, whatsapp, emergency.",
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send alert: {str(exc)}",
        )

    alert_id = f"alert_{uuid.uuid4().hex[:10]}"
    entry = {
        "alert_id": alert_id,
        "message_id": result.get("message_id", ""),
        "channel": result.get("channel", channel),
        "recipient": result.get("recipient", request.recipient),
        "status": result.get("status", "delivered"),
        "sent_at": result.get("sent_at", datetime.utcnow().isoformat()),
        "patient_id": request.patient_id,
        "sent_by": current_user.sub,
    }
    _alert_store[alert_id] = entry

    return AlertResponse(**{k: v for k, v in entry.items() if k != "sent_by"})


@router.get("/{alert_id}/status")
async def get_alert_status(
    alert_id: str,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Return the delivery status of a previously sent alert."""
    entry = _alert_store.get(alert_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' not found.",
        )
    return entry
