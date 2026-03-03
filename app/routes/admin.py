"""
Admin Blueprint — full user management, role-switch requests,
dashboard analytics, and audit logging.
Restricted to users with role='admin'.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
import logging

from ..models import User, ShopProduct, HomeNeed, RoleSwitchRequest, Item, AdminLog
from ..extensions import db, bcrypt
from ..utils import role_required
from ..email_templates import render_welcome_email

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ─── HELPERS ───────────────────────────────────────────────
def log_action(action, target_user_id=None, details=None):
    """Write an entry to the admin audit log."""
    entry = AdminLog(
        admin_id=current_user.id,
        action=action,
        target_user_id=target_user_id,
        details=details,
    )
    db.session.add(entry)


def _notify_user_email(user, subject, body, html=False):
    """Best-effort email notification (failures are logged, never raised)."""
    try:
        from ..email_utils import send_email
        send_email(user.email, subject, body, html=html)
    except Exception as e:
        logger.warning(f"Email notification failed for {user.email}: {e}")


# ═══════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════
@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    users = User.query.all()
    shop_count = sum(1 for u in users if u.role == 'shop')
    home_count = sum(1 for u in users if u.role == 'home')
    admin_count = sum(1 for u in users if u.role == 'admin')
    active_count = sum(1 for u in users if u.is_active)
    inactive_count = len(users) - active_count

    total_products = ShopProduct.query.count()
    total_needs = HomeNeed.query.count()
    total_items = Item.query.count()

    # Recent uploads — last 20 shop products and home needs
    recent_products = ShopProduct.query.order_by(ShopProduct.created_at.desc()).limit(20).all()
    recent_needs = HomeNeed.query.order_by(HomeNeed.created_at.desc()).limit(20).all()

    # Pending role-switch requests
    pending_requests = RoleSwitchRequest.query.filter_by(status='pending').all()

    return render_template('admin_dashboard.html',
                           users=users,
                           shop_count=shop_count,
                           home_count=home_count,
                           admin_count=admin_count,
                           active_count=active_count,
                           inactive_count=inactive_count,
                           total_products=total_products,
                           total_needs=total_needs,
                           total_items=total_items,
                           recent_products=recent_products,
                           recent_needs=recent_needs,
                           pending_requests=pending_requests)


# ═══════════════════════════════════════════════════════════
#  USER MANAGEMENT — LIST
# ═══════════════════════════════════════════════════════════
@admin_bp.route('/users')
@role_required('admin')
def users_list():
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    search = request.args.get('q', '').strip()

    query = User.query
    if role_filter:
        query = query.filter_by(role=role_filter)
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) | (User.email.ilike(f'%{search}%'))
        )

    all_users = query.order_by(User.id.asc()).all()
    return render_template('admin_users.html', users=all_users,
                           role_filter=role_filter, status_filter=status_filter,
                           search=search)


# ═══════════════════════════════════════════════════════════
#  USER MANAGEMENT — ADD
# ═══════════════════════════════════════════════════════════
@admin_bp.route('/users/add', methods=['GET', 'POST'])
@role_required('admin')
def add_user():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        role = request.form.get('role', 'home')

        if role not in ('shop', 'home', 'admin'):
            flash("Invalid role selected", "danger")
            return redirect(request.url)

        if User.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect(request.url)
        if User.query.filter_by(username=username).first():
            flash("Username already taken", "danger")
            return redirect(request.url)

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email,
                    password_hash=hashed_pw, role=role)
        db.session.add(user)

        log_action('create_user', details=f"Created user '{username}' with role '{role}'")
        db.session.commit()

        # Send welcome email
        html_body = render_welcome_email(user.username, user.role)
        _notify_user_email(user, "Welcome to ExpiryGuard! 🎉", html_body, html=True)

        flash(f"User '{username}' created successfully", "success")
        return redirect(url_for('admin.users_list'))

    return render_template('admin_user_form.html', mode='add', user=None)


# ═══════════════════════════════════════════════════════════
#  USER MANAGEMENT — EDIT
# ═══════════════════════════════════════════════════════════
@admin_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit_user(id):
    user = User.query.get_or_404(id)

    if request.method == 'POST':
        old_role = user.role
        user.username = request.form['username'].strip()
        user.email = request.form['email'].strip()
        user.role = request.form.get('role', user.role)

        new_password = request.form.get('password', '').strip()
        if new_password:
            user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')

        changes = []
        if old_role != user.role:
            changes.append(f"role {old_role}→{user.role}")
        changes.append(f"updated username/email")
        if new_password:
            changes.append("password reset")

        log_action('edit_user', target_user_id=user.id,
                   details=', '.join(changes))
        db.session.commit()

        flash(f"User '{user.username}' updated", "success")
        return redirect(url_for('admin.users_list'))

    return render_template('admin_user_form.html', mode='edit', user=user)


# ═══════════════════════════════════════════════════════════
#  USER MANAGEMENT — TOGGLE ACTIVE
# ═══════════════════════════════════════════════════════════
@admin_bp.route('/users/<int:id>/toggle-active', methods=['POST'])
@role_required('admin')
def toggle_active(id):
    user = User.query.get_or_404(id)

    if user.id == current_user.id:
        flash("You cannot deactivate your own account", "danger")
        return redirect(url_for('admin.users_list'))

    user.is_active = not user.is_active
    status_word = "activated" if user.is_active else "deactivated"

    log_action(f'{status_word}_user', target_user_id=user.id,
               details=f"Account {status_word}")
    db.session.commit()

    # Send styled HTML email notification
    from ..email_templates import render_account_change
    html_body = render_account_change(user.username, status_word)
    _notify_user_email(user, f"ExpiryGuard — Account {status_word.title()}", html_body, html=True)

    flash(f"User '{user.username}' {status_word}", "success" if user.is_active else "warning")
    return redirect(url_for('admin.users_list'))


# ═══════════════════════════════════════════════════════════
#  USER MANAGEMENT — DELETE
# ═══════════════════════════════════════════════════════════
@admin_bp.route('/users/<int:id>/delete', methods=['POST'])
@role_required('admin')
def delete_user(id):
    user = User.query.get_or_404(id)

    if user.id == current_user.id:
        flash("You cannot delete your own account", "danger")
        return redirect(url_for('admin.users_list'))

    username = user.username
    log_action('delete_user', target_user_id=user.id,
               details=f"Deleted user '{username}'")

    # Delete related records first to avoid FK constraint errors
    Item.query.filter_by(user_id=user.id).delete()
    ShopProduct.query.filter_by(user_id=user.id).delete()
    HomeNeed.query.filter_by(user_id=user.id).delete()
    RoleSwitchRequest.query.filter_by(user_id=user.id).delete()

    # Nullify admin_log references (preserve audit trail, remove FK link)
    AdminLog.query.filter_by(target_user_id=user.id).update({'target_user_id': None})
    AdminLog.query.filter_by(admin_id=user.id).update({'admin_id': current_user.id})

    db.session.delete(user)
    db.session.commit()

    flash(f"User '{username}' permanently deleted", "danger")
    return redirect(url_for('admin.users_list'))


# ═══════════════════════════════════════════════════════════
#  ROLE-SWITCH REQUEST HANDLING
# ═══════════════════════════════════════════════════════════
@admin_bp.route('/role-request/<int:id>/<action>', methods=['GET', 'POST'])
@role_required('admin')
def handle_role_request(id, action):
    req = RoleSwitchRequest.query.get_or_404(id)
    user = req.user

    logger.info(f"Admin {current_user.username} handling role request {id} for user {user.username if user else 'N/A'}: Action={action}")

    if not user:
        flash("Associated user not found", "danger")
        return redirect(url_for('admin.dashboard'))

    from ..email_templates import render_role_switch_email

    try:
        if action == 'approve':
            req.status = 'approved'
            user.role = req.requested_role
            log_action('approve_role_switch', target_user_id=user.id,
                       details=f"{req.current_role} → {req.requested_role}")
            
            # Commit BEFORE sending email to ensure DB is updated even if SMTP hangs
            db.session.commit()
            logger.info(f"Role switch approved in DB for {user.username}")

            html_body = render_role_switch_email(
                user.username, 'approved', req.current_role, req.requested_role
            )
            _notify_user_email(user, "ExpiryGuard — Role Switch Approved ✅", html_body, html=True)
            flash(f"Role switch approved for {user.username}", "success")

        elif action == 'reject':
            req.status = 'rejected'
            log_action('reject_role_switch', target_user_id=user.id,
                       details=f"{req.current_role} → {req.requested_role} (rejected)")
            
            db.session.commit()
            logger.info(f"Role switch rejected in DB for {user.username}")

            html_body = render_role_switch_email(
                user.username, 'rejected', req.current_role, req.requested_role
            )
            _notify_user_email(user, "ExpiryGuard — Role Switch Rejected ❌", html_body, html=True)
            flash("Role switch rejected", "warning")
        else:
            flash("Invalid action", "danger")
            return redirect(url_for('admin.dashboard'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error handling role request {id}: {str(e)}", exc_info=True)
        flash(f"Error processing request: {str(e)}", "danger")

    return redirect(url_for('admin.dashboard'))


# ═══════════════════════════════════════════════════════════
#  AUDIT LOG
# ═══════════════════════════════════════════════════════════
@admin_bp.route('/logs')
@role_required('admin')
def logs():
    log_entries = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(200).all()
    return render_template('admin_logs.html', logs=log_entries)
