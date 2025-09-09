import gradio as gr

from blossomtune_gradio import database as db
from blossomtune_gradio.ui import components
from blossomtune_gradio.ui import callbacks


with gr.Blocks(theme=gr.themes.Soft(), title="Flower Superlink & Runner") as demo:
    db.init()
    gr.Markdown("BlossomTune 🌸 Flower Superlink & Runner")
    with gr.Row():
        login_button = gr.LoginButton()
        components.auth_status_md.render()

    with gr.Tabs():
        with gr.TabItem("Live Status"):
            gr.Markdown("## 📡 Service Status")
            with gr.Row():
                superlink_status_public_txt = (
                    components.superlink_status_public_txt.render()
                )
            gr.Markdown("## 📜 Live Logs")
            log_output = components.log_output.render()

        with gr.TabItem("Join Federation"):
            gr.Markdown("## Check Status or Request to Join")
            hf_handle_tb = components.hf_handle_tb.render()
            email_tb = components.email_tb.render()
            activation_code_tb = components.activation_code_tb.render()
            gr.Markdown(
                "You do not need to enter an activation code to register. This field is only for after you have received your authentication email."
            )
            check_status_btn = gr.Button("Submit Request / Activate", variant="primary")
            request_status_md = components.request_status_md.render()
            check_status_btn.click(
                fn=callbacks.on_check_participant_status,
                inputs=[hf_handle_tb, email_tb, activation_code_tb],
                outputs=[request_status_md],
            )

        with gr.TabItem("Admin Panel"):
            admin_panel = components.admin_panel.render()
            with admin_panel:
                gr.Markdown("## ⚙️ Infrastructure Control")
                with gr.Row():
                    superlink_status_admin_txt = (
                        components.superlink_status_admin_txt.render()
                    )
                    superlink_toggle_btn = components.superlink_toggle_btn.render()

                gr.Markdown("## 💐 Federation Control")
                with gr.Row():
                    runner_status_txt = components.runner_status_txt.render()
                    runner_toggle_btn = components.runner_toggle_btn.render()
                with gr.Row():
                    runner_app_dd = components.runner_app_dd.render()
                    run_id_tb = components.run_id_tb.render()
                    num_partitions_tb = components.num_partitions_tb.render()

                gr.Markdown("--- \n ## 🛂 Federation Requests")
                with gr.Row():
                    with gr.Column(scale=3):
                        pending_requests_df = components.pending_requests_df.render()
                        approved_participants_df = (
                            components.approved_participants_df.render()
                        )
                    with gr.Column(scale=2):
                        gr.Markdown("#### Manage Selection")
                        selected_participant_id_tb = (
                            components.selected_participant_id_tb.render()
                        )
                        partition_id_tb = components.partition_id_tb.render()
                        with gr.Row():
                            approve_btn = gr.Button("✅ Approve")
                            deny_btn = gr.Button("❌ Deny")

    outputs_to_update = [
        components.admin_panel,
        components.auth_status_md,
        # components.log_output,
        components.superlink_status_public_txt,
        components.superlink_status_admin_txt,
        components.runner_status_txt,
        components.pending_requests_df,
        components.approved_participants_df,
        components.superlink_toggle_btn,
        components.runner_toggle_btn,
        components.hf_handle_tb,
    ]

    superlink_toggle_btn.click(
        fn=callbacks.toggle_superlink, inputs=None, outputs=None
    ).then(fn=callbacks.get_full_status_update, inputs=None, outputs=outputs_to_update)

    runner_toggle_btn.click(
        fn=callbacks.toggle_runner,
        inputs=[
            components.runner_app_dd,
            components.run_id_tb,
            components.num_partitions_tb,
        ],
        outputs=None,
    ).then(fn=callbacks.get_full_status_update, inputs=None, outputs=outputs_to_update)

    approve_btn.click(
        fn=callbacks.on_manage_fed_request,
        inputs=[
            components.selected_participant_id_tb,
            components.partition_id_tb,
            gr.Textbox("approve", visible=False),
        ],
        outputs=None,
    ).then(fn=callbacks.get_full_status_update, inputs=None, outputs=outputs_to_update)
    deny_btn.click(
        fn=callbacks.on_manage_fed_request,
        inputs=[
            components.selected_participant_id_tb,
            components.partition_id_tb,
            gr.Textbox("deny", visible=False),
        ],
        outputs=None,
    ).then(fn=callbacks.get_full_status_update, inputs=None, outputs=outputs_to_update)

    pending_requests_df.select(
        fn=callbacks.on_select_pending,
        inputs=[components.pending_requests_df],
        outputs=[components.selected_participant_id_tb, components.partition_id_tb],
    )

    # Full UI refresh on load and after login
    demo.load(
        fn=callbacks.get_full_status_update,
        inputs=None,
        outputs=outputs_to_update,
    )
    login_button.click(
        fn=callbacks.get_full_status_update, inputs=None, outputs=outputs_to_update
    )
    # Live log updates
    demo.load(fn=callbacks.log_updater_generator, inputs=None, outputs=[log_output])
