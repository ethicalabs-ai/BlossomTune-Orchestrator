import pytest
import socket
import dns.resolver
from unittest.mock import MagicMock

from blossomtune_gradio.util import is_port_open, validate_email, strtobool


def test_is_port_open_success(mocker):
    """
    Tests the case where the port is open and the connection succeeds.
    """
    mock_socket = mocker.patch("blossomtune_gradio.util.socket.socket")
    mock_socket.return_value.__enter__.return_value.connect.return_value = None

    result = is_port_open("testhost", 1234)

    assert result is True
    # Verify that the socket was created and connect was called with the correct args
    mock_socket.return_value.__enter__.return_value.settimeout.assert_called_once_with(
        1.0
    )
    mock_socket.return_value.__enter__.return_value.connect.assert_called_once_with(
        ("testhost", 1234)
    )


@pytest.mark.parametrize("exception", [ConnectionRefusedError, socket.timeout, OSError])
def test_is_port_open_failures(mocker, exception):
    """
    Tests various failure scenarios where the port is not open.
    - ConnectionRefusedError: The host actively refuses the connection.
    - socket.timeout: The connection attempt times out.
    - OSError: A generic network error occurs.
    """
    mock_socket = mocker.patch("blossomtune_gradio.util.socket.socket")
    mock_socket.return_value.__enter__.return_value.connect.side_effect = exception

    result = is_port_open("testhost", 1234)
    assert result is False


def test_validate_email_valid(monkeypatch):
    """Tests a syntactically valid email with an existing MX record."""
    # Mock the dns.resolver.query to return a successful result.
    mock_query = MagicMock()
    monkeypatch.setattr(dns.resolver, "resolve", mock_query)

    email = "test@google.com"
    assert validate_email(email) is True
    # Verify that the query function was called with the correct arguments.
    mock_query.assert_called_once_with("google.com", "MX")


def test_validate_email_invalid_format():
    """Tests an email with an invalid regex format."""
    assert validate_email("invalid-email") is False
    assert validate_email("user@.com") is False
    assert validate_email("@domain.com") is False


def test_validate_email_no_mx_record(monkeypatch):
    """Tests a domain that exists but has no MX record."""
    # Mock the dns.resolver.query to raise a NoAnswer exception.
    mock_query = MagicMock(side_effect=dns.resolver.NoAnswer)
    monkeypatch.setattr(dns.resolver, "resolve", mock_query)

    email = "user@example.com"
    assert validate_email(email) is False
    mock_query.assert_called_once_with("example.com", "MX")


def test_validate_email_non_existent_domain(monkeypatch):
    """Tests a domain that does not exist."""
    # Mock the dns.resolver.query to raise an NXDOMAIN exception.
    mock_query = MagicMock(side_effect=dns.resolver.NXDOMAIN)
    monkeypatch.setattr(dns.resolver, "resolve", mock_query)

    email = "user@not-a-real-domain-123.com"
    assert validate_email(email) is False
    mock_query.assert_called_once_with("not-a-real-domain-123.com", "MX")


@pytest.mark.parametrize(
    "value, expected",
    [
        ("y", True),
        ("yes", True),
        ("on", True),
        ("1", True),
        ("true", True),
        ("t", True),
        ("Y", True),
        ("YES", True),
        ("On", True),
        ("0", False),
        ("n", False),
        ("off", False),
        ("false", False),
        ("f", False),
        ("no", False),
        ("anything else", False),
        ("", False),
        (None, False),  # Test with None to ensure it doesn't crash
    ],
)
def test_strtobool(value, expected):
    """Tests the strtobool function with various inputs."""
    assert strtobool(value) == expected
