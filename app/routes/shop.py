"""
ExpiryGuard — Shop Routes Blueprint
=====================================
Product management, stock tracking, pricing, and promotions.
Restricted to users with role='shop' or role='admin'.

Endpoints:
    /shop/dashboard    — Shop dashboard with inventory stats.
    /shop/products     — View all products for the current user.
    /shop/upload       — Upload products via CSV/Excel/JSON (GET/POST).
    /shop/delete/<id>  — Delete a product.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
import pandas as pd
import json
import logging

from ..models import ShopProduct
from ..extensions import db
from ..utils import role_required

logger = logging.getLogger(__name__)

shop_bp = Blueprint('shop', __name__, url_prefix='/shop')


# ─── DASHBOARD ───
@shop_bp.route('/dashboard')
@role_required('shop', 'admin')
def dashboard():
    products = ShopProduct.query.filter_by(user_id=current_user.id).all()
    total = len(products)
    low_stock = sum(1 for p in products if (p.stock or 0) < 10)
    active_promos = sum(1 for p in products if p.promotion)
    total_value = sum((p.price or 0) * (p.stock or 0) for p in products)

    return render_template('shop_dashboard.html',
                           total=total, low_stock=low_stock,
                           active_promos=active_promos,
                           total_value=round(total_value, 2))


# ─── ADD SINGLE PRODUCT ───
@shop_bp.route('/add', methods=['GET', 'POST'])
@role_required('shop', 'admin')
def add_product():
    categories = ['Food', 'Beverage', 'Medicine', 'Cosmetics', 'Household', 'Other']
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            category = request.form.get('category', 'Other')
            stock = int(request.form.get('stock', 0))
            price = float(request.form.get('price', 0.0))
            promotion = request.form.get('promotion')
            
            if not name:
                flash("Product name is required", "danger")
                return redirect(request.url)

            product = ShopProduct(
                name=name,
                category=category,
                stock=stock,
                price=price,
                promotion=promotion if promotion else None,
                user_id=current_user.id
            )
            db.session.add(product)
            db.session.commit()
            
            flash(f"Product '{name}' added successfully", "success")
            return redirect(url_for('shop.products'))
        except ValueError:
            flash("Stock and Price must be valid numbers", "danger")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding single product: {e}")
            flash("Failed to add product. Please try again.", "danger")
            
    return render_template('shop_add_product.html', categories=categories)


# ─── VIEW PRODUCTS ───
@shop_bp.route('/products')
@role_required('shop', 'admin')
def products():
    products = ShopProduct.query.filter_by(user_id=current_user.id).all()
    return render_template('shop_products.html', products=products)


# ─── UPLOAD ───
@shop_bp.route('/upload', methods=['GET', 'POST'])
@role_required('shop', 'admin')
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
            required = {'name', 'category', 'stock', 'price'}
            if not required.issubset(set(df.columns)):
                missing = required - set(df.columns)
                flash(f"Missing columns: {', '.join(missing)}", "danger")
                return redirect(request.url)

            count = 0
            for _, row in df.iterrows():
                product = ShopProduct(
                    name=row['name'],
                    category=row.get('category', 'Other'),
                    stock=int(row.get('stock', 0)),
                    price=float(row.get('price', 0)),
                    promotion=row.get('promotion', None) if 'promotion' in df.columns else None,
                    user_id=current_user.id
                )
                # Handle NaN promotion
                if pd.isna(product.promotion):
                    product.promotion = None
                db.session.add(product)
                count += 1

            db.session.commit()
            flash(f"Upload successful — {count} products added", "success")
            return redirect(url_for('shop.products'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Shop upload error: {e}")
            flash(f"Upload failed: {str(e)}", "danger")
            return redirect(request.url)

    return render_template('shop_upload.html')


# ─── DELETE PRODUCT ───
@shop_bp.route('/delete/<int:id>')
@role_required('shop', 'admin')
def delete_product(id):
    product = ShopProduct.query.get_or_404(id)
    if product.user_id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for('shop.products'))
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted", "danger")
    return redirect(url_for('shop.products'))
