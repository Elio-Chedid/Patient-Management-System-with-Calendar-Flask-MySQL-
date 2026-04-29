# PhysioWay — Physiotherapy Practice Management System

A Flask-based web application for managing patients, appointments, payments, expenses, and staff at a physiotherapy clinic.

---

## ✨ Features

- **Multi-role authentication** — Admin and Doctor roles with session-based login
- **Patient management** — Add, edit, and delete patient records with case details, session history, and fees
- **Appointment scheduling** — Track first and follow-up sessions per patient
- **Payment tracking** — Log, view, and delete individual payments; paid fees auto-recalculated
- **Expense management** — Add and delete clinic expenses, filterable by doctor
- **WhatsApp reminders** — Manual (and optional automated) appointment reminders via Twilio
- **Analytics dashboard** — Monthly revenue, expenses, and profit charts; per-doctor breakdowns (admin only)
- **Calendar view** — FullCalendar-powered visual schedule of all patient sessions
- **Doctor management** — Admin can create, delete, and reset passwords for doctor accounts

---

## 📁 Project Structure

```
.
├── app.py                  # Flask routes, auth, DB helpers, Twilio integration
├── config.py               # App config (DB credentials, secret key, etc.)
├── templates/
│   ├── index.html          # Main patient listing
│   ├── patient.html        # Edit patient / payments / reminders
│   ├── newpatient.html     # Add new patient
│   ├── calendar.html       # FullCalendar session view
│   ├── analytics.html      # Revenue, expense & profit charts
│   ├── expenses.html       # Expense listing
│   ├── new_expense.html    # Add expense form
│   ├── manage_doctors.html # Admin: doctor list & stats
│   ├── add_doctor.html     # Admin: create doctor account
│   └── login.html          # Login page
├── static/
│   ├── css/                # Custom styles
│   └── js/                 # Custom JavaScript
├── requirements.txt        # Python dependencies
└── README.md
```

---

## 🗄️ Database Schema

The app expects a MySQL database with the following tables:

| Table | Key Columns |
|---|---|
| `doctors` | `id`, `username`, `password_hash`, `full_name`, `role` |
| `patient` | `id`, `name`, `details`, `casetype`, `description`, `lastsession`, `nextsession`, `totalfees`, `paidfees`, `doctor_id` |
| `payments` | `id`, `patient_id`, `amount`, `payment_date` |
| `expenses` | `id`, `description`, `amount`, `expense_date`, `doctor_id` |
| `reminders_sent` | `id`, `patient_id`, `session_datetime`, `sent_at` |

---

## 🧪 Setup Instructions

### 1. Clone the repository

```bash
git clone <repo-url>
cd physioway
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure the application

Edit `config.py` with your database credentials and secret key:

```python
MYSQL_HOST     = 'localhost'
MYSQL_USER     = 'your_db_user'
MYSQL_PASSWORD = 'your_db_password'
MYSQL_DB       = 'physioway'
SECRET_KEY     = 'your_secret_key'
```

### 4. Set up Twilio (for WhatsApp reminders)

In `app.py`, replace the placeholder credentials:

```python
sid   = "YOUR_TWILIO_ACCOUNT_SID"
token = "YOUR_TWILIO_AUTH_TOKEN"
```

Ensure your Twilio sandbox number is configured for WhatsApp (`whatsapp:+14155238886` or your own).

### 5. Set up the MySQL database

Create the database and tables matching the schema above, then run the app — it will auto-create a default admin account on first launch:

```
Username: admin
Password: admin123
```

> ⚠️ Change the admin password immediately after first login.

### 6. Run the application

```bash
python app.py
```

The app runs on `http://0.0.0.0:5001` by default.

---

## 👤 Roles & Permissions

| Feature | Doctor | Admin |
|---|---|---|
| View own patients | ✅ | ✅ (all) |
| Add / edit patients | ✅ | ✅ |
| Delete patients | ✅ (own) | ✅ (all) |
| Manage payments | ✅ | ✅ |
| Manage expenses | ✅ (own) | ✅ (all) |
| Analytics | Own data | Full clinic |
| Manage doctors | ❌ | ✅ |
| Reset passwords | ❌ | ✅ |

---

## 📲 WhatsApp Reminders

Patient phone numbers are extracted from the `details` field using the `+961` prefix (Lebanese numbers). The `sendwtsp()` function sends a formatted reminder via the Twilio WhatsApp sandbox.

**Manual reminders** can be triggered from the patient edit page for any scheduled session.

**Automated reminders** (sends 2 hours before a session) are implemented but currently commented out. To enable, uncomment the scheduler block in `app.py` and ensure the `reminders_sent` table exists to prevent duplicate sends.

---

## 📦 Key Dependencies

- [Flask](https://flask.palletsprojects.com/)
- [Flask-MySQLdb](https://flask-mysqldb.readthedocs.io/)
- [Werkzeug](https://werkzeug.palletsprojects.com/) — password hashing
- [APScheduler](https://apscheduler.readthedocs.io/) — background reminder scheduling
- [Twilio](https://www.twilio.com/docs) — WhatsApp messaging
- [FullCalendar](https://fullcalendar.io/) — calendar view (via CDN in template)
