import resend
import logging
from backend.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

if settings.RESEND_API_KEY:
    resend.api_key = settings.RESEND_API_KEY

class EmailService:
    @staticmethod
    async def send_otp_email(to_email: str, otp: str):
        """Send an OTP email using Resend."""
        if not settings.RESEND_API_KEY:
            logger.warning(f"RESEND_API_KEY not set. Cannot send OTP to {to_email}. OTP is {otp}")
            return False

        try:
            params = {
                "from": "Kosh-AI <onboarding@resend.dev>", # Use your verified domain in production
                "to": [to_email],
                "subject": "Your Kosh-AI Password Reset OTP",
                "html": f"""
                    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;">
                        <h2 style="color: #6366f1;">Kosh-AI Password Reset</h2>
                        <p>You requested to reset your password. Use the following OTP to proceed. This code will expire in 15 minutes.</p>
                        <div style="background: #f1f5f9; padding: 20px; text-align: center; border-radius: 8px; margin: 24px 0;">
                            <span style="font-size: 32px; font-weight: 800; letter-spacing: 4px; color: #1e293b;">{otp}</span>
                        </div>
                        <p style="color: #64748b; font-size: 14px;">If you didn't request this, you can safely ignore this email.</p>
                        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 24px 0;">
                        <p style="font-size: 12px; color: #94a3b8; text-align: center;">Built for Indian Merchants. Built for the data truth.</p>
                    </div>
                """,
            }
            
            # Resend's python library doesn't have an async client yet, 
            # so we run it in a thread if needed, or just call it directly for now.
            # In a high-traffic app, we would use a background task (Celery).
            resend.Emails.send(params)
            logger.info(f"OTP email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send OTP email to {to_email}: {str(e)}")
            return False
