import gradio as gr
from huggingface_hub import whoami


from blossomtune_gradio import config as cfg


def is_space_owner(profile: gr.OAuthProfile | None, oauth_token: gr.OAuthToken | None):
    """Check if the user is the owner. Always returns True for local development."""
    if cfg.SPACE_OWNER is None:
        return True
    if oauth_token:
        org_names = [org["name"] for org in whoami(oauth_token.token)["orgs"]]
    else:
        org_names = []
    return profile is not None and (
        profile.preferred_username == cfg.SPACE_OWNER or cfg.SPACE_OWNER in org_names
    )
