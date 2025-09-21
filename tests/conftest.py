import pytest
import sqlite3

from blossomtune_gradio import database


@pytest.fixture
def in_memory_db(mocker):
    """
    Fixture to set up and tear down an in-memory SQLite database for tests.
    It ensures that the same connection object is used for both schema
    initialization and the test execution.
    """
    con = sqlite3.connect(":memory:")
    mocker.patch("sqlite3.connect", return_value=con)
    database.init()
    yield con
    con.close()
