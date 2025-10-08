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


def get_db():
    """
    Dependency function to get a new database session.
    This ensures that each request gets a clean session that is closed afterward.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
