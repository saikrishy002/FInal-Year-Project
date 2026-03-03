"""
ExpiryGuard — Configuration Classes
=====================================
Environment-specific configuration for the Flask application.

Classes:
    Config            — Base configuration (used by all environments).
    DevelopmentConfig — Enables debug mode.
    ProductionConfig  — Disables debug mode.
    TestingConfig     — Uses in-memory SQLite for fast tests.

Usage in create_app():
    app.config.from_object(config['development'])
"""

import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()


class Config:
    """Base configuration shared by all environments."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'expiryguard_secret')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///expiryguard.db'
    )
    # Fix for Heroku/Render postgres:// vs postgresql://
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security Settings
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = False # Set to True in production with HTTPS
    PERMANENT_SESSION_LIFETIME = 3600 # 1 hour


class DevelopmentConfig(Config):
    """Development configuration — enables Flask debug mode."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration — debug off, use env vars for secrets."""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration — uses in-memory SQLite, enables TESTING flag."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Quick-access dict for selecting configuration by name
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}
