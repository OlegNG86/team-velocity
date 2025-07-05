import pytest
import os
import tempfile
import importlib
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from core.models import Base
from db.database import get_session, get_async_session, DatabaseManager

# Save original database configuration
original_database_manager = None

@pytest.fixture(scope="session")
def test_db():
    """Create a test database for the entire test session."""
    # Use in-memory SQLite database for faster tests
    temp_db = ":memory:"
    
    # Create engine and tables
    engine = create_engine(f"sqlite:///{temp_db}")
    Base.metadata.create_all(engine)
    
    yield engine

@pytest.fixture(scope="function")
def db_session(monkeypatch, test_db):
    """Create a database session for each test function and patch all database access."""
    global original_database_manager
    
    # Create a test session
    Session = sessionmaker(bind=test_db, expire_on_commit=False)
    session = Session()
    
    # Save original database manager
    if original_database_manager is None:
        import db.database
        original_database_manager = db.database.db_manager
    
    # Create and patch database manager with test configuration
    test_db_manager = DatabaseManager()
    test_db_manager.database_url = f"sqlite:///{test_db.url.database}"
    test_db_manager.engine = test_db
    test_db_manager.SessionLocal = Session
    
    # Replace the global database manager
    import db.database
    db.database.db_manager = test_db_manager
    
    # Replace get_session to return our test session
    def mock_get_session():
        return session
    
    monkeypatch.setattr(db.database, "get_session", mock_get_session)
    
    # For async tests, patch the async session too
    @pytest.fixture
    def mock_async_session():
        async def _mock_async_session():
            yield session
        return _mock_async_session
    
    monkeypatch.setattr(db.database, "get_async_session", mock_async_session)
    
    # Clean up any existing data
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    
    yield session
    
    # Clean up after the test
    session.rollback()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    session.close()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "telegram_id": "123456789",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User"
    }


@pytest.fixture
def sample_story_point_data():
    """Sample story point data for testing."""
    return {
        "points": 5.0,
        "description": "Test task implementation"
    }


@pytest.fixture
def sample_team_data():
    """Sample team data for testing."""
    return {
        "name": "Test Team",
        "description": "A test team for unit testing"
    }