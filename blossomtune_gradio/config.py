import os

from blossomtune_gradio import util

# BlossomTune yaml config path
BLOSSOMTUNE_CONFIG = os.getenv("BLOSSOMTUNE_CONFIG", None)

# HF Space ID
SPACE_ID = os.getenv("SPACE_ID", "ethicalabs/BlossomTune-Orchestrator")
SPACE_OWNER = os.getenv("SPACE_OWNER", SPACE_ID.split("/")[0] if SPACE_ID else None)

# Use persistent storage if available
DB_PATH = "/data/federation.db" if os.path.isdir("/data") else "federation.db"
MAX_NUM_NODES = int(os.getenv("MAX_NUM_NODES", "20"))
SMTP_SENDER = os.getenv("SMTP_SENDER", "hello@ethicalabs.ai")
SMTP_SERVER = os.getenv("SMTP_SERVER", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SMTP_REQUIRE_TLS = util.strtobool(os.getenv("SMTP_REQUIRE_TLS", "false"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "smtp")
SUPERLINK_HOST = os.getenv("SUPERLINK_HOST", "")
SUPERLINK_PORT = int(os.getenv("SUPERLINK_PORT", 9092))
