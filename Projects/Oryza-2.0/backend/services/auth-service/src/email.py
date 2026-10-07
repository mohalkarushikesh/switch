"""
Email utilities for authentication service
"""
import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "Oryza <noreply@oryza.com>")
APP_URL = os.getenv("APP_URL", "http://localhost:3000")


async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None
):
    """Send email using SMTP"""
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = EMAIL_FROM
    message["To"] = to_email
    
    # Add text and HTML parts
    if text_body:
        text_part = MIMEText(text_body, "plain")
        message.attach(text_part)
    
    html_part = MIMEText(html_body, "html")
    message.attach(html_part)
    
    # Send email
    if SMTP_USER and SMTP_PASSWORD:  # Only send if configured
        try:
            await aiosmtplib.send(
                message,
                hostname=SMTP_HOST,
                port=SMTP_PORT,
                username=SMTP_USER,
                password=SMTP_PASSWORD,
                start_tls=True
            )
        except Exception as e:
            print(f"Failed to send email: {e}")
            # In production, you'd want to log this properly
    else:
        # For development, just print the email
        print(f"Email to {to_email}: {subject}")
        print(f"Body: {html_body}")


async def send_verification_email(email: str, token: str):
    """Send email verification link"""
    verification_url = f"{APP_URL}/verify-email?token={token}"
    
    subject = "Verify your Oryza account"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #D4AF37; color: white; padding: 20px; text-align: center; }}
            .content {{ background-color: #f4f4f4; padding: 20px; margin-top: 20px; }}
            .button {{ display: inline-block; background-color: #D4AF37; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to Oryza</h1>
            </div>
            <div class="content">
                <h2>Verify Your Email Address</h2>
                <p>Thank you for signing up with Oryza! To complete your registration, please verify your email address by clicking the button below:</p>
                <p style="text-align: center;">
                    <a href="{verification_url}" class="button">Verify Email</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p>{verification_url}</p>
                <p>This link will expire in 24 hours.</p>
                <p>If you didn't create an account with Oryza, please ignore this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    Welcome to Oryza!
    
    Please verify your email address by visiting this link:
    {verification_url}
    
    This link will expire in 24 hours.
    
    If you didn't create an account with Oryza, please ignore this email.
    """
    
    await send_email(email, subject, html_body, text_body)


async def send_password_reset_email(email: str, token: str):
    """Send password reset link"""
    reset_url = f"{APP_URL}/reset-password?token={token}"
    
    subject = "Reset your Oryza password"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #D4AF37; color: white; padding: 20px; text-align: center; }}
            .content {{ background-color: #f4f4f4; padding: 20px; margin-top: 20px; }}
            .button {{ display: inline-block; background-color: #D4AF37; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Oryza Password Reset</h1>
            </div>
            <div class="content">
                <h2>Reset Your Password</h2>
                <p>We received a request to reset your password. Click the button below to create a new password:</p>
                <p style="text-align: center;">
                    <a href="{reset_url}" class="button">Reset Password</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p>{reset_url}</p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request a password reset, please ignore this email. Your password won't be changed.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    Oryza Password Reset
    
    We received a request to reset your password. Visit this link to create a new password:
    {reset_url}
    
    This link will expire in 1 hour.
    
    If you didn't request a password reset, please ignore this email.
    """
    
    await send_email(email, subject, html_body, text_body)


async def send_2fa_enabled_email(email: str):
    """Send notification that 2FA was enabled"""
    subject = "Two-Factor Authentication Enabled"
    
    html_body = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background-color: #D4AF37; color: white; padding: 20px; text-align: center; }
            .content { background-color: #f4f4f4; padding: 20px; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Oryza Security Update</h1>
            </div>
            <div class="content">
                <h2>Two-Factor Authentication Enabled</h2>
                <p>Two-factor authentication has been successfully enabled on your Oryza account.</p>
                <p>From now on, you'll need to enter a verification code from your authenticator app when logging in.</p>
                <p>If you didn't enable 2FA, please contact support immediately.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    await send_email(email, subject, html_body) 