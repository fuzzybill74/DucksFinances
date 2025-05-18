import pytest
from app import create_app
from app.extensions import db

@pytest.fixture
def app():
    """Create and configure a new app instance for testing."""
    # Create a test config
    class TestConfig:
        TESTING = True
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        JWT_SECRET_KEY = 'test-secret-key'
    
    # Create the app with test config
    app = create_app(TestConfig)
    
    # Create the database and load test data
    with app.app_context():
        db.create_all()
    
    yield app
    
    # Clean up the database after the test
    with app.app_context():
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

def test_health_check(client):
    ""Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {
        'status': 'healthy',
        'database': 'connected'
    }
