# User Guide: For Administrators

This guide explains how to manage the federation as an administrator (or Space owner).

## Accessing the Admin Panel

1.  Navigate to the orchestrator's Gradio URL.
2.  Log in with the Hugging Face account that **owns the Space**.
3.  If running locally, admin controls are enabled by default.
4.  The **"Admin Panel"** tab will become visible.

## Infrastructure Control

This section controls the core Flower services.

* **Superlink Status**: Shows if the Superlink is `🟢 Running` or `🔴 Not Running`.
* **Start/Stop Superlink**: Toggles the Flower Superlink process. This is the central server that participants connect to. *This must be running for participants to connect.*

## Federation Control

This section controls the federated learning experiment itself.

* **Runner Status**: Shows if a federated run is `🟢 Running` or `🔴 Not Running`.
* **Select Runner App**: A dropdown of all available Flower Apps found in the `flower_apps/` directory.
* **Run ID**: A unique name for this experiment (e.g., `run_123`).
* **Total Partitions**: The total number of data partitions for this run. This number is given to all clients.
* **Start/Stop Federated Run**: Toggles the Flower Runner process. This process loads the selected "Runner App" and coordinates the training rounds.

## Federation Requests

This section is for managing participants.

### Pending Requests
This table lists all participants who have successfully **activated their email** and are waiting for approval.

### Approved Participants
This table lists all participants who have been approved and assigned a Partition ID.

### Approval Workflow

1.  Click on a row in the **"Pending Requests"** table.
2.  The participant's ID will appear in the **"Selected Participant ID"** field.
3.  A unique, available **"Assign Partition ID"** will be automatically suggested. You can change this, but it must be unique.
4.  Click **"✅ Approve"** or **"❌ Deny"**.

* **On Approval**:
    1.  The participant's status is set to "approved".
    2.  A new EC key pair (`.key` and `.pub`) is generated for them and stored in the `data/keys` volume.
    3.  Their public key is added to the `authorized_supernodes.csv` file, granting them access to the Superlink.
    4.  The next time the participant checks their status, they will get the "Approved" message and their `.blossomfile` download.

* **On Denial**:
    1.  The participant's status is set to "denied".
    2.  If they were previously approved, their public key is **removed** from `authorized_supernodes.csv`, revoking their access.