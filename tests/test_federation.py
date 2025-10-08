import pytest
from datetime import datetime

from blossomtune_gradio import federation as fed
from blossomtune_gradio.database import Request


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
    """Test suite for the check_participant_status function using SQLAlchemy."""

    def test_new_user_registration_success(self, db_session, mock_settings, mock_mail):
        """Verify successful registration for a new user."""
        mock_mail.return_value = (True, "")
        approved, message, download = fed.check_participant_status(
            "new_user", "new@example.com", ""
        )
        assert approved is False
        assert download is None
        assert message == "mock_registration_submitted_md"

        # Verify the user was added to the database
        request = db_session.query(Request).filter_by(hf_handle="new_user").first()
        assert request is not None
        assert request.email == "new@example.com"

    def test_new_user_invalid_email(self, db_session, mock_settings):
        """Verify registration fails with an invalid email."""
        approved, message, download = fed.check_participant_status(
            "user", "invalid-email", ""
        )
        assert approved is False
        assert download is None
        assert message == "mock_invalid_email_md"

    def test_new_user_federation_full(self, db_session, mock_settings, mocker):
        """Verify registration fails when the federation is full."""
        mocker.patch("blossomtune_gradio.config.MAX_NUM_NODES", 0)
        approved, message, download = fed.check_participant_status(
            "another_user", "another@example.com", ""
        )
        assert approved is False
        assert download is None
        assert message == "mock_federation_full_md"

    def test_user_activation_success(self, db_session, mock_settings):
        """Verify a user can successfully activate their account."""
        # Setup: Add a pending, non-activated user
        pending_user = Request(
            participant_id="PID123",
            hf_handle="test_user",
            email="test@example.com",
            activation_code="ABCDEF",
            is_activated=0,
        )
        db_session.add(pending_user)
        db_session.commit()

        approved, message, download = fed.check_participant_status(
            "test_user", "test@example.com", "ABCDEF"
        )
        assert approved is False
        assert download is None
        assert message == "mock_activation_successful_md"
        # Verify the user is now activated
        activated_user = (
            db_session.query(Request).filter_by(hf_handle="test_user").first()
        )
        assert activated_user.is_activated == 1

    def test_user_activation_invalid_code(self, db_session, mock_settings):
        """Verify activation fails with an invalid code."""
        pending_user = Request(
            participant_id="PID123",
            hf_handle="test_user",
            email="test@example.com",
            activation_code="ABCDEF",
            is_activated=0,
        )
        db_session.add(pending_user)
        db_session.commit()

        approved, message, download = fed.check_participant_status(
            "test_user", "test@example.com", "WRONGCODE"
        )
        assert approved is False
        assert download is None
        assert message == "mock_activation_invalid_md"

    def test_status_check_approved(self, db_session, mock_settings):
        """Verify the status check for an approved user."""
        approved_user = Request(
            participant_id="PID456",
            status="approved",
            hf_handle="approved_user",
            email="approved@example.com",
            activation_code="GHIJKL",
            is_activated=1,
            partition_id=5,
        )
        db_session.add(approved_user)
        db_session.commit()

        approved, message, download = fed.check_participant_status(
            "approved_user", "approved@example.com", "GHIJKL"
        )
        assert approved is True
        assert download is not None
        assert "mock_status_approved_md" in message


class TestManageRequest:
    """Test suite for the manage_request function using SQLAlchemy."""

    def test_approve_success(self, db_session):
        """Verify successful approval of a participant."""
        pending_user = Request(
            participant_id="PENDING1",
            status="pending",
            hf_handle="pending_user",
            email="pending@example.com",
            is_activated=1,
        )
        db_session.add(pending_user)
        db_session.commit()

        success, message = fed.manage_request("PENDING1", "10", "approve")
        assert success is True
        assert "is allowed to join" in message

        # Verify status in DB
        updated_user = (
            db_session.query(Request).filter_by(participant_id="PENDING1").first()
        )
        assert updated_user.status == "approved"
        assert updated_user.partition_id == 10

    def test_approve_not_activated(self, db_session, mock_settings):
        """Verify approval fails if the user is not activated."""
        pending_user = Request(
            participant_id="PENDING2",
            status="pending",
            hf_handle="pending_user2",
            is_activated=0,
        )
        db_session.add(pending_user)
        db_session.commit()
        success, message = fed.manage_request("PENDING2", "11", "approve")
        assert success is False
        assert message == "mock_participant_not_activated_warning_md"

    def test_deny_success(self, db_session):
        """Verify successful denial of a participant."""
        pending_user = Request(
            participant_id="PENDING3",
            status="pending",
            hf_handle="pending_user3",
            is_activated=1,
        )
        db_session.add(pending_user)
        db_session.commit()
        success, message = fed.manage_request("PENDING3", "", "deny")
        assert success is True
        assert "is not allowed to join" in message

        # Verify status in DB
        updated_user = (
            db_session.query(Request).filter_by(participant_id="PENDING3").first()
        )
        assert updated_user.status == "denied"


def test_get_next_partition_id(db_session):
    """Verify the logic for finding the next available partition ID."""
    # No approved users yet
    assert fed.get_next_partion_id() == 0

    # Add some approved users with assigned partitions
    db_session.add(
        Request(
            participant_id="P1",
            status="approved",
            partition_id=0,
            timestamp=datetime.utcnow(),
        )
    )
    db_session.add(
        Request(
            participant_id="P2",
            status="approved",
            partition_id=1,
            timestamp=datetime.utcnow(),
        )
    )
    db_session.commit()
    assert fed.get_next_partion_id() == 2

    # Add another user, skipping a partition ID
    db_session.add(
        Request(
            participant_id="P3",
            status="approved",
            partition_id=3,
            timestamp=datetime.utcnow(),
        )
    )
    db_session.commit()
    assert fed.get_next_partion_id() == 2
