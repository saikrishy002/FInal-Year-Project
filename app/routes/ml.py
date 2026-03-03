"""
Blueprint for ML prediction endpoints and leaderboard.
"""

from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
import logging

from ..extensions import db
from ..models import User, Item
from ..ml_models import predict_waste, predict_recommendation, predict_waste_score, compute_features

logger = logging.getLogger(__name__)

ml_bp = Blueprint("ml", __name__, url_prefix="/ml")


# ──────────────────────────────────────────────
# API: /ml/predict-waste  (Model 1)
# ──────────────────────────────────────────────
@ml_bp.route("/predict-waste", methods=["POST"])
@login_required
def api_predict_waste():
    """Accept JSON array of items, return predicted waste per item."""
    try:
        data = request.get_json(force=True)
        if not isinstance(data, list):
            data = [data]
        predictions = predict_waste(data)
        return jsonify({"predictions": predictions}), 200
    except Exception as e:
        logger.error(f"predict-waste error: {e}")
        return jsonify({"error": str(e)}), 400


# ──────────────────────────────────────────────
# API: /ml/recommend  (Model 2)
# ──────────────────────────────────────────────
@ml_bp.route("/recommend", methods=["POST"])
@login_required
def api_recommend():
    """Accept JSON array of items, return recommendation per item."""
    try:
        data = request.get_json(force=True)
        if not isinstance(data, list):
            data = [data]
        recommendations = predict_recommendation(data)
        return jsonify({"recommendations": recommendations}), 200
    except Exception as e:
        logger.error(f"recommend error: {e}")
        return jsonify({"error": str(e)}), 400


# ──────────────────────────────────────────────
# API: /ml/waste-score  (Model 3)
# ──────────────────────────────────────────────
@ml_bp.route("/waste-score", methods=["POST"])
@login_required
def api_waste_score():
    """Accept JSON with total_quantity, total_waste, waste_ratio → waste_score."""
    try:
        data = request.get_json(force=True)
        efficiency = predict_waste_score(
            float(data["total_quantity"]),
            float(data["total_waste"]),
            float(data["waste_ratio"]),
        )
        score = round(100.0 - efficiency, 2)
        return jsonify({"waste_score": score}), 200
    except Exception as e:
        logger.error(f"waste-score error: {e}")
        return jsonify({"error": str(e)}), 400


# ──────────────────────────────────────────────
# PAGE: /ml/leaderboard  (uses Model 3)
# ──────────────────────────────────────────────
@ml_bp.route("/leaderboard")
@login_required
def leaderboard():
    """Compute waste score for every user and render a leaderboard sorted ascending."""
    users = User.query.all()
    board = []

    for user in users:
        items = Item.query.filter_by(user_id=user.id).all()
        if not items:
            continue

        total_quantity = sum(it.quantity or 0 for it in items)
        total_waste = sum(it.predicted_waste or 0 for it in items)

        if total_quantity == 0:
            waste_ratio = 0.0
        else:
            waste_ratio = round(total_waste / total_quantity, 4)

        try:
            # The model returns an Efficiency Score (High = Good Efficiency/Low Waste)
            # We invert it (100 - score) to convert it to a "Waste Score" (Low = Good/Small Waste)
            # as per the UI design and sorting expectations.
            efficiency = predict_waste_score(total_quantity, total_waste, waste_ratio)
            score = round(100.0 - efficiency, 2)
        except Exception:
            score = 100.0

        board.append({
            "username": user.username,
            "total_quantity": total_quantity,
            "total_waste": round(total_waste, 2),
            "waste_ratio": round(waste_ratio * 100, 2),
            "waste_score": score,
        })

    # Sort primary by waste score (efficiency)
    # Secondary sort by total waste (absolute) to favor users with lower real-world waste
    board.sort(key=lambda x: (x["waste_score"], x["total_waste"]))

    return render_template("leaderboard.html", board=board)


# ──────────────────────────────────────────────
# HELPER: run predictions on a list of Item ORM objects
# ──────────────────────────────────────────────
def run_predictions_on_items(items):
    """Run Model 1 & 2 on a list of Item ORM objects and persist results."""
    if not items:
        return

    payload = []
    for it in items:
        payload.append({
            "name": it.name,
            "category": it.category or "Other",
            "purchase_date": str(it.purchase_date),
            "expiry_date": str(it.expiry_date),
            "quantity": it.quantity or 1,
        })

    try:
        wastes = predict_waste(payload)
        recs = predict_recommendation(payload)
        for i, it in enumerate(items):
            # Final safety clip
            it.predicted_waste = max(0.0, min(float(wastes[i]), float(it.quantity or 1)))
            
            # Expiry Safety Override
            from datetime import date
            today = date.today()
            if it.expiry_date < today:
                it.recommendation = "Dispose"
            else:
                it.recommendation = recs[i]
            
            # Behavioral Advice Logic
            qty = it.quantity if it.quantity and it.quantity > 0 else 1
            waste_ratio = min(it.predicted_waste / qty, 1.0)
            
            days_left = (it.expiry_date - it.purchase_date).days
            
            if waste_ratio > 0.7:
                it.buying_advice = "High waste alert: Reduce quantity by 50% next time."
            elif waste_ratio > 0.4:
                it.buying_advice = "Reduce quantity by 25% for better efficiency."
            elif waste_ratio > 0.2 and days_left < 7:
                it.buying_advice = "Short shelf life: Buy in smaller, frequent batches."
            else:
                it.buying_advice = "Quantity looks optimal for this usage pattern."
                
        db.session.commit()
    except Exception as e:
        logger.error(f"run_predictions_on_items error: {e}")
        db.session.rollback()


# ──────────────────────────────────────────────
# ROUTE: /ml/refresh-all
# ──────────────────────────────────────────────
@ml_bp.route("/refresh-all")
@login_required
def refresh_all_predictions():
    """Trigger ML predictions for all items belonging to the current user."""
    items = Item.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash("No items found to refresh.", "info")
        return redirect(url_for('item.view_items'))

    try:
        run_predictions_on_items(items)
        flash(f"Successfully refreshed predictions for {len(items)} items.", "success")
    except Exception as e:
        logger.error(f"Manual refresh error: {e}")
        flash("Failed to refresh predictions. Check server logs.", "danger")

    return redirect(url_for('item.view_items'))

