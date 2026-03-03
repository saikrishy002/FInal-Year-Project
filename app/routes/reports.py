from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models import Item
from app.extensions import db
from datetime import datetime, timedelta
import sqlalchemy as sa

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/sustainability')
@login_required
def dashboard():
    """Render the Sustainability & Savings dashboard."""
    return render_template('sustainability.html')

@reports_bp.route('/api/impact-stats')
@login_required
def get_impact_stats():
    """Calculate and return sustainability metrics for the current user."""
    # 1. Financial Savings Estimate
    # (Simplified: Sum of (quantity * price) for items that didn't go to waste)
    # We'll use a dummy price of 50 if price is missing for calculations
    items = Item.query.filter_by(user_id=current_user.id).all()
    
    total_items = len(items)
    saved_count = 0
    wasted_count = 0
    estimated_savings = 0.0
    co2_reduction = 0.0 # kg of CO2
    
    for item in items:
        # If predicted waste is low (< 20%), consider it "saved"
        waste_amt = item.predicted_waste or 0
        qty = item.quantity or 1
        
        # Assume an average price of 100 per unit for savings calculation if not specified elsewhere
        # (In a real app, we'd use the product's actual price)
        price_per_unit = 100 
        
        if waste_amt / qty < 0.2:
            saved_count += 1
            estimated_savings += (qty - waste_amt) * 0.5 * price_per_unit # 50% of value reclaimed
        else:
            wasted_count += 1
            
        # CO2 Impact: ~2.5kg CO2 per kg of food waste prevented (avg)
        co2_reduction += (qty - waste_amt) * 0.25 # Assuming 0.25kg per unit
        
    # 2. Dynamic Efficiency Trend
    # Group items by month created and calculate average efficiency
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=180) # Last 6 months
    
    # Query to get average efficiency per month
    month_stats = db.session.query(
        sa.func.date_format(Item.created_at, '%Y-%m').label('month'),
        sa.func.avg(1 - (sa.func.coalesce(Item.predicted_waste, 0) / sa.func.nullif(Item.quantity, 0)))
    ).filter(
        Item.user_id == current_user.id,
        Item.created_at >= start_date
    ).group_by('month').order_by('month').all()
    
    trend_labels = []
    trend_efficiency = []
    
    for month_str, avg_eff in month_stats:
        # Convert YYYY-MM to MMM (e.g., 2024-03 -> Mar)
        dt = datetime.strptime(month_str, '%Y-%m')
        trend_labels.append(dt.strftime('%b'))
        # Convert decimal to percentage (e.g., 0.85 -> 85)
        trend_efficiency.append(round(float(avg_eff or 0) * 100, 1))

    # Fallback if no trend data yet
    if not trend_labels:
        trend_labels = ["No Data"]
        trend_efficiency = [0]
        
    trend_data = {
        "labels": trend_labels,
        "efficiency": trend_efficiency
    }
    
    return jsonify({
        "savings": round(estimated_savings, 2),
        "co2": round(co2_reduction, 2),
        "items_saved": saved_count,
        "items_wasted": wasted_count,
        "efficiency_score": round(100 - ((wasted_count / total_items * 100) if total_items > 0 else 0), 1),
        "trend": trend_data
    })
