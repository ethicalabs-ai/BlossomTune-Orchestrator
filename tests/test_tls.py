import os
import pytest
from cryptography import x509
from cryptography.x509.oid import NameOID

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

        # Check if files were created
        assert os.path.exists(os.path.join(tls_generator.cert_dir, "ca.key"))
        assert os.path.exists(os.path.join(tls_generator.cert_dir, "ca.crt"))

        # Verify the certificate properties
        assert ca_cert.issuer == ca_cert.subject
        assert (
            ca_cert.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
            is True
        )
        common_name = ca_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[
            0
        ].value
        assert common_name == "BlossomTune Self-Signed CA"

    def test_generate_server_certificate_with_new_ca(self, tls_generator):
        """
        Test generating a server certificate, which should also create a new CA
        when one is not provided.
        """
        common_name = "test.local"
        sans = ["test.local", "192.168.1.10"]
        tls_generator.generate_server_certificate(common_name=common_name, sans=sans)

        # Check for all expected files
        assert os.path.exists(os.path.join(tls_generator.cert_dir, "ca.key"))
        assert os.path.exists(os.path.join(tls_generator.cert_dir, "ca.crt"))
        assert os.path.exists(os.path.join(tls_generator.cert_dir, "server.key"))
        assert os.path.exists(os.path.join(tls_generator.cert_dir, "server.crt"))

        # Load certs to verify issuer relationship
        with open(os.path.join(tls_generator.cert_dir, "ca.crt"), "rb") as f:
            ca_cert = x509.load_pem_x509_certificate(f.read())
        with open(os.path.join(tls_generator.cert_dir, "server.crt"), "rb") as f:
            server_cert = x509.load_pem_x509_certificate(f.read())

        assert server_cert.issuer == ca_cert.subject
        assert (
            server_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
            == common_name
        )

        # Verify SANs
        san_ext = server_cert.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        )
        dns_names = san_ext.value.get_values_for_type(x509.DNSName)
        ip_addresses = san_ext.value.get_values_for_type(x509.IPAddress)

        assert set(dns_names) == {"test.local"}
        assert str(ip_addresses[0]) == "192.168.1.10"

    def test_generate_server_certificate_with_existing_ca(self, tls_generator):
        """Test generating a server certificate using a pre-existing CA."""
        # First, create a CA
        tls_generator.create_ca()
        ca_key_path = os.path.join(tls_generator.cert_dir, "ca.key")
        ca_cert_path = os.path.join(tls_generator.cert_dir, "ca.crt")

        # Now, create a new generator in a different directory to simulate separation
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
        # Check that a *new* CA was NOT created in the server directory
        assert not os.path.exists(os.path.join(server_gen_dir, "ca.key"))

        # Load certs to verify the issuer relationship
        with open(ca_cert_path, "rb") as f:
            ca_cert = x509.load_pem_x509_certificate(f.read())
        with open(os.path.join(server_gen_dir, "server.crt"), "rb") as f:
            server_cert = x509.load_pem_x509_certificate(f.read())

        assert server_cert.issuer == ca_cert.subject
        assert (
            server_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
            == "prod.local"
        )
