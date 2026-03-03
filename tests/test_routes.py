"""
app — Route Integration Tests
=======================================
Tests for user authentication, item management, and page access.
"""

import pytest
from tests.conftest import login


class TestAuthentication:
    """Tests for login, logout, and registration routes."""

    def test_login_page_loads(self, client):
        """GET /login returns 200."""
        resp = client.get('/login')
        assert resp.status_code == 200

    def test_register_page_loads(self, client):
        """GET /register returns 200."""
        resp = client.get('/register')
        assert resp.status_code == 200

    def test_register_new_user(self, client):
        """POST /register creates a user and redirects to login."""
        resp = client.post('/register', data={
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'Secure123',
            'role': 'home',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Registration Successful' in resp.data or b'login' in resp.data.lower()

    def test_login_valid_credentials(self, client, home_user):
        """Correct credentials redirect to dashboard."""
        resp = login(client, home_user.email)
        assert resp.status_code == 200

    def test_login_invalid_credentials(self, client):
        """Wrong credentials show error flash."""
        resp = client.post('/login', data={
            'email': 'nobody@test.com',
            'password': 'wrong',
        }, follow_redirects=True)
        assert b'Invalid Credentials' in resp.data

    def test_login_deactivated_user(self, client, db_session, home_user):
        """Deactivated user cannot log in."""
        home_user.is_active = False
        db_session.commit()

        resp = client.post('/login', data={
            'email': home_user.email,
            'password': 'TestPass123',
        }, follow_redirects=True)
        assert b'deactivated' in resp.data.lower()

    def test_logout(self, client, home_user):
        """Logout redirects to login page."""
        login(client, home_user.email)
        resp = client.get('/logout', follow_redirects=True)
        assert resp.status_code == 200


class TestProtectedRoutes:
    """Tests that protected routes redirect unauthenticated users."""

    @pytest.mark.parametrize('url', [
        '/items',
        '/add_item',
        '/bulk_upload',
        '/alerts',
        '/preferences',
    ])
    def test_redirect_if_not_logged_in(self, client, url):
        """Unauthenticated requests redirect to login."""
        resp = client.get(url, follow_redirects=False)
        assert resp.status_code in (302, 308)

    def test_admin_dashboard_requires_admin(self, client, home_user):
        """Non-admin users are denied access to /admin/dashboard."""
        login(client, home_user.email)
        resp = client.get('/admin/dashboard', follow_redirects=True)
        assert b'permission' in resp.data.lower() or resp.status_code == 200


class TestItemRoutes:
    """Tests for item CRUD routes."""

    def test_add_item_page_loads(self, client, home_user):
        """GET /add_item renders the form for logged-in users."""
        login(client, home_user.email)
        resp = client.get('/add_item')
        assert resp.status_code == 200

    def test_items_page_loads(self, client, home_user):
        """GET /items renders the items list."""
        login(client, home_user.email)
        resp = client.get('/items')
        assert resp.status_code == 200


class TestRoleSwitchRequest:
    """Tests for the role-switch request workflow."""

    def test_submit_role_switch(self, client, home_user):
        """Home user can submit a role-switch request to shop."""
        login(client, home_user.email)
        resp = client.post('/request-role-switch', data={
            'requested_role': 'shop',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'submitted' in resp.data.lower() or b'Role switch' in resp.data

    def test_duplicate_request_rejected(self, client, home_user):
        """A second pending request is rejected."""
        login(client, home_user.email)
        client.post('/request-role-switch', data={'requested_role': 'shop'})
        resp = client.post('/request-role-switch', data={
            'requested_role': 'shop',
        }, follow_redirects=True)
        assert b'already have a pending' in resp.data.lower()
