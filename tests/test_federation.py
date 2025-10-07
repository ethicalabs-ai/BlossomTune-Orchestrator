import pytest
from unittest.mock import MagicMock

from blossomtune_gradio import federation as fed


@pytest.fixture
def mock_settings(mocker):
    """Fixture to mock the settings module."""
    # The lambda returns a formatted string to simulate Jinja2's behavior
    mock_get = MagicMock(
        side_effect=lambda key, **kwargs: f"mock_{key}".format(**kwargs)
    )
    mocker.patch("blossomtune_gradio.federation.settings.get_text", mock_get)
    return mock_get


@pytest.fixture
def mock_mail(mocker):
    """Fixture to mock the mail module."""
    return mocker.patch("blossomtune_gradio.mail.send_activation_email")


def test_generate_participant_id():
    """Test the generation of a participant ID."""
    pid = fed.generate_participant_id()
    assert isinstance(pid, str)
    assert len(pid) == 6
    assert pid.isalnum() and pid.isupper()


def test_generate_activation_code():
    """Test the generation of an activation code."""
    code = fed.generate_activation_code()
    assert isinstance(code, str)
    assert len(code) == 8
    assert code.isalnum() and code.isupper()


class TestCheckParticipantStatus:
    """Test suite for the check_participant_status function."""

    def test_new_user_registration_success(
        self, in_memory_db, mock_settings, mock_mail
    ):
        """Verify successful registration for a new user."""
        mock_mail.return_value = (True, "")
        success, message, download = fed.check_participant_status(
            "new_user", "new@example.com", ""
        )
        assert success is True
        assert download is None
        assert message == "mock_registration_submitted_md"

        # Verify the user was added to the database
        cursor = in_memory_db.cursor()
        cursor.execute("SELECT hf_handle FROM requests WHERE hf_handle = 'new_user'")
        assert cursor.fetchone() is not None

    def test_new_user_invalid_email(self, in_memory_db, mock_settings):
        """Verify registration fails with an invalid email."""
        success, message, download = fed.check_participant_status(
            "user", "invalid-email", ""
        )
        assert success is False
        assert download is None
        assert message == "mock_invalid_email_md"

    def test_new_user_federation_full(self, in_memory_db, mock_settings, mocker):
        """Verify registration fails when the federation is full."""
        mocker.patch("blossomtune_gradio.federation.cfg.MAX_NUM_NODES", 0)
        success, message, download = fed.check_participant_status(
            "another_user", "another@example.com", ""
        )
        assert success is False
        assert download is None
        assert message == "mock_federation_full_md"

    def test_user_activation_success(self, in_memory_db, mock_settings):
        """Verify a user can successfully activate their account."""
        # Setup: Add a pending, non-activated user
        cursor = in_memory_db.cursor()
        cursor.execute(
            "INSERT INTO requests (participant_id, status, timestamp, hf_handle, email, activation_code, is_activated) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("PID123", "pending", "now", "test_user", "test@example.com", "ABCDEF", 0),
        )
        in_memory_db.commit()

        success, message, download = fed.check_participant_status(
            "test_user", "test@example.com", "ABCDEF"
        )
        assert success is True
        assert download is None
        assert message == "mock_activation_successful_md"
        # Verify the user is now activated
        cursor.execute(
            "SELECT is_activated FROM requests WHERE hf_handle = 'test_user'"
        )
        assert cursor.fetchone()[0] == 1

    def test_user_activation_invalid_code(self, in_memory_db, mock_settings):
        """Verify activation fails with an invalid code."""
        # Setup: Add a pending, non-activated user
        cursor = in_memory_db.cursor()
        cursor.execute(
            "INSERT INTO requests (participant_id, status, timestamp, hf_handle, email, activation_code, is_activated) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("PID123", "pending", "now", "test_user", "test@example.com", "ABCDEF", 0),
        )
        in_memory_db.commit()

        success, message, download = fed.check_participant_status(
            "test_user", "test@example.com", "WRONGCODE"
        )
        assert success is False
        assert download is None
        assert message == "mock_activation_invalid_md"

    def test_status_check_approved(self, in_memory_db, mock_settings):
        """Verify the status check for an approved user."""
        cursor = in_memory_db.cursor()
        cursor.execute(
            "INSERT INTO requests (participant_id, status, timestamp, hf_handle, email, activation_code, is_activated, partition_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "PID456",
                "approved",
                "now",
                "approved_user",
                "approved@example.com",
                "GHIJKL",
                1,
                5,
            ),
        )
        in_memory_db.commit()
        success, message, download = fed.check_participant_status(
            "approved_user", "approved@example.com", "GHIJKL"
        )
        assert success is True
        assert download is not None
        assert "mock_status_approved_md" in message


class TestManageRequest:
    """Test suite for the manage_request function."""

    def test_approve_success(self, in_memory_db):
        """Verify successful approval of a participant."""
        # Setup: Add an activated, pending user
        cursor = in_memory_db.cursor()
        cursor.execute(
            "INSERT INTO requests (participant_id, status, timestamp, hf_handle, email, activation_code, is_activated) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "PENDING1",
                "pending",
                "now",
                "pending_user",
                "pending@example.com",
                "CODE",
                1,
            ),
        )
        in_memory_db.commit()

        success, message = fed.manage_request("PENDING1", "10", "approve")
        assert success is True
        assert "is allowed to join" in message

        # Verify status in DB
        cursor.execute(
            "SELECT status, partition_id FROM requests WHERE participant_id = 'PENDING1'"
        )
        status, partition_id = cursor.fetchone()
        assert status == "approved"
        assert partition_id == 10

    def test_approve_not_activated(self, in_memory_db, mock_settings):
        """Verify approval fails if the user is not activated."""
        cursor = in_memory_db.cursor()
        cursor.execute(
            "INSERT INTO requests (participant_id, status, timestamp, hf_handle, email, activation_code, is_activated) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "PENDING2",
                "pending",
                "now",
                "pending_user2",
                "pending2@example.com",
                "CODE",
                0,
            ),
        )
        in_memory_db.commit()
        success, message = fed.manage_request("PENDING2", "11", "approve")
        assert success is False
        assert message == "mock_participant_not_activated_warning_md"

    def test_deny_success(self, in_memory_db):
        """Verify successful denial of a participant."""
        cursor = in_memory_db.cursor()
        cursor.execute(
            "INSERT INTO requests (participant_id, status, timestamp, hf_handle, email, activation_code, is_activated) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "PENDING3",
                "pending",
                "now",
                "pending_user3",
                "pending3@example.com",
                "CODE",
                1,
            ),
        )
        in_memory_db.commit()
        success, message = fed.manage_request("PENDING3", "", "deny")
        assert success is True
        assert "is not allowed to join" in message

        # Verify status in DB
        cursor.execute("SELECT status FROM requests WHERE participant_id = 'PENDING3'")
        assert cursor.fetchone()[0] == "denied"


def test_get_next_partition_id(in_memory_db):
    """Verify the logic for finding the next available partition ID."""
    cursor = in_memory_db.cursor()
    # No approved users yet
    assert fed.get_next_partion_id() == 0

    # Add some approved users with assigned partitions, including the required timestamp
    cursor.execute(
        "INSERT INTO requests (participant_id, status, timestamp, partition_id) VALUES (?, ?, ?, ?)",
        ("P1", "approved", "now", 0),
    )
    cursor.execute(
        "INSERT INTO requests (participant_id, status, timestamp, partition_id) VALUES (?, ?, ?, ?)",
        ("P2", "approved", "now", 1),
    )
    in_memory_db.commit()
    assert fed.get_next_partion_id() == 2

    # Add another user, skipping a partition ID
    cursor.execute(
        "INSERT INTO requests (participant_id, status, timestamp, partition_id) VALUES (?, ?, ?, ?)",
        ("P3", "approved", "now", 3),
    )
    in_memory_db.commit()
    assert fed.get_next_partion_id() == 2
