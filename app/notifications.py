import os, json
import firebase_admin
from firebase_admin import credentials, messaging

# --- init ---
if not firebase_admin._apps:
    raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    if raw:
        cred_info = json.loads(raw)
        cred = credentials.Certificate(cred_info)
        firebase_admin.initialize_app(cred)
    else:
        # không có key thì thôi, chỉ log
        print("⚠ FIREBASE_SERVICE_ACCOUNT_JSON not set, notifications disabled")


def send_notification_to_token(token: str, title: str, body: str, data: dict | None = None):
    """
    Gửi 1 push notif tới 1 thiết bị (theo FCM token)
    """
    if not token:
        return

    message = messaging.Message(
        token=token,
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
    )
    try:
        resp = messaging.send(message)
        print("✅ Sent FCM:", resp)
    except Exception as e:
        print("❌ FCM error:", e)
