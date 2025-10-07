import os
import shutil
import sqlite3
import threading
import subprocess

from blossomtune_gradio.logs import log
from blossomtune_gradio import config as cfg


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
    command = [shutil.which("flower-superlink"), "--insecure"]
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
    if (
        not (process_store["superlink"] and process_store["superlink"].poll() is None)
        and not cfg.SUPERLINK_MODE == "external"
    ):
        return (
            False,
            "Superlink is not running. Please start it before starting the runner.",
        )
    # TODO: check if external superlink is running
    if not all([runner_app, run_id, num_partitions]):
        return False, "Please provide a Runner App, Run ID, and Total Partitions."
    if not num_partitions.isdigit() or int(num_partitions) <= 0:
        return False, "Total Partitions must be a positive integer."

    with sqlite3.connect(cfg.DB_PATH) as conn:
        conn.execute(
            "UPDATE config SET value = ? WHERE key = 'num_partitions'",
            (num_partitions,),
        )
        conn.commit()

    runner_app_path = runner_app.replace(".", os.path.sep)
    if not os.path.exists(runner_app_path):
        return False, f"Unable to find app path '{runner_app_path}'."

    command = [
        shutil.which("flwr"),
        "run",
        runner_app_path,
        "local-deployment",
        "--root-certificates",
        cfg.BLOSSOMTUNE_TLS_CERT_PATH,
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
