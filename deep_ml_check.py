import sys
import os
import joblib
# Absolute path to the app directory
base_dir = r"c:\Users\ManuM\Downloads\Final Year Project\ExpiryGuard"
sys.path.append(base_dir)
from app import create_app
from app.models import Item
from app.extensions import db
from datetime import date

app = create_app()
with app.app_context():
    print("--- Item Analysis ---")
    items = Item.query.all()
    today = date.today()
    for it in items:
        days_left = (it.expiry_date - today).days if it.expiry_date else 'N/A'
        print(f"ID: {it.id}, Name: {it.name}, Days Left: {days_left}, Rec: {it.recommendation}")
    
    print("\n--- Model Analysis ---")
    _ML_DIR = os.path.join(base_dir, "app", "ml")
    _label_encoder_path = os.path.join(_ML_DIR, "label_encoder_rec.pkl")
    if os.path.exists(_label_encoder_path):
        le = joblib.load(_label_encoder_path)
        print(f"Classes in Label Encoder: {le.classes_}")
    else:
        print("Label encoder not found.")
