"""
ExpiryGuard — Alert Routes Blueprint
======================================
Routes for viewing, sending, and managing expiry alerts.

Endpoints:
    /alerts            — View all alerts for the current user.
    /preferences       — Manage alert notification preferences.
    /send-alerts       — Trigger immediate alert sending.
    /dismiss-alert/<id> — Mark an alert as acknowledged.
    /api/alerts-count  — JSON API returning alert counts by level.
    /test-email        — Test email configuration and connectivity.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from .alert_utils import get_alert_items, send_smart_alerts
from .email_utils import send_email, test_email_connection
from .extensions import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

alert_bp = Blueprint("alert", __name__)

# -------- VIEW ALERTS --------
@alert_bp.route("/alerts")
@login_required
def alerts():
    """Display alerts for the current user"""
    alerts = get_alert_items(current_user)
    return render_template("alerts.html", alerts=alerts)

# -------- ALERT PREFERENCES --------
@alert_bp.route("/preferences", methods=['GET', 'POST'])
@login_required
def preferences():
    """Manage alert notification preferences"""
    if request.method == 'POST':
        current_user.email_alerts_enabled = request.form.get('email_alerts') == 'on'
        current_user.alert_before_days = int(request.form.get('alert_before_days', 3))
        
        db.session.commit()
        flash("Preferences updated successfully!", "success")
        return redirect(url_for('alert.preferences'))
    
    return render_template("preferences.html", user=current_user)

# -------- SEND IMMEDIATE ALERTS --------
@alert_bp.route("/send-alerts", methods=['POST'])
@login_required
def send_alerts():
    """Trigger immediate alert sending"""
    result = send_smart_alerts(current_user)
    
    if result.get('sent', 0) > 0 and result.get('failed', 0) == 0:
        flash(f"Alerts sent successfully! ({result['sent']} notifications)", "success")
    elif result.get('failed', 0) > 0:
        # build a more informative message
        msg = f"Failed to send some alerts. ({result['failed']} failed)"
        if result.get('errors'):
            # convert first few errors to human text
            details = []
            for err in result['errors'][:3]:
                details.append(f"{err['channel']} for '{err['item']}': {err['message']}")
            msg += " — " + "; ".join(details)
        msg += ". Please check your configuration (use /test-email) and server logs."
        flash(msg, "danger")
    else:
        flash("No alerts to send at this time.", "info")
    
    return redirect(url_for('alert.alerts'))

# -------- MARK ALERT AS ACKNOWLEDGED --------
@alert_bp.route("/dismiss-alert/<int:item_id>", methods=['POST'])
@login_required
def dismiss_alert(item_id):
    """Mark an alert as seen/acknowledged"""
    from .models import Item
    
    item = Item.query.get_or_404(item_id)
    
    # Verify the item belongs to the current user
    if item.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    item.alert_sent = True
    db.session.commit()
    
    return jsonify({"status": "success", "message": "Alert dismissed"})

# -------- API FOR ALERTS STATUS --------
@alert_bp.route("/api/alerts-count")
@login_required
def alerts_count():
    """Get count of pending alerts (JSON API)"""
    alerts = get_alert_items(current_user)
    
    count_by_level = {
        "EXPIRED": len([a for a in alerts if a['level'] == 'EXPIRED']),
        "CRITICAL": len([a for a in alerts if a['level'] == 'CRITICAL']),
        "WARNING": len([a for a in alerts if a['level'] == 'WARNING'])
    }
    
    return jsonify({
        "total": len(alerts),
        "by_level": count_by_level,
        "timestamp": datetime.now().isoformat()
    })

# -------- TEST EMAIL SERVICE --------
@alert_bp.route("/test-email", methods=['GET', 'POST'])
@login_required
def test_email():
    """Test email configuration and send test email to current user"""
    if request.method == 'GET':
        # Just show test result
        test_result = test_email_connection()
        return jsonify(test_result)
    
    elif request.method == 'POST':
        # Send a test email to the user
        test_result = test_email_connection()
        
        if not test_result['auth_test']:
            return jsonify({
                'success': False,
                'message': 'Email service not configured. ' + test_result['message'],
                'details': test_result
            }), 400
        
        # Try to send test email
        send_result = send_email(
            current_user.email,
            "[ExpiryGuard] Test Email",
            """This is a test email from your ExpiryGuard application.

If you're seeing this, your email service is working correctly!

Best regards,
ExpiryGuard Team"""
        )
        
        return jsonify({
            'success': send_result.get('success', False),
            'message': send_result.get('message', 'Test email sent'),
            'config_valid': test_result['auth_test']
        })

