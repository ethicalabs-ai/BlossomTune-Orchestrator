import string
import secrets

from blossomtune_gradio import config as cfg
from blossomtune_gradio import mail
from blossomtune_gradio import util
from blossomtune_gradio.settings import settings
from blossomtune_gradio.database import SessionLocal, Request, Config


def generate_participant_id(length=6):
    """Generates a random, uppercase alphanumeric participant ID."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_activation_code(length=8):
    """Generates a random, uppercase alphanumeric activation code."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def check_participant_status(pid_to_check: str, email: str, activation_code: str):
    """
    Handles a participant's request to join, activate, or check status using SQLAlchemy.
    Returns a tuple: (is_approved: bool, message: str, data: any | None)
    The 'is_approved' boolean is True ONLY when the participant's final status is 'approved'.
    """
    with SessionLocal() as db:
        query = db.query(Request).filter(
            Request.hf_handle == pid_to_check, Request.email == email
        )
        if activation_code:
            query = query.filter(Request.activation_code == activation_code)

        request = query.first()

        num_partitions_config = (
            db.query(Config).filter(Config.key == "num_partitions").first()
        )
        num_partitions = num_partitions_config.value if num_partitions_config else "10"

        # Case 1: New user registration
        if request is None:
            if activation_code:
                return (False, settings.get_text("activation_invalid_md"), None)
            if not util.validate_email(email):
                return (False, settings.get_text("invalid_email_md"), None)

            approved_count = (
                db.query(Request).filter(Request.status == "approved").count()
            )
            if approved_count >= cfg.MAX_NUM_NODES:
                return (False, settings.get_text("federation_full_md"), None)

            participant_id = generate_participant_id()
            new_activation_code = generate_activation_code()
            mail_sent, message = mail.send_activation_email(email, new_activation_code)

            if mail_sent:
                new_request = Request(
                    participant_id=participant_id,
                    hf_handle=pid_to_check,
                    email=email,
                    activation_code=new_activation_code,
                )
                db.add(new_request)
                db.commit()
                # A successful registration step, but not yet approved for federation.
                return (False, settings.get_text("registration_submitted_md"), None)
            else:
                return (False, message, None)

        # Case 2: User is activating their account
        if not request.is_activated:
            if activation_code == request.activation_code:
                request.is_activated = 1
                db.commit()
                # A successful activation step, but not yet approved.
                return (False, settings.get_text("activation_successful_md"), None)
            else:
                return (False, settings.get_text("activation_invalid_md"), None)

        # At this point, user is activated.
        # They must provide the activation code to check their final status.
        if not activation_code:
            return (False, settings.get_text("missing_activation_code_md"), None)

        # Case 3: Activated user is checking their final status
        if request.status == "approved":
            hostname = (
                "localhost"
                if not cfg.SPACE_ID
                else f"{cfg.SPACE_ID.split('/')[1]}-{cfg.SPACE_ID.split('/')[0]}.hf.space"
            )
            superlink_hostname = cfg.SUPERLINK_HOST or hostname

            connection_string = settings.get_text(
                "status_approved_md",
                participant_id=request.participant_id,
                partition_id=request.partition_id,
                superlink_hostname=superlink_hostname,
                num_partitions=num_partitions,
            )
            # The user is fully approved. Return success and the cert path.
            return (True, connection_string, cfg.BLOSSOMTUNE_TLS_CERT_PATH)
        elif request.status == "pending":
            return (False, settings.get_text("status_pending_md"), None)
        else:  # Denied
            return (
                False,
                settings.get_text(
                    "status_denied_md", participant_id=request.participant_id
                ),
                None,
            )


def manage_request(participant_id: str, partition_id: str, action: str):
    """Admin function to approve/deny a request and assign a partition ID."""
    if not participant_id:
        return False, "Please select a participant from the pending requests table."

    with SessionLocal() as db:
        request = (
            db.query(Request).filter(Request.participant_id == participant_id).first()
        )
        if not request:
            return False, "Participant not found."

        if action == "approve":
            if not partition_id or not partition_id.isdigit():
                return False, "Please provide a valid integer for the Partition ID."

            p_id_int = int(partition_id)
            if not request.is_activated:
                return (
                    False,
                    settings.get_text("participant_not_activated_warning_md"),
                )

            existing_participant = (
                db.query(Request)
                .filter(Request.partition_id == p_id_int, Request.status == "approved")
                .first()
            )

            if existing_participant:
                return (
                    False,
                    settings.get_text(
                        "partition_in_use_warning_md", partition_id=p_id_int
                    ),
                )

            request.status = "approved"
            request.partition_id = p_id_int
            db.commit()
            return (
                True,
                f"Participant {participant_id} is allowed to join the federation.",
            )
        else:  # Deny
            request.status = "denied"
            request.partition_id = None
            db.commit()
            return (
                True,
                f"Participant {participant_id} is not allowed to join the federation.",
            )


def get_next_partion_id() -> int:
    """Finds the lowest available partition ID."""
    with SessionLocal() as db:
        used_ids_query = (
            db.query(Request.partition_id)
            .filter(Request.status == "approved", Request.partition_id.isnot(None))
            .all()
        )
        used_ids = {row[0] for row in used_ids_query}

    next_id = 0
    while next_id in used_ids:
        next_id += 1
    return next_id
