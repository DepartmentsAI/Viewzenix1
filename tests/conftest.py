"""
Pytest configuration file with common fixtures.
"""
import pytest
from src.backend.app import create_app

@pytest.fixture
def app():
    """Create the Flask application for testing."""
    app = create_app('testing')
    yield app

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    with app.test_client() as client:
        yield client 