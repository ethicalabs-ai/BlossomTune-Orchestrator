import re
import socket
import dns.resolver


def is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """
    Checks if a TCP port is open on a given host.

    Args:
        host: The hostname or IP address to check.
        port: The port number to check.
        timeout: The connection timeout in seconds.

    Returns:
        True if the port is open and a connection can be established,
        False otherwise.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))
        print(f"TCP check successful: Port {port} is open on {host}.")
        return True
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        print(f"TCP check failed: Port {port} on {host} is not open. Error: {e}")
        return False


def validate_email(email_address: str) -> bool:
    """
    Validates an email address using regex for format and
    DNS for domain's MX record.

    Args:
        email_address (str): The email address to validate.

    Returns:
        bool: True if the email is syntactically valid and
              the domain has an MX record, False otherwise.
    """
    # Regex validation for basic format
    regex = r"[^@]+@[^@]+\.[^@]+"
    if not re.match(regex, email_address):
        return False

    # DNS MX record validation
    try:
        domain = email_address.rsplit("@", 1)[-1]
        dns.resolver.resolve(domain, "MX")
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, IndexError):
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


def strtobool(value: str) -> bool:
    if not value:
        return False
    value = value.lower()
    if value in ("y", "yes", "on", "1", "true", "t"):
        return True
    return False
