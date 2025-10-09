import pytest
from unittest.mock import MagicMock, patch

from blossomtune_gradio import processing
from blossomtune_gradio.database import Config


@pytest.fixture(autouse=True)
def reset_process_store():
    """
    Fixture that runs automatically for every test in this module.
    It resets the process_store to its default state to ensure test isolation.
    """
    processing.process_store = {"superlink": None, "runner": None}
    yield
    processing.process_store = {"superlink": None, "runner": None}


@patch("blossomtune_gradio.processing.threading.Thread")
@patch(
    "blossomtune_gradio.processing.shutil.which",
    return_value="/fake/path/flower-superlink",
)
def test_start_superlink_success(mock_which, mock_thread):
    """Verify that start_superlink successfully starts a thread."""
    success, message = processing.start_superlink()

    assert success is True
    assert message == "Superlink process started."
    mock_thread.assert_called_once()
    call_args = mock_thread.call_args
    assert call_args.kwargs["target"] == processing.run_process
    assert call_args.kwargs["args"][0][0] == "/fake/path/flower-superlink"
    assert call_args.kwargs["args"][0][1] == "--insecure"


def test_start_superlink_already_running(mocker):
    """Verify that start_superlink returns False if a process is already running."""
    mock_process = MagicMock()
    mock_process.poll.return_value = None
    processing.process_store["superlink"] = mock_process

    success, message = processing.start_superlink()
    assert success is False
    assert "already running" in message


@patch("blossomtune_gradio.processing.os.path.exists", return_value=True)
@patch("blossomtune_gradio.processing.threading.Thread")
@patch("blossomtune_gradio.processing.shutil.which", return_value="/fake/path/flwr")
def test_start_runner_success_internal_superlink(
    mock_which, mock_thread, mock_exists, db_session
):
    """Verify start_runner succeeds with an internal superlink and updates the DB."""
    # Arrange: Mock a running internal superlink process
    mock_superlink = MagicMock()
    mock_superlink.poll.return_value = None
    processing.process_store["superlink"] = mock_superlink

    # Act
    success, message = processing.start_runner("app.main", "run1", "15")

    # Assert
    assert success is True
    assert message == "Federation Run is starting...."
    mock_thread.assert_called_once()

    # Verify DB was updated using SQLAlchemy
    config_entry = db_session.query(Config).filter_by(key="num_partitions").first()
    assert config_entry is not None
    assert config_entry.value == "15"


@patch("blossomtune_gradio.processing.os.path.exists", return_value=True)
@patch("blossomtune_gradio.processing.threading.Thread")
@patch("blossomtune_gradio.processing.shutil.which", return_value="/fake/path/flwr")
def test_start_runner_success_external_superlink(
    mock_which, mock_thread, mock_exists, db_session, mocker
):
    """Verify start_runner succeeds with an external superlink."""
    # Arrange
    mocker.patch("blossomtune_gradio.config.SUPERLINK_MODE", "external")
    mocker.patch("blossomtune_gradio.util.is_port_open", return_value=True)

    # Act
    success, message = processing.start_runner("app.main", "run1", "10")

    # Assert
    assert success is True
    assert message == "Federation Run is starting...."
    mock_thread.assert_called_once()


def test_start_runner_internal_superlink_not_running(db_session):
    """Verify start_runner fails if internal superlink is not running."""
    processing.process_store["superlink"] = None
    success, message = processing.start_runner("app.main", "run1", "10")
    assert success is False
    assert "Internal Superlink is not running" in message


def test_start_runner_missing_args(db_session):
    """Verify start_runner fails if arguments are missing."""
    mock_superlink = MagicMock()
    mock_superlink.poll.return_value = None
    processing.process_store["superlink"] = mock_superlink

    success, message = processing.start_runner("", "run1", "10")
    assert success is False
    assert "provide a Runner App" in message


@patch("blossomtune_gradio.processing.os.path.exists", return_value=False)
def test_start_runner_app_path_not_found(mock_exists, db_session):
    """Verify start_runner fails if the app path doesn't exist."""
    mock_superlink = MagicMock()
    mock_superlink.poll.return_value = None
    processing.process_store["superlink"] = mock_superlink

    success, message = processing.start_runner("non.existent.app", "run1", "10")
    assert success is False
    assert "Unable to find app path" in message


def test_stop_process_running():
    """Verify stop_process terminates a running process."""
    mock_process = MagicMock()
    mock_process.poll.return_value = None
    processing.process_store["superlink"] = mock_process

    processing.stop_process("superlink")

    mock_process.terminate.assert_called_once()
    mock_process.wait.assert_called_once()
    assert processing.process_store["superlink"] is None


def test_stop_process_not_running(mocker):
    """Verify stop_process does nothing if the process is not running."""
    log_mock = mocker.patch("blossomtune_gradio.processing.log")
    processing.process_store["superlink"] = None

    processing.stop_process("superlink")

    log_mock.assert_any_call(
        "[Superlink] Stop command received, but no process was running."
    )
