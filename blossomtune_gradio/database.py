import sqlite3
from blossomtune_gradio import config as cfg


def init():
    """Initializes the DB, adds columns, and creates config table."""
    with sqlite3.connect(cfg.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                participant_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        # Safely add new columns
        try:
            cursor.execute("ALTER TABLE requests ADD COLUMN partition_id INTEGER")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise  # Re-raise if it's not the expected error
        try:
            cursor.execute("ALTER TABLE requests ADD COLUMN email TEXT")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
        try:
            cursor.execute("ALTER TABLE requests ADD COLUMN hf_handle TEXT")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
        try:
            cursor.execute("ALTER TABLE requests ADD COLUMN activation_code TEXT")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
        try:
            cursor.execute(
                "ALTER TABLE requests ADD COLUMN is_activated INTEGER DEFAULT 0"
            )
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise

        # Create a simple key-value config table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        # Initialize default number of partitions if not present
        cursor.execute(
            "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)",
            ("num_partitions", "10"),
        )
        conn.commit()
