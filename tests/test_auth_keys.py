import os
import csv
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
        # In non-Windows environments, check for 600 permissions.
        if os.name != "nt":
            file_mode = stat.S_IMODE(os.stat(priv_path).st_mode)
            assert file_mode == 0o600

        # 3. Verify key formats and consistency
        with open(priv_path, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
        with open(pub_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())
            _ = f.read()  # Read again to get bytes

        assert isinstance(private_key, ec.EllipticCurvePrivateKey)
        assert isinstance(public_key, ec.EllipticCurvePublicKey)

        # Check that the returned PEM string matches the public key
        generated_public_key = private_key.public_key()
        pem_from_private = generated_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")
        assert pub_pem == pem_from_private


class TestRebuildCSV:
    """Test suite for the rebuild_authorized_keys_csv function."""

    def test_rebuild_csv_creates_file_with_header_for_empty_list(self, tmp_path):
        """Verify a CSV with only a header is created for an empty participant list."""
        key_dir = tmp_path / "csv_test"
        os.makedirs(key_dir)
        csv_path = os.path.join(key_dir, "authorized_supernodes.csv")

        rebuild_authorized_keys_csv(key_dir, [])

        assert os.path.exists(csv_path)
        with open(csv_path, "r") as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == ["participant_id", "public_key_pem"]
            # Check that there are no more rows
            with pytest.raises(StopIteration):
                next(reader)

    def test_rebuild_csv_writes_correct_data(self, tmp_path):
        """Verify the CSV is created with the correct participant data."""
        key_dir = tmp_path / "csv_test"
        os.makedirs(key_dir)
        csv_path = os.path.join(key_dir, "authorized_supernodes.csv")

        participants = [
            ("p1", "---BEGIN PUBLIC KEY---...p1...---END PUBLIC KEY---"),
            ("p2", "---BEGIN PUBLIC KEY---...p2...---END PUBLIC KEY---"),
        ]
        rebuild_authorized_keys_csv(key_dir, participants)

        with open(csv_path, "r") as f:
            reader = csv.reader(f)
            header = next(reader)
            row1 = next(reader)
            row2 = next(reader)
            assert header == ["participant_id", "public_key_pem"]
            assert row1 == list(participants[0])
            assert row2 == list(participants[1])

    def test_rebuild_csv_overwrites_existing_file(self, tmp_path):
        """Verify that an existing CSV file is correctly overwritten."""
        key_dir = tmp_path / "csv_test"
        os.makedirs(key_dir)
        csv_path = os.path.join(key_dir, "authorized_supernodes.csv")

        # First run with initial data
        initial_participants = [("old_p1", "old_key_1")]
        rebuild_authorized_keys_csv(key_dir, initial_participants)

        # Second run with new data
        new_participants = [("new_p1", "new_key_1"), ("new_p2", "new_key_2")]
        rebuild_authorized_keys_csv(key_dir, new_participants)

        with open(csv_path, "r") as f:
            reader = csv.reader(f)
            _ = next(reader)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0] == list(new_participants[0])
        assert rows[1] == list(new_participants[1])
