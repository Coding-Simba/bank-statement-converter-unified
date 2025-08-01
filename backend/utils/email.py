"""Email service for sending notifications."""

import os
from typing import Dict, Optional
import logging
from datetime import datetime
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for sending notifications."""
    
    def __init__(self):
        # Email configuration from environment
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.sendgrid.net")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "apikey")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@bankcsvconverter.com")
        self.from_name = os.getenv("FROM_NAME", "BankCSV")
        self.enabled = bool(self.smtp_password)
        
        if not self.enabled:
            logger.warning("Email service disabled - SMTP_PASSWORD not configured")
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send an email."""
        if not self.enabled:
            logger.info(f"Email service disabled - would send to {to_email}: {subject}")
            return True
        
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{self.from_name} <{self.from_email}>"
            message['To'] = to_email
            
            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                message.attach(text_part)
            
            html_part = MIMEText(html_content, 'html')
            message.attach(html_part)
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_username,
                password=self.smtp_password,
                start_tls=True
            )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    async def send_password_changed_email(self, to_email: str, user_name: Optional[str] = None):
        """Send password changed notification."""
        subject = "Your password has been changed"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Password Changed</h2>
            <p>Hi {user_name or 'there'},</p>
            <p>Your password was successfully changed on {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}.</p>
            <p>If you did not make this change, please contact us immediately.</p>
            <br>
            <p>Best regards,<br>The BankCSV Team</p>
        </div>
        """
        
        text_content = f"""
        Password Changed
        
        Hi {user_name or 'there'},
        
        Your password was successfully changed on {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}.
        
        If you did not make this change, please contact us immediately.
        
        Best regards,
        The BankCSV Team
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    async def send_email_verification(self, to_email: str, verification_url: str):
        """Send email verification link."""
        subject = "Verify your new email address"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Verify Your Email Address</h2>
            <p>Please click the button below to verify your new email address:</p>
            <div style="margin: 30px 0;">
                <a href="{verification_url}" style="background-color: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Verify Email Address
                </a>
            </div>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all;">{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
            <br>
            <p>Best regards,<br>The BankCSV Team</p>
        </div>
        """
        
        text_content = f"""
        Verify Your Email Address
        
        Please click the link below to verify your new email address:
        
        {verification_url}
        
        This link will expire in 24 hours.
        
        Best regards,
        The BankCSV Team
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    async def send_2fa_enabled_email(self, to_email: str, user_name: Optional[str] = None):
        """Send 2FA enabled notification."""
        subject = "Two-Factor Authentication enabled"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Two-Factor Authentication Enabled</h2>
            <p>Hi {user_name or 'there'},</p>
            <p>Two-factor authentication has been successfully enabled on your account.</p>
            <p>You will now need to enter a verification code from your authenticator app when logging in.</p>
            <p>Make sure to save your backup codes in a secure location.</p>
            <br>
            <p>Best regards,<br>The BankCSV Team</p>
        </div>
        """
        
        return await self.send_email(to_email, subject, html_content)
    
    async def send_2fa_disabled_email(self, to_email: str, user_name: Optional[str] = None):
        """Send 2FA disabled notification."""
        subject = "Two-Factor Authentication disabled"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Two-Factor Authentication Disabled</h2>
            <p>Hi {user_name or 'there'},</p>
            <p>Two-factor authentication has been disabled on your account.</p>
            <p>Your account is now protected only by your password. We recommend enabling 2FA for better security.</p>
            <br>
            <p>Best regards,<br>The BankCSV Team</p>
        </div>
        """
        
        return await self.send_email(to_email, subject, html_content)
    
    async def send_account_deletion_confirmation(self, to_email: str, deletion_url: str, user_name: Optional[str] = None):
        """Send account deletion confirmation email."""
        subject = "Confirm account deletion"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Account Deletion Request</h2>
            <p>Hi {user_name or 'there'},</p>
            <p>We received a request to permanently delete your BankCSV account.</p>
            <p><strong>Warning:</strong> This action cannot be undone. All your data will be permanently deleted.</p>
            <div style="margin: 30px 0;">
                <a href="{deletion_url}" style="background-color: #dc3545; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Confirm Account Deletion
                </a>
            </div>
            <p>If you did not request this, please ignore this email and your account will remain active.</p>
            <p>This link will expire in 1 hour.</p>
            <br>
            <p>Best regards,<br>The BankCSV Team</p>
        </div>
        """
        
        return await self.send_email(to_email, subject, html_content)
    
    async def send_api_key_generated_email(self, to_email: str, api_key_preview: str, user_name: Optional[str] = None):
        """Send API key generated notification."""
        subject = "New API key generated"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>New API Key Generated</h2>
            <p>Hi {user_name or 'there'},</p>
            <p>A new API key has been generated for your account.</p>
            <p>Key preview: <code>{api_key_preview}</code></p>
            <p>For security reasons, we only show the last 4 characters. Make sure to save your full API key securely.</p>
            <p>If you did not generate this key, please revoke it immediately in your account settings.</p>
            <br>
            <p>Best regards,<br>The BankCSV Team</p>
        </div>
        """
        
        return await self.send_email(to_email, subject, html_content)


# Global email service instance
email_service = EmailService()