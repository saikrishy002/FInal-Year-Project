"""
app — Admin Action Tests
==================================
Tests for admin-only operations: user CRUD, role-switch approval,
audit logging, and access control.
"""

import pytest
from app.models import User, AdminLog, RoleSwitchRequest
from tests.conftest import login


class TestAdminAccess:
    """Ensure only admin-role users can access admin routes."""

    def test_admin_dashboard_accessible(self, client, admin_user):
        """Admin can access /admin/dashboard."""
        login(client, admin_user.email)
        resp = client.get('/admin/dashboard')
        assert resp.status_code == 200

    def test_admin_users_accessible(self, client, admin_user):
        """Admin can access /admin/users."""
        login(client, admin_user.email)
        resp = client.get('/admin/users')
        assert resp.status_code == 200

    def test_admin_logs_accessible(self, client, admin_user):
        """Admin can access /admin/logs."""
        login(client, admin_user.email)
        resp = client.get('/admin/logs')
        assert resp.status_code == 200

    def test_non_admin_denied(self, client, home_user):
        """Home user is denied access to admin pages."""
        login(client, home_user.email)
        resp = client.get('/admin/dashboard', follow_redirects=True)
        assert b'permission' in resp.data.lower()


class TestUserManagement:
    """Tests for admin user CRUD operations."""

    def test_add_user(self, client, admin_user, db_session):
        """Admin can create a new user via POST /admin/users/add."""
        login(client, admin_user.email)
        resp = client.post('/admin/users/add', data={
            'username': 'createduser',
            'email': 'created@test.com',
            'password': 'NewPass123',
            'role': 'shop',
        }, follow_redirects=True)
        assert resp.status_code == 200

        new_user = User.query.filter_by(username='createduser').first()
        assert new_user is not None
        assert new_user.role == 'shop'

    def test_add_user_form_loads(self, client, admin_user):
        """GET /admin/users/add renders the add form."""
        login(client, admin_user.email)
        resp = client.get('/admin/users/add')
        assert resp.status_code == 200

    def test_edit_user(self, client, admin_user, home_user, db_session):
        """Admin can edit a user's role via POST /admin/users/<id>/edit."""
        login(client, admin_user.email)
        resp = client.post(f'/admin/users/{home_user.id}/edit', data={
            'username': home_user.username,
            'email': home_user.email,
            'role': 'shop',
        }, follow_redirects=True)
        assert resp.status_code == 200

        updated = User.query.get(home_user.id)
        assert updated.role == 'shop'

    def test_toggle_active(self, client, admin_user, home_user, db_session):
        """Admin can deactivate a user."""
        login(client, admin_user.email)
        resp = client.post(
            f'/admin/users/{home_user.id}/toggle-active',
            follow_redirects=True,
        )
        assert resp.status_code == 200

        updated = User.query.get(home_user.id)
        assert updated.is_active is False

    def test_cannot_deactivate_self(self, client, admin_user):
        """Admin cannot deactivate their own account."""
        login(client, admin_user.email)
        resp = client.post(
            f'/admin/users/{admin_user.id}/toggle-active',
            follow_redirects=True,
        )
        assert b'cannot deactivate your own' in resp.data.lower()

    def test_delete_user(self, client, admin_user, home_user, db_session):
        """Admin can delete a user permanently."""
        login(client, admin_user.email)
        uid = home_user.id
        resp = client.post(
            f'/admin/users/{uid}/delete',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert User.query.get(uid) is None

    def test_cannot_delete_self(self, client, admin_user):
        """Admin cannot delete their own account."""
        login(client, admin_user.email)
        resp = client.post(
            f'/admin/users/{admin_user.id}/delete',
            follow_redirects=True,
        )
        assert b'cannot delete your own' in resp.data.lower()


class TestRoleSwitchApproval:
    """Tests for admin approval/rejection of role-switch requests."""

    def test_approve_role_switch(self, client, admin_user, home_user, db_session):
        """Admin approves a pending role-switch → user role changes."""
        req = RoleSwitchRequest(
            user_id=home_user.id,
            current_role='home',
            requested_role='shop',
        )
        db_session.add(req)
        db_session.commit()

        login(client, admin_user.email)
        resp = client.post(
            f'/admin/role-request/{req.id}/approve',
            follow_redirects=True,
        )
        assert resp.status_code == 200

        updated_req = RoleSwitchRequest.query.get(req.id)
        assert updated_req.status == 'approved'
        assert User.query.get(home_user.id).role == 'shop'

    def test_reject_role_switch(self, client, admin_user, home_user, db_session):
        """Admin rejects a pending role-switch → status changes, role stays."""
        req = RoleSwitchRequest(
            user_id=home_user.id,
            current_role='home',
            requested_role='shop',
        )
        db_session.add(req)
        db_session.commit()

        login(client, admin_user.email)
        resp = client.post(
            f'/admin/role-request/{req.id}/reject',
            follow_redirects=True,
        )
        assert resp.status_code == 200

        updated_req = RoleSwitchRequest.query.get(req.id)
        assert updated_req.status == 'rejected'
        assert User.query.get(home_user.id).role == 'home'


class TestAdminAuditLog:
    """Tests that admin actions are properly logged."""

    def test_create_user_logged(self, client, admin_user, db_session):
        """Creating a user generates an AdminLog entry."""
        login(client, admin_user.email)
        client.post('/admin/users/add', data={
            'username': 'logged',
            'email': 'logged@test.com',
            'password': 'Pass123',
            'role': 'home',
        }, follow_redirects=True)

        log = AdminLog.query.filter_by(action='create_user').first()
        assert log is not None
        assert log.admin_id == admin_user.id

    def test_delete_user_logged(self, client, admin_user, home_user, db_session):
        """Deleting a user generates an AdminLog entry."""
        login(client, admin_user.email)
        uid = home_user.id
        client.post(f'/admin/users/{uid}/delete', follow_redirects=True)

        log = AdminLog.query.filter_by(action='delete_user').first()
        assert log is not None
        # target_user_id is nullified after deletion (FK cleanup by design)
        assert log.target_user_id is None
