import os

from blossomtune_gradio import util

# BlossomTune yaml config path
BLOSSOMTUNE_CONFIG = os.getenv("BLOSSOMTUNE_CONFIG", None)

# HF Space ID
SPACE_ID = os.getenv("SPACE_ID", "ethicalabs/BlossomTune-Orchestrator")
SPACE_OWNER = os.getenv("SPACE_OWNER", SPACE_ID.split("/")[0] if SPACE_ID else None)

# Use persistent storage if available
DB_PATH = (
    "/data/db/federation.db" if os.path.isdir("/data/db") else "./data/db/federation.db"
)
SQLALCHEMY_URL = f"sqlite:///{os.path.abspath(DB_PATH)}"
MAX_NUM_NODES = int(os.getenv("MAX_NUM_NODES", "20"))
SMTP_SENDER = os.getenv("SMTP_SENDER", "hello@ethicalabs.ai")
SMTP_SERVER = os.getenv("SMTP_SERVER", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SMTP_REQUIRE_TLS = util.strtobool(os.getenv("SMTP_REQUIRE_TLS", "false"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "smtp")
SUPERLINK_HOST = os.getenv("SUPERLINK_HOST", "127.0.0.1:9092")
SUPERLINK_PORT = int(os.getenv("SUPERLINK_PORT", 9092))
SUPERLINK_CONTROL_API_PORT = int(os.getenv("SUPERLINK_CONTROL_API_PORT", 9093))
SUPERLINK_MODE = os.getenv("SUPERLINK_MODE", "internal").lower()  # Or external
RUN_MIGRATIONS_ON_STARTUP = util.strtobool(
    os.getenv("RUN_MIGRATIONS_ON_STARTUP", "true")
)  # Set to false in prod.

# TLS root cert path. For production only.
TLS_CERT_DIR = os.getenv("TLS_CERT_DIR", "./certs/")
TLS_CA_KEY_PATH = os.getenv("TLS_CA_KEY_PATH", False)
TLS_CA_CERT_PATH = os.getenv("TLS_CA_CERT_PATH", False)

PROJECT_PATH = os.path.realpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
)

# BlossomTune cert - To be distributed to the participants (supernodes).
BLOSSOMTUNE_TLS_CERT_PATH = os.getenv(
    "BLOSSOMTUNE_TLS_CERT_PATH",
    "/data/certs"
    if os.path.isdir("/data/certs")
    else os.path.join(PROJECT_PATH, "./data/certs"),
)
BLOSSOMTUNE_TLS_CA_CERTFILE = os.path.join(BLOSSOMTUNE_TLS_CERT_PATH, "ca.crt")
BLOSSOMTUNE_TLS_CERTFILE = os.path.join(BLOSSOMTUNE_TLS_CERT_PATH, "server.pem")
BLOSSOMTUNE_TLS_KEYFILE = os.path.join(BLOSSOMTUNE_TLS_CERT_PATH, "server.key")

# EC Auth - Keys
AUTH_KEYS_DIR = os.getenv(
    "AUTH_KEYS_DIR",
    "/data/keys/"
    if os.path.isdir("/data/keys")
    else os.path.join(PROJECT_PATH, "./data/keys/"),
)

# EC Auth - CSV File
AUTH_KEYS_CSV_PATH = os.getenv(
    "AUTH_KEYS_CSV_PATH",
    os.path.join(AUTH_KEYS_DIR, "authorized_supernodes.csv"),
)

# Flower Apps
FLOWER_APPS = os.getenv("FLOWER_APPS", ["flower_apps.quickstart_huggingface"])
FLOWER_APPS = (
    FLOWER_APPS
    if isinstance(FLOWER_APPS, list)
    else [app.strip() for app in FLOWER_APPS.split(",")]
)
