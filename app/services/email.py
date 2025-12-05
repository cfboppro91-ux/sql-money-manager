import os
import resend

resend.api_key = os.getenv("RESEND_API_KEY")
RESEND_FROM = os.getenv("RESEND_FROM", "onboarding@resend.dev")


def send_email(to_email: str, subject: str, body: str) -> bool:
    try:
        r = resend.Emails.send({
            "from": RESEND_FROM,
            "to": to_email,
            "subject": subject,
            "text": body
        })
        print("📧 Resend OK:", r)
        return True
    except Exception as e:
        print("❌ Resend error:", repr(e))
        return False
