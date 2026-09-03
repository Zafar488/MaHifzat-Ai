"""Communication node — sends alerts via SMS/WhatsApp/emergency alerts based on context."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple

from backend.schemas.state import AgentState
from backend.integrations.messaging_client import MessagingClient

logger = logging.getLogger(__name__)


async def _llm_message(message_type: str, context: Dict[str, Any], fallback: str) -> Tuple[str, bool]:
    """Generate a message via the Groq LLM, falling back to template text.

    Returns (message, llm_generated). Never raises — message dispatch must
    keep working even when the LLM is unavailable.
    """
    try:
        from backend.services.llm import get_llm_service

        llm = get_llm_service()
        if llm is None:
            return fallback, False

        # Run the sync Groq call in a worker thread so we don't block the loop.
        text = await asyncio.to_thread(
            llm.generate_communication_message, message_type, context
        )
        if text and text.strip():
            return text.strip(), True
    except Exception as exc:
        logger.warning("LLM communication message generation failed: %s", exc)
    return fallback, False


async def communication(state: AgentState) -> dict:
    """Determine message type from state context and send via MessagingClient.

    - Emergency: sends emergency_alert to configured recipients
    - Referral: sends referral notification via SMS or WhatsApp
    - ANC follow-up: sends reminder message
    Tracks delivery status for all sent messages.
    """
    timestamp = datetime.utcnow().isoformat()
    node_name = "communication"

    try:
        is_emergency: bool = state.get("emergency", False)
        patient_id: str = state.get("patient_id", "unknown")
        channel: str = state.get("channel", "sms")
        demographics: Dict[str, Any] = state.get("demographics") or {}
        clinical_risk_result: Dict[str, Any] = state.get("clinical_risk_result") or {}
        referral_result: Dict[str, Any] = state.get("referral_result") or {}
        anc_result: Dict[str, Any] = state.get("anc_result") or {}
        language: str = state.get("language", "ur")

        phone = demographics.get("phone", "+923000000000")
        messaging = MessagingClient()
        delivery_log: List[Dict[str, Any]] = []
        llm_generated = False

        # --- Emergency alert -------------------------------------------
        if is_emergency:
            triage_level = clinical_risk_result.get("who_red_flags", {}).get("triage_level", "UNKNOWN")
            fallback_alert = (
                f"EMERGENCY ALERT: Patient {patient_id} - Critical maternal/fetal "
                f"condition detected. Immediate action required."
            )
            alert_message, alert_llm = await _llm_message(
                "emergency_alert",
                {
                    "patient_id": patient_id,
                    "reason": "Critical maternal/fetal condition detected",
                    "triage_level": triage_level,
                    "language": language,
                },
                fallback_alert,
            )
            llm_generated = llm_generated or alert_llm

            alert_data = {
                "patient_id": patient_id,
                "reason": "Critical maternal/fetal condition detected",
                "triage_level": triage_level,
                "message": alert_message,
            }
            # Alert to health worker + supervisor
            recipients = [phone, "+923001111111"]
            alert_results = await messaging.send_emergency_alert(recipients, alert_data)
            delivery_log.extend(alert_results)

        # --- Referral notification -------------------------------------
        elif referral_result.get("selected_facility"):
            facility_name = referral_result["selected_facility"].get("name", "facility")
            urgency = referral_result.get("urgency_level", "routine")
            travel_time = referral_result.get("estimated_travel_time_min", "N/A")

            fallback_message = (
                f"Referral Notice: You have been referred to {facility_name}. "
                f"Urgency: {urgency}. Estimated travel: {travel_time} min. "
                f"Please proceed as soon as possible."
            )
            message, used_llm = await _llm_message(
                "referral_notification",
                {
                    "patient_id": patient_id,
                    "facility_name": facility_name,
                    "urgency": urgency,
                    "estimated_travel_time_min": travel_time,
                    "language": language,
                },
                fallback_message,
            )
            llm_generated = llm_generated or used_llm

            if channel == "whatsapp":
                result = await messaging.send_whatsapp(phone, message, priority=urgency)
            else:
                result = await messaging.send_sms(phone, message, priority=urgency)
            delivery_log.append(result)

        # --- ANC follow-up reminder ------------------------------------
        elif anc_result.get("recommended_action"):
            action = anc_result["recommended_action"]
            priority_score = anc_result.get("priority_score", 0)

            fallback_reminder = (
                f"MaaHifazat ANC Reminder: Your health check-up is important. "
                f"Priority: {anc_result.get('priority', 'low')}. "
                f"Please visit your nearest health center."
            )
            reminder_message, used_llm = await _llm_message(
                "anc_followup_reminder",
                {
                    "patient_id": patient_id,
                    "priority": anc_result.get("priority", "low"),
                    "priority_score": priority_score,
                    "recommended_action": action,
                    "language": language,
                },
                fallback_reminder,
            )
            llm_generated = llm_generated or used_llm

            if action == "sms":
                result = await messaging.send_sms(phone, reminder_message, priority="normal")
            elif action == "call":
                # For call action, send SMS + mark as needing phone call
                result = await messaging.send_sms(
                    phone,
                    reminder_message + " A health worker will also call you.",
                    priority="high",
                )
            else:
                result = await messaging.send_sms(phone, reminder_message, priority="normal")
            delivery_log.append(result)

        # --- Default: status update ------------------------------------
        else:
            risk_level = clinical_risk_result.get("maternal_risk", {}).get("risk_level", "unknown")
            fallback_message = (
                f"MaaHifazat Update: Your health screening is complete. "
                f"Risk level: {risk_level}. Stay healthy!"
            )
            message, used_llm = await _llm_message(
                "screening_status_update",
                {
                    "patient_id": patient_id,
                    "maternal_risk_level": risk_level,
                    "language": language,
                },
                fallback_message,
            )
            llm_generated = llm_generated or used_llm
            result = await messaging.send_sms(phone, message, priority="normal")
            delivery_log.append(result)

        # --- Build communication result --------------------------------
        all_delivered = all(
            d.get("status") == "delivered" for d in delivery_log
        )

        communication_result: Dict[str, Any] = {
            "messages_sent": len(delivery_log),
            "delivery_status": delivery_log,
            "all_delivered": all_delivered,
            "is_emergency_alert": is_emergency,
            "channel_used": channel,
            "language": language,
            "llm_generated": llm_generated,
            "timestamp": timestamp,
        }

        result_summary = (
            f"Communication: {len(delivery_log)} messages sent | "
            f"All delivered: {all_delivered} | Emergency: {is_emergency} | "
            f"LLM: {llm_generated}"
        )

        audit_entry = {
            "agent": node_name,
            "timestamp": timestamp,
            "action": "communication_dispatch",
            "result_summary": result_summary,
        }

        return {
            "communication_result": communication_result,
            "current_step": "communication_complete",
            "audit_trail": [audit_entry],
        }

    except Exception as e:
        error_entry = {
            "agent": node_name,
            "error": str(e),
            "timestamp": timestamp,
        }
        audit_entry = {
            "agent": node_name,
            "timestamp": timestamp,
            "action": "communication_error",
            "result_summary": f"Error during communication: {e}",
        }
        return {
            "errors": [error_entry],
            "audit_trail": [audit_entry],
        }
