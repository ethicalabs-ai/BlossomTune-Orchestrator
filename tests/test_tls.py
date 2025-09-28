import os
import pytest
from cryptography import x509

from blossomtune_gradio.tls import TLSGenerator


@pytest.fixture
def tls_generator(tmp_path):
    """Fixture to create a TLSGenerator instance in a temporary directory."""
    cert_dir = tmp_path / "certs"
    return TLSGenerator(cert_dir=str(cert_dir))


class TestTLSGenerator:
    """Test suite for the TLSGenerator class."""

    def test_init_creates_directory(self, tmp_path):
        """Verify that the certificate directory is created on initialization."""
        cert_dir = tmp_path / "new_certs"
        assert not os.path.exists(cert_dir)
        TLSGenerator(cert_dir=str(cert_dir))
        assert os.path.exists(cert_dir)

    def test_create_ca(self, tls_generator):
        """Test the creation of a self-signed Certificate Authority."""
        ca_key, ca_cert = tls_generator.create_ca()

        assert os.path.exists(os.path.join(tls_generator.cert_dir, "ca.key"))
        assert os.path.exists(os.path.join(tls_generator.cert_dir, "ca.crt"))
        assert ca_cert.issuer == ca_cert.subject
        assert (
            ca_cert.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
            is True
        )

    def test_generate_server_certificate_with_new_ca(self, tls_generator):
        """
        Test generating a server certificate, which should also create a new CA
        and the combined server.pem file.
        """
        common_name = "test.local"
        sans = ["test.local", "192.168.1.10"]
        tls_generator.generate_server_certificate(common_name=common_name, sans=sans)

        # Check for all expected files
        assert os.path.exists(os.path.join(tls_generator.cert_dir, "ca.key"))
        assert os.path.exists(os.path.join(tls_generator.cert_dir, "ca.crt"))
        assert os.path.exists(os.path.join(tls_generator.cert_dir, "server.key"))
        assert os.path.exists(os.path.join(tls_generator.cert_dir, "server.crt"))
        assert os.path.exists(os.path.join(tls_generator.cert_dir, "server.pem"))

        # Load certs to verify issuer relationship
        with open(os.path.join(tls_generator.cert_dir, "ca.crt"), "rb") as f:
            ca_cert = x509.load_pem_x509_certificate(f.read())
        with open(os.path.join(tls_generator.cert_dir, "server.crt"), "rb") as f:
            server_cert = x509.load_pem_x509_certificate(f.read())

        assert server_cert.issuer == ca_cert.subject

        # Verify PEM content
        with open(os.path.join(tls_generator.cert_dir, "server.pem"), "r") as f:
            pem_content = f.read()
        assert "-----BEGIN CERTIFICATE-----" in pem_content
        assert "-----BEGIN RSA PRIVATE KEY-----" in pem_content

    def test_generate_server_certificate_with_existing_ca(self, tls_generator):
        """Test generating a server certificate using a pre-existing CA."""
        tls_generator.create_ca()
        ca_key_path = os.path.join(tls_generator.cert_dir, "ca.key")
        ca_cert_path = os.path.join(tls_generator.cert_dir, "ca.crt")

        server_gen_dir = os.path.join(
            os.path.dirname(tls_generator.cert_dir), "server_certs"
        )
        server_generator = TLSGenerator(cert_dir=server_gen_dir)

        server_generator.generate_server_certificate(
            common_name="prod.local", ca_key_path=ca_key_path, ca_cert_path=ca_cert_path
        )

        # Check that server files were created in the new directory
        assert os.path.exists(os.path.join(server_gen_dir, "server.key"))
        assert os.path.exists(os.path.join(server_gen_dir, "server.crt"))
        assert os.path.exists(os.path.join(server_gen_dir, "server.pem"))
        # Check that a *new* CA was NOT created in the server directory
        assert not os.path.exists(os.path.join(server_gen_dir, "ca.key"))

        # Verify PEM content
        with open(os.path.join(server_gen_dir, "server.pem"), "r") as f:
            pem_content = f.read()
        assert "-----BEGIN CERTIFICATE-----" in pem_content
        assert "-----BEGIN RSA PRIVATE KEY-----" in pem_content
