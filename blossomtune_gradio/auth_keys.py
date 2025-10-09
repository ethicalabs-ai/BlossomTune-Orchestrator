import os
import logging
from typing import List, Tuple
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

log = logging.getLogger(__name__)


def rebuild_authorized_keys_csv(
    key_dir: str, authorized_participants: List[Tuple[str, str]]
):
    """
    Overwrites the public key file with a fresh list from a trusted source,
    using the specific single-line format expected by Flower.

    Args:
        key_dir (str): The directory where the CSV will be stored.
        authorized_participants (List[Tuple[str, str]]): A list of tuples,
            where each tuple contains (participant_id, public_key_pem).
    """
    csv_path = os.path.join(key_dir, "authorized_supernodes.csv")
    log.info(f"Rebuilding authorized keys file at: {csv_path}")

    # Extract just the public key strings from the database results.
    # The PEM format from the cryptography library includes newlines,
    # which we must handle. A simple approach is to remove them.
    public_keys = [pem.replace("\n", "") for _, pem in authorized_participants]

    # Join all public keys into a single comma-separated string.
    content = ",".join(public_keys)

    # Write the single line to the file, followed by a newline.
    with open(csv_path, "w") as f:
        f.write(content + "\n")

    log.info(
        f"Successfully rebuilt {csv_path} with {len(authorized_participants)} keys."
    )


class AuthKeyGenerator:
    """
    Handles the generation of Elliptic Curve (EC) key pairs for Flower
    SuperNode authentication.
    """

    def __init__(self, key_dir: str = "keys"):
        """
        Initializes the generator and ensures the key directory exists.

        Args:
            key_dir (str): The directory where key files will be stored.
        """
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
        # Set file permissions to read/write for owner only (600)
        os.chmod(priv_key_path, 0o600)
        log.info(f"Private key for {participant_id} saved securely to {priv_key_path}")
        return priv_key_path

    def _save_public_key_file(
        self, private_key: ec.EllipticCurvePublicKey, participant_id: str
    ) -> str:
        """Saves the public key to a .pub file in OpenSSH format."""
        pub_key_path = os.path.join(self.key_dir, f"{participant_id}.pub")
        with open(pub_key_path, "wb") as f:
            f.write(
                private_key.public_key().public_bytes(
                    encoding=serialization.Encoding.OpenSSH,
                    format=serialization.PublicFormat.OpenSSH,
                )
            )
        log.info(f"Public key for {participant_id} saved to {pub_key_path}")
        return pub_key_path

    def generate_participant_keys(self, participant_id: str) -> Tuple[str, str, str]:
        """
        Generates and saves a new EC key pair for a participant.

        This is the main public method to call when a new participant is approved.

        Args:
            participant_id (str): A unique identifier for the participant.

        Returns:
            A tuple containing:
            - The file path to the generated private key.
            - The file path to the generated public key.
            - The public key as a PEM-encoded string (for database storage).
        """
        private_key = self._generate_key_pair()
        public_key = private_key.public_key()

        priv_key_path = self._save_private_key(private_key, participant_id)
        pub_key_path = self._save_public_key_file(private_key, participant_id)

        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        return (priv_key_path, pub_key_path, public_key_pem)
