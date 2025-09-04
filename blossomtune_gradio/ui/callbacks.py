import time
import sqlite3
import gradio as gr
import pandas as pd

from blossomtune_gradio import config as cfg
from blossomtune_gradio.logs import log
from blossomtune_gradio import federation as fed
from blossomtune_gradio import processing

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
            auth_status = (
                f"✅ Logged in as **{profile.name}**. You are the space owner."
                if owner
                else f"Logged in as: {profile.name}."
            )
            hf_handle_val = profile.name
        else:
            auth_status = "⚠️ You are not logged in. Please log in with Hugging Face."
    else:
        auth_status = "Running in local mode. Admin controls enabled."

    with sqlite3.connect(cfg.DB_PATH) as conn:
        pending_rows = conn.execute(
            "SELECT participant_id, hf_handle, email FROM requests WHERE status = 'pending' AND is_activated = 1 ORDER BY timestamp ASC"
        ).fetchall()
        approved_rows = conn.execute(
            "SELECT participant_id, hf_handle, email, partition_id FROM requests WHERE status = 'approved' ORDER BY timestamp DESC"
        ).fetchall()

    superlink_is_running = (
        processing.process_store["superlink"]
        and processing.process_store["superlink"].poll() is None
    )
    runner_is_running = (
        processing.process_store["runner"]
        and processing.process_store["runner"].poll() is None
    )

    superlink_status = "🟢 Running" if superlink_is_running else "🔴 Not Running"
    runner_status = "🟢 Running" if runner_is_running else "🔴 Not Running"

    # --- Start of Fix ---
    # Use gr.update() to modify existing components instead of creating new ones.
    if superlink_is_running:
        superlink_btn_update = gr.update(value="🛑 Stop Superlink", variant="stop")
    else:
        superlink_btn_update = gr.update(
            value="🚀 Start Superlink", variant="secondary"
        )

    if runner_is_running:
        runner_btn_update = gr.update(value="🛑 Stop Runner", variant="stop")
    else:
        runner_btn_update = gr.update(value="▶️ Start Federated Run", variant="primary")

    return {
        components.admin_panel: gr.update(visible=owner),
        components.auth_status_md: gr.update(value=auth_status),
        # components.log_output: gr.update(value=log.output),
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

    # Ensure pending_data is a Pandas DataFrame
    pending_df = pd.DataFrame(
        pending_data, columns=["Participant ID", "HF Handle", "Email"]
    )

    row_index = evt.index[0]
    # Use pending_df.empty to check for truthiness
    if pending_df.empty or row_index >= len(pending_df):
        return "", ""

    # Use .iloc to safely access the row by index
    participant_id = pending_df.iloc[row_index, 0]
    return participant_id, str(fed.get_next_partion_id())


def on_check_participant_status(
    hf_handle: str, email: str, activation_code: str, profile: gr.OAuthProfile | None
):
    is_on_space = cfg.SPACE_ID is not None
    if is_on_space and not profile:
        return {
            components.request_status_md: gr.update(
                "### ❌ Authentication Required\n**Please log in with Hugging Face to request to join the federation.**"
            )
        }

    user_hf_handle = profile.name if is_on_space else hf_handle
    if not user_hf_handle or not user_hf_handle.strip():
        return {
            components.request_status_md: gr.update(
                value="Hugging Face handle cannot be empty."
            )
        }

    pid_to_check = user_hf_handle.strip()
    email_to_add = email.strip()
    activation_code_to_check = activation_code.strip()
    _, message = fed.check_participant_status(
        pid_to_check, email_to_add, activation_code_to_check
    )
    return {components.request_status_md: gr.update(value=message)}


def on_manage_fed_request(participant_id: str, partition_id: str, action: str):
    result, message = fed.manage_request(participant_id, partition_id, action)
    if result:
        gr.Info(message)
    else:
        gr.Warning(message)
