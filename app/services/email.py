# app/services/email.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import traceback

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")      # tài khoản gửi mail
EMAIL_PASS = os.getenv("EMAIL_PASS")      # app password
EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USER)


def send_email(to_email: str, subject: str, body: str):
    if not EMAIL_USER or not EMAIL_PASS:
        print("❌ Chưa cấu hình EMAIL_USER / EMAIL_PASS")
        return False

    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print("✅ Sent email to:", to_email)
        return True
    except Exception as e:
        print("❌ Error sending email:", e)
        return False
