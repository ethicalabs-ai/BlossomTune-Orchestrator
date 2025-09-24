import os
import json
import zipfile
import logging
from typing import Dict, Any

# Configure logging for the module
log = logging.getLogger(__name__)


def create_blossomfile(
    participant_id: str,
    output_dir: str,
    ca_cert_path: str,
    auth_key_path: str,
    auth_pub_path: str,
    superlink_address: str,
    partition_id: int,
    num_partitions: int,
) -> str:
    """
    Generates a .blossomfile for a participant.

    This function packages all necessary credentials and configuration into a
    single, portable .zip archive that a participant can use to easily
    connect to the federation.

    Args:
        participant_id: The unique identifier for the participant.
        output_dir: The directory where the final .blossomfile will be saved.
        ca_cert_path: Path to the CA public certificate (`ca.crt`).
        auth_key_path: Path to the participant's private EC key (`auth.key`).
        auth_pub_path: Path to the participant's public EC key (`auth.pub`).
        superlink_address: The public address of the Flower SuperLink.
        partition_id: The data partition ID assigned to the participant.
        num_partitions: The total number of partitions in the federation.

    Returns:
        The full path to the generated .blossomfile.
    """
    os.makedirs(output_dir, exist_ok=True)
    blossomfile_path = os.path.join(output_dir, f"{participant_id}.blossomfile")
    log.info(f"Creating Blossomfile for {participant_id} at {blossomfile_path}")

    # 1. Create the blossom.json configuration data
    blossom_config: Dict[str, Any] = {
        "superlink_address": superlink_address,
        "node_config": {
            "partition-id": partition_id,
            "num-partitions": num_partitions,
        },
    }

    # 2. Define the files to be included in the archive
    files_to_add = {
        ca_cert_path: "ca.crt",
        auth_key_path: "auth.key",
        auth_pub_path: "auth.pub",
    }

    # 3. Create the zip archive
    try:
        with zipfile.ZipFile(blossomfile_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add the configuration file
            zf.writestr("blossom.json", json.dumps(blossom_config, indent=2))
            log.info("Added blossom.json to archive.")

            # Add the certificate and key files
            for src_path, arc_name in files_to_add.items():
                if os.path.exists(src_path):
                    zf.write(src_path, arcname=arc_name)
                    log.info(f"Added {arc_name} to archive from {src_path}.")
                else:
                    log.error(f"Credential file not found: {src_path}. Aborting.")
                    raise FileNotFoundError(
                        f"Required credential file not found: {src_path}"
                    )

    except Exception as e:
        log.critical(f"Failed to create Blossomfile: {e}")
        # Clean up partially created file on failure
        if os.path.exists(blossomfile_path):
            os.remove(blossomfile_path)
        raise

    log.info(f"Successfully created Blossomfile: {blossomfile_path}")
    return blossomfile_path
