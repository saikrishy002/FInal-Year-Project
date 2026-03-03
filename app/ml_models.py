"""
ML Model Loader & Feature Engineering for ExpiryGuard.
Loads all trained models once at import time and exposes prediction helpers.
"""

import os
import joblib
import numpy as np
import pandas as pd
from datetime import date, datetime

# --------------- paths ---------------
_ML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml")

_waste_forecast_path = os.path.join(_ML_DIR, "waste_forecast_model.pkl")
_recommendation_path = os.path.join(_ML_DIR, "recommendation_model.pkl")
_waste_score_path = os.path.join(_ML_DIR, "waste_score_model.pkl")
_category_encoder_path = os.path.join(_ML_DIR, "category_encoder_rec.pkl")
_label_encoder_path = os.path.join(_ML_DIR, "label_encoder_rec.pkl")

# --------------- load models ---------------
waste_forecast_model = joblib.load(_waste_forecast_path)
recommendation_model = joblib.load(_recommendation_path)
waste_score_model = joblib.load(_waste_score_path)
category_encoder = joblib.load(_category_encoder_path)
label_encoder = joblib.load(_label_encoder_path)


# --------------- feature engineering ---------------

def _to_date(val):
    """Convert various date representations to a Python date object."""
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                continue
    raise ValueError(f"Cannot parse date: {val}")


def compute_features(name, category, purchase_date, expiry_date, quantity):
    """
    Compute derived features for a single item.
    Returns dict with: days_left, shelf_life, life_used_ratio
    """
    purchase = _to_date(purchase_date)
    expiry = _to_date(expiry_date)
    today = date.today()

    shelf_life = max((expiry - purchase).days, 1)  # avoid div-by-zero
    days_left = (expiry - today).days
    life_used_ratio = round((shelf_life - days_left) / shelf_life, 4)

    return {
        "name": name,
        "category": category,
        "purchase_date": purchase,
        "expiry_date": expiry,
        "quantity": int(quantity),
        "days_left": days_left,
        "shelf_life": shelf_life,
        "life_used_ratio": life_used_ratio,
    }


# --------------- Model 1: Waste Forecasting ---------------

def predict_waste(items: list[dict]) -> list[float]:
    """
    Model 1 – Waste Forecasting & Inventory Optimization (Regression).
    Inputs expected per item: name, category, purchase_date, expiry_date, quantity
    Returns list of predicted_waste floats.
    """
    rows = []
    for it in items:
        f = compute_features(
            it["name"], it["category"],
            it["purchase_date"], it["expiry_date"],
            it["quantity"],
        )
        rows.append(f)

    df = pd.DataFrame(rows)
    
    # Use the same safe encoding as Model 2 for consistency
    def safe_encode_category(cat):
        try:
            return category_encoder.transform([cat])[0]
        except (ValueError, KeyError):
            return -1

    df["category_encoded"] = df["category"].apply(safe_encode_category)
    # Name encoding: if no encoder, use 0 or hash if model requires it, 
    # but based on feature_cols it expects numeric. 
    # For now, let's keep it consistent or use a simple hash if model was trained on it.
    df["name_encoded"] = df["name"].apply(lambda x: hash(x) % 1000)

    feature_cols = ["name_encoded", "category_encoded", "quantity", "shelf_life", "days_left"]
    X = df[feature_cols].values
    predictions = waste_forecast_model.predict(X)
    
    # Clip predictions to [0, quantity]
    clipped = []
    for i, p in enumerate(predictions):
        q = df.iloc[i]["quantity"]
        p_clipped = max(0.0, min(float(p), float(q)))
        clipped.append(round(p_clipped, 2))
        
    return clipped


# --------------- Model 2: Recommendation ---------------

def predict_recommendation(items: list[dict]) -> list[str]:
    """
    Model 2 – Personalized Recommendation Enhancer (Classifier).
    Inputs per item: category, shelf_life, days_left, quantity, life_used_ratio
    Returns list of recommendation strings.
    """
    rows = []
    for it in items:
        f = compute_features(
            it["name"], it["category"],
            it["purchase_date"], it["expiry_date"],
            it["quantity"],
        )
        rows.append(f)

    df = pd.DataFrame(rows)

    # Encode category using the saved encoder — handle unseen labels gracefully
    def safe_encode_category(cat):
        try:
            return category_encoder.transform([cat])[0]
        except (ValueError, KeyError):
            return -1  # unseen category

    df["category_encoded"] = df["category"].apply(safe_encode_category)

    feature_cols = ["category_encoded", "shelf_life", "days_left", "quantity", "life_used_ratio"]
    X = df[feature_cols].values
    pred_encoded = recommendation_model.predict(X)

    # Decode predictions back to labels
    recommendations = label_encoder.inverse_transform(pred_encoded.astype(int))
    return [str(r) for r in recommendations]


# --------------- Model 3: Waste Score ---------------

def predict_waste_score(total_quantity: float, total_waste: float, waste_ratio: float) -> float:
    """
    Model 3 – Waste Score Predictor (Leaderboard).
    Inputs: total_quantity, total_waste, waste_ratio
    Returns waste_score (0–100).
    """
    X = np.array([[total_quantity, total_waste, waste_ratio]])
    score = waste_score_model.predict(X)
    return round(float(np.clip(score[0], 0, 100)), 2)
