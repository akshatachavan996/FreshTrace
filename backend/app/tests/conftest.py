"""Pytest fixtures for FreshTrace backend tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes.verify import get_db
from app.config import Settings
from app.database.base import Base
from app.main import app

# Create in-memory SQLite database for isolated test execution
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create fresh database tables for each test and tear them down afterward."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_settings():
    """Configured test settings."""
    return Settings(
        APP_ENV="testing",
        DEBUG=True,
        BIFROST_BASE_URL="http://test-bifrost:8080/v1",
        BIFROST_API_KEY="test-bifrost-key-12345",
        AI_MODEL="gpt-4o-mini",
        AI_PROVIDER="openai",
        TAVILY_API_KEY="tvly-test-tavily-key-12345",
        CACHE_EXPIRATION_HOURS=1,
    )
