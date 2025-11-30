# app/notifications.py
from firebase_admin import messaging

def send_notification_to_token(
    token: str,
    title: str,
    body: str,
    data: dict | None = None,
):
    """
    Gửi 1 push notif tới 1 thiết bị (theo FCM token)
    """
    if not token:
        print("⚠ Không có FCM token, bỏ qua gửi notif")
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
