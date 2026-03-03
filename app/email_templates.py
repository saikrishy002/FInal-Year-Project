"""
ExpiryGuard — HTML Email Templates
====================================
Professional, responsive email templates for all notification types.

Templates:
    render_base_email          — Master layout wrapper (header, footer, branding).
    render_expiry_alert        — Item expiry notifications.
    render_role_switch_email   — Role-switch approval/rejection.
    render_account_change      — Account deactivation, deletion, or edits.
    render_welcome_email       — New user welcome message.
    render_weekly_summary      — Weekly digest of items and stats.

All templates use inline CSS for maximum email-client compatibility.
"""

# ─── Brand Colours ────────────────────────────────────────
PRIMARY = "#10b981"          # Emerald green
PRIMARY_DARK = "#065f46"
ACCENT = "#f59e0b"           # Amber
DANGER = "#ef4444"
WARNING = "#f59e0b"
INFO = "#3b82f6"
BG = "#f8fafc"
TEXT_MAIN = "#1e293b"
TEXT_MUTED = "#64748b"
WHITE = "#ffffff"
BORDER = "#e2e8f0"
APP_URL = "http://127.0.0.1:5000"


def _base_layout(content_html, preview_text=""):
    """
    Master email layout with header, content area, and footer.

    Args:
        content_html (str): The inner HTML content to place in the body.
        preview_text (str): Hidden preview text shown in inbox listings.

    Returns:
        str: Complete HTML email string.
    """
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ExpiryGuard Notification</title>
<!--[if mso]>
<style>table,td,div,p,a {{font-family: Arial, sans-serif;}}</style>
<![endif]-->
</head>
<body style="margin:0;padding:0;background-color:{BG};font-family:'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;-webkit-font-smoothing:antialiased;">

<!-- Preview Text (hidden in body, shown in inbox) -->
<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;">
    {preview_text}&nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌
</div>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:{BG};padding:24px 0;">
<tr><td align="center">

<!-- ═══ Email Container ═══ -->
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background-color:{WHITE};border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

    <!-- ─── Header ─── -->
    <tr>
        <td style="background:linear-gradient(135deg,{PRIMARY},{PRIMARY_DARK});padding:32px 40px;text-align:center;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
            <tr>
                <td style="text-align:center;">
                    <div style="display:inline-block;background:{WHITE};width:48px;height:48px;border-radius:12px;line-height:48px;text-align:center;font-size:24px;margin-bottom:12px;">
                        🛡️
                    </div>
                    <h1 style="margin:8px 0 0;font-size:22px;font-weight:700;color:{WHITE};letter-spacing:-0.3px;">ExpiryGuard</h1>
                    <p style="margin:4px 0 0;font-size:13px;color:rgba(255,255,255,0.8);font-weight:400;">Smart Inventory &amp; Expiry Management</p>
                </td>
            </tr>
            </table>
        </td>
    </tr>

    <!-- ─── Body Content ─── -->
    <tr>
        <td style="padding:36px 40px 24px;">
            {content_html}
        </td>
    </tr>

    <!-- ─── Footer ─── -->
    <tr>
        <td style="padding:0 40px 32px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
            <tr><td style="border-top:1px solid {BORDER};padding-top:24px;text-align:center;">
                <p style="margin:0 0 8px;font-size:12px;color:{TEXT_MUTED};">
                    This is an automated notification from <strong>ExpiryGuard</strong>.
                </p>
                <p style="margin:0 0 12px;font-size:12px;color:{TEXT_MUTED};">
                    Manage your alert preferences in
                    <a href="{APP_URL}/preferences" style="color:{PRIMARY};text-decoration:none;font-weight:600;">Settings</a>.
                </p>
                <p style="margin:0;font-size:11px;color:#94a3b8;">
                    &copy; 2026 ExpiryGuard &bull; All rights reserved
                </p>
            </td></tr>
            </table>
        </td>
    </tr>

</table>
<!-- ═══ End Container ═══ -->

</td></tr>
</table>
</body>
</html>
"""


def _button(text, url, color=PRIMARY):
    """Render a call-to-action button."""
    return f"""
    <table role="presentation" cellpadding="0" cellspacing="0" style="margin:24px auto 8px;">
    <tr><td style="border-radius:8px;background:{color};">
        <a href="{url}" target="_blank"
           style="display:inline-block;padding:14px 32px;font-size:14px;font-weight:700;
                  color:{WHITE};text-decoration:none;border-radius:8px;
                  letter-spacing:0.3px;">
            {text}
        </a>
    </td></tr>
    </table>
    """


def _info_row(label, value):
    """Render a key→value row inside an info card."""
    return f"""
    <tr>
        <td style="padding:8px 16px;font-size:13px;color:{TEXT_MUTED};font-weight:600;width:140px;border-bottom:1px solid {BORDER};">{label}</td>
        <td style="padding:8px 16px;font-size:13px;color:{TEXT_MAIN};border-bottom:1px solid {BORDER};">{value}</td>
    </tr>
    """


def _info_card(rows_html, accent_color=PRIMARY):
    """Wrap info rows in a styled card."""
    return f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="border:1px solid {BORDER};border-radius:10px;overflow:hidden;margin:16px 0;border-left:4px solid {accent_color};">
        {rows_html}
    </table>
    """


# ═══════════════════════════════════════════════════════════
#  TEMPLATE 1 — Expiry Alert
# ═══════════════════════════════════════════════════════════
def render_expiry_alert(username, items):
    """
    Expiry alert email for items nearing or past their expiry date.

    Args:
        username (str): Recipient's display name.
        items (list[dict]): Each dict has: name, category, days_left, level, expiry_date, quantity.

    Returns:
        str: Complete HTML email.
    """
    level_colors = {"EXPIRED": DANGER, "CRITICAL": "#ea580c", "WARNING": ACCENT}

    item_rows = ""
    for it in items:
        color = level_colors.get(it['level'], TEXT_MUTED)
        badge = f"""<span style="display:inline-block;padding:3px 10px;font-size:11px;font-weight:700;
                     color:{WHITE};background:{color};border-radius:20px;letter-spacing:0.5px;">
                     {it['level']}</span>"""

        if it['days_left'] < 0:
            time_text = f"Expired {abs(it['days_left'])} day(s) ago"
        elif it['days_left'] == 0:
            time_text = "Expires <strong>TODAY</strong>"
        else:
            time_text = f"Expires in <strong>{it['days_left']}</strong> day(s)"

        item_rows += f"""
        <tr>
            <td style="padding:12px 16px;border-bottom:1px solid {BORDER};">
                <strong style="color:{TEXT_MAIN};font-size:14px;">{it['name']}</strong><br>
                <span style="font-size:12px;color:{TEXT_MUTED};">{it.get('category','—')} &bull; Qty: {it.get('quantity',1)}</span>
            </td>
            <td style="padding:12px 16px;border-bottom:1px solid {BORDER};text-align:center;">
                {badge}
            </td>
            <td style="padding:12px 16px;border-bottom:1px solid {BORDER};text-align:right;font-size:13px;color:{TEXT_MAIN};">
                {time_text}<br>
                <span style="font-size:11px;color:{TEXT_MUTED};">{it['expiry_date']}</span>
            </td>
        </tr>
        """

    content = f"""
    <h2 style="margin:0 0 8px;font-size:20px;color:{TEXT_MAIN};">⚠️ Expiry Alert</h2>
    <p style="margin:0 0 20px;font-size:14px;color:{TEXT_MUTED};line-height:1.6;">
        Hello <strong>{username}</strong>,<br>
        The following items in your inventory need your attention:
    </p>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="border:1px solid {BORDER};border-radius:10px;overflow:hidden;">
        <tr style="background:{BG};">
            <td style="padding:10px 16px;font-size:11px;font-weight:700;color:{TEXT_MUTED};text-transform:uppercase;letter-spacing:0.5px;">Item</td>
            <td style="padding:10px 16px;font-size:11px;font-weight:700;color:{TEXT_MUTED};text-transform:uppercase;text-align:center;letter-spacing:0.5px;">Status</td>
            <td style="padding:10px 16px;font-size:11px;font-weight:700;color:{TEXT_MUTED};text-transform:uppercase;text-align:right;letter-spacing:0.5px;">Expiry</td>
        </tr>
        {item_rows}
    </table>

    <p style="margin:20px 0 0;font-size:13px;color:{TEXT_MUTED};line-height:1.6;">
        Review your items and take action to reduce waste.
    </p>

    {_button("View My Items →", f"{APP_URL}/items")}
    """
    return _base_layout(content, f"{len(items)} items need attention — ExpiryGuard Alert")


# ═══════════════════════════════════════════════════════════
#  TEMPLATE 2 — Role-Switch Approval / Rejection
# ═══════════════════════════════════════════════════════════
def render_role_switch_email(username, action, old_role, new_role):
    """
    Email sent when an admin approves or rejects a role-switch request.

    Args:
        username (str): Recipient's display name.
        action (str): 'approved' or 'rejected'.
        old_role (str): The user's previous role.
        new_role (str): The role the user requested.

    Returns:
        str: Complete HTML email.
    """
    is_approved = action.lower() == "approved"
    status_color = PRIMARY if is_approved else DANGER
    status_icon = "✅" if is_approved else "❌"
    status_word = "Approved" if is_approved else "Rejected"

    if is_approved:
        message = f"Great news! Your request to switch from <strong>{old_role}</strong> to <strong>{new_role}</strong> has been approved. Your account has been updated and you now have access to all {new_role} features."
        cta = _button("Explore Your New Dashboard →", f"{APP_URL}/dashboard")
    else:
        message = f"Your request to switch from <strong>{old_role}</strong> to <strong>{new_role}</strong> has been reviewed and was not approved at this time. If you believe this was in error, please contact the administrator."
        cta = _button("Contact Support", f"{APP_URL}/profile", color=TEXT_MUTED)

    rows = _info_row("Request", f"{old_role.title()} → {new_role.title()}")
    rows += _info_row("Status", f'<span style="color:{status_color};font-weight:700;">{status_icon} {status_word}</span>')
    rows += _info_row("Current Role", f"<strong>{new_role.title() if is_approved else old_role.title()}</strong>")

    content = f"""
    <h2 style="margin:0 0 8px;font-size:20px;color:{TEXT_MAIN};">Role Switch {status_word}</h2>
    <p style="margin:0 0 20px;font-size:14px;color:{TEXT_MUTED};line-height:1.6;">
        Hello <strong>{username}</strong>,
    </p>
    <p style="margin:0 0 20px;font-size:14px;color:{TEXT_MAIN};line-height:1.7;">
        {message}
    </p>

    {_info_card(rows, status_color)}
    {cta}
    """
    return _base_layout(content, f"Your role-switch request has been {action} — ExpiryGuard")


# ═══════════════════════════════════════════════════════════
#  TEMPLATE 3 — Account Change (Deactivation / Deletion / Edit)
# ═══════════════════════════════════════════════════════════
def render_account_change(username, change_type, details=None):
    """
    Email sent when an admin modifies the user's account.

    Args:
        username (str): Recipient's display name.
        change_type (str): 'deactivated', 'activated', 'deleted', 'edited'.
        details (str|None): Optional description of changes made.

    Returns:
        str: Complete HTML email.
    """
    config = {
        "deactivated": {
            "icon": "🔒",
            "title": "Account Deactivated",
            "color": DANGER,
            "message": "Your ExpiryGuard account has been <strong>temporarily deactivated</strong> by an administrator. You will not be able to log in until it is reactivated. If you believe this was a mistake, please contact the admin.",
        },
        "activated": {
            "icon": "🔓",
            "title": "Account Reactivated",
            "color": PRIMARY,
            "message": "Your ExpiryGuard account has been <strong>reactivated</strong>. You can now log in and use all features as before. Welcome back!",
        },
        "deleted": {
            "icon": "🗑️",
            "title": "Account Removed",
            "color": DANGER,
            "message": "Your ExpiryGuard account and all associated data have been <strong>permanently removed</strong> by an administrator. If you believe this was in error, please reach out to the team.",
        },
        "edited": {
            "icon": "✏️",
            "title": "Account Updated",
            "color": INFO,
            "message": "Your ExpiryGuard account details have been <strong>updated</strong> by an administrator. Please review your profile to ensure everything is correct.",
        },
    }

    c = config.get(change_type, config["edited"])
    detail_html = ""
    if details:
        detail_html = f"""
        <div style="background:{BG};border-left:4px solid {c['color']};padding:14px 18px;border-radius:0 8px 8px 0;margin:16px 0;">
            <p style="margin:0;font-size:13px;color:{TEXT_MAIN};"><strong>Details:</strong> {details}</p>
        </div>
        """

    cta = ""
    if change_type in ("activated", "edited"):
        cta = _button("Log In to Your Account →", f"{APP_URL}/login")

    content = f"""
    <div style="text-align:center;margin-bottom:20px;">
        <div style="display:inline-block;width:60px;height:60px;line-height:60px;font-size:30px;
                    background:{BG};border-radius:50%;border:2px solid {c['color']};">
            {c['icon']}
        </div>
    </div>

    <h2 style="margin:0 0 8px;font-size:20px;color:{TEXT_MAIN};text-align:center;">{c['title']}</h2>
    <p style="margin:0 0 20px;font-size:14px;color:{TEXT_MUTED};line-height:1.6;">
        Hello <strong>{username}</strong>,
    </p>
    <p style="margin:0 0 16px;font-size:14px;color:{TEXT_MAIN};line-height:1.7;">
        {c['message']}
    </p>

    {detail_html}
    {cta}
    """
    return _base_layout(content, f"{c['title']} — ExpiryGuard")


# ═══════════════════════════════════════════════════════════
#  TEMPLATE 4 — Welcome Email (New User)
# ═══════════════════════════════════════════════════════════
def render_welcome_email(username, role):
    """
    Welcome email sent after a new user is registered (or admin-created).

    Args:
        username (str): New user's display name.
        role (str): Assigned role (home/shop/admin).

    Returns:
        str: Complete HTML email.
    """
    role_features = {
        "home": "Track household items, manage needs, and receive smart expiry alerts.",
        "shop": "Manage shop inventory, set prices and promotions, and upload products in bulk.",
        "admin": "Manage users, approve requests, and monitor the entire platform.",
    }
    features_text = role_features.get(role, role_features["home"])

    content = f"""
    <div style="text-align:center;margin-bottom:20px;">
        <div style="display:inline-block;width:60px;height:60px;line-height:60px;font-size:30px;
                    background:{BG};border-radius:50%;border:2px solid {PRIMARY};">
            🎉
        </div>
    </div>

    <h2 style="margin:0 0 8px;font-size:22px;color:{TEXT_MAIN};text-align:center;">Welcome to ExpiryGuard!</h2>
    <p style="margin:0 0 20px;font-size:14px;color:{TEXT_MUTED};line-height:1.6;">
        Hello <strong>{username}</strong>,
    </p>
    <p style="margin:0 0 16px;font-size:14px;color:{TEXT_MAIN};line-height:1.7;">
        Your account has been created successfully. You've been assigned the
        <strong style="color:{PRIMARY};">{role.title()}</strong> role.
    </p>
    <p style="margin:0 0 20px;font-size:14px;color:{TEXT_MAIN};line-height:1.7;">
        {features_text}
    </p>

    <div style="background:{BG};border-radius:10px;padding:20px;margin:16px 0;">
        <p style="margin:0 0 10px;font-size:13px;font-weight:700;color:{TEXT_MAIN};">🚀 Quick Start</p>
        <ul style="margin:0;padding-left:20px;font-size:13px;color:{TEXT_MAIN};line-height:2;">
            <li>Log in to your dashboard</li>
            <li>Add your first items or upload in bulk</li>
            <li>Configure your alert preferences</li>
            <li>Check the leaderboard to see your ranking</li>
        </ul>
    </div>

    {_button("Get Started →", f"{APP_URL}/login")}
    """
    return _base_layout(content, f"Welcome to ExpiryGuard, {username}!")


# ═══════════════════════════════════════════════════════════
#  TEMPLATE 5 — Weekly Summary
# ═══════════════════════════════════════════════════════════
def render_weekly_summary(username, total_items, expired_count, expiring_soon,
                          waste_score, recommendation):
    """
    Weekly digest email with item stats and waste score.

    Args:
        username (str): Recipient's display name.
        total_items (int): Total tracked items.
        expired_count (int): Items past expiry.
        expiring_soon (int): Items expiring within 3 days.
        waste_score (float): User's current waste score (0–100).
        recommendation (str): A tip or recommendation message.

    Returns:
        str: Complete HTML email.
    """
    score_color = PRIMARY if waste_score < 30 else (ACCENT if waste_score < 60 else DANGER)

    content = f"""
    <h2 style="margin:0 0 8px;font-size:20px;color:{TEXT_MAIN};">📊 Your Weekly Summary</h2>
    <p style="margin:0 0 24px;font-size:14px;color:{TEXT_MUTED};line-height:1.6;">
        Hello <strong>{username}</strong>, here's how your inventory looks this week:
    </p>

    <!-- Stats Grid -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;">
    <tr>
        <td width="33%" style="padding:4px;">
            <div style="background:{BG};border-radius:10px;padding:18px 12px;text-align:center;">
                <p style="margin:0;font-size:24px;font-weight:800;color:{PRIMARY};">{total_items}</p>
                <p style="margin:4px 0 0;font-size:11px;color:{TEXT_MUTED};text-transform:uppercase;font-weight:600;">Total Items</p>
            </div>
        </td>
        <td width="33%" style="padding:4px;">
            <div style="background:{BG};border-radius:10px;padding:18px 12px;text-align:center;">
                <p style="margin:0;font-size:24px;font-weight:800;color:{DANGER};">{expired_count}</p>
                <p style="margin:4px 0 0;font-size:11px;color:{TEXT_MUTED};text-transform:uppercase;font-weight:600;">Expired</p>
            </div>
        </td>
        <td width="33%" style="padding:4px;">
            <div style="background:{BG};border-radius:10px;padding:18px 12px;text-align:center;">
                <p style="margin:0;font-size:24px;font-weight:800;color:{ACCENT};">{expiring_soon}</p>
                <p style="margin:4px 0 0;font-size:11px;color:{TEXT_MUTED};text-transform:uppercase;font-weight:600;">Expiring Soon</p>
            </div>
        </td>
    </tr>
    </table>

    <!-- Waste Score -->
    <div style="background:{BG};border-radius:10px;padding:20px;text-align:center;margin-bottom:20px;">
        <p style="margin:0 0 6px;font-size:12px;color:{TEXT_MUTED};text-transform:uppercase;font-weight:600;">Waste Score</p>
        <p style="margin:0;font-size:36px;font-weight:800;color:{score_color};">{waste_score}</p>
        <p style="margin:4px 0 0;font-size:12px;color:{TEXT_MUTED};">out of 100 (lower is better)</p>
    </div>

    <!-- Recommendation -->
    <div style="background:linear-gradient(135deg,{PRIMARY},{PRIMARY_DARK});border-radius:10px;padding:20px;margin-bottom:8px;">
        <p style="margin:0 0 6px;font-size:11px;color:rgba(255,255,255,0.7);text-transform:uppercase;font-weight:600;letter-spacing:0.5px;">💡 Recommendation</p>
        <p style="margin:0;font-size:14px;color:{WHITE};line-height:1.6;">{recommendation}</p>
    </div>

    {_button("View Full Dashboard →", f"{APP_URL}/dashboard")}
    """
    return _base_layout(content, f"Weekly Summary: {expired_count} expired, score {waste_score} — ExpiryGuard")
