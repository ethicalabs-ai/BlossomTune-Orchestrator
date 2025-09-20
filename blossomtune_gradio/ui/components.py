import gradio as gr


# This component's value is updated dynamically by callbacks.
# We'll use a simple initial value here as the schema doesn't define an "authenticating" state.
auth_status_md = gr.Markdown("Authenticating...", render=False)

superlink_status_public_txt = gr.Textbox(
    "🔴 Not Running", label="Superlink Status", interactive=False, render=False
)
log_output = gr.Textbox(
    label="Logs (Superlink & Runner)",
    lines=20,
    autoscroll=True,
    interactive=False,
    show_copy_button=True,
    render=False,
)
# The button's text/variant is updated dynamically by callbacks.
superlink_toggle_btn = gr.Button("🚀 Start Superlink", variant="secondary")

hf_handle_tb = gr.Textbox(
    label="Your Hugging Face Handle",
    placeholder="Enter for local testing...",
    interactive=True,  # This is controlled by callbacks
    render=False,
)
email_tb = gr.Textbox(
    label="Your Contact E-mail",
    placeholder="e.g., user@example.com",
    render=False,
)
activation_code_tb = gr.Textbox(
    label="Activation Code",
    placeholder="Enter code from your email...",
    render=False,
)
admin_panel = gr.Column(visible=False)
superlink_status_admin_txt = gr.Textbox(
    "🔴 Not Running",
    label="Superlink Status",
    interactive=False,
    render=False,
)
runner_status_txt = gr.Textbox(
    "🔴 Not Running", label="Runner Status", interactive=False, render=False
)
runner_toggle_btn = gr.Button("▶️ Start Federated Run", variant="primary")
runner_app_dd = gr.Dropdown(
    ["flower_apps.quickstart_huggingface"],
    label="Select Runner App",
    value="flower_apps.quickstart_huggingface",
    render=False,
)
run_id_tb = gr.Textbox(label="Run ID", placeholder="e.g., run_123")
num_partitions_tb = gr.Textbox(
    label="Total Partitions", value="10", placeholder="e.g., 10", render=False
)
# This component is populated by callbacks using the settings file.
request_status_md = gr.Markdown(render=False)

pending_requests_df = gr.DataFrame(
    headers=["Participant ID", "HF Handle", "Email"],
    label="Pending Requests (click a row to select)",
    row_count=(5, "dynamic"),
    interactive=False,
    render=False,
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
    render=False,
)
selected_participant_id_tb = gr.Textbox(
    label="Selected Participant ID",
    interactive=False,
    render=False,
)
partition_id_tb = gr.Textbox(
    label="Assign Partition ID",
    placeholder="Auto-filled on selection...",
    render=False,
)
