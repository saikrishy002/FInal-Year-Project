"""
ExpiryGuard — Alert Utility Functions
======================================
Core alert logic: determines alert levels, builds messages,
and orchestrates email notifications for expiring items.

Functions:
    get_alert_level         — categorise urgency (EXPIRED/CRITICAL/WARNING/SAFE).
    get_alert_items         — gather items needing alerts for a user.
    build_alert_message     — compose human-readable alert text.
    send_smart_alerts       — send alerts per user preferences.
    process_all_user_alerts — batch-process all users (called by scheduler).
"""

from datetime import date, datetime, timedelta
from .models import Item
from .extensions import db
from .email_utils import send_email, test_email_connection
from .email_templates import render_expiry_alert
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# Alert configuration from environment
CRITICAL_DAYS = int(os.getenv('CRITICAL_DAYS', 2))
WARNING_DAYS = int(os.getenv('WARNING_DAYS', 5))
DEFAULT_ALERT_DAYS = int(os.getenv('DEFAULT_ALERT_DAYS', 3))

def get_alert_level(days_left):
    """
    Determine alert level based on days left until expiry.
    Smart categorization for better prioritization.
    """
    if days_left < 0:
        return "EXPIRED", 5  # Highest priority
    elif days_left <= CRITICAL_DAYS:
        return "CRITICAL", 4  # High priority
    elif days_left <= WARNING_DAYS:
        return "WARNING", 3   # Medium priority
    else:
        return "SAFE", 0      # No alert needed

def get_alert_items(user):
    """
    Get items that need alerts for a specific user.
    Smart filtering based on user preferences and alert levels.
    """
    today = date.today()
    alerts = []

    items = Item.query.filter_by(user_id=user.id).all()

    for item in items:
        days_left = (item.expiry_date - today).days
        
        # Check if item should be alerted based on user's preference
        if days_left > user.alert_before_days and days_left >= 0:
            continue
        
        level, priority = get_alert_level(days_left)
        
        # Skip items that don't meet alert criteria
        if level == "SAFE":
            continue

        alerts.append({
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "days_left": days_left,
            "level": level,
            "priority": priority,
            "email": user.email,
            "expiry_date": item.expiry_date.strftime('%Y-%m-%d'),
            "quantity": item.quantity
        })

    # Sort by priority (highest first)
    alerts.sort(key=lambda x: x['priority'], reverse=True)
    
    return alerts

def build_alert_message(alert_item):
    """Build human-readable alert message"""
    level_emoji = {
        "EXPIRED": "🔴",
        "CRITICAL": "🟠",
        "WARNING": "🟡"
    }
    
    emoji = level_emoji.get(alert_item['level'], "")
    
    message = f"""{emoji} {alert_item['level']} ALERT

Item: {alert_item['name']}
Category: {alert_item['category']}
Quantity: {alert_item['quantity']}
Expires: {alert_item['expiry_date']}

{format_time_left(alert_item['days_left'])}

Check ExpiryGuard dashboard for more details."""
    
    return message

def format_time_left(days_left):
    """Format days left into readable text"""
    if days_left < 0:
        abs_days = abs(days_left)
        return f"⚠️ Already expired {abs_days} day(s) ago!"
    elif days_left == 0:
        return "⏰ Expires TODAY!"
    else:
        return f"⏱️ Expires in {days_left} day(s)"

def send_smart_alerts(user):
    """
    Send intelligent alerts to user based on their preferences.
    Uses email notification based on user settings.
    Consolidates multiple alerts into a single professional HTML email.
    """
    alerts = get_alert_items(user)
    
    if not alerts:
        return {"sent": 0, "failed": 0}
    
    # Send email alert if enabled
    if user.email_alerts_enabled:
        # Build consolidated HTML email using professional template
        html_body = render_expiry_alert(user.username, alerts)
        
        # Subject line based on the most urgent alert
        highest_priority_level = alerts[0]['level']
        subject = f"[{highest_priority_level}] ExpiryGuard Inventory Alert ({len(alerts)} items)"
        
        result = send_email(user.email, subject, html_body, html=True)
        
        if result.get('success', False):
            logger.info(f"Consolidated HTML alert sent to {user.email} for {len(alerts)} items")
            return {"sent": len(alerts), "failed": 0}
        else:
            msg = result.get('message', 'Unknown error')
            logger.error(f"Failed to send consolidated alert to {user.email}: {msg}")
            return {
                "sent": 0, 
                "failed": len(alerts), 
                "errors": [{
                    'channel': 'email',
                    'item': 'consolidated_alert',
                    'message': msg
                }]
            }
    
    return {"sent": 0, "failed": 0}

def process_all_user_alerts():
    """
    Process and send alerts for all users.
    Called by the scheduler at regular intervals.
    """
    from .models import User
    
    users = User.query.all()
    total_sent = 0
    total_failed = 0
    
    for user in users:
        result = send_smart_alerts(user)
        total_sent += result.get('sent', 0)
        total_failed += result.get('failed', 0)
    
    return {
        "timestamp": datetime.now(),
        "total_sent": total_sent,
        "total_failed": total_failed,
        "users_processed": len(users)
    }