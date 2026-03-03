"""
ExpiryGuard — Utility Functions
================================
Shared helper functions used across multiple blueprints.

Functions:
    calculate_days_left  — days between today and an expiry date.
    get_expiry_status    — human-readable status label for an item.
    role_required        — decorator to restrict routes by user role.
"""

from datetime import date
from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user, login_required


def calculate_days_left(expiry_date):
    """
    Calculate the number of days remaining until expiry.

    Args:
        expiry_date (date): The expiry date of the item.

    Returns:
        int: Positive = days left, 0 = today, negative = past expiry.
    """
    today = date.today()
    return (expiry_date - today).days


def get_expiry_status(days_left):
    """
    Return a human-readable status string based on days remaining.

    Args:
        days_left (int): Number of days until expiry.

    Returns:
        str: One of 'Expired', 'Expiring Soon', 'Near Expiry', or 'Safe'.
    """
    if days_left < 0:
        return "Expired"
    elif days_left <= 3:
        return "Expiring Soon"
    elif days_left <= 7:
        return "Near Expiry"
    else:
        return "Safe"


def role_required(*roles):
    """
    Decorator to restrict route access to specific user roles.

    Usage::

        @app.route('/admin/dashboard')
        @role_required('admin')
        def admin_dashboard():
            ...

    Args:
        *roles: One or more role strings (e.g. 'admin', 'shop', 'home').

    Returns:
        function: Decorated view function.
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for('user.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator