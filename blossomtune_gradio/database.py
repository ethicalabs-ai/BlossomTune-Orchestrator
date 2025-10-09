from alembic import config
from sqlalchemy import create_engine, Column, String, Integer, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base


from blossomtune_gradio import config as cfg


Base = declarative_base()
engine = create_engine(cfg.SQLALCHEMY_URL)

# The sessionmaker factory generates new Session objects when called.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Request(Base):
    """
    SQLAlchemy model for the 'requests' table.
    This table stores information about participants wanting to join the federation.
    """

    __tablename__ = "requests"

    participant_id = Column(String, primary_key=True)
    status = Column(String, nullable=False, default="pending")
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    partition_id = Column(Integer, nullable=True)
    email = Column(String, nullable=True)
    hf_handle = Column(String, nullable=True)
    activation_code = Column(String, nullable=True)
    is_activated = Column(Integer, nullable=False, default=0)
    public_key_pem = Column(String(), nullable=True)

    def __repr__(self):
        return (
            f"<Request(participant_id='{self.participant_id}', status='{self.status}')>"
        )


class Config(Base):
    """
    SQLAlchemy model for the 'config' table.
    A simple key-value store for application settings.
    """

    __tablename__ = "config"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)

    def __repr__(self):
        return f"<Config(key='{self.key}', value='{self.value}')>"


def run_migrations():
    """
    Applies any pending Alembic migrations to the database.
    This should be called on application startup.
    """
    print("Running database migrations...")
    alembicArgs = [
        "--raiseerr",
        "upgrade",
        "head",
    ]
    config.main(argv=alembicArgs)
