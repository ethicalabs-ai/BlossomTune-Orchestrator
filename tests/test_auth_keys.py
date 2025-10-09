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

    def test_generate_participant_keys_creates_files_and_returns_data(
        self, key_generator
    ):
        """
        Verify that the main method generates all expected files and returns
        the correct data tuple.
        """
        participant_id = "participant_01"
        priv_path, pub_path, pub_pem = key_generator.generate_participant_keys(
            participant_id
        )

        # 1. Check if files exist
        assert os.path.exists(priv_path)
        assert os.path.exists(pub_path)
        assert priv_path == os.path.join(key_generator.key_dir, f"{participant_id}.key")
        assert pub_path == os.path.join(key_generator.key_dir, f"{participant_id}.pub")

        # 2. Check private key file permissions (security check)
        if os.name != "nt":
            file_mode = stat.S_IMODE(os.stat(priv_path).st_mode)
            assert file_mode == 0o600

        # 3. Verify key formats and consistency
        with open(priv_path, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
        with open(pub_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())

        assert isinstance(private_key, ec.EllipticCurvePrivateKey)
        assert isinstance(public_key, ec.EllipticCurvePublicKey)

        generated_public_key = private_key.public_key()
        pem_from_private = generated_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")
        assert pub_pem == pem_from_private


class TestRebuildAuthorizedKeysFile:
    """Test suite for the rebuild_authorized_keys_csv function."""

    def test_rebuild_creates_file_with_only_newline_for_empty_list(self, tmp_path):
        """Verify an empty participant list results in a file with just a newline."""
        key_dir = tmp_path / "keys_test"
        os.makedirs(key_dir)
        csv_path = os.path.join(key_dir, "authorized_supernodes.csv")

        rebuild_authorized_keys_csv(key_dir, [])

        assert os.path.exists(csv_path)
        with open(csv_path, "r") as f:
            content = f.read()
        assert content == "\n"

    def test_rebuild_writes_correct_single_line_format(self, tmp_path):
        """Verify the file is created in the single-line, comma-separated format."""
        key_dir = tmp_path / "keys_test"
        os.makedirs(key_dir)
        csv_path = os.path.join(key_dir, "authorized_supernodes.csv")

        participants = [
            ("p1", "key1_part1\nkey1_part2\n"),
            ("p2", "key2_part1\nkey2_part2\n"),
        ]
        rebuild_authorized_keys_csv(key_dir, participants)

        with open(csv_path, "r") as f:
            content = (
                f.read().strip()
            )  # Use strip() to remove the trailing newline for comparison

        expected_content = "key1_part1key1_part2,key2_part1key2_part2"
        assert content == expected_content

    def test_rebuild_overwrites_existing_file(self, tmp_path):
        """Verify that an existing file is correctly overwritten with the new format."""
        key_dir = tmp_path / "keys_test"
        os.makedirs(key_dir)
        csv_path = os.path.join(key_dir, "authorized_supernodes.csv")

        # First run with initial data
        initial_participants = [("old_p1", "old_key_1\n")]
        rebuild_authorized_keys_csv(key_dir, initial_participants)

        # Second run with new data
        new_participants = [("new_p1", "new_key_1\n"), ("new_p2", "new_key_2\n")]
        rebuild_authorized_keys_csv(key_dir, new_participants)

        with open(csv_path, "r") as f:
            content = f.read().strip()

        expected_content = "new_key_1,new_key_2"
        assert content == expected_content
