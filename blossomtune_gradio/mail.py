import smtplib
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
import requests

from blossomtune_gradio.logs import log
from blossomtune_gradio import config as cfg


class EmailSender(ABC):
    """
    Abstract Base Class for email sending.

    This class defines the interface for all email sending implementations,
    ensuring they have a consistent `send_email` method.
    """

    @abstractmethod
    def send_email(
        self, recipient_email: str, subject: str, body: str
    ) -> tuple[bool, str]:
        """
        Sends an email to the specified recipient.

        Args:
            recipient_email: The email address of the recipient.
            subject: The subject line of the email.
            body: The body content of the email.

        Returns:
            A tuple containing a boolean success status and an error message string.
            The error message is empty if the email was sent successfully.
        """
        pass


class SMTPMailSender(EmailSender):
    """
    Concrete implementation of EmailSender using standard SMTP.
    """

    def send_email(
        self, recipient_email: str, subject: str, body: str
    ) -> tuple[bool, str]:
        """
        Sends an email using the SMTP server configured in `cfg`.
        """
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = cfg.SMTP_SENDER
        msg["To"] = recipient_email

        try:
            with smtplib.SMTP(cfg.SMTP_SERVER, cfg.SMTP_PORT) as server:
                if cfg.SMTP_REQUIRE_TLS:
                    server.starttls()
                    server.login(cfg.SMTP_USER, cfg.SMTP_PASSWORD)
                server.send_message(msg)
            log("[Email] SMTP email sent.")
            return True, ""
        except Exception as e:
            log(f"[Email] CRITICAL ERROR sending to {recipient_email} via SMTP: {e}")
            return False, f"Error sending email via SMTP: {e}"


class MailjetSender(EmailSender):
    """
    Concrete implementation of EmailSender using the Mailjet API.
    """

    def send_email(
        self, recipient_email: str, subject: str, body: str
    ) -> tuple[bool, str]:
        """
        Sends an email using the Mailjet transactional API v3.1.
        """
        if not all([hasattr(cfg, "SMTP_USER"), hasattr(cfg, "SMTP_PASSWORD")]):
            error_msg = "Mailjet API keys are not configured."
            log(f"[Email] {error_msg}")
            return False, error_msg

        api_key = cfg.SMTP_USER
        api_secret = cfg.SMTP_PASSWORD

        url = "https://api.mailjet.com/v3.1/send"
        data = {
            "Messages": [
                {
                    "From": {
                        "Email": cfg.SMTP_SENDER,
                        "Name": cfg.SMTP_SENDER.split("@")[0],
                    },
                    "To": [{"Email": recipient_email}],
                    "Subject": subject,
                    "TextPart": body,
                }
            ]
        }

        try:
            response = requests.post(url, auth=(api_key, api_secret), json=data)
            response.raise_for_status()
            log(f"[Email] Mailjet email sent. Status: {response.status_code}")
            return True, ""
        except requests.exceptions.RequestException as e:
            error_msg = f"Error sending email via Mailjet API: {e}. Response: {e.response.text if e.response else 'No response'}"
            log(f"[Email] CRITICAL ERROR: {error_msg}")
            return False, error_msg


def get_email_sender() -> EmailSender:
    """
    Factory function to get the correct email sender implementation.

    This function reads the `EMAIL_PROVIDER` variable from the `config` module
    and returns an appropriate EmailSender instance. Defaults to SMTP.
    """
    provider = getattr(cfg, "EMAIL_PROVIDER", "smtp")
    if provider == "mailjet":
        return MailjetSender()
    # Default to SMTP if the provider is not Mailjet or is missing.
    return SMTPMailSender()


def send_activation_email(
    recipient_email: str, activation_code: str
) -> tuple[bool, str]:
    """
    Sends the activation code to the user using the configured email provider.

    This function uses the factory to get the correct sender and abstracts the
    implementation details.
    """
    subject = "Your BlossomTune Activation Code"
    body = (
        "Welcome to BlossomTune!\n\n"
        "Please use the following code to activate your participation request:\n\n"
        f"{activation_code}\n\n"
        "Thank you!"
    )

    sender = get_email_sender()
    success, error_message = sender.send_email(recipient_email, subject, body)

    if not success:
        return (
            False,
            f"There was an error sending the activation email. Please contact an administrator. Original error: {error_message}",
        )

    return True, ""
