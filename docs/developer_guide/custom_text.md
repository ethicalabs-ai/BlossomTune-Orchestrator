# How-To: Customize UI Text

All user-facing text (labels, descriptions, error messages) is loaded from an external YAML file and is not hardcoded in the Python source. This makes it easy to customize or translate the UI.

## 1. The Configuration File

The text is loaded from:

`blossomtune_gradio/settings/blossomtune.yaml`

This file's location can be overridden at runtime by setting the `BLOSSOMTUNE_CONFIG` environment variable.

## 2. The Schema

All keys in the YAML file are validated against a JSON schema to prevent typos and ensure all required text is defined:

`blossomtune_gradio/settings/blossomtune.schema.json`

If you add a new text item, you must also add it to the schema's `properties` and `required` sections.

## 3. The Loading Mechanism

The `blossomtune_gradio.settings.Settings` class is a singleton that loads, validates, and parses the YAML file on application startup.

It uses **Jinja2** to render templates, allowing for dynamic content in the UI.

## Example: Changing an Error Message

1.  **Open `blossomtune.yaml`**

    Find the key you want to change. For example, the message for an invalid email:

    ```yaml
    # blossomtune_gradio/settings/blossomtune.yaml
    ui:
      # ...
      invalid_email_md: |
        ### Invalid Input
        Please provide a valid email address.
      # ...
    ```

2.  **Edit the Text**

    You can change the text (including markdown) to whatever you need:

    ```yaml
    # blossomtune_gradio/settings/blossomtune.yaml
    ui:
      # ...
      invalid_email_md: |
        ### Email Not Valid
        **Warning:** Your email address appears to be incorrect. Please try again.
      # ...
    ```

3.  **Using Dynamic Content**

    Some text fields, like the "approved" status, use Jinja2 variables.

    ```yaml
    status_approved_md: |
      ### ✅ Approved
      Your request for ID `{{ participant_id }}` has been approved.
      - **Your Assigned Partition ID:** `{{ partition_id }}`
    ```

    When the application renders this text, it passes the participant's data to the template, filling in the `{{ ... }}` placeholders.
