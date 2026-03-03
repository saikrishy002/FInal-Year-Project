"""
ExpiryGuard — Item Routes Blueprint
=====================================
CRUD operations for tracked inventory items with ML prediction integration.

Endpoints:
    /add_item     — Add a single item (GET/POST) → triggers ML predictions.
    /items        — View all items for the current user with expiry status.
    /delete_item/<id> — Delete an item.
    /bulk_upload  — Upload items via CSV/Excel (GET/POST) → triggers ML predictions.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import pandas as pd
from datetime import datetime
import logging

from ..models import Item
from ..extensions import db
from ..utils import calculate_days_left, get_expiry_status

logger = logging.getLogger(__name__)

item_bp = Blueprint('item', __name__)

# predefined categories for dropdown
CATEGORIES = [
    'Food',
    'Beverage',
    'Medicine',
    'Cosmetics',
    'Household',
    'Other'
]

# ---------------- ADD ITEM ----------------
@item_bp.route('/add_item', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        item = Item(
            name=request.form['name'],
            category=request.form['category'],
            purchase_date=request.form['purchase_date'],
            expiry_date=request.form['expiry_date'],
            quantity=request.form['quantity'],
            user_id=current_user.id
        )
        db.session.add(item)
        db.session.commit()

        # Run ML predictions on the newly added item
        try:
            from ..routes.ml import run_predictions_on_items
            run_predictions_on_items([item])
        except Exception as e:
            logger.error(f"ML prediction error on add_item: {e}")

        flash("Item added successfully", "success")
        return redirect(url_for('item.view_items'))

    # pass categories list for the select field
    return render_template('add_item.html', categories=CATEGORIES)


# ---------------- VIEW ITEMS ----------------
@item_bp.route('/items')
@login_required
def view_items():
    items = Item.query.filter_by(user_id=current_user.id).all()
    item_data = []

    for item in items:
        days_left = calculate_days_left(item.expiry_date)
        status = get_expiry_status(days_left)
        item_data.append((item, days_left, status))

    return render_template('items.html', items=item_data)

    


# ---------------- DELETE ITEM ----------------
@item_bp.route('/delete_item/<int:id>')
@login_required
def delete_item(id):
    item = Item.query.get_or_404(id)

    if item.user_id != current_user.id:
        flash("Unauthorized action", "danger")
        return redirect(url_for('item.view_items'))

    db.session.delete(item)
    db.session.commit()
    flash("Item deleted", "danger")
    return redirect(url_for('item.view_items'))


# ---------------- CLEAR ALL ITEMS ----------------
@item_bp.route('/clear_inventory', methods=['POST'])
@login_required
def clear_inventory():
    try:
        Item.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        flash("All inventory items cleared successfully", "success")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error clearing inventory: {e}")
        flash("Failed to clear inventory", "danger")
    return redirect(url_for('item.view_items'))


# ---------------- BULK UPLOAD ----------------
@item_bp.route('/bulk_upload', methods=['GET', 'POST'])
@login_required
def bulk_upload():
    if request.method == 'POST':
        file = request.files['file']

        if not file:
            flash("No file selected", "danger")
            return redirect(request.url)

        # Read file
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith('.xlsx'):
            df = pd.read_excel(file)
        else:
            flash("Upload CSV or Excel only", "danger")
            return redirect(request.url)

        # Validate required columns
        required_cols = {'name', 'category', 'purchase_date', 'expiry_date', 'quantity'}
        if not required_cols.issubset(set(df.columns)):
            missing = required_cols - set(df.columns)
            flash(f"Missing columns: {', '.join(missing)}", "danger")
            return redirect(request.url)

        new_items = []
        skipped_count = 0
        for _, row in df.iterrows():
            name = str(row['name'])
            cat = str(row['category'])
            p_date = str(row['purchase_date'])
            e_date = str(row['expiry_date'])
            qty = row['quantity']

            # Duplicate check
            exists = Item.query.filter_by(
                user_id=current_user.id,
                name=name,
                category=cat,
                purchase_date=p_date,
                expiry_date=e_date
            ).first()

            if exists:
                skipped_count += 1
                continue

            item = Item(
                name=name,
                category=cat,
                purchase_date=p_date,
                expiry_date=e_date,
                quantity=qty,
                user_id=current_user.id
            )
            db.session.add(item)
            new_items.append(item)

        db.session.commit()

        # Run ML predictions on all uploaded items
        try:
            from ..routes.ml import run_predictions_on_items
            run_predictions_on_items(new_items)
            msg = f"Bulk upload successful — {len(new_items)} items added."
            if skipped_count > 0:
                msg += f" {skipped_count} duplicates skipped."
            flash(msg, "success")
        except Exception as e:
            logger.error(f"ML prediction error on bulk_upload: {e}")
            flash(f"Bulk upload successful — {len(new_items)} items (predictions skipped)", "warning")

        return redirect(url_for('item.view_items'))

    return render_template('bulk_upload.html')