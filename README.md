# 🛡️ ExpiryGuard

**ExpiryGuard** is an intelligent inventory and expiry management platform built with Flask.  
It uses **Machine Learning** to predict waste, recommend actions, and rank users on a sustainability leaderboard — helping households and shops reduce food waste effectively.

---

## ✨ Features

### Core Functionality
- **Item Tracking** — Add items individually or via bulk upload (CSV/Excel) with automatic expiry monitoring.
- **Smart Alerts** — Email notifications for expiring items with configurable thresholds (Critical / Warning / Safe).
- **ML-Powered Predictions** — Three trained models provide waste forecasting, personalised recommendations, and waste scoring.
- **Leaderboard** — Users are ranked by waste score (lower = better), encouraging sustainable habits.

### Role-Based Access
| Role | Capabilities |
|------|-------------|
| **Home** | Track household needs, manage personal inventory, request role switch |
| **Shop** | Manage shop products, stock, pricing, promotions, bulk upload |
| **Admin** | Full user management, approve/reject requests, audit logs, dashboard analytics |

### Admin Panel
- **Dashboard** — At-a-glance stats: total users, active/inactive, pending requests, items, products.
- **User Management** — Add, edit, deactivate, or permanently delete any user.
- **Role-Switch Approval** — Approve or reject home↔shop role-switch requests with email notifications.
- **Audit Logging** — Every admin action is recorded in an immutable log with timestamps.
- **Self-Protection** — Admins cannot deactivate or delete their own account.

### ML Models
| Model | Type | Purpose |
|-------|------|---------|
| Waste Forecast | Regression | Predicts waste quantity per item |
| Recommendation | Classifier | Suggests actions (Consume, Donate, etc.) |
| Waste Score | Regression | Computes a 0–100 sustainability score per user |

---

## 📂 Project Structure

ExpiryGuard/
├── app/                            # Main application package
│   ├── __init__.py                 # App factory & auto-migration
│   ├── routes.py                   # Centralized route registration
│   ├── models.py                   # SQLAlchemy models
│   ├── forms.py                    # Form definitions (currently skeleton)
│   ├── extensions.py               # Flask extensions (db, bcrypt, login_manager)
│   ├── utils.py                    # Shared helpers (role_required, expiry status)
│   ├── ml_models.py                # ML model loading & prediction functions
│   ├── email_utils.py              # Email sending via SMTP
│   ├── alert_utils.py              # Alert logic & batch processing
│   ├── scheduler.py                # APScheduler background tasks
│   │
│   ├── ml/                         # Trained ML model files (.pkl)
│   │   ├── waste_forecast_model.pkl
│   │   └── ...
│   │
│   ├── routes/                     # Blueprint route modules
│   │   ├── admin.py
│   │   ├── users.py
│   │   ├── items.py
│   │   ├── ml.py
│   │   ├── shop.py
│   │   └── home.py
│   │
│   ├── static/                     # Global styles & assets
│   └── templates/                  # Jinja2 HTML templates
│
├── tests/                          # Test suite
├── config.py                       # Configuration classes
├── run.py                          # Application entry point
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (secrets)
└── .gitignore

---

## 🚀 Installation

### Prerequisites
- **Python 3.10+**
- **MySQL** (or MariaDB)
- **pip** (Python package manager)

### Step-by-Step Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ExpiryGuard
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS / Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create the MySQL database**
   ```sql
   CREATE DATABASE expiryguard_db;
   ```

5. **Configure environment variables**  
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your_secret_key
   SQLALCHEMY_DATABASE_URI=mysql+pymysql://root:yourpassword@localhost/expiryguard_db

   # Email (optional — for alert notifications)
   EMAIL_ADDRESS=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   ```

6. **Run the application**
   ```bash
   python run.py
   ```
   The app will automatically create all required tables on first startup.

7. **Open in browser**
   ```
   http://127.0.0.1:5000
   ```

---

## 📖 Usage

### Registration & Login
1. Navigate to `/register` to create an account.
2. Select your role: **Home** or **Shop**.
3. Log in at `/login`.

### Adding Items
- **Single item:** Go to `/add_item` and fill in the form.
- **Bulk upload:** Go to `/bulk_upload` and upload a CSV/Excel file with columns: `name`, `category`, `purchase_date`, `expiry_date`, `quantity`.
- ML predictions (waste forecast & recommendation) run automatically after adding items.

### Viewing Alerts
- Visit `/alerts` to see items nearing expiry, grouped by urgency level.
- Configure alert preferences at `/preferences` (email toggle, threshold days).

### Leaderboard
- Visit `/ml/leaderboard` to see the sustainability ranking of all users.

### Role-Switch Request
- Go to your `/profile` and submit a role-switch request (Home → Shop or vice versa).
- An admin must approve the request before the role changes.

---

## 🔐 Admin Panel Features

Access the admin panel from the **Admin** dropdown in the navbar (visible only to admin users).

| Feature | Route | Description |
|---------|-------|-------------|
| Dashboard | `/admin/dashboard` | Stats overview, pending requests, recent uploads |
| Manage Users | `/admin/users` | Searchable user table with role/status badges |
| Add User | `/admin/users/add` | Create a new user with role assignment |
| Edit User | `/admin/users/<id>/edit` | Update username, email, role, or password |
| Toggle Active | `/admin/users/<id>/toggle-active` | Deactivate or reactivate accounts |
| Delete User | `/admin/users/<id>/delete` | Permanently remove a user and their data |
| Approve/Reject | `/admin/role-request/<id>/<action>` | Handle role-switch requests with email notification |
| Activity Logs | `/admin/logs` | View audit trail of all admin actions |

### Admin Action Logging
Every admin operation is recorded in the `admin_logs` table:
- `create_user`, `edit_user`, `delete_user`
- `activated_user`, `deactivated_user`
- `approve_role_switch`, `reject_role_switch`

---

## 🧪 Testing

### Prerequisites
```bash
pip install pytest
```

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Test Coverage

| Module | Tests | What's Covered |
|--------|-------|----------------|
| `test_models.py` | 10 | User CRUD, defaults, constraints, Item ML fields, all 6 models |
| `test_utils.py` | 8 | `calculate_days_left`, `get_expiry_status` edge cases |
| `test_routes.py` | 15 | Login/register, protected routes, item pages, role-switch |
| `test_admin.py` | 18 | Access control, user CRUD, self-protection, approval, audit log |
| **Total** | **51** | **All passing ✅** |

### Run a Specific Test File
```bash
python -m pytest tests/test_admin.py -v
```

### Run a Single Test
```bash
python -m pytest tests/test_admin.py::TestUserManagement::test_delete_user -v
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask, Flask-SQLAlchemy, Flask-Login, Flask-Bcrypt |
| Database | MySQL (PyMySQL driver) |
| ML | scikit-learn, joblib, pandas, numpy |
| Frontend | Bootstrap 5, DataTables.js, Font Awesome |
| Scheduler | APScheduler |
| Testing | pytest |

---

## 📄 License

This project is developed as a Final Year Project for academic purposes.
