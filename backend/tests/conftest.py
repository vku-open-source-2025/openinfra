"""Pytest configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from app.main import app
from app.infrastructure.database.mongodb import db
from app.core.config import settings
import asyncio
from typing import AsyncGenerator


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
async def authenticated_client(test_client: AsyncClient) -> AsyncGenerator[AsyncClient, None]:
    """Create authenticated test client."""
    # Create test user and login
    # This will be implemented based on your auth setup
    yield test_client


@pytest.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Setup test database."""
    # Connect to test database
    test_db_name = f"{settings.DATABASE_NAME}_test"
    db.connect()
    yield
    # Cleanup
    if db.client:
        db.client.drop_database(test_db_name)
    db.close()
