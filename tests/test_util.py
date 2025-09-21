import pytest
import dns.resolver
from unittest.mock import MagicMock

from blossomtune_gradio.util import validate_email, strtobool


def test_validate_email_valid(monkeypatch):
    """Tests a syntactically valid email with an existing MX record."""
    # Mock the dns.resolver.query to return a successful result.
    mock_query = MagicMock()
    monkeypatch.setattr(dns.resolver, "query", mock_query)

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
    monkeypatch.setattr(dns.resolver, "query", mock_query)

    email = "user@example.com"
    assert validate_email(email) is False
    mock_query.assert_called_once_with("example.com", "MX")


def test_validate_email_non_existent_domain(monkeypatch):
    """Tests a domain that does not exist."""
    # Mock the dns.resolver.query to raise an NXDOMAIN exception.
    mock_query = MagicMock(side_effect=dns.resolver.NXDOMAIN)
    monkeypatch.setattr(dns.resolver, "query", mock_query)

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
