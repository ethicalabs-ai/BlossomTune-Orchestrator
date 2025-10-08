import pytest
from unittest.mock import MagicMock

from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from blossomtune_gradio import config


@pytest.fixture(scope="session")
def alembic_config():
    """Fixture to create a valid Alembic Config object."""
    return Config("alembic.ini")


@pytest.fixture
def db_session(mocker, tmp_path):
    """
    Fixture to set up a clean file-based SQLite database for each test function.
    It creates the database schema using Alembic programmatically and ensures all
    modules use the same test database session.
    """
    db_file = tmp_path / "test_federation.db"
    db_url = f"sqlite:///{db_file}"
    mocker.patch.object(config, "SQLALCHEMY_URL", db_url)

    # Create an Alembic Config object and point it to the temp database.
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", "alembic")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    # Apply the migrations to create the schema in the temporary database.
    command.upgrade(alembic_cfg, "head")

    # Set up the SQLAlchemy engine and session factory for the tests to use.
    engine = create_engine(db_url)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Mock the SessionLocal factory in each module where it is imported and used.
    mocker.patch("blossomtune_gradio.federation.SessionLocal", return_value=session)
    mocker.patch("blossomtune_gradio.processing.SessionLocal", return_value=session)
    mocker.patch("blossomtune_gradio.ui.callbacks.SessionLocal", return_value=session)

    yield session

    session.close()


@pytest.fixture
def mock_settings(mocker):
    """Fixture to mock the settings module, available to all tests."""
    mock_get = MagicMock(
        side_effect=lambda key, **kwargs: f"mock_{key}".format(**kwargs)
    )
    mocker.patch("blossomtune_gradio.federation.settings.get_text", mock_get)
    mocker.patch("blossomtune_gradio.ui.callbacks.settings.get_text", mock_get)
    return mock_get
