import os
import secrets
import random
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
MAIL_FROM        = os.getenv("MAIL_FROM")


def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)


def generate_otp() -> str:
    return str(random.randint(100000, 999999))


async def send_otp_email(email: str, name: str, otp: str):
    html = f"""
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
    """
    message = Mail(
        from_email   = MAIL_FROM,
        to_emails    = email,
        subject      = "Your KALRIC Login Code 🔐",
        html_content = html
    )
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    sg.send(message)


async def send_verification_email(email: str, name: str, token: str):
    frontend_url = os.getenv("FRONTEND_URL")
    verify_link  = f"{frontend_url}/verify-email?token={token}"
    html = f"""
    <html>
    <body style="font-family: Arial; max-width: 600px; margin: auto; padding: 20px;">
        <div style="background: linear-gradient(135deg,#ff6b35,#f7931e);
                    padding: 30px; border-radius: 12px; text-align: center;">
            <h1 style="color: white; margin: 0;">💪 KALRIC</h1>
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
        </div>
    </body>
    </html>
    """
    message = Mail(
        from_email   = MAIL_FROM,
        to_emails    = email,
        subject      = "Verify Your KALRIC Account 💪",
        html_content = html
    )
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    sg.send(message)


async def send_new_device_alert(email: str, name: str, device_info: dict):
    html = f"""
    <html>
    <body style="font-family: Arial; max-width: 600px; margin: auto; padding: 20px;">
        <div style="background: #e74c3c; padding: 30px; border-radius: 12px; text-align: center;">
            <h1 style="color: white; margin: 0;">⚠️ New Login Detected</h1>
        </div>
        <div style="padding: 30px; background: #f9f9f9; border-radius: 12px; margin-top: 20px;">
            <h2 style="color: #333;">Hi {name},</h2>
            <p style="color: #666;">A new login was detected on your account.</p>
            <p style="color:#e74c3c; font-weight:bold;">
                If this was not you, change your password immediately!
            </p>
        </div>
    </body>
    </html>
    """
    message = Mail(
        from_email   = MAIL_FROM,
        to_emails    = email,
        subject      = "⚠️ New Device Login — KALRIC",
        html_content = html
    )
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    sg.send(message)