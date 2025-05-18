"""Pytest configuration and shared fixtures."""
import os
import tempfile
import pytest
from app import create_app
from app.extensions import db as _db
from app.models.user import User

# Set the testing configuration
os.environ['FLASK_ENV'] = 'testing'

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
        'JWT_SECRET_KEY': 'test-jwt-secret-key'
    })

    # Create the database and load test data
    with app.app_context():
        _db.create_all()

    yield app

    # Clean up the database after the test
    with app.app_context():
        _db.session.remove()
        _db.drop_all()
    
    # Remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture(scope='session')
db(app):
    """Provide the transactional fixtures with access to the database."""
    return _db

@pytest.fixture
db_session(db):
    """Create a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)
    
    db.session = session
    
    yield session
    
    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
        is_active=True,
        is_admin=False
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def auth_headers(test_user, client):
    """Get authentication headers for the test user."""
    response = client.post('/api/auth/login', json={
        'email': test_user.email,
        'password': 'testpass123'
    })
    access_token = response.json['access_token']
    return {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
