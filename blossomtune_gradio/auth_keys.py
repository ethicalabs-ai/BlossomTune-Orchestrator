import os
import logging
from typing import List, Tuple
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

# Configure logging for the module
log = logging.getLogger(__name__)


def _sanitize_key(participant_id: str, key_str: str) -> str | None:
    """
    Inspects a key string and converts it to the required OpenSSH format if necessary.
    This provides resilience against old, PEM-formatted keys in the database.
    """
    if not key_str:
        return None
    # If the key is already in the correct OpenSSH format, return it as is.
    if key_str.startswith("ecdsa-sha2-nistp384"):
        return key_str
    # If the key is in the old PEM format, attempt to convert it.
    if "-----BEGIN PUBLIC KEY-----" in key_str:
        log.warning(
            f"Found PEM-formatted key for participant {participant_id}. Converting to OpenSSH."
        )
        try:
            public_key = serialization.load_pem_public_key(key_str.encode("utf-8"))
            key_body = public_key.public_bytes(
                encoding=serialization.Encoding.OpenSSH,
                format=serialization.PublicFormat.OpenSSH,
            ).decode("utf-8")
            # Re-add the participant_id as a comment to conform to the 3-part format.
            return f"{key_body} {participant_id}"
        except Exception as e:
            log.error(f"Could not convert PEM key for {participant_id}: {e}")
            return None
    # If the key format is unknown, log an error and skip it.
    log.error(f"Unknown public key format for participant {participant_id}. Skipping.")
    return None


def rebuild_authorized_keys_csv(
    key_dir: str, authorized_participants: List[Tuple[str, str]]
):
    """
    Overwrites the public key file with a fresh list from a trusted source,
    using the specific single-line, comma-separated format expected by Flower.
    """
    csv_path = os.path.join(key_dir, "authorized_supernodes.csv")
    log.info(f"Rebuilding authorized keys file at: {csv_path}")

    # Sanitize each key before adding it to the list.
    public_keys = [
        sanitized_key
        for p_id, key_string in authorized_participants
        if (sanitized_key := _sanitize_key(p_id, key_string)) is not None
    ]

    # Join all valid public keys into a single comma-separated string.
    content = ",".join(public_keys)

    # Write the single line to the file, followed by a newline.
    with open(csv_path, "w") as f:
        f.write(content + "\n")

    log.info(f"Successfully rebuilt {csv_path} with {len(public_keys)} keys.")


class AuthKeyGenerator:
    """
    Handles the generation of Elliptic Curve (EC) key pairs for Flower
    SuperNode authentication.
    """

    def __init__(self, key_dir: str = "keys"):
        self.key_dir = key_dir
        os.makedirs(self.key_dir, exist_ok=True)
        log.info(f"Authentication key directory set to: {self.key_dir}")

    def _generate_key_pair(self) -> ec.EllipticCurvePrivateKey:
        """Generates a single EC private key using the SECP384R1 curve."""
        return ec.generate_private_key(ec.SECP384R1())

    def _save_private_key(
        self, private_key: ec.EllipticCurvePrivateKey, participant_id: str
    ) -> str:
        """Saves the private key to a file with secure permissions."""
        priv_key_path = os.path.join(self.key_dir, f"{participant_id}.key")
        with open(priv_key_path, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
        os.chmod(priv_key_path, 0o600)
        log.info(f"Private key for {participant_id} saved securely to {priv_key_path}")
        return priv_key_path

    def _save_public_key_file(
        self, public_key_ssh_string: str, participant_id: str
    ) -> str:
        """Saves the full OpenSSH public key string to a .pub file."""
        pub_key_path = os.path.join(self.key_dir, f"{participant_id}.pub")
        with open(pub_key_path, "w") as f:
            f.write(public_key_ssh_string)
        log.info(f"Public key for {participant_id} saved to {pub_key_path}")
        return pub_key_path

    def generate_participant_keys(self, participant_id: str) -> Tuple[str, str, str]:
        """
        Generates and saves a new EC key pair for a participant.

        Returns:
            A tuple containing:
            - The file path to the generated private key.
            - The file path to the generated public key.
            - The public key as a single-line OpenSSH string with a comment.
        """
        private_key = self._generate_key_pair()
        public_key = private_key.public_key()

        # Generate the base OpenSSH key string (type and key data)
        key_body = public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        ).decode("utf-8")

        # Append the participant_id as a comment, creating the full 3-part key.
        public_key_ssh_string = f"{key_body} {participant_id}"

        priv_key_path = self._save_private_key(private_key, participant_id)
        pub_key_path = self._save_public_key_file(public_key_ssh_string, participant_id)

        return (priv_key_path, pub_key_path, public_key_ssh_string)
