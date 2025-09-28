import os
import datetime
import logging
from ipaddress import ip_address
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

log = logging.getLogger(__name__)


class TLSGenerator:
    """
    A class to handle the generation of TLS certificates, keys, and CSRs.
    This class contains the core cryptographic logic and is separated from
    any user interface.
    """

    def __init__(self, cert_dir: str = "certificates"):
        self.cert_dir = cert_dir
        os.makedirs(self.cert_dir, exist_ok=True)
        log.info(f"Certificate directory set to: {self.cert_dir}")

    def _generate_private_key(self, filename: str) -> rsa.RSAPrivateKey:
        """Generates and saves a 4096-bit RSA private key."""
        log.info(f"Generating private key: {filename}...")
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=4096, backend=default_backend()
        )
        key_path = os.path.join(self.cert_dir, filename)
        with open(key_path, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
        log.info(f"Private key saved to {key_path}")
        return private_key

    def create_ca(self) -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
        """Generates a new self-signed CA key and certificate."""
        log.info("Generating a new self-signed CA...")
        ca_private_key = self._generate_private_key("ca.key")

        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "DE"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "BlossomTune CA"),
                x509.NameAttribute(NameOID.COMMON_NAME, "BlossomTune Self-Signed CA"),
            ]
        )
        cert_builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(ca_private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=730))
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None), critical=True
            )
        )
        ca_cert = cert_builder.sign(ca_private_key, hashes.SHA256(), default_backend())

        ca_cert_path = os.path.join(self.cert_dir, "ca.crt")
        with open(ca_cert_path, "wb") as f:
            f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
        log.info(f"CA certificate saved to {ca_cert_path}")
        return ca_private_key, ca_cert

    def generate_server_certificate(
        self,
        common_name: str,
        sans: list[str] | None = None,
        ca_key_path: str | None = None,
        ca_cert_path: str | None = None,
    ):
        """
        Generates a server key, signs a certificate, and creates a combined server.pem file.
        - If a CA is provided, it uses it.
        - Otherwise, it generates a new self-signed CA first.
        """
        server_private_key = self._generate_private_key("server.key")

        if ca_key_path and ca_cert_path:
            log.info(f"Loading existing CA from {ca_cert_path}")
            with open(ca_key_path, "rb") as f:
                ca_private_key = serialization.load_pem_private_key(
                    f.read(), password=None
                )
            with open(ca_cert_path, "rb") as f:
                ca_cert = x509.load_pem_x509_certificate(f.read())
        else:
            ca_private_key, ca_cert = self.create_ca()

        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
        san_list = [x509.DNSName(common_name)]
        if sans:
            for name in set(sans):
                try:
                    san_list.append(x509.IPAddress(ip_address(name)))
                except ValueError:
                    san_list.append(x509.DNSName(name))

        builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(ca_cert.subject)
            .public_key(server_private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .add_extension(x509.SubjectAlternativeName(san_list), critical=False)
        )
        server_cert = builder.sign(ca_private_key, hashes.SHA256(), default_backend())

        # Save the individual server certificate (.crt)
        server_cert_path = os.path.join(self.cert_dir, "server.crt")
        server_cert_bytes = server_cert.public_bytes(serialization.Encoding.PEM)
        with open(server_cert_path, "wb") as f:
            f.write(server_cert_bytes)
        log.info(f"Server certificate saved to {server_cert_path}")

        # Create the combined server.pem file for Flower Superlink
        server_key_bytes = server_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        server_pem_path = os.path.join(self.cert_dir, "server.pem")
        with open(server_pem_path, "wb") as f:
            f.write(server_cert_bytes)
            f.write(server_key_bytes)
        log.info(f"Server PEM file (cert + key) saved to {server_pem_path}")
