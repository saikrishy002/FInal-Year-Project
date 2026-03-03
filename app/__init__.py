"""
ExpiryGuard — Application Factory
===================================
Central package initialiser.  Exposes ``create_app()`` which:
    1. Configures Flask, SQLAlchemy, Bcrypt and Flask-Login.
    2. Registers all blueprints (items, users, alerts, ml, shop, home, admin).
    3. Sets up context processors and error handlers.

Flask factory pattern docs:
    https://flask.palletsprojects.com/en/latest/patterns/appfactories/
"""

from flask import Flask
import logging
from .extensions import db, bcrypt, login_manager
from sqlalchemy import inspect, text
import sys
import os

# Add root directory to sys.path to import config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import config

# ── Logging configuration ────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    """
    Application factory — creates and configures the Flask app.

    Returns:
        Flask: Fully configured Flask application instance.
    """
    app = Flask(__name__, template_folder='templates', static_folder='static')

    # ── Core configuration ───────────────────────────────
    app.config.from_object(config['development'])

    # ── Initialise extensions ────────────────────────────
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'user.login'  # redirect target for @login_required
    
    from .extensions import csrf, limiter, talisman
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Configure Talisman with a relaxed CSP for external scripts/styles
    csp = {
        'default-src': '\'self\'',
        'script-src': [
            '\'self\'',
            'https://cdn.jsdelivr.net',
            'https://code.jquery.com',
            'https://cdnjs.cloudflare.com',
            '\'unsafe-inline\''  # Required for inline scripts in templates
        ],
        'style-src': [
            '\'self\'',
            'https://cdn.jsdelivr.net',
            'https://cdnjs.cloudflare.com',
            'https://fonts.googleapis.com',
            '\'unsafe-inline\''
        ],
        'font-src': [
            '\'self\'',
            'https://fonts.gstatic.com',
            'https://cdnjs.cloudflare.com'
        ],
        'img-src': ['\'self\'', 'data:']
    }
    talisman.init_app(app, content_security_policy=csp, force_https=False)

    # ── Register blueprints ──────────────────────────────
    from .routes import register_routes
    register_routes(app)

    # ── Register error handlers ──────────────────────────
    from .errors import register_error_handlers
    register_error_handlers(app)

    # ── Context processors ───────────────────────────────
    @app.context_processor
    def inject_now():
        """Make ``now`` (current UTC time) available in all templates."""
        from datetime import datetime
        return {'now': datetime.utcnow()}

    # ── User loader for Flask-Login ──────────────────────
    @login_manager.user_loader
    def load_user(user_id):
        """Load a user by primary key for session management."""
        from .models import User
        return User.query.get(int(user_id))

    # ── Database Auto-Migration ──────────────────────────
    def auto_migrate():
        """
        Automatically add missing columns and create missing tables so the
        application can start without manual SQL migration scripts.
        """
        try:
            inspector = inspect(db.engine)
            table_names = inspector.get_table_names()

            # ── users table ──────────────────────────────────────────
            if 'users' in table_names:
                existing = {c['name'] for c in inspector.get_columns('users')}
                if 'email_alerts_enabled' not in existing:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN email_alerts_enabled BOOLEAN DEFAULT TRUE;"))
                if 'alert_before_days' not in existing:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN alert_before_days INTEGER DEFAULT 3;"))
                if 'role' not in existing:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'home';"))
                if 'is_active' not in existing:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE;"))

            # ── items table ──────────────────────────────────────────
            if 'items' in table_names:
                existing = {c['name'] for c in inspector.get_columns('items')}
                if 'alert_sent' not in existing:
                    db.session.execute(text("ALTER TABLE items ADD COLUMN alert_sent BOOLEAN DEFAULT FALSE;"))
                if 'created_at' not in existing:
                    db.session.execute(text("ALTER TABLE items ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;"))
                if 'predicted_waste' not in existing:
                    db.session.execute(text("ALTER TABLE items ADD COLUMN predicted_waste FLOAT;"))
                if 'recommendation' not in existing:
                    db.session.execute(text("ALTER TABLE items ADD COLUMN recommendation VARCHAR(50);"))
                if 'buying_advice' not in existing:
                    db.session.execute(text("ALTER TABLE items ADD COLUMN buying_advice VARCHAR(200);"))

            # ── shop_products table ──────────────────────────────────
            if 'shop_products' not in table_names:
                db.session.execute(text("""
                    CREATE TABLE shop_products (
                        id INTEGER PRIMARY KEY AUTO_INCREMENT,
                        name VARCHAR(150) NOT NULL,
                        category VARCHAR(100),
                        stock INTEGER DEFAULT 0,
                        price FLOAT DEFAULT 0.0,
                        promotion VARCHAR(200),
                        user_id INTEGER NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    );
                """))

            # ── home_needs table ─────────────────────────────────────
            if 'home_needs' not in table_names:
                db.session.execute(text("""
                    CREATE TABLE home_needs (
                        id INTEGER PRIMARY KEY AUTO_INCREMENT,
                        name VARCHAR(150) NOT NULL,
                        category VARCHAR(100),
                        priority VARCHAR(20) DEFAULT 'medium',
                        status VARCHAR(20) DEFAULT 'pending',
                        user_id INTEGER NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    );
                """))

            # ── role_switch_requests table ───────────────────────────
            if 'role_switch_requests' not in table_names:
                db.session.execute(text("""
                    CREATE TABLE role_switch_requests (
                        id INTEGER PRIMARY KEY AUTO_INCREMENT,
                        user_id INTEGER NOT NULL,
                        current_role VARCHAR(20) NOT NULL,
                        requested_role VARCHAR(20) NOT NULL,
                        status VARCHAR(20) DEFAULT 'pending',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    );
                """))

            # ── admin_logs table (audit trail) ───────────────────────
            if 'admin_logs' not in table_names:
                db.session.execute(text("""
                    CREATE TABLE admin_logs (
                        id INTEGER PRIMARY KEY AUTO_INCREMENT,
                        admin_id INTEGER NOT NULL,
                        action VARCHAR(100) NOT NULL,
                        target_user_id INTEGER,
                        details TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (admin_id) REFERENCES users(id),
                        FOREIGN KEY (target_user_id) REFERENCES users(id)
                    );
                """))

            db.session.commit()
            logger.info("Database schema migrated successfully")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Auto-migration failed: {e}")

    # Run migration and initialize scheduler
    with app.app_context():
        try:
            db.create_all()
            auto_migrate()
            
            # Initialize the background alert scheduler for production/development
            from .scheduler import init_scheduler
            init_scheduler(app)
            
        except Exception as e:
            logger.error(f"Error during app context initialization: {e}")

    return app
