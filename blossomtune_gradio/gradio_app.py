import os
import time
import shutil
import pandas as pd
import gradio as gr
import subprocess
import sqlite3
import threading
import secrets
import string
import importlib
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from huggingface_hub import whoami


import blossomtune_gradio.database as db
import blossomtune_gradio.config as cfg

from blossomtune_gradio.logs import log


# In-memory store for background processes and logs
process_store = {"superlink": None, "runner": None}


def generate_participant_id(length=6):
    """Generates a random, uppercase alphanumeric participant ID."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_activation_code(length=8):
    """Generates a random, uppercase alphanumeric activation code."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


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


def check_participant_status(
    hf_handle: str, email: str, activation_code: str, profile: gr.OAuthProfile | None
):
    """Handles a participant's request to join, activate, or check status."""
    is_on_space = cfg.SPACE_ID is not None

    if is_on_space and not profile:
        return {
            request_status_md: gr.Markdown(
                "### Authentication Required\n**Please log in with Hugging Face to request to join the federation.**"
            )
        }

    user_hf_handle = profile.name if is_on_space else hf_handle
    if not user_hf_handle or not user_hf_handle.strip():
        return {request_status_md: gr.Markdown("Hugging Face handle cannot be empty.")}

    pid_to_check = user_hf_handle.strip()
    email_to_add = email.strip()
    activation_code_to_check = activation_code.strip()

    with sqlite3.connect(cfg.DB_PATH) as conn:
        cursor = conn.cursor()
        # NOTE: Assumes DB schema is updated with `is_activated` and `activation_code`
        if activation_code_to_check:
            cursor.execute(
                "SELECT participant_id, status, partition_id, is_activated, activation_code FROM requests WHERE hf_handle = ? AND email = ? AND activation_code = ?",
                (pid_to_check, email_to_add, activation_code_to_check),
            )
        else:
            cursor.execute(
                "SELECT participant_id, status, partition_id, is_activated, activation_code FROM requests WHERE hf_handle = ? AND email = ?",
                (pid_to_check, email_to_add),
            )
        result = cursor.fetchone()

        cursor.execute("SELECT value FROM config WHERE key = 'num_partitions'")
        num_partitions_res = cursor.fetchone()
        num_partitions = num_partitions_res[0] if num_partitions_res else "10"

    # Case 1: New user registration
    if result is None:
        if activation_code_to_check:
            return {
                request_status_md: gr.Markdown(
                    "### ❌ Activation code is not valid, or participant hasn't subscribed yet."
                )
            }
        if not email_to_add or "@" not in email_to_add:
            return {
                request_status_md: gr.Markdown("Please provide a valid email address.")
            }

        with sqlite3.connect(cfg.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM requests WHERE status = 'approved'")
            approved_count = cursor.fetchone()[0]
            if approved_count >= cfg.MAX_NUM_NODES:
                return {
                    request_status_md: gr.Markdown(
                        "### Federation Full\n**We're sorry, but we cannot accept new participants at this time.**"
                    )
                }

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
                    email_to_add,
                    new_activation_code,
                    0,
                ),
            )
        send_activation_email(email_to_add, new_activation_code)
        return {
            request_status_md: gr.Markdown(
                "✅ **Registration Submitted!** Please check your email for an activation code to complete your request."
            )
        }

    # Existing user
    participant_id, status, partition_id, is_activated, stored_code = result

    # Case 2: User is activating their account
    if not is_activated:
        if activation_code_to_check == stored_code:
            with sqlite3.connect(cfg.DB_PATH) as conn:
                conn.execute(
                    "UPDATE requests SET is_activated = 1 WHERE hf_handle = ?",
                    (pid_to_check,),
                )
            return {
                request_status_md: gr.Markdown(
                    "✅ **Activation Successful!** Your request is now pending review by an administrator."
                )
            }
        else:
            return {
                request_status_md: gr.Markdown(
                    "### ❌ Activation code is not valid, or participant hasn't subscribed yet."
                )
            }
    else:
        if not activation_code_to_check:
            return {
                request_status_md: gr.Markdown(
                    "⏳ **Missing Activation Code.** Please check your email and enter the activation code you received."
                )
            }

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
        return {request_status_md: gr.Markdown(connection_string)}
    elif status == "pending":
        return {
            request_status_md: gr.Markdown(
                "### ⏳ Pending\nYour request has been activated and is awaiting administrator review."
            )
        }
    else:  # Denied
        return {
            request_status_md: gr.Markdown(
                f"### ❌ Denied\nYour request for ID `{participant_id}` has been denied."
            )
        }


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


# --- Backend Process Management ---
def run_process(command, process_key):
    """Generic function to run a background process and log its output."""
    global process_store
    log(f"[{process_key.title()}] Starting: {' '.join(command)}")
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
        process_store[process_key] = process
        for line in iter(process.stdout.readline, ""):
            log(f"[{process_key.title()}] {line.strip()}")
        process.wait()
    except Exception as e:
        log(f"[{process_key.title()}] CRITICAL ERROR: {e}")
    finally:
        log(f"[{process_key.title()}] Process finished.")
        process_store[process_key] = None


def start_superlink(profile: gr.OAuthProfile | None, oauth_token: gr.OAuthToken | None):
    if not is_space_owner(profile, oauth_token):
        return
    if process_store["superlink"] and process_store["superlink"].poll() is None:
        return
    command = [shutil.which("flower-superlink"), "--insecure"]
    threading.Thread(
        target=run_process, args=(command, "superlink"), daemon=True
    ).start()


def start_runner(
    runner_app: str,
    run_id: str,
    num_partitions: str,
    profile: gr.OAuthProfile | None,
    oauth_token: gr.OAuthToken | None,
):
    if not is_space_owner(profile, oauth_token):
        return
    if process_store["runner"] and process_store["runner"].poll() is None:
        gr.Warning("A Runner process is already running.")
        return
    if not (process_store["superlink"] and process_store["superlink"].poll() is None):
        gr.Warning(
            "Superlink is not running. Please start it before starting the runner."
        )
        return
    if not all([runner_app, run_id, num_partitions]):
        gr.Warning("Please provide a Runner App, Run ID, and Total Partitions.")
        return
    if not num_partitions.isdigit() or int(num_partitions) <= 0:
        gr.Warning("Total Partitions must be a positive integer.")
        return

    with sqlite3.connect(cfg.DB_PATH) as conn:
        conn.execute(
            "UPDATE config SET value = ? WHERE key = 'num_partitions'",
            (num_partitions,),
        )
        conn.commit()
    try:
        runner_app_path = os.path.dirname(importlib.import_module(runner_app).__file__)
    except ModuleNotFoundError:
        gr.Warning(f"Unable to find app module '{runner_app}'.")
        return
    command = [
        shutil.which("flwr"),
        "run",
        runner_app_path,
        "local-deployment",
        "--stream",
    ]
    threading.Thread(target=run_process, args=(command, "runner"), daemon=True).start()


def stop_process(
    process_key: str, profile: gr.OAuthProfile | None, oauth_token: gr.OAuthToken | None
):
    if not is_space_owner(profile, oauth_token):
        return
    process = process_store.get(process_key)
    if process and process.poll() is None:
        process.terminate()
        process.wait()
        log(f"[{process_key.title()}] Process stopped by user.")
        process_store[process_key] = None
    else:
        log(
            f"[{process_key.title()}] Stop command received, but no process was running."
        )


def toggle_superlink(
    profile: gr.OAuthProfile | None, oauth_token: gr.OAuthToken | None
):
    """Toggles the Superlink process on or off."""
    if process_store["superlink"] and process_store["superlink"].poll() is None:
        stop_process("superlink", profile, oauth_token)
    else:
        start_superlink(profile, oauth_token)


def toggle_runner(
    runner_app: str,
    run_id: str,
    num_partitions: str,
    profile: gr.OAuthProfile | None,
    oauth_token: gr.OAuthToken | None,
):
    """Toggles the Runner process on or off."""
    if process_store["runner"] and process_store["runner"].poll() is None:
        stop_process("runner", profile, oauth_token)
    else:
        start_runner(runner_app, run_id, num_partitions, profile, oauth_token)


def is_space_owner(profile: gr.OAuthProfile | None, oauth_token: gr.OAuthToken | None):
    """Check if the user is the owner. Always returns True for local development."""
    if cfg.SPACE_OWNER is None:
        return True
    org_names = [org["name"] for org in whoami(oauth_token.token)["orgs"]]
    return profile is not None and (
        profile.name == cfg.SPACE_OWNER or cfg.SPACE_OWNER in org_names
    )


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

    with sqlite3.connect(cfg.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT partition_id FROM requests WHERE status = 'approved' AND partition_id IS NOT NULL"
        )
        used_ids = {row[0] for row in cursor.fetchall()}

    next_id = 0
    while next_id in used_ids:
        next_id += 1

    return participant_id, str(next_id)


def log_updater_generator():
    """Continuously yields log updates every 1 second."""
    while True:
        yield log.output
        time.sleep(1)


def get_full_status_update(
    profile: gr.OAuthProfile | None, oauth_token: gr.OAuthToken | None
):
    owner = is_space_owner(profile, oauth_token)
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
        process_store["superlink"] and process_store["superlink"].poll() is None
    )
    runner_is_running = (
        process_store["runner"] and process_store["runner"].poll() is None
    )

    superlink_status = "🟢 Running" if superlink_is_running else "🔴 Not Running"
    runner_status = "🟢 Running" if runner_is_running else "🔴 Not Running"

    superlink_btn_ui = (
        gr.Button("🛑 Stop Superlink", variant="stop")
        if superlink_is_running
        else gr.Button("🚀 Start Superlink", variant="secondary")
    )
    runner_btn_ui = (
        gr.Button("🛑 Stop Runner", variant="stop")
        if runner_is_running
        else gr.Button("▶️ Start Federated Run", variant="primary")
    )

    return {
        admin_panel: gr.Column(visible=owner),
        auth_status_md: auth_status,
        log_output: log.output,
        superlink_status_public_txt: superlink_status,
        superlink_status_admin_txt: superlink_status,
        runner_status_txt: runner_status,
        pending_requests_df: pending_rows if pending_rows else [[]],
        approved_participants_df: approved_rows if approved_rows else [[]],
        superlink_toggle_btn: superlink_btn_ui,
        runner_toggle_btn: runner_btn_ui,
        hf_handle_tb: gr.Textbox(
            value=hf_handle_val, interactive=hf_handle_interactive
        ),
    }


def get_log_update():
    return {
        log_output: log.output,
    }


with gr.Blocks(theme=gr.themes.Soft(), title="Flower Superlink & Runner") as demo:
    db.init()
    gr.Markdown("BlossomTune 🌸 Flower Superlink & Runner")
    with gr.Row():
        login_button = gr.LoginButton()
        auth_status_md = gr.Markdown("Authenticating...")

    with gr.Tabs():
        with gr.TabItem("Live Status"):
            gr.Markdown("## 📡 Service Status")
            with gr.Row():
                superlink_status_public_txt = gr.Textbox(
                    "🔴 Not Running", label="Superlink Status", interactive=False
                )
            gr.Markdown("## 📜 Live Logs")
            log_output = gr.Textbox(
                label="Logs (Superlink & Runner)",
                lines=20,
                autoscroll=True,
                interactive=False,
                show_copy_button=True,
            )

        with gr.TabItem("Join Federation"):
            gr.Markdown("## Check Status or Request to Join")
            hf_handle_tb = gr.Textbox(
                label="Your Hugging Face Handle",
                placeholder="Enter for local testing...",
                interactive=True,  # Will be updated by get_full_status_update
            )
            email_tb = gr.Textbox(
                label="Your Contact E-mail",
                placeholder="e.g., user@example.com",
            )
            activation_code_tb = gr.Textbox(
                label="Activation Code",
                placeholder="Enter code from your email...",
            )
            gr.Markdown(
                "You do not need to enter an activation code to register. This field is only for after you have received your authentication email."
            )
            check_status_btn = gr.Button("Submit Request / Activate", variant="primary")
            request_status_md = gr.Markdown()
            check_status_btn.click(
                fn=check_participant_status,
                inputs=[hf_handle_tb, email_tb, activation_code_tb],
                outputs=[request_status_md],
            )

        with gr.TabItem("Admin Panel"):
            admin_panel = gr.Column(visible=False)
            with admin_panel:
                gr.Markdown("## ⚙️ Infrastructure Control")
                with gr.Row():
                    superlink_status_admin_txt = gr.Textbox(
                        "🔴 Not Running",
                        label="Superlink Status",
                        interactive=False,
                    )
                    superlink_toggle_btn = gr.Button(
                        "🚀 Start Superlink", variant="secondary"
                    )

                gr.Markdown("## 💐 Federation Control")
                with gr.Row():
                    runner_status_txt = gr.Textbox(
                        "🔴 Not Running", label="Runner Status", interactive=False
                    )
                    runner_toggle_btn = gr.Button(
                        "▶️ Start Federated Run", variant="primary"
                    )
                with gr.Row():
                    runner_app_dd = gr.Dropdown(
                        ["flower_apps.quickstart_huggingface"],
                        label="Select Runner App",
                        value="flower_apps.quickstart_huggingface",
                    )
                    run_id_tb = gr.Textbox(label="Run ID", placeholder="e.g., run_123")
                    num_partitions_tb = gr.Textbox(
                        label="Total Partitions", value="10", placeholder="e.g., 10"
                    )

                gr.Markdown("--- \n ## 🛂 Federation Requests")
                with gr.Row():
                    with gr.Column(scale=3):
                        pending_requests_df = gr.DataFrame(
                            headers=["Participant ID", "HF Handle", "Email"],
                            label="Pending Requests (click a row to select)",
                            row_count=(5, "dynamic"),
                            interactive=False,
                        )
                        approved_participants_df = gr.DataFrame(
                            headers=[
                                "Participant ID",
                                "HF Handle",
                                "Email",
                                "Partition ID",
                            ],
                            label="Approved Participants",
                            interactive=False,
                            row_count=(5, "dynamic"),
                        )
                    with gr.Column(scale=2):
                        gr.Markdown("#### Manage Selection")
                        selected_participant_id_tb = gr.Textbox(
                            label="Selected Participant ID",
                            interactive=False,
                        )
                        partition_id_tb = gr.Textbox(
                            label="Assign Partition ID",
                            placeholder="Auto-filled on selection...",
                        )
                        with gr.Row():
                            approve_btn = gr.Button("✅ Approve")
                            deny_btn = gr.Button("❌ Deny")

    outputs_to_update = [
        admin_panel,
        auth_status_md,
        log_output,
        superlink_status_public_txt,
        superlink_status_admin_txt,
        runner_status_txt,
        pending_requests_df,
        approved_participants_df,
        superlink_toggle_btn,
        runner_toggle_btn,
        hf_handle_tb,
    ]

    superlink_toggle_btn.click(fn=toggle_superlink, inputs=None, outputs=None).then(
        fn=get_full_status_update, inputs=None, outputs=outputs_to_update
    )

    runner_toggle_btn.click(
        fn=toggle_runner,
        inputs=[runner_app_dd, run_id_tb, num_partitions_tb],
        outputs=None,
    ).then(fn=get_full_status_update, inputs=None, outputs=outputs_to_update)

    approve_btn.click(
        fn=manage_request,
        inputs=[
            selected_participant_id_tb,
            partition_id_tb,
            gr.Textbox("approve", visible=False),
        ],
        outputs=None,
    ).then(fn=get_full_status_update, inputs=None, outputs=outputs_to_update)
    deny_btn.click(
        fn=manage_request,
        inputs=[
            selected_participant_id_tb,
            partition_id_tb,
            gr.Textbox("deny", visible=False),
        ],
        outputs=None,
    ).then(fn=get_full_status_update, inputs=None, outputs=outputs_to_update)

    pending_requests_df.select(
        fn=on_select_pending,
        inputs=[pending_requests_df],
        outputs=[selected_participant_id_tb, partition_id_tb],
    )

    # Full UI refresh on load and after login
    demo.load(
        fn=get_full_status_update,
        inputs=None,
        outputs=outputs_to_update,
    )
    login_button.click(
        fn=get_full_status_update, inputs=None, outputs=outputs_to_update
    )

    # Live log updates
    demo.load(fn=log_updater_generator, inputs=None, outputs=[log_output])
