"""
app — Model Unit Tests
================================
Tests for all SQLAlchemy models: User, Item, ShopProduct,
HomeNeed, RoleSwitchRequest, and AdminLog.
"""

import pytest
from datetime import date, datetime
from app.models import (
    User, Item, ShopProduct, HomeNeed, RoleSwitchRequest, AdminLog
)


class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self, db_session):
        """A user can be created with required fields and defaults."""
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash='hashed',
            role='home',
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.username == 'testuser'
        assert user.role == 'home'
        assert user.is_active is True
        assert user.email_alerts_enabled is True
        assert user.alert_before_days == 3

    def test_user_default_role(self, db_session):
        """Default role should be 'home'."""
        user = User(username='u2', email='u2@test.com', password_hash='h')
        db_session.add(user)
        db_session.commit()
        assert user.role == 'home'

    def test_user_deactivation(self, db_session):
        """is_active can be toggled to False."""
        user = User(username='u3', email='u3@test.com', password_hash='h')
        db_session.add(user)
        db_session.commit()

        user.is_active = False
        db_session.commit()
        assert user.is_active is False

    def test_unique_email(self, db_session):
        """Duplicate email should raise an integrity error."""
        u1 = User(username='a', email='dup@test.com', password_hash='h')
        u2 = User(username='b', email='dup@test.com', password_hash='h')
        db_session.add(u1)
        db_session.commit()
        db_session.add(u2)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()

    def test_unique_username(self, db_session):
        """Duplicate username should raise an integrity error."""
        u1 = User(username='same', email='a@test.com', password_hash='h')
        u2 = User(username='same', email='b@test.com', password_hash='h')
        db_session.add(u1)
        db_session.commit()
        db_session.add(u2)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()


class TestItemModel:
    """Tests for the Item model."""

    def test_create_item(self, db_session):
        """An item can be created and linked to a user."""
        user = User(username='owner', email='o@test.com', password_hash='h')
        db_session.add(user)
        db_session.commit()

        item = Item(
            name='Milk',
            category='Food',
            purchase_date=date(2026, 1, 1),
            expiry_date=date(2026, 3, 15),
            quantity=2,
            user_id=user.id,
        )
        db_session.add(item)
        db_session.commit()

        assert item.id is not None
        assert item.user_id == user.id
        assert item.alert_sent is False
        assert item.predicted_waste is None

    def test_item_ml_fields(self, db_session):
        """ML prediction fields can be set."""
        user = User(username='ml', email='ml@test.com', password_hash='h')
        db_session.add(user)
        db_session.commit()

        item = Item(name='Rice', category='Food',
                    purchase_date=date(2026, 1, 1),
                    expiry_date=date(2026, 6, 1),
                    quantity=5, user_id=user.id)
        db_session.add(item)
        db_session.commit()

        item.predicted_waste = 0.35
        item.recommendation = 'Consume Soon'
        db_session.commit()

        assert item.predicted_waste == 0.35
        assert item.recommendation == 'Consume Soon'


class TestShopProductModel:
    """Tests for the ShopProduct model."""

    def test_create_product(self, db_session):
        user = User(username='shopown', email='s@test.com', password_hash='h', role='shop')
        db_session.add(user)
        db_session.commit()

        product = ShopProduct(
            name='Widget', category='Electronics',
            stock=50, price=9.99, user_id=user.id,
        )
        db_session.add(product)
        db_session.commit()

        assert product.id is not None
        assert product.stock == 50
        assert product.price == 9.99


class TestHomeNeedModel:
    """Tests for the HomeNeed model."""

    def test_create_need(self, db_session):
        user = User(username='homeown', email='h@test.com', password_hash='h')
        db_session.add(user)
        db_session.commit()

        need = HomeNeed(name='Soap', category='Household', user_id=user.id)
        db_session.add(need)
        db_session.commit()

        assert need.priority == 'medium'
        assert need.status == 'pending'


class TestRoleSwitchRequestModel:
    """Tests for the RoleSwitchRequest model."""

    def test_create_request(self, db_session):
        user = User(username='req', email='r@test.com', password_hash='h')
        db_session.add(user)
        db_session.commit()

        req = RoleSwitchRequest(
            user_id=user.id,
            current_role='home',
            requested_role='shop',
        )
        db_session.add(req)
        db_session.commit()

        assert req.status == 'pending'
        assert req.user.username == 'req'


class TestAdminLogModel:
    """Tests for the AdminLog model."""

    def test_create_log(self, db_session):
        admin = User(username='adm', email='adm@test.com', password_hash='h', role='admin')
        target = User(username='tgt', email='t@test.com', password_hash='h')
        db_session.add_all([admin, target])
        db_session.commit()

        log = AdminLog(
            admin_id=admin.id,
            action='delete_user',
            target_user_id=target.id,
            details='Deleted user tgt',
        )
        db_session.add(log)
        db_session.commit()

        assert log.admin.username == 'adm'
        assert log.target_user.username == 'tgt'
        assert log.action == 'delete_user'
