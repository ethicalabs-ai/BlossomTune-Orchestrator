import string
import secrets
import sqlite3

from datetime import datetime

from blossomtune_gradio import config as cfg
from blossomtune_gradio import mail
from blossomtune_gradio import util
from blossomtune_gradio.settings import settings


def generate_participant_id(length=6):
    """Generates a random, uppercase alphanumeric participant ID."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_activation_code(length=8):
    """Generates a random, uppercase alphanumeric activation code."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def check_participant_status(pid_to_check: str, email: str, activation_code: str):
    """Handles a participant's request to join, activate, or check status."""
    with sqlite3.connect(cfg.DB_PATH) as conn:
        cursor = conn.cursor()
        if activation_code:
            cursor.execute(
                "SELECT participant_id, status, partition_id, is_activated, activation_code FROM requests WHERE hf_handle = ? AND email = ? AND activation_code = ?",
                (pid_to_check, email, activation_code),
            )
        else:
            cursor.execute(
                "SELECT participant_id, status, partition_id, is_activated, activation_code FROM requests WHERE hf_handle = ? AND email = ?",
                (pid_to_check, email),
            )
        result = cursor.fetchone()

        cursor.execute("SELECT value FROM config WHERE key = 'num_partitions'")
        num_partitions_res = cursor.fetchone()
        num_partitions = num_partitions_res[0] if num_partitions_res else "10"

    # Case 1: New user registration
    if result is None:
        if activation_code:
            return (False, settings.get_text("activation_invalid_md"), None)
        if not util.validate_email(email):
            return (False, settings.get_text("invalid_email_md"), None)

        with sqlite3.connect(cfg.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM requests WHERE status = 'approved'")
            approved_count = cursor.fetchone()[0]
            if approved_count >= cfg.MAX_NUM_NODES:
                return (False, settings.get_text("federation_full_md"), None)

        participant_id = generate_participant_id()
        new_activation_code = generate_activation_code()
        mail_sent, message = mail.send_activation_email(email, new_activation_code)
        if mail_sent:
            with sqlite3.connect(cfg.DB_PATH) as conn:
                conn.execute(
                    "INSERT INTO requests (participant_id, status, timestamp, hf_handle, email, activation_code, is_activated) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        participant_id,
                        "pending",
                        datetime.utcnow().isoformat(),
                        pid_to_check,
                        email,
                        new_activation_code,
                        0,
                    ),
                )
            return (True, settings.get_text("registration_submitted_md"), None)
        else:
            return (False, message, None)

    # Existing user
    participant_id, status, partition_id, is_activated, stored_code = result

    # Case 2: User is activating their account
    if not is_activated:
        if activation_code == stored_code:
            with sqlite3.connect(cfg.DB_PATH) as conn:
                conn.execute(
                    "UPDATE requests SET is_activated = 1 WHERE hf_handle = ?",
                    (pid_to_check,),
                )
            return (True, settings.get_text("activation_successful_md"), None)
        else:
            return (False, settings.get_text("activation_invalid_md"), None)
    else:
        if not activation_code:
            return (False, settings.get_text("missing_activation_code_md"))

    # Case 3: Activated user is checking their status
    if status == "approved":
        hostname = (
            "localhost"
            if not cfg.SPACE_ID
            else f"{cfg.SPACE_ID.split('/')[1]}-{cfg.SPACE_ID.split('/')[0]}.hf.space"
        )
        superlink_hostname = cfg.SUPERLINK_HOST or hostname

        connection_string = settings.get_text(
            "status_approved_md",
            participant_id=participant_id,
            partition_id=partition_id,
            superlink_hostname=superlink_hostname,
            superlink_port=cfg.SUPERLINK_PORT,
            num_partitions=num_partitions,
        )
        # TODO: build and provide .blossomfile for download
        return (True, connection_string, cfg.BLOSSOMTUNE_TLS_CERT_PATH)
    elif status == "pending":
        return (False, settings.get_text("status_pending_md"))
    else:  # Denied
        return (
            False,
            settings.get_text("status_denied_md", participant_id=participant_id),
            None,
        )


def manage_request(participant_id: str, partition_id: str, action: str):
    """Admin function to approve/deny a request and assign a partition ID."""
    if not participant_id:
        return False, "Please select a participant from the pending requests table."

    if action == "approve":
        if not partition_id or not partition_id.isdigit():
            return False, "Please provide a valid integer for the Partition ID."

        p_id_int = int(partition_id)
        with sqlite3.connect(cfg.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT is_activated FROM requests WHERE participant_id = ?",
                (participant_id,),
            )
            is_activated_res = cursor.fetchone()
            if not is_activated_res or not is_activated_res[0]:
                return (
                    False,
                    settings.get_text("participant_not_activated_warning_md"),
                )

            cursor.execute(
                "SELECT 1 FROM requests WHERE partition_id = ? AND status = 'approved'",
                (p_id_int,),
            )
            if cursor.fetchone():
                return (
                    False,
                    settings.get_text(
                        "partition_in_use_warning_md", partition_id=p_id_int
                    ),
                )

            conn.execute(
                "UPDATE requests SET status = ?, partition_id = ? WHERE participant_id = ?",
                ("approved", p_id_int, participant_id),
            )
            return (
                True,
                f"Participant {participant_id} is allowed to join the federation.",
            )
    else:  # Deny
        with sqlite3.connect(cfg.DB_PATH) as conn:
            conn.execute(
                "UPDATE requests SET status = ?, partition_id = NULL WHERE participant_id = ?",
                ("denied", participant_id),
            )
            return (
                True,
                f"Participant {participant_id} is not allowed to join the federation.",
            )


def get_next_partion_id() -> int:
    with sqlite3.connect(cfg.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT partition_id FROM requests WHERE status = 'approved' AND partition_id IS NOT NULL"
        )
        used_ids = {row[0] for row in cursor.fetchall()}

    next_id = 0
    while next_id in used_ids:
        next_id += 1
    return next_id
