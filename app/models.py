"""
ExpiryGuard — Database Models
==============================
SQLAlchemy ORM models for all database tables.

Models:
    User             — Registered users with role-based access (shop / home / admin).
    Item             — Tracked items with expiry dates and ML predictions.
    ShopProduct      — Products managed by shop-role users.
    HomeNeed         — Household needs tracked by home-role users.
    RoleSwitchRequest — Requests from users to change their role (needs admin approval).
    AdminLog         — Audit trail of all administrative actions.
"""

from flask_login import UserMixin
from .extensions import db


# ═══════════════════════════════════════════════════════════
#  USER MODEL
# ═══════════════════════════════════════════════════════════
class User(db.Model, UserMixin):
    """
    Registered user account.

    Roles:
        - ``shop``  — can manage shop products, inventory, pricing.
        - ``home``  — can track household needs and items.
        - ``admin`` — full access to user management and system settings.

    Attributes:
        is_active (bool): When False the user cannot log in (soft-delete).
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='home')  # shop / home / admin
    is_active = db.Column(db.Boolean, default=True)

    # Alert Preferences
    email_alerts_enabled = db.Column(db.Boolean, default=True)
    alert_before_days = db.Column(db.Integer, default=3)

    # Relationships
    items = db.relationship('Item', backref='user', lazy=True)
    shop_products = db.relationship('ShopProduct', backref='user', lazy=True)
    home_needs = db.relationship('HomeNeed', backref='user', lazy=True)


# ═══════════════════════════════════════════════════════════
#  ITEM MODEL — tracked inventory items
# ═══════════════════════════════════════════════════════════
class Item(db.Model):
    """
    A tracked item with purchase/expiry dates and optional ML predictions.

    ML Fields:
        predicted_waste  — output of the waste forecast model (Model 1).
        recommendation   — output of the recommendation model (Model 2).
    """
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100))
    purchase_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    quantity = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    alert_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    # ML prediction columns
    predicted_waste = db.Column(db.Float, nullable=True)
    recommendation = db.Column(db.String(50), nullable=True)
    buying_advice = db.Column(db.String(200), nullable=True)


# ═══════════════════════════════════════════════════════════
#  SHOP PRODUCT MODEL — managed by shop-role users
# ═══════════════════════════════════════════════════════════
class ShopProduct(db.Model):
    """Shop inventory product with stock, price, and optional promotions."""
    __tablename__ = 'shop_products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100))
    stock = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, default=0.0)
    promotion = db.Column(db.String(200), nullable=True)  # e.g. "20% off", "Buy 1 Get 1"
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())


# ═══════════════════════════════════════════════════════════
#  HOME NEED MODEL — managed by home-role users
# ═══════════════════════════════════════════════════════════
class HomeNeed(db.Model):
    """Household need with priority level and fulfilment status."""
    __tablename__ = 'home_needs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100))
    priority = db.Column(db.String(20), default='medium')  # low / medium / high
    status = db.Column(db.String(20), default='pending')    # pending / fulfilled
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())


# ═══════════════════════════════════════════════════════════
#  ROLE SWITCH REQUEST — home ↔ shop role change
# ═══════════════════════════════════════════════════════════
class RoleSwitchRequest(db.Model):
    """
    A request from a user to switch between 'home' and 'shop' roles.
    Must be approved or rejected by an admin.
    """
    __tablename__ = 'role_switch_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    current_role = db.Column(db.String(20), nullable=False)
    requested_role = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending / approved / rejected
    created_at = db.Column(db.DateTime, default=db.func.now())

    user = db.relationship('User', backref='role_switch_requests', foreign_keys=[user_id])


# ═══════════════════════════════════════════════════════════
#  ADMIN LOG — audit trail for all admin actions
# ═══════════════════════════════════════════════════════════
class AdminLog(db.Model):
    """
    Immutable log entry recording an admin action.

    Every significant admin operation (create/edit/delete user,
    approve/reject role switch) writes one row to this table.
    """
    __tablename__ = 'admin_logs'

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now())

    # Relationships (explicit FK needed because two FKs point at users)
    admin = db.relationship('User', foreign_keys=[admin_id], backref='admin_logs')
    target_user = db.relationship('User', foreign_keys=[target_user_id])
