import os
import json
import zipfile
import pytest

from blossomtune_gradio.blossomfile import create_blossomfile


@pytest.fixture
def dummy_credential_files(tmp_path):
    """
    Pytest fixture to create dummy credential files in a temporary directory.
    Returns the paths to the created files.
    """
    creds_dir = tmp_path / "creds"
    os.makedirs(creds_dir)

    ca_cert_path = creds_dir / "ca.crt"
    auth_key_path = creds_dir / "auth.key"
    auth_pub_path = creds_dir / "auth.pub"

    ca_cert_path.write_text("---BEGIN CERTIFICATE---")
    auth_key_path.write_text("---BEGIN EC PRIVATE KEY---")
    auth_pub_path.write_text("---BEGIN PUBLIC KEY---")

    return {
        "ca_cert_path": str(ca_cert_path),
        "auth_key_path": str(auth_key_path),
        "auth_pub_path": str(auth_pub_path),
    }


def test_create_blossomfile_success(tmp_path, dummy_credential_files):
    """
    Tests the successful creation of a .blossomfile, verifying its contents.
    """
    output_dir = tmp_path / "output"
    participant_id = "participant_abc"

    blossomfile_path = create_blossomfile(
        participant_id=participant_id,
        output_dir=str(output_dir),
        ca_cert_path=dummy_credential_files["ca_cert_path"],
        auth_key_path=dummy_credential_files["auth_key_path"],
        auth_pub_path=dummy_credential_files["auth_pub_path"],
        superlink_address="blossomtune-test.ethicalabs.ai:9092",
        partition_id=5,
        num_partitions=10,
    )

    # 1. Verify the file was created at the correct path
    assert os.path.exists(blossomfile_path)
    assert blossomfile_path == str(output_dir / f"{participant_id}.blossomfile")

    # 2. Verify the contents of the zip archive
    with zipfile.ZipFile(blossomfile_path, "r") as zf:
        # Check that all expected files are present
        namelist = zf.namelist()
        assert "blossom.json" in namelist
        assert "ca.crt" in namelist
        assert "auth.key" in namelist
        assert "auth.pub" in namelist
        assert len(namelist) == 4

        # Check the content of blossom.json
        with zf.open("blossom.json") as f:
            config_data = json.load(f)
            assert (
                config_data["superlink_address"]
                == "blossomtune-test.ethicalabs.ai:9092"
            )
            assert config_data["node_config"]["partition-id"] == 5
            assert config_data["node_config"]["num-partitions"] == 10

        # Check the content of the credential files
        assert zf.read("ca.crt").decode("utf-8") == "---BEGIN CERTIFICATE---"
        assert zf.read("auth.key").decode("utf-8") == "---BEGIN EC PRIVATE KEY---"
        assert zf.read("auth.pub").decode("utf-8") == "---BEGIN PUBLIC KEY---"


def test_create_blossomfile_missing_input_file(tmp_path):
    """
    Tests that the function raises FileNotFoundError if a required credential
    file is missing and cleans up the partial archive.
    """
    output_dir = tmp_path / "output"
    participant_id = "participant_xyz"
    missing_file_path = tmp_path / "creds" / "non_existent.key"
    blossomfile_path = output_dir / f"{participant_id}.blossomfile"

    with pytest.raises(FileNotFoundError, match="Required credential file not found"):
        create_blossomfile(
            participant_id=participant_id,
            output_dir=str(output_dir),
            ca_cert_path=str(missing_file_path),  # Pass a path that doesn't exist
            auth_key_path="dummy",
            auth_pub_path="dummy",
            superlink_address="test:9092",
            partition_id=1,
            num_partitions=2,
        )

    # Verify that the partially created blossomfile was removed
    assert not os.path.exists(blossomfile_path)
