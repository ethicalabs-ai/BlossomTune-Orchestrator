import time
import sqlite3
import gradio as gr
import pandas as pd

from blossomtune_gradio import config as cfg
from blossomtune_gradio.logs import log
from blossomtune_gradio import federation as fed
from blossomtune_gradio import processing
from blossomtune_gradio.settings import settings
from blossomtune_gradio import util

from . import components
from . import auth


def log_updater_generator():
    """Continuously yields log updates every 1 second."""
    while True:
        yield log.output
        time.sleep(1)


def get_full_status_update(
    profile: gr.OAuthProfile | None, oauth_token: gr.OAuthToken | None
):
    owner = auth.is_space_owner(profile, oauth_token)
    auth_status = "Authenticating..."
    is_on_space = cfg.SPACE_OWNER is not None
    hf_handle_val = ""
    hf_handle_interactive = not is_on_space

    if is_on_space:
        if profile:
            if owner:
                auth_status = settings.get_text(
                    "auth_status_logged_in_owner_md", profile=profile
                )
            else:
                auth_status = settings.get_text(
                    "auth_status_logged_in_user_md", profile=profile
                )
            hf_handle_val = profile.username
        else:
            auth_status = settings.get_text("auth_status_not_logged_in_md")
    else:
        auth_status = settings.get_text("auth_status_local_mode_md")

    with sqlite3.connect(cfg.DB_PATH) as conn:
        pending_rows = conn.execute(
            "SELECT participant_id, hf_handle, email FROM requests WHERE status = 'pending' AND is_activated = 1 ORDER BY timestamp ASC"
        ).fetchall()
        approved_rows = conn.execute(
            "SELECT participant_id, hf_handle, email, partition_id FROM requests WHERE status = 'approved' ORDER BY timestamp DESC"
        ).fetchall()

    # Superlink Status Logic
    superlink_btn_update = gr.update()  # Default empty update

    if cfg.SUPERLINK_MODE == "internal":
        superlink_is_running = (
            processing.process_store["superlink"]
            and processing.process_store["superlink"].poll() is None
        )
        superlink_status = "🟢 Running" if superlink_is_running else "🔴 Not Running"
        if superlink_is_running:
            superlink_btn_update = gr.update(
                value="🛑 Stop Superlink", variant="stop", interactive=True
            )
        else:
            superlink_btn_update = gr.update(
                value="🚀 Start Superlink", variant="secondary", interactive=True
            )

    elif cfg.SUPERLINK_MODE == "external":
        if not cfg.SUPERLINK_HOST:
            superlink_status = "🔴 Not Configured"
        else:
            is_open = util.is_port_open(cfg.SUPERLINK_HOST, cfg.SUPERLINK_PORT)
            superlink_status = "🟢 Running" if is_open else "🔴 Not Running"
        # Disable the button in external mode
        superlink_btn_update = gr.update(value="Managed Externally", interactive=False)
    else:
        superlink_status = "⚠️ Invalid Mode"
        superlink_btn_update = gr.update(interactive=False)

    runner_is_running = (
        processing.process_store["runner"]
        and processing.process_store["runner"].poll() is None
    )
    runner_status = "🟢 Running" if runner_is_running else "🔴 Not Running"

    if runner_is_running:
        runner_btn_update = gr.update(value="🛑 Stop Runner", variant="stop")
    else:
        runner_btn_update = gr.update(value="▶️ Start Federated Run", variant="primary")

    return {
        components.admin_panel: gr.update(visible=owner),
        components.auth_status_md: gr.update(value=auth_status),
        components.superlink_status_public_txt: gr.update(value=superlink_status),
        components.superlink_status_admin_txt: gr.update(value=superlink_status),
        components.runner_status_txt: gr.update(value=runner_status),
        components.pending_requests_df: gr.update(
            value=pending_rows if pending_rows else [[]]
        ),
        components.approved_participants_df: gr.update(
            value=approved_rows if approved_rows else [[]]
        ),
        components.superlink_toggle_btn: superlink_btn_update,
        components.runner_toggle_btn: runner_btn_update,
        components.hf_handle_tb: gr.update(
            value=hf_handle_val, interactive=hf_handle_interactive
        ),
    }


def get_log_update():
    return {
        components.log_output: gr.update(value=log.output),
    }


def toggle_superlink(
    profile: gr.OAuthProfile | None, oauth_token: gr.OAuthToken | None
):
    """Toggles the Superlink process on or off."""
    if not auth.is_space_owner(profile, oauth_token):
        # Hardcode warning text as it's not in the schema
        gr.Warning("You are not authorized to perform this operation.")
        return
    if (
        processing.process_store["superlink"]
        and processing.process_store["superlink"].poll() is None
    ):
        processing.stop_process("superlink")
    else:
        processing.start_superlink()


def toggle_runner(
    runner_app: str,
    run_id: str,
    num_partitions: str,
    profile: gr.OAuthProfile | None,
    oauth_token: gr.OAuthToken | None,
):
    """Toggles the Runner process on or off."""
    if not auth.is_space_owner(profile, oauth_token):
        # Hardcode warning text as it's not in the schema
        gr.Warning("You are not authorized to perform this operation.")
        return
    if (
        processing.process_store["runner"]
        and processing.process_store["runner"].poll() is None
    ):
        processing.stop_process("runner")
    else:
        result, message = processing.start_runner(runner_app, run_id, num_partitions)
        if not result:
            gr.Warning(message)
        else:
            gr.Info(message)


def on_select_pending(pending_data: list, evt: gr.SelectData):
    """Handles selection from the pending requests table to pre-fill the form."""
    if not evt.index:
        return "", ""

    pending_df = pd.DataFrame(
        pending_data, columns=["Participant ID", "HF Handle", "Email"]
    )

    row_index = evt.index[0]
    if pending_df.empty or row_index >= len(pending_df):
        return "", ""

    participant_id = pending_df.iloc[row_index, 0]
    return participant_id, str(fed.get_next_partion_id())


def on_check_participant_status(
    hf_handle: str, email: str, activation_code: str, profile: gr.OAuthProfile | None
):
    is_on_space = cfg.SPACE_ID is not None
    if is_on_space and not profile:
        return {
            components.request_status_md: gr.update(
                value=settings.get_text("auth_required_md")
            )
        }

    user_hf_handle = profile.username if is_on_space else hf_handle
    if not user_hf_handle or not user_hf_handle.strip():
        return {
            components.request_status_md: gr.update(
                value=settings.get_text("hf_handle_empty_md")
            )
        }

    pid_to_check = user_hf_handle.strip()
    email_to_add = email.strip()
    activation_code_to_check = activation_code.strip()
    # The federation module is responsible for getting the correct text from settings
    _, message = fed.check_participant_status(
        pid_to_check, email_to_add, activation_code_to_check
    )
    return {components.request_status_md: gr.update(value=message)}


def on_manage_fed_request(participant_id: str, partition_id: str, action: str):
    # The federation module is responsible for getting the correct text from settings
    result, message = fed.manage_request(participant_id, partition_id, action)
    if result:
        gr.Info(message)
    else:
        gr.Warning(message)
