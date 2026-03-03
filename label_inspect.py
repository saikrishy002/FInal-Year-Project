import sys
import os
import joblib
# Absolute path to the app directory
base_dir = r"c:\Users\ManuM\Downloads\Final Year Project\ExpiryGuard"
sys.path.append(base_dir)
from app import create_app
from app.models import Item
from datetime import date

app = create_app()
with app.app_context():
    print("--- Sorting items by expiry ---")
    items = Item.query.order_by(Item.expiry_date).all()
    today = date.today()
    for it in items[:10]:
        days_left = (it.expiry_date - today).days if it.expiry_date else 'N/A'
        print(f"Name: {it.name}, Days Left: {days_left}, Rec: {it.recommendation}")
    
    print("\n--- Listing Labels ---")
    _ML_DIR = os.path.join(base_dir, "app", "ml")
    _label_encoder_path = os.path.join(_ML_DIR, "label_encoder_rec.pkl")
    le = joblib.load(_label_encoder_path)
    print(f"Classes: {le.classes_.tolist()}")
