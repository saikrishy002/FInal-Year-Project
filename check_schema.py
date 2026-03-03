import sys
import os
# Absolute path to the app directory
base_dir = r"c:\Users\ManuM\Downloads\Final Year Project\ExpiryGuard"
sys.path.append(base_dir)
from app import create_app
from sqlalchemy import inspect, text
from app.extensions import db

app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    print("--- Table Columns: role_switch_requests ---")
    columns = inspector.get_columns('role_switch_requests')
    for col in columns:
        print(f"Col: {col['name']}, Type: {col['type']}")
    
    print("\n--- Table Columns: users ---")
    columns = inspector.get_columns('users')
    for col in columns:
        print(f"Col: {col['name']}, Type: {col['type']}")
