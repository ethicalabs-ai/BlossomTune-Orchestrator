import re
import dns.resolver


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
        dns.resolver.query(domain, "MX")
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
