import os
import shutil
import threading
import subprocess

from blossomtune_gradio.logs import log
from blossomtune_gradio import config as cfg
from blossomtune_gradio import util
from blossomtune_gradio.database import SessionLocal, Config


# In-memory store for background processes and logs
process_store = {"superlink": None, "runner": None}


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


def start_superlink():
    # Do not start an internal process if in external mode.
    if cfg.SUPERLINK_MODE == "external":
        log.warning("start_superlink called while in external mode. Operation aborted.")
        return False, "Application is in external Superlink mode."

    if process_store["superlink"] and process_store["superlink"].poll() is None:
        return False, "Superlink process is already running."

    command = [
        shutil.which("flower-superlink"),
        "--ssl-ca-certfile",
        cfg.BLOSSOMTUNE_TLS_CA_CERTFILE,
        "--ssl-certfile",
        cfg.BLOSSOMTUNE_TLS_CERTFILE,
        "--ssl-keyfile",
        cfg.BLOSSOMTUNE_TLS_KEYFILE,
        "--auth-list-public-keys",
        cfg.AUTH_KEYS_CSV_PATH,
    ]
    threading.Thread(
        target=run_process, args=(command, "superlink"), daemon=True
    ).start()
    return True, "Superlink process started."


def start_runner(
    runner_app: str,
    run_id: str,
    num_partitions: str,
):
    if process_store["runner"] and process_store["runner"].poll() is None:
        return False, "A Runner process is already running."

    # Check if the Superlink is running, respecting the configured mode
    if cfg.SUPERLINK_MODE == "external":
        if not util.is_port_open(cfg.SUPERLINK_HOST, cfg.SUPERLINK_PORT):
            return False, "External Superlink is not running or unreachable."
    elif not (process_store["superlink"] and process_store["superlink"].poll() is None):
        return (
            False,
            "Internal Superlink is not running. Please start it before starting the runner.",
        )

    if not all([runner_app, run_id, num_partitions]):
        return False, "Please provide a Runner App, Run ID, and Total Partitions."
    if not num_partitions.isdigit() or int(num_partitions) <= 0:
        return False, "Total Partitions must be a positive integer."

    # Update the number of partitions in the database using SQLAlchemy
    with SessionLocal() as db:
        config_entry = db.query(Config).filter(Config.key == "num_partitions").first()
        if config_entry:
            config_entry.value = num_partitions
        else:
            db.add(Config(key="num_partitions", value=num_partitions))
        db.commit()

    runner_app_path = runner_app.replace(".", os.path.sep)
    if not os.path.exists(runner_app_path):
        return False, f"Unable to find app path '{runner_app_path}'."

    # Construct the command for a TLS-enabled runner
    command = [
        shutil.which("flwr"),
        "run",
        runner_app_path,
        "local-deployment",
        "--federation-config",
        f'address="{cfg.SUPERLINK_HOST}:{cfg.SUPERLINK_CONTROL_API_PORT}" root-certificates="{cfg.BLOSSOMTUNE_TLS_CA_CERTFILE}"',
        "--stream",
    ]
    threading.Thread(target=run_process, args=(command, "runner"), daemon=True).start()
    return True, "Federation Run is starting...."


def stop_process(
    process_key: str,
):
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
