from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    Centralized email service for sending various types of emails
    """

    @staticmethod
    def _get_template_config(email_type):
        """Get email template configuration"""
        return settings.EMAIL_TEMPLATES.get(email_type, {})

    @staticmethod
    def send_email(to_email, subject, body, action_url=None, action_text=None, footer_text=None):
        """
        Send a generic email using the base template

        Args:
            to_email (str or list): Recipient email address(es)
            subject (str): Email subject
            body (str): Email body content (can include HTML)
            action_url (str, optional): URL for the action button
            action_text (str, optional): Text for the action button
            footer_text (str, optional): Custom footer text
        """
        logger.info(f"Preparing to send email to: {to_email}")
        logger.info(f"Subject: {subject}")

        template_name = f"{settings.EMAIL_TEMPLATE_DIR}/base_email.html"
        context = {
            "subject": subject,
            "body": body,
            "action_url": action_url,
            "action_text": action_text,
            "footer_text": footer_text,
        }

        try:
            # Render HTML content
            html_content = render_to_string(template_name, context)
            text_content = strip_tags(html_content)

            # Create email message
            email = EmailMessage(
                subject=f"{settings.EMAIL_SUBJECT_PREFIX}{subject}",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email] if isinstance(to_email, str) else to_email,
            )
            email.content_subtype = "html"
            email.body = html_content

            # Send email
            sent = email.send()

            if sent:
                logger.info(f"Email sent successfully to: {to_email}")
            else:
                logger.warning(f"Failed to send email to: {to_email}")

            return sent

        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False

    @classmethod
    def send_verification_email(cls, user, verification_url):
        """
        Send email verification link

        Args:
            user: User instance
            verification_url: URL for email verification
        """
        logger.info(f"Sending verification email to: {user.email}")

        template_config = cls._get_template_config("verification")
        subject = template_config.get("subject", "Verify Your Email Address")

        body = f"""
        <p>Hello {user.get_full_name() or user.username},</p>
        <p>Thank you for registering! Please verify your email address to activate your account.</p>
        <p>Click the button below to verify your email address:</p>
        """

        return cls.send_email(
            to_email=user.email,
            subject=subject,
            body=body,
            action_url=verification_url,
            action_text="Verify Email",
            footer_text="If you didn't create this account, please ignore this email.",
        )

    @classmethod
    def send_password_reset_email(cls, user, reset_url):
        """
        Send password reset link

        Args:
            user: User instance
            reset_url: URL for password reset
        """
        template_config = cls._get_template_config("password_reset")
        subject = template_config.get("subject", "Reset Your Password")

        body = f"""
        <p>Hello {user.get_full_name() or user.username},</p>
        <p>We received a request to reset your password.</p>
        <p>Click the button below to reset your password:</p>
        """

        return cls.send_email(
            to_email=user.email,
            subject=subject,
            body=body,
            action_url=reset_url,
            action_text="Reset Password",
            footer_text="If you didn't request this, please ignore this email.",
        )

    @classmethod
    def send_welcome_email(cls, user, login_url=None):
        """
        Send welcome email after successful email verification

        Args:
            user: User instance
            login_url: Optional URL to the login page
        """
        logger.info(f"Sending welcome email to: {user.email}")

        template_config = cls._get_template_config("welcome")
        subject = template_config.get("subject", "Welcome to Management System")

        body = f"""
        <p>Hello {user.get_full_name() or user.username},</p>
        <p>Your email has been successfully verified!</p>
        <p>You can now log in to your account and start using our services.</p>
        """

        return cls.send_email(
            to_email=user.email,
            subject=subject,
            body=body,
            action_url=login_url,
            action_text="Login Now" if login_url else None,
            footer_text="Welcome aboard! We're excited to have you with us.",
        )
