"""
ExpiryGuard — Route Registration
=================================
Centralized registration of all application blueprints.
"""

from .items import item_bp
from .users import user_bp
from ..alerts import alert_bp
from .ml import ml_bp
from .shop import shop_bp
from .home import home_bp
from .admin import admin_bp
from .reports import reports_bp

def register_routes(app):
    """Register all blueprints with the Flask application."""
    app.register_blueprint(item_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(alert_bp)
    app.register_blueprint(ml_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(reports_bp)
