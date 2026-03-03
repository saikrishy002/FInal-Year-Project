"""
ExpiryGuard — Home Routes Blueprint
=====================================
Household needs tracking, item requests, and fulfilment management.
Restricted to users with role='home' or role='admin'.

Endpoints:
    /home/dashboard     — Home dashboard with inventory and needs stats.
    /home/needs         — View all household needs for the current user.
    /home/upload        — Upload needs via CSV/Excel/JSON (GET/POST).
    /home/toggle/<id>   — Toggle need status between pending/fulfilled.
    /home/delete/<id>   — Delete a household need.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
import pandas as pd
import json
import logging

from ..models import HomeNeed, Item, ShopProduct
from ..extensions import db
from ..utils import role_required, calculate_days_left, get_expiry_status

logger = logging.getLogger(__name__)

home_bp = Blueprint('home', __name__, url_prefix='/home')


# ─── DASHBOARD ───
@home_bp.route('/dashboard')
@role_required('home', 'admin')
def dashboard():
    needs = HomeNeed.query.filter_by(user_id=current_user.id).all()
    items = Item.query.filter_by(user_id=current_user.id).all()

    total_needs = len(needs)
    pending = sum(1 for n in needs if n.status == 'pending')
    fulfilled = sum(1 for n in needs if n.status == 'fulfilled')

    # Inventory stats and Smart Insights
    expired = expiring_soon = safe_count = 0
    category_waste = {} # category -> [total_waste, count]

    for item in items:
        days_left = calculate_days_left(item.expiry_date)
        status = get_expiry_status(days_left)
        if status == "Expired":
            expired += 1
        elif status in ("Expiring Soon", "Near Expiry"):
            expiring_soon += 1
        else:
            safe_count += 1
            
        # Group waste by category
        if item.category:
            waste = item.predicted_waste or 0.0
            qty = item.quantity if item.quantity and item.quantity > 0 else 1
            if item.category not in category_waste:
                category_waste[item.category] = [0.0, 0] # [total_waste, total_qty]
            category_waste[item.category][0] += waste
            category_waste[item.category][1] += qty

    # Format insights
    smart_insights = []
    for cat, (total_w, total_q) in category_waste.items():
        avg_waste = total_w / total_q if total_q > 0 else 0
        if avg_waste > 0.3:
            advice = ""
            if avg_waste > 0.6:
                advice = f"🚨 High waste in {cat}: Buy 50% less."
            else:
                advice = f"💡 Efficiency tip for {cat}: Buy 25% less."
            smart_insights.append({"category": cat, "advice": advice, "impact": round(avg_waste * 100)})

    # Sort insights by impact
    smart_insights.sort(key=lambda x: x["impact"], reverse=True)

    # ─── SMART MATCH: Needs vs Shop Promotions ───
    pending_needs = [n.name.lower() for n in needs if n.status == 'pending']
    local_deals = []
    
    if pending_needs:
        # Find all shop products with active promotions
        promoted_products = ShopProduct.query.filter(ShopProduct.promotion.isnot(None)).all()
        
        for prod in promoted_products:
            # Simple keyword matching
            if any(need_name in prod.name.lower() or prod.name.lower() in need_name for need_name in pending_needs):
                local_deals.append({
                    "shop_name": prod.user.username,
                    "product_name": prod.name,
                    "price": prod.price,
                    "promotion": prod.promotion,
                    "category": prod.category
                })

    return render_template('home_dashboard.html',
                           total_needs=total_needs, pending=pending,
                           fulfilled=fulfilled, total_items=len(items),
                           expired=expired, expiring_soon=expiring_soon,
                           safe_count=safe_count,
                           smart_insights=smart_insights[:3],
                           local_deals=local_deals)


# ─── ADD SINGLE NEED ───
@home_bp.route('/add', methods=['GET', 'POST'])
@role_required('home', 'admin')
def add_need():
    categories = ['Food', 'Beverage', 'Medicine', 'Cosmetics', 'Household', 'Other']
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            category = request.form.get('category', 'Other')
            priority = request.form.get('priority', 'medium')
            
            if not name:
                flash("Product name is required", "danger")
                return redirect(request.url)

            need = HomeNeed(
                name=name,
                category=category,
                priority=priority,
                status='pending',
                user_id=current_user.id
            )
            db.session.add(need)
            db.session.commit()
            
            flash(f"'{name}' added to your needs list", "success")
            return redirect(url_for('home.needs'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding single need: {e}")
            flash("Failed to add need. Please try again.", "danger")
            
    return render_template('home_add_need.html', categories=categories)


# ─── VIEW NEEDS ───
@home_bp.route('/needs')
@role_required('home', 'admin')
def needs():
    needs = HomeNeed.query.filter_by(user_id=current_user.id).all()
    return render_template('home_needs.html', needs=needs)


# ─── UPLOAD ───
@home_bp.route('/upload', methods=['GET', 'POST'])
@role_required('home', 'admin')
def upload():
    if request.method == 'POST':
        file = request.files.get('file')

        if not file or not file.filename:
            flash("No file selected", "danger")
            return redirect(request.url)

        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.filename.endswith('.xlsx'):
                df = pd.read_excel(file)
            elif file.filename.endswith('.json'):
                data = json.load(file)
                df = pd.DataFrame(data)
            else:
                flash("Upload CSV, Excel, or JSON only", "danger")
                return redirect(request.url)

            # Validate columns
            required = {'name', 'category'}
            if not required.issubset(set(df.columns)):
                missing = required - set(df.columns)
                flash(f"Missing columns: {', '.join(missing)}", "danger")
                return redirect(request.url)

            count = 0
            for _, row in df.iterrows():
                need = HomeNeed(
                    name=row['name'],
                    category=row.get('category', 'Other'),
                    priority=row.get('priority', 'medium') if 'priority' in df.columns else 'medium',
                    status=row.get('status', 'pending') if 'status' in df.columns else 'pending',
                    user_id=current_user.id
                )
                # Handle NaN values
                if pd.isna(need.priority):
                    need.priority = 'medium'
                if pd.isna(need.status):
                    need.status = 'pending'
                db.session.add(need)
                count += 1

            db.session.commit()
            flash(f"Upload successful — {count} needs added", "success")
            return redirect(url_for('home.needs'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Home upload error: {e}")
            flash(f"Upload failed: {str(e)}", "danger")
            return redirect(request.url)

    return render_template('home_upload.html')


# ─── TOGGLE STATUS ───
@home_bp.route('/toggle/<int:id>')
@role_required('home', 'admin')
def toggle_status(id):
    need = HomeNeed.query.get_or_404(id)
    if need.user_id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for('home.needs'))
    need.status = 'fulfilled' if need.status == 'pending' else 'pending'
    db.session.commit()
    flash(f"Status updated to {need.status}", "success")
    return redirect(url_for('home.needs'))


# ─── DELETE NEED ───
@home_bp.route('/delete/<int:id>')
@role_required('home', 'admin')
def delete_need(id):
    need = HomeNeed.query.get_or_404(id)
    if need.user_id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for('home.needs'))
    db.session.delete(need)
    db.session.commit()
    flash("Need deleted", "danger")
    return redirect(url_for('home.needs'))
