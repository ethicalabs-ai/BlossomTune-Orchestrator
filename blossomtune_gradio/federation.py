import string
import secrets
import sqlite3
import gradio as gr
from datetime import datetime

from blossomtune_gradio import config as cfg
from blossomtune_gradio import mail


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
        # NOTE: Assumes DB schema is updated with `is_activated` and `activation_code`
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
            return (
                False,
                "### ❌ Activation code is not valid, or participant hasn't subscribed yet.",
            )
        if not email or "@" not in email:
            return False, "Please provide a valid email address."

        with sqlite3.connect(cfg.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM requests WHERE status = 'approved'")
            approved_count = cursor.fetchone()[0]
            if approved_count >= cfg.MAX_NUM_NODES:
                return (
                    False,
                    "### ❌ Federation Full\n**We're sorry, but we cannot accept new participants at this time.**",
                )

        participant_id = generate_participant_id()
        new_activation_code = generate_activation_code()
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
        mail.send_activation_email(email, new_activation_code)
        return (
            True,
            "✅ **Registration Submitted!** Please check your email for an activation code to complete your request.",
        )

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
            return (
                True,
                "✅ **Activation Successful!** Your request is now pending review by an administrator.",
            )
        else:
            return (
                False,
                "### ❌ Activation code is not valid, or participant hasn't subscribed yet.",
            )
    else:
        if not activation_code:
            (
                False,
                "⏳ **Missing Activation Code.** Please check your email and enter the activation code you received.",
            )

    # Case 3: Activated user is checking their status
    if status == "approved":
        hostname = (
            "localhost"
            if not cfg.SPACE_ID
            else f"{cfg.SPACE_ID.split('/')[1]}-{cfg.SPACE_ID.split('/')[0]}.hf.space"
        )
        connection_string = f"""### ✅ Approved
        Your request for ID `{participant_id}` has been approved.
        - **Your Assigned Partition ID:** `{partition_id}`
        - **Superlink Address:** `{hostname}:9092`

        **Instructions:** Your Flower client code should use your assigned Partition ID to load the correct data subset.
        The server address is for your client's connection command.
        
        *Example `flower-supernode` command:*
        ```bash
        flower-supernode --superlink {hostname}:9092 --insecure --node-config "partition-id={partition_id} num-partitions={num_partitions}"
        ```
        """
        return True, connection_string
    elif status == "pending":
        return (
            False,
            "### ⏳ Pending\nYour request has been activated and is awaiting administrator review.",
        )
    else:  # Denied
        return (
            False,
            f"### ❌ Denied\nYour request for ID `{participant_id}` has been denied.",
        )


def manage_request(participant_id: str, partition_id: str, action: str):
    """Admin function to approve/deny a request and assign a partition ID."""
    if not participant_id:
        gr.Warning("Please select a participant from the pending requests table.")
        return

    if action == "approve":
        if not partition_id or not partition_id.isdigit():
            gr.Warning("Please provide a valid integer for the Partition ID.")
            return

        p_id_int = int(partition_id)
        with sqlite3.connect(cfg.DB_PATH) as conn:
            cursor = conn.cursor()
            # Check if participant is activated before approval
            cursor.execute(
                "SELECT is_activated FROM requests WHERE participant_id = ?",
                (participant_id,),
            )
            is_activated_res = cursor.fetchone()
            if not is_activated_res or not is_activated_res[0]:
                gr.Warning(
                    "This participant has not activated their email yet. Approval is not allowed."
                )
                return

            # Check if the partition ID is already in use by an approved participant
            cursor.execute(
                "SELECT 1 FROM requests WHERE partition_id = ? AND status = 'approved'",
                (p_id_int,),
            )
            if cursor.fetchone():
                gr.Warning(
                    f"Partition ID {p_id_int} is already assigned. Please choose a different one."
                )
                return

            conn.execute(
                "UPDATE requests SET status = ?, partition_id = ? WHERE participant_id = ?",
                ("approved", p_id_int, participant_id),
            )
    else:  # Deny
        with sqlite3.connect(cfg.DB_PATH) as conn:
            conn.execute(
                "UPDATE requests SET status = ?, partition_id = NULL WHERE participant_id = ?",
                ("denied", participant_id),
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
