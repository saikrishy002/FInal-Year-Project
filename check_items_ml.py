import sys
import os
# Absolute path to the app directory
base_dir = r"c:\Users\ManuM\Downloads\Final Year Project\ExpiryGuard"
sys.path.append(base_dir)
from app import create_app
from app.models import Item
from app.extensions import db

app = create_app()
with app.app_context():
    print("--- Item Predictions ---")
    items = Item.query.all()
    if not items:
        print("No items found.")
    for it in items:
        print(f"ID: {it.id}, Name: {it.name}, Waste: {it.predicted_waste}, Rec: {it.recommendation}")
