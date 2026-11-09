# PhysioWay — Physiotherapy Practice Management System

A Flask + MySQL web application for managing patients, treatment sessions, payments, documents, expenses, and staff at a physiotherapy clinic — with automated WhatsApp appointment reminders.

---

## ✨ Features

- **Multi-role authentication** — Admin and Doctor roles with session-based login; doctors only see their own patients and expenses
- **Patient management** — Add, view, edit, and delete patients; searchable, paginated patient list
- **Session tracking** — Unlimited sessions per patient (first session + follow-ups), each with its own date/time and description
- **Patient documents** — Upload images and PDFs (PNG, JPG, GIF, WEBP, PDF; max 25 MB each) to a patient's file, view inline or download
- **Payment tracking** — Record and delete payments; paid fees are recalculated automatically
- **Expense management** — Add and bulk-delete clinic expenses, scoped per doctor
- **WhatsApp reminders** — Manual per-session reminders plus an automatic background job, sent through WhatsApp Web (Baileys)
- **Customizable reminders** — Admin can edit the reminder message template and how far ahead reminders are sent
- **Calendar view** — FullCalendar month view of all scheduled sessions
- **Analytics dashboard** — Monthly revenue, expense, and profit charts, per-patient breakdowns, and per-doctor stats (admin)
- **Doctor management** — Admin can create, delete, and reset passwords for staff accounts

---

## 📁 Project Structure

```
.
├── app.py                  # Flask routes, auth, DB migrations, scheduler, helpers
├── config.example.py       # Config template — copy to config.py (git-ignored)
├── sendwtsp.py             # Python wrapper that calls sender.js
├── sender.js               # Node.js WhatsApp sender (Baileys)
├── package.json            # Node dependencies for sender.js
├── patient.sql             # MySQL/MariaDB dump (schema + sample data)
├── requirements.txt        # Python dependencies
├── uploads/                # Uploaded patient documents (created automatically)
├── auth_info/              # WhatsApp session credentials (created on first QR login)
└── templates/
    ├── login.html          # Login page
    ├── index.html          # Patient list (search + pagination)
    ├── newpatient.html     # Add new patient
    ├── view_patient.html   # Read-only patient overview
    ├── patient.html        # Edit patient: sessions, documents, payments, reminders
    ├── calendar.html       # FullCalendar session view
    ├── analytics.html      # Revenue, expense & profit charts
    ├── expenses.html       # Expense listing
    ├── new_expense.html    # Add expense form
    ├── manage_doctors.html # Admin: doctor list & stats
    ├── add_doctor.html     # Admin: create doctor account
    └── settings.html       # Admin: reminder template & timing
```

---

## 🗄️ Database Schema

| Table | Key Columns |
|---|---|
| `doctors` | `id`, `username` (unique), `password_hash`, `full_name`, `role` (`admin` / `doctor`) |
| `patient` | `id`, `name`, `details`, `casetype`, `totalfees`, `paidfees`, `doctor_id` |
| `sessions` | `id`, `patient_id`, `session_datetime`, `description`, `is_first`, `sort_order` |
| `payments` | `id`, `patient_id`, `amount`, `payment_date` |
| `documents` | `id`, `patient_id`, `filename`, `stored_filename`, `mime_type`, `uploaded_at` |
| `expenses` | `id`, `description`, `amount`, `expense_date`, `doctor_id` |
| `reminders_sent` | `id`, `patient_id`, `session_datetime`, `sent_at` — unique on (`patient_id`, `session_datetime`) |
| `settings` | `key`, `value` — stores `reminder_template` and `reminder_delta_minutes` |

Deleting a patient cascades to their sessions, payments, documents, and reminder log. Deleting a doctor sets `doctor_id` to `NULL` on their patients and expenses.

On the first request, `app.py` runs lightweight migrations: it creates the `sessions`, `settings`, and `documents` tables if missing, migrates legacy `lastsession` / `nextsession` / `description` columns from `patient` into `sessions`, and creates a default admin account if none exists.

---

## 🧪 Setup Instructions

### Prerequisites

- Python 3.10+
- MySQL or MariaDB
- Node.js 18+ (for WhatsApp reminders)
- MySQL client development headers (needed to build `mysqlclient`), e.g. on Debian/Ubuntu:
  ```bash
  sudo apt install python3-dev default-libmysqlclient-dev build-essential pkg-config
  ```

### 1. Clone the repository

```bash
git clone <repo-url>
cd Patient-Management-System-with-Calendar-Flask-MySQL-
```

### 2. Install Python dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Install Node dependencies

```bash
npm install
```

### 4. Configure the application

Copy the example config and edit it (`config.py` is git-ignored so your credentials stay local):

```bash
cp config.example.py config.py
```

```python
MYSQL_HOST     = '127.0.0.1'
MYSQL_USER     = 'your_db_user'
MYSQL_PASSWORD = 'your_db_password'
MYSQL_DB       = 'patient'
SECRET_KEY     = 'a-long-random-string'
```

> ⚠️ Never commit real credentials. Generate a secret key with
> `python -c "import secrets; print(secrets.token_hex(32))"`.

### 5. Set up the database

Create the database and import the dump:

```bash
mysql -u root -p -e "CREATE DATABASE patient CHARACTER SET utf8mb4;"
mysql -u root -p patient < patient.sql
```

`patient.sql` includes sample rows; delete them if you want a clean start. Alternatively, create just the `doctors`, `patient`, `payments`, `expenses`, and `reminders_sent` tables yourself — the app creates the rest on first run.

If no admin account exists, one is created automatically:

```
Username: admin
Password: admin123
```

> ⚠️ Change the admin password immediately after first login (Doctors → Reset Password).

### 6. Link WhatsApp (one-time)

Reminders are sent from a regular WhatsApp account linked as a device. Run the sender once by hand and scan the QR code shown in the terminal (WhatsApp → Settings → Linked Devices → Link a device):

```bash
node sender.js 9617XXXXXXX "Test message"
```

Credentials are saved to `auth_info/`. If the session is logged out, delete that folder and repeat this step.

### 7. Run the application

```bash
python app.py
```

The app runs on `http://0.0.0.0:5001`.

---

## 👤 Roles & Permissions

| Feature | Doctor | Admin |
|---|---|---|
| View patients | Own only | All |
| Add / edit / delete patients | ✅ (own) | ✅ (all, can reassign doctor) |
| Upload / delete documents | ✅ (own patients) | ✅ |
| Manage payments | ✅ | ✅ |
| Manage expenses | ✅ (own) | ✅ (all) |
| Calendar | Own sessions | All sessions |
| Analytics | Own data | Full clinic + per-doctor stats |
| Manage doctors / reset passwords | ❌ | ✅ |
| Reminder settings | ❌ | ✅ |

---

## 📲 WhatsApp Reminders

Messages are sent through [Baileys](https://github.com/WhiskeySockets/Baileys), an unofficial WhatsApp Web client. `app.py` calls `send_whatsapp()` in `sendwtsp.py`, which runs `node sender.js <number> <message>` for each message.

- **Phone numbers** are read from the patient's `details` field and must be written with the `+961` prefix (Lebanese numbers, e.g. `+96170123456`).
- **Manual reminders** — use the 📱 *Send Reminder* button next to any session on the patient edit page.
- **Automatic reminders** — a background APScheduler job runs every 5 minutes and sends a reminder for any session starting within the configured window (default 120 minutes). Each session is reminded only once, tracked in `reminders_sent`.
- **Message template** — editable under **Settings** (admin). Supported placeholders: `{name}`, `{date}`, `{time}`.

> Because Baileys is unofficial, WhatsApp may occasionally change its protocol. If sending fails with a 405 error, see the comment in `sender.js` about pinning the WhatsApp Web version.

---

## 📦 Key Dependencies

**Python**
- [Flask](https://flask.palletsprojects.com/) — web framework
- [Flask-MySQLdb](https://flask-mysqldb.readthedocs.io/) / `mysqlclient` — MySQL access
- [Werkzeug](https://werkzeug.palletsprojects.com/) — password hashing, secure filenames
- [APScheduler](https://apscheduler.readthedocs.io/) — background reminder job

**Node.js**
- [@whiskeysockets/baileys](https://github.com/WhiskeySockets/Baileys) — WhatsApp Web messaging
- [qrcode-terminal](https://www.npmjs.com/package/qrcode-terminal) — QR code for device linking

**Front end (via CDN)**
- [Bootstrap 5](https://getbootstrap.com/) — UI
- [Chart.js](https://www.chartjs.org/) — analytics charts
- [FullCalendar](https://fullcalendar.io/) — calendar view
