import pytest
from app.db.models import Base
from app.db.session import engine


@pytest.fixture(autouse=True, scope="session")
def setup_test_database():
    """Ensures database tables exist for test executions."""
    Base.metadata.create_all(bind=engine)
    yield