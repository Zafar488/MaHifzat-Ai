"""Free contact action URL composers for local client invocation."""
import re
from urllib.parse import quote

def sanitize_phone(phone: str) -> str | None:
    if not phone or not isinstance(phone, str):
        return None
    cleaned = re.sub(r"[^\d+]", "", phone.strip())
    if not cleaned or "javascript" in cleaned.lower() or len(cleaned) < 5 or len(cleaned) > 20:
        return None
    return cleaned

def contact_links(phone: str, message: str) -> dict[str, str] | None:
    sanitized = sanitize_phone(phone)
    if not sanitized:
        return None
    pk_phone = sanitized
    if pk_phone.startswith("0"):
        pk_phone = "92" + pk_phone[1:]
    elif pk_phone.startswith("+"):
        pk_phone = pk_phone[1:]
    encoded_msg = quote(message or "")
    return {
        "call": f"tel:{sanitized}",
        "sms": f"sms:{sanitized}?body={encoded_msg}",
        "whatsapp": f"https://wa.me/{pk_phone}?text={encoded_msg}",
    }
