import os
import shutil
import logging


from blossomtune_gradio.tls import TLSGenerator
from blossomtune_gradio import config as cfg


# Configure basic logging for the script
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def generate_dev_cert():
    """Generates a self-signed certificate for localhost development."""
    try:
        print("\n--- Generating self-signed certificate for localhost ---")
        cert_dir = "certificates_localhost"
        if os.path.exists(cert_dir):
            shutil.rmtree(cert_dir)

        generator = TLSGenerator(cert_dir=cert_dir)
        # Note: No existing CA is passed, so a new one will be created.
        generator.generate_server_certificate(
            common_name="localhost", sans=["localhost", "127.0.0.1"]
        )
        print(f"\n✅ Success! Self-signed CA and server cert created in '{cert_dir}'.")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")


def generate_prod_cert():
    """Generates a server certificate signed by the CA specified in config."""
    if not cfg.TLS_CA_KEY_PATH or not cfg.TLS_CA_CERT_PATH:
        print(
            "\n❌ Error: TLS_CA_KEY_PATH and TLS_CA_CERT_PATH are not set in your config."
        )
        print("Please configure the paths to your main CA certificate and key.")
        return

    try:
        print(
            f"\n--- Generating production certificate signed by {cfg.TLS_CA_CERT_PATH} ---"
        )
        common_name = input(
            "Enter the primary domain name for the server (e.g., fl.mydomain.com): "
        ).strip()
        if not common_name:
            print("Error: Domain name cannot be empty.")
            return

        generator = TLSGenerator(cert_dir=cfg.TLS_CERT_DIR)
        generator.generate_server_certificate(
            common_name=common_name,
            ca_key_path=cfg.TLS_CA_KEY_PATH,
            ca_cert_path=cfg.TLS_CA_CERT_PATH,
        )
        print(
            f"\n✅ Success! Server certificate and key created in '{cfg.TLS_CERT_DIR}'."
        )
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")


def main():
    """Main function to run the interactive menu."""
    while True:
        print("\n===== BlossomTune TLS Certificate Generator =====")
        print("Select an option:")
        print("  1. Generate a self-signed 'localhost' certificate (for Development)")
        print("  2. Generate a server certificate using the main CA (for Production)")
        print("  3. Exit")

        choice = input("Enter your choice [1]: ").strip() or "1"

        if choice == "1":
            generate_dev_cert()
        elif choice == "2":
            generate_prod_cert()
        elif choice == "3":
            print("Exiting.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
