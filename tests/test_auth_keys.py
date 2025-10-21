import os
import stat
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from blossomtune_gradio.auth_keys import AuthKeyGenerator, rebuild_authorized_keys_csv


@pytest.fixture
def key_generator(tmp_path):
    """Fixture to create an AuthKeyGenerator instance in a temporary directory."""
    key_dir = tmp_path / "auth_keys"
    return AuthKeyGenerator(key_dir=str(key_dir))


class TestAuthKeyGenerator:
    """Test suite for the AuthKeyGenerator class."""

    def test_init_creates_directory(self, tmp_path):
        """Verify that the key directory is created on initialization."""
        key_dir = tmp_path / "new_keys"
        assert not os.path.exists(key_dir)
        AuthKeyGenerator(key_dir=str(key_dir))
        assert os.path.exists(key_dir)

    def test_generate_participant_keys_creates_files_and_returns_openssh_with_comment(
        self, key_generator
    ):
        """
        Verify the main method generates files and returns the public key
        in the correct OpenSSH format including a comment.
        """
        participant_id = "participant_01"
        priv_path, pub_path, pub_ssh_string = key_generator.generate_participant_keys(
            participant_id
        )

        # 1. Check file existence and permissions
        assert os.path.exists(priv_path)
        assert os.path.exists(pub_path)
        if os.name != "nt":
            file_mode = stat.S_IMODE(os.stat(priv_path).st_mode)
            assert file_mode == 0o600

        # 2. Verify that the returned string has three parts (type, key, comment)
        assert pub_ssh_string.startswith("ecdsa-sha2-nistp384")
        assert pub_ssh_string.endswith(participant_id)
        assert len(pub_ssh_string.split(" ")) == 3

        # 3. Verify that the public key file can be loaded as an SSH key
        with open(pub_path, "rb") as f:
            public_key_from_file = serialization.load_ssh_public_key(f.read())
        assert isinstance(public_key_from_file, ec.EllipticCurvePublicKey)


class TestRebuildAuthorizedKeysFile:
    """Test suite for the rebuild_authorized_keys_csv function."""

    def test_rebuild_creates_file_with_only_newline_for_empty_list(self, tmp_path):
        """Verify an empty participant list results in a file with just a newline."""
        key_dir = tmp_path / "keys_test"
        os.makedirs(key_dir)
        rebuild_authorized_keys_csv(str(key_dir), [])

        csv_path = os.path.join(key_dir, "authorized_supernodes.csv")
        with open(csv_path, "r") as f:
            content = f.read()
        assert content == "\n"

    def test_rebuild_writes_correct_single_line_format(self, tmp_path):
        """Verify the file is created in the single-line, comma-separated format."""
        key_dir = tmp_path / "keys_test"
        os.makedirs(key_dir)

        participants = [
            ("p1", "ecdsa-sha2-nistp384 AAAA...key1 p1"),
            ("p2", "ecdsa-sha2-nistp384 AAAA...key2 p2"),
        ]
        rebuild_authorized_keys_csv(str(key_dir), participants)

        csv_path = os.path.join(key_dir, "authorized_supernodes.csv")
        with open(csv_path, "r") as f:
            content = f.read().strip()

        expected_content = (
            "ecdsa-sha2-nistp384 AAAA...key1 p1,ecdsa-sha2-nistp384 AAAA...key2 p2"
        )
        assert content == expected_content

    def test_rebuild_overwrites_existing_file(self, tmp_path):
        """Verify that an existing file is correctly overwritten."""
        key_dir = tmp_path / "keys_test"
        os.makedirs(key_dir)

        # Use dummy data that matches the expected OpenSSH format
        initial_participants = [("old_p1", "ecdsa-sha2-nistp384 old_key_1 old_p1")]
        rebuild_authorized_keys_csv(str(key_dir), initial_participants)

        new_participants = [
            ("new_p1", "ecdsa-sha2-nistp384 new_key_1 new_p1"),
            ("new_p2", "ecdsa-sha2-nistp384 new_key_2 new_p2"),
        ]
        rebuild_authorized_keys_csv(str(key_dir), new_participants)

        csv_path = os.path.join(key_dir, "authorized_supernodes.csv")
        with open(csv_path, "r") as f:
            content = f.read().strip()

        expected_content = (
            "ecdsa-sha2-nistp384 new_key_1 new_p1,ecdsa-sha2-nistp384 new_key_2 new_p2"
        )
        assert content == expected_content

    def test_rebuild_sanitizes_pem_keys_to_ssh_format(self, tmp_path):
        """
        Tests the self-healing capability of the rebuild function to convert
        old PEM keys from the database into the correct OpenSSH format.
        """
        key_dir = tmp_path / "keys_test"
        os.makedirs(key_dir)

        # Generate a real key pair to get a valid PEM string
        private_key = ec.generate_private_key(ec.SECP384R1())
        public_key = private_key.public_key()
        pem_key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        participants = [("p1_pem", pem_key)]
        rebuild_authorized_keys_csv(str(key_dir), participants)

        csv_path = os.path.join(key_dir, "authorized_supernodes.csv")
        with open(csv_path, "r") as f:
            content = f.read().strip()

        # Verify the output is now in the correct OpenSSH format with the comment
        assert content.startswith("ecdsa-sha2-nistp384")
        assert content.endswith("p1_pem")
