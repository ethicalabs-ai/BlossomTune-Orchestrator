import requests
import pytest
from unittest.mock import MagicMock, patch

from blossomtune_gradio import mail
from blossomtune_gradio import config as cfg


class TestSMTPMailSender:
    """Tests for the SMTPMailSender class."""

    @pytest.fixture
    def sender(self):
        return mail.SMTPMailSender()

    def test_send_email_success(self, sender, mocker):
        """Verify that a successful email send works as expected."""
        mock_smtp = mocker.patch("smtplib.SMTP")
        recipient = "test@example.com"
        subject = "Test Subject"
        body = "Test Body"

        success, message = sender.send_email(recipient, subject, body)

        assert success is True
        assert message == ""
        mock_smtp.assert_called_once_with(cfg.SMTP_SERVER, cfg.SMTP_PORT)
        # Check that send_message was called on the context manager's result
        mock_smtp.return_value.__enter__.return_value.send_message.assert_called_once()

    def test_send_email_failure(self, sender, mocker):
        """Verify that an SMTP error is handled correctly."""
        mocker.patch("smtplib.SMTP", side_effect=Exception("SMTP Connection Error"))
        recipient = "test@example.com"
        subject = "Test Subject"
        body = "Test Body"

        success, message = sender.send_email(recipient, subject, body)

        assert success is False
        assert "SMTP Connection Error" in message


class TestMailjetSender:
    """Tests for the MailjetSender class."""

    @pytest.fixture
    def sender(self):
        return mail.MailjetSender()

    def test_send_email_success(self, sender, mocker):
        """Verify a successful send via the Mailjet API."""
        mock_post = mocker.patch("requests.post")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Mock config attributes
        mocker.patch.object(cfg, "SMTP_USER", "test_api_key")
        mocker.patch.object(cfg, "SMTP_PASSWORD", "test_api_secret")

        success, message = sender.send_email("test@example.com", "Subject", "Body")

        assert success is True
        assert message == ""
        mock_post.assert_called_once()

    def test_send_email_api_failure(self, sender, mocker):
        """Verify that a Mailjet API error is handled correctly."""
        mock_post = mocker.patch(
            "requests.post",
            side_effect=requests.exceptions.RequestException("API Error"),
        )
        # Mock the response attribute on the exception
        mock_post.side_effect.response = MagicMock(text="Bad Request")

        mocker.patch.object(cfg, "SMTP_USER", "test_api_key")
        mocker.patch.object(cfg, "SMTP_PASSWORD", "test_api_secret")

        success, message = sender.send_email("test@example.com", "Subject", "Body")

        assert success is False
        assert "API Error" in message

    def test_send_email_no_credentials(self, sender, mocker):
        """Verify failure when Mailjet credentials are not configured."""
        # Ensure the attributes don't exist
        if hasattr(cfg, "SMTP_USER"):
            mocker.stopall()  # Stop any previous mocks if needed
            mocker.patch.object(cfg, "SMTP_USER", None)

        success, message = sender.send_email("test@example.com", "Subject", "Body")
        assert success is False
        assert "Mailjet API keys are not configured" in message


class TestEmailFactory:
    """Tests for the get_email_sender factory function."""

    def test_get_smtp_sender_by_default(self, mocker):
        """Verify it returns SMTP sender if provider is not set."""
        # Ensure EMAIL_PROVIDER is not set on cfg
        if hasattr(cfg, "EMAIL_PROVIDER"):
            mocker.patch.object(cfg, "EMAIL_PROVIDER", None)
        sender = mail.get_email_sender()
        assert isinstance(sender, mail.SMTPMailSender)

    def test_get_smtp_sender_explicitly(self, mocker):
        """Verify it returns SMTP sender when configured."""
        mocker.patch.object(cfg, "EMAIL_PROVIDER", "smtp")
        sender = mail.get_email_sender()
        assert isinstance(sender, mail.SMTPMailSender)

    def test_get_mailjet_sender(self, mocker):
        """Verify it returns Mailjet sender when configured."""
        mocker.patch.object(cfg, "EMAIL_PROVIDER", "mailjet")
        sender = mail.get_email_sender()
        assert isinstance(sender, mail.MailjetSender)


@patch("blossomtune_gradio.mail.get_email_sender")
def test_send_activation_email_success(mock_get_sender):
    """Test successful activation email dispatch."""
    mock_sender_instance = MagicMock()
    mock_sender_instance.send_email.return_value = (True, "")
    mock_get_sender.return_value = mock_sender_instance

    success, message = mail.send_activation_email("test@example.com", "12345")

    assert success is True
    assert message == ""
    mock_sender_instance.send_email.assert_called_once()
    # Check that the subject contains the right text
    call_args, _ = mock_sender_instance.send_email.call_args
    assert "Your BlossomTune Activation Code" in call_args[1]


@patch("blossomtune_gradio.mail.get_email_sender")
def test_send_activation_email_failure(mock_get_sender):
    """Test failed activation email dispatch."""
    mock_sender_instance = MagicMock()
    mock_sender_instance.send_email.return_value = (False, "Provider Error")
    mock_get_sender.return_value = mock_sender_instance

    success, message = mail.send_activation_email("test@example.com", "12345")

    assert success is False
    assert "Provider Error" in message
