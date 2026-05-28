from __future__ import annotations

from agents import function_tool

from .outbound import send_confirmed_sms_rcs_text


@function_tool
def send_confirmed_sms_rcs(
    message_text: str,
    recipient_phone: str = "",
    contact_name: str = "",
    user_confirmed: bool = False,
    confirmation_text: str = "",
    preferred_service: str = "SMS",
) -> str:
    """Send one SMS/RCS via macOS Messages only after explicit confirmation and status verification."""
    return send_confirmed_sms_rcs_text(
        message_text=message_text,
        recipient_phone=recipient_phone,
        contact_name=contact_name,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
        preferred_service=preferred_service,
    )
