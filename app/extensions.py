"""
ExpiryGuard — Flask Extensions
================================
Instantiates Flask extensions without binding them to an app yet.
They are bound later in ``create_app()`` via ``ext.init_app(app)``.

This module avoids circular imports by keeping extension objects
in a single, importable location.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman

# Database ORM
db = SQLAlchemy()

# Password hashing
bcrypt = Bcrypt()

# Session-based authentication
login_manager = LoginManager()

# CSRF Protection
csrf = CSRFProtect()

# Rate Limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["1000 per day", "200 per hour"])

# Security Headers
talisman = Talisman()
