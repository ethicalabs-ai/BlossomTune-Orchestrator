import smtplib
import gradio as gr
from email.mime.text import MIMEText


from blossomtune_gradio.logs import log
from blossomtune_gradio import config as cfg


def send_activation_email(recipient_email, activation_code):
    """Sends the activation code to the user.

    Note: This function assumes that SMTP server settings (SMTP_SERVER, SMTP_PORT,
    SMTP_SENDER) are configured in the `blossomtune_gradio.config` module.
    """
    subject = "Your BlossomTune Activation Code"
    body = (
        "Welcome to BlossomTune!\n\n"
        "Please use the following code to activate your participation request:\n\n"
        f"{activation_code}\n\n"
        "Thank you!"
    )
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = cfg.SMTP_SENDER
    msg["To"] = recipient_email

    try:
        # For local testing with a basic SMTP server like MailHog
        with smtplib.SMTP(cfg.SMTP_SERVER, cfg.SMTP_PORT) as server:
            # If your SMTP server requires TLS or authentication, add:
            if cfg.SMTP_REQUIRE_TLS:
                server.starttls()
                server.login(cfg.SMTP_USER, cfg.SMTP_PASSWORD)
            server.send_message(msg)
        log(f"[Email] Activation code sent to {recipient_email}")
    except Exception as e:
        log(f"[Email] CRITICAL ERROR sending to {recipient_email}: {e}")
        gr.Warning(
            "There was an error sending the activation email. Please contact an administrator."
        )
