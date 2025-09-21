import pytest
from unittest.mock import MagicMock, patch

from blossomtune_gradio import processing


@pytest.fixture(autouse=True)
def reset_process_store():
    """
    Fixture that runs automatically for every test in this module.
    It resets the process_store to its default state to ensure test isolation.
    """
    processing.process_store = {"superlink": None, "runner": None}
    yield
    # Teardown is not strictly necessary as it's reset at the start,
    # but it's good practice.
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
    # Check that the thread is targeting the run_process function
    call_args = mock_thread.call_args
    assert call_args.kwargs["target"] == processing.run_process
    # Check that the command is correct
    assert call_args.kwargs["args"][0] == ["/fake/path/flower-superlink", "--insecure"]


def test_start_superlink_already_running(mocker):
    """Verify that start_superlink returns False if a process is already running."""
    # Mock a running process
    mock_process = MagicMock()
    mock_process.poll.return_value = None  # None means it's running
    processing.process_store["superlink"] = mock_process

    success, message = processing.start_superlink()
    assert success is False
    assert "already running" in message


@patch("blossomtune_gradio.processing.os.path.exists", return_value=True)
@patch("blossomtune_gradio.processing.sqlite3.connect")
@patch("blossomtune_gradio.processing.threading.Thread")
@patch("blossomtune_gradio.processing.shutil.which", return_value="/fake/path/flwr")
def test_start_runner_success(mock_which, mock_thread, mock_sqlite, mock_exists):
    """Verify that start_runner successfully starts a thread when conditions are met."""
    # Mock a running superlink process
    mock_superlink = MagicMock()
    mock_superlink.poll.return_value = None
    processing.process_store["superlink"] = mock_superlink

    success, message = processing.start_runner("app.main", "run1", "10")

    assert success is True
    assert message == "Federation Run is starting...."
    mock_thread.assert_called_once()
    mock_sqlite.assert_called_once()  # Check if DB was updated


def test_start_runner_superlink_not_running():
    """Verify start_runner fails if superlink is not running."""
    processing.process_store["superlink"] = None
    success, message = processing.start_runner("app.main", "run1", "10")
    assert success is False
    assert "Superlink is not running" in message


def test_start_runner_missing_args():
    """Verify start_runner fails if arguments are missing."""
    mock_superlink = MagicMock()
    mock_superlink.poll.return_value = None
    processing.process_store["superlink"] = mock_superlink

    success, message = processing.start_runner("", "run1", "10")
    assert success is False
    assert "provide a Runner App" in message


@patch("blossomtune_gradio.processing.os.path.exists", return_value=False)
def test_start_runner_app_path_not_found(mock_exists, in_memory_db):
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
    mock_process.poll.return_value = None  # Running
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

    # Check that the specific "no process was running" log was called
    log_mock.assert_any_call(
        "[Superlink] Stop command received, but no process was running."
    )
