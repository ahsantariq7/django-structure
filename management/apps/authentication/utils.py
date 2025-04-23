from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


class EmailManager:
    """
    A utility class for sending templated emails
    """

    def __init__(self):
        self.template_name = "email/base_email.html"
        self.from_email = settings.DEFAULT_FROM_EMAIL

    def send_email(
        self, to_email, subject, body, action_url=None, action_text=None, footer_text=None
    ):
        """
        Send an email using the base template

        Args:
            to_email (str or list): Recipient email address(es)
            subject (str): Email subject
            body (str): Email body content (can include HTML)
            action_url (str, optional): URL for the action button
            action_text (str, optional): Text for the action button
            footer_text (str, optional): Custom footer text
        """
        context = {
            "subject": subject,
            "body": body,
            "action_url": action_url,
            "action_text": action_text,
            "footer_text": footer_text,
        }

        # Render HTML content
        html_content = render_to_string(self.template_name, context)
        # Create plain text version
        text_content = strip_tags(html_content)

        # Create email message
        email = EmailMessage(
            subject=subject,
            body=text_content,
            from_email=self.from_email,
            to=[to_email] if isinstance(to_email, str) else to_email,
        )
        email.content_subtype = "html"
        email.body = html_content

        return email.send()
