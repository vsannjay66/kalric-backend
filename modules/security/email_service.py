import os
import secrets
import random
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import load_dotenv

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME   = os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD   = os.getenv("MAIL_PASSWORD"),
    MAIL_FROM       = os.getenv("MAIL_FROM"),
    MAIL_PORT       = int(os.getenv("MAIL_PORT", 465)),
    MAIL_SERVER     = os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS   = True,
    MAIL_SSL_TLS    = False,
    USE_CREDENTIALS = True
)

fm = FastMail(conf)


def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)


def generate_otp() -> str:
    return str(random.randint(100000, 999999))


async def send_verification_email(email: str, name: str, token: str):
    frontend_url = os.getenv("FRONTEND_URL")
    verify_link  = f"{frontend_url}/verify-email?token={token}"

    message = MessageSchema(
        subject    = "Verify Your Gym AI Agent Account 💪",
        recipients = [email],
        body       = f"""
        <html>
        <body style="font-family: Arial; max-width: 600px; margin: auto; padding: 20px;">
            <div style="background: linear-gradient(135deg,#ff6b35,#f7931e);
                        padding: 30px; border-radius: 12px; text-align: center;">
                <h1 style="color: white; margin: 0;">💪 Gym AI Agent</h1>
            </div>
            <div style="padding: 30px; background: #f9f9f9; border-radius: 12px; margin-top: 20px;">
                <h2 style="color: #333;">Welcome, {name}!</h2>
                <p style="color: #666;">Click below to verify your email:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verify_link}"
                       style="background: #ff6b35; color: white; padding: 14px 32px;
                              text-decoration: none; border-radius: 8px; font-size: 16px;
                              font-weight: bold; display: inline-block;">
                        ✅ Verify My Email
                    </a>
                </div>
                <p style="color: #999; font-size: 12px;">
                    Link expires in 24 hours.
                    If you did not create this account, ignore this email.
                </p>
            </div>
        </body>
        </html>
        """,
        subtype = "html"
    )
    await fm.send_message(message)


async def send_otp_email(email: str, name: str, otp: str):
    message = MessageSchema(
        subject    = "Your Gym AI Agent Login Code 🔐",
        recipients = [email],
        body       = f"""
        <html>
        <body style="font-family: Arial; max-width: 600px; margin: auto; padding: 20px;">
            <div style="background: linear-gradient(135deg,#ff6b35,#f7931e);
                        padding: 30px; border-radius: 12px; text-align: center;">
                <h1 style="color: white; margin: 0;">🔐 Login Code</h1>
            </div>
            <div style="padding: 30px; background: #f9f9f9; border-radius: 12px; margin-top: 20px;">
                <h2 style="color: #333;">Hi {name},</h2>
                <p style="color: #666;">Your one-time login code:</p>
                <div style="background: white; border: 2px solid #ff6b35;
                            border-radius: 12px; padding: 20px; text-align: center; margin: 20px 0;">
                    <h1 style="color: #ff6b35; letter-spacing: 15px; font-size: 40px; margin: 0;">
                        {otp}
                    </h1>
                </div>
                <p style="color: #999; font-size: 13px;">
                    ⏰ Expires in 10 minutes.<br/>
                    🚫 Never share this with anyone.
                </p>
            </div>
        </body>
        </html>
        """,
        subtype = "html"
    )
    await fm.send_message(message)


async def send_new_device_alert(email: str, name: str, device_info: dict):
    message = MessageSchema(
        subject    = "⚠️ New Device Login — Gym AI Agent",
        recipients = [email],
        body       = f"""
        <html>
        <body style="font-family: Arial; max-width: 600px; margin: auto; padding: 20px;">
            <div style="background: #e74c3c; padding: 30px; border-radius: 12px; text-align: center;">
                <h1 style="color: white; margin: 0;">⚠️ New Login Detected</h1>
            </div>
            <div style="padding: 30px; background: #f9f9f9; border-radius: 12px; margin-top: 20px;">
                <h2 style="color: #333;">Hi {name},</h2>
                <p style="color: #666;">A new login was detected:</p>
                <table style="width:100%; border-collapse: collapse;">
                    <tr style="background: white;">
                        <td style="padding:10px; border:1px solid #ddd; font-weight:bold;">Device</td>
                        <td style="padding:10px; border:1px solid #ddd;">{device_info.get('device_name','Unknown')}</td>
                    </tr>
                    <tr>
                        <td style="padding:10px; border:1px solid #ddd; font-weight:bold;">Browser</td>
                        <td style="padding:10px; border:1px solid #ddd;">{device_info.get('browser','Unknown')}</td>
                    </tr>
                    <tr style="background: white;">
                        <td style="padding:10px; border:1px solid #ddd; font-weight:bold;">OS</td>
                        <td style="padding:10px; border:1px solid #ddd;">{device_info.get('os','Unknown')}</td>
                    </tr>
                    <tr>
                        <td style="padding:10px; border:1px solid #ddd; font-weight:bold;">IP</td>
                        <td style="padding:10px; border:1px solid #ddd;">{device_info.get('ip_address','Unknown')}</td>
                    </tr>
                </table>
                <p style="color:#e74c3c; font-weight:bold; margin-top:20px;">
                    If this was not you, change your password immediately!
                </p>
            </div>
        </body>
        </html>
        """,
        subtype = "html"
    )
    await fm.send_message(message)