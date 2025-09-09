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
                timestamp TEXT NOT NULL,
                partition_id INTEGER,
                email TEXT,
                hf_handle TEXT,
                activation_code TEXT,
                is_activated INTEGER DEFAULT 0
            )
        """)

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
