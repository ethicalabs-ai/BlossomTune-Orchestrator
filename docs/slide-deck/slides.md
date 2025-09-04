---
marp: true
theme: gaia
_class: lead
paginate: true
backgroundColor: #fff
backgroundImage: url('https://marp.app/assets/hero-background.svg')
---

BlossomTune 🌸
Orchestrating Federated Learning with Flower & Gradio

A Technical Overview

<!--
notes: |
Federated Learning is a powerful concept, but putting it into practice reveals significant operational hurdles.

First, there's the challenge of onboarding participants. How do you securely register new clients, verify them, and provide them with the unique configurations they need to join the network without manual intervention?

Second is infrastructure management. An FL system has several moving parts, like the central server. You need an easy way to start, stop, and monitor these components.

Finally, there's experiment coordination. As your federation grows, managing different training runs and tracking the status of dozens or hundreds of participants becomes incredibly complex and error-prone. These are the problems BlossomTune is designed to solve.
-->

---

The Challenge: Operational Complexity in FL

- Participant Onboarding & Configuration
- Infrastructure Management & Monitoring
- Experiment Coordination & Scaling

<!--
notes: |
Our solution is BlossomTune, a web-based orchestrator that provides a comprehensive UI to manage the entire lifecycle of a federated learning experiment.

It's built on a modern stack: It uses Flower as the underlying federated learning framework, Gradio to create the highly interactive and user-friendly web interface, and it leverages Hugging Face for secure user authentication via OAuth and for hosting the example ML models.

Essentially, BlossomTune acts as a central control plane, simplifying the complexities of federated learning for both the administrators running the system and the participants joining it.
-->

---

Our Solution: BlossomTune

A web-based orchestrator for the entire FL lifecycle.

Core Technologies:

- Flower: The FL Framework
- Gradio: The Interactive Web UI
- Hugging Face: User Authentication & ML Models

<!--
notes: |
BlossomTune's features are designed around three core functions.

First, it provides centralized control for administrators. From a secure admin panel, you can start and stop the core Flower Superlink server and the Runner that executes the experiment.

Second, it offers a streamlined onboarding workflow for participants. This is a secure, multi-step process involving authentication, email activation, and admin approval, which ensures only verified clients can join.

And third, it includes live monitoring. The UI provides a real-time log stream from all backend processes, giving administrators clear visibility into the health and status of the federation.
-->

---

Key Features

- Centralized Federation Control (Admin)
- Streamlined Participant Onboarding
- Live System Monitoring

<!--
notes: |
BlossomTune has a clean, modular architecture that separates concerns effectively.

At the top, we have the Gradio Web UI, which is the user-facing interface for all interactions.

This UI communicates with the BlossomTune Backend, which is where our core Python logic lives. This backend handles UI events, manages the database, and controls the lifecycle of the external Flower processes.

Participant data, requests, and system configuration are persisted in a lightweight SQLite Database.

The backend manages the Flower Processes—specifically, the flower-superlink and flwr run commands—as background subprocesses, capturing their logs and status.

Finally, the actual machine learning task is defined in a Decoupled Flower App. This is a critical design choice, as it means the orchestration platform is generic and can run any compatible Flower application without modification.
-->

---

System Architecture

![width:720px](blossomtune-diagram.png)

<!--
notes: |
A quick look at the codebase reveals a well-engineered project that emphasizes maintainability.

The structure is highly modular, with a clear separation between the orchestrator code in blossomtune_gradio and the federated learning tasks in flower_apps.

Configuration is centralized in a single config.py file that sources settings from environment variables, which is a best practice for modern applications.

Within the orchestrator code, there's a clear separation between the UI and backend logic. The ui package defines the Gradio components and their callbacks, keeping the presentation layer distinct from the core business logic in files like federation.py and processing.py.

Finally, the project maintains high code quality by using the ruff tool for linting and formatting, and this is automatically enforced with pre-commit hooks, ensuring a consistent and clean codebase.
-->

---

Codebase Deep Dive: Structure & Quality

- Modular & Decoupled Structure (blossomtune_gradio vs. flower_apps)
- Centralized Configuration (config.py)
- Clear UI/Backend Separation (ui/ package)
- High Code Quality (Enforced by ruff & pre-commit hooks)

<!--
notes: |
For a participant, the journey to join the federation is secure and straightforward.

It begins when a user requests access by logging in with their Hugging Face account and submitting their email.

They then receive an activation code via email and must activate their request, verifying that they own the email address.

Once activated, the request appears in the admin panel for admin review.

The administrator can then approve the request and assign the participant a unique data partition ID.

Finally, the participant's status page updates to show they are approved, and they are presented with the exact connection details they need to configure their client and join the federated run.
-->

---

The Participant Journey

- Request Access (Login & Submit Email)
- Activate (Verify with Email Code)
- Admin Review (Request appears in Admin Panel)
- Approval & Configuration (Admin assigns Partition ID)
- Connect (User receives connection details)

<!--
notes: |
The Admin Panel provides centralized and powerful control over the entire federation.

Admins have one-click infrastructure management, with simple buttons to start and stop the core Superlink process.

They have controlled experiment execution. They can launch a new federated run by selecting the desired Flower App, defining a unique Run ID for tracking, and setting the total number of data partitions for the experiment.

And finally, they have an intuitive interface for request management, with clear tables for pending and approved participants that make it easy to manage the federation's members.
-->

---

The Admin Experience

- One-Click Infrastructure Management
- Controlled Experiment Execution
- Intuitive Request Management

<!--
notes: |
To make the system fully functional out-of-the-box, BlossomTune is bundled with a ready-to-run federated learning application.

The task is sentiment analysis on the well-known IMDB dataset.

The model is a bert-tiny, a lightweight and efficient transformer model from the Hugging Face Hub, making it suitable for federated settings.

Most importantly, the federation logic is designed for this ecosystem. The client app is coded to read its partition-id from the configuration provided by the Flower runtime. This ID is the same one the administrator assigns within the BlossomTune UI, demonstrating the seamless integration between the orchestrator and the individual FL clients.
-->

---

Example FL App: quickstart_huggingface

- Task: Sentiment Analysis (IMDB Dataset)
- Model: bert-tiny (Lightweight Transformer)
- Federation: Client reads partition-id from orchestrator's configuration.

<!--
notes: |
In summary, BlossomTune is a high-quality, robust orchestrator that successfully abstracts away the operational complexity of managing a federated learning system. Its modular design and user-friendly interface make it an excellent tool for both research and production environments.

Looking ahead, we have several ideas for future work. We'd like to build enhanced monitoring with visual charts and performance metrics, not just logs. We plan to add support for dynamically discovering and selecting from multiple Flower Apps, making the platform even more flexible. We also want to expose more granular control over the Runner's configurations directly in the UI and integrate with other authentication providers beyond Hugging Face.
-->

---

Conclusion & Future Work

Conclusion: A high-quality, robust orchestrator that solves key operational challenges in FL.

Future Work:

- Enhanced monitoring with visualizations & metrics
- Support for dynamic selection of multiple Flower Apps
- Granular control over Runner configurations
- Integration with other authentication providers

---

Q&A