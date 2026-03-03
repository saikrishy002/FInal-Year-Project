"""
app — Test Configuration & Fixtures
=============================================
Shared pytest fixtures used across all test modules.

Provides:
    app        — Flask app configured for testing (SQLite in-memory).
    client     — Flask test client for simulating HTTP requests.
    db_session — Clean database session, rolled back after each test.
    admin_user — Pre-created admin user for auth-required tests.
    home_user  — Pre-created home-role user.
    shop_user  — Pre-created shop-role user.
"""

import sys
import os
import pytest

# Ensure the project root is on the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.extensions import db as _db, bcrypt


@pytest.fixture(scope='session')
def app():
    """Create the Flask application configured for testing."""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret',
        'SERVER_NAME': 'localhost',
    })

    # Create all tables in the in-memory database
    with app.app_context():
        _db.create_all()

    yield app

    # Teardown
    with app.app_context():
        _db.drop_all()


@pytest.fixture(scope='function')
def db_session(app):
    """Provide a clean database session for each test function."""
    with app.app_context():
        _db.create_all()
        yield _db.session
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app, db_session):
    """Flask test client for simulating HTTP requests."""
    return app.test_client()


# ── Helper to create a user ──────────────────────────────
def _make_user(db_sess, username, email, role, password='TestPass123'):
    """Internal helper — create and persist a User record."""
    from app.models import User
    hashed = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(
        username=username,
        email=email,
        password_hash=hashed,
        role=role,
        is_active=True,
    )
    db_sess.add(user)
    db_sess.commit()
    return user


@pytest.fixture
def admin_user(db_session):
    """Pre-created admin user (username='admin', password='TestPass123')."""
    return _make_user(db_session, 'admin', 'admin@test.com', 'admin')


@pytest.fixture
def home_user(db_session):
    """Pre-created home-role user (username='homeuser', password='TestPass123')."""
    return _make_user(db_session, 'homeuser', 'home@test.com', 'home')


@pytest.fixture
def shop_user(db_session):
    """Pre-created shop-role user (username='shopuser', password='TestPass123')."""
    return _make_user(db_session, 'shopuser', 'shop@test.com', 'shop')


# ── Login helper ─────────────────────────────────────────
def login(client, email, password='TestPass123'):
    """Simulate a login POST and return the response."""
    return client.post('/login', data={
        'email': email,
        'password': password,
    }, follow_redirects=True)
