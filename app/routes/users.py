"""
ExpiryGuard — User Routes Blueprint
=====================================
Authentication, profile, and role-switch request routes.

Endpoints:
    /register             — New user registration (GET/POST).
    /login                — User login with is_active check (GET/POST).
    /logout               — Log out the current session.
    /dashboard            — Redirect to role-specific dashboard.
    /profile              — View and update user profile (GET/POST).
    /request-role-switch  — Submit a role-switch request for admin approval.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

from ..models import User, Item, RoleSwitchRequest
from ..extensions import db, bcrypt, limiter

from ..utils import calculate_days_left, get_expiry_status
from ..email_utils import send_email
from ..email_templates import render_welcome_email

user_bp = Blueprint('user', __name__)


@user_bp.route('/')
def index():
    """Redirect root to login page."""
    return redirect(url_for('user.login'))


@user_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("100 per hour")
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'home')

        # Validate role
        if role not in ('shop', 'home'):
            flash("Invalid role selected", "danger")
            return redirect(request.url)

        # Check uniqueness
        if User.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect(request.url)
        if User.query.filter_by(username=username).first():
            flash("Username already taken", "danger")
            return redirect(request.url)

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

        user = User(
            username=username,
            email=email,
            password_hash=hashed_pw,
            role=role,
            email_alerts_enabled=True,
            alert_before_days=3
        )
        db.session.add(user)
        db.session.commit()

        # Send welcome email notification
        try:
            html_body = render_welcome_email(user.username, user.role)
            send_email(user.email, "Welcome to ExpiryGuard! 🎉", html_body, html=True)
        except Exception as e:
            # Registration still succeeds even if email fails
            pass

        flash("Registration Successful", "success")
        return redirect(url_for('user.login'))

    return render_template('register.html')


@user_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("100 per minute")
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash("Your account has been deactivated. Contact an administrator.", "danger")
                return render_template('login.html')
            login_user(user)
            return redirect(url_for('user.dashboard'))
        else:
            flash("Invalid Credentials", "danger")

    return render_template('login.html')


@user_bp.route('/dashboard')
@login_required
def dashboard():
    """Redirect to role-specific dashboard."""
    if current_user.role == 'shop':
        return redirect(url_for('shop.dashboard'))
    elif current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    else:
        return redirect(url_for('home.dashboard'))


@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('user.login'))


@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile and settings."""
    if request.method == 'POST':
        db.session.commit()
        flash("Profile updated successfully", "success")
        return redirect(url_for('user.profile'))

    return render_template('profile.html', user=current_user)


@user_bp.route('/request-role-switch', methods=['POST'])
@login_required
def request_role_switch():
    """Submit a role-switch request for admin approval."""
    requested_role = request.form.get('requested_role')

    if requested_role not in ('shop', 'home'):
        flash("Invalid role", "danger")
        return redirect(url_for('user.profile'))

    if requested_role == current_user.role:
        flash("You already have this role", "warning")
        return redirect(url_for('user.profile'))

    # Check for existing pending request
    existing = RoleSwitchRequest.query.filter_by(
        user_id=current_user.id, status='pending'
    ).first()
    if existing:
        flash("You already have a pending role-switch request", "warning")
        return redirect(url_for('user.profile'))

    req = RoleSwitchRequest(
        user_id=current_user.id,
        current_role=current_user.role,
        requested_role=requested_role
    )
    db.session.add(req)
    db.session.commit()
    flash("Role switch request submitted for admin approval", "success")
    return redirect(url_for('user.profile'))
