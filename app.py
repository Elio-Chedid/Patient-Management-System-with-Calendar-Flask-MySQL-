from flask import (Flask, render_template, request,
                   redirect, url_for, session, flash,
                   send_from_directory, abort)
from flask_mysqldb import MySQL
from datetime import date, datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from apscheduler.schedulers.background import BackgroundScheduler
from math import ceil
import atexit
import uuid
import config
from sendwtsp import send_whatsapp
import os

app = Flask(__name__)
app.config.from_object(config)
app.secret_key = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25 MB per upload

mysql = MySQL(app)

PER_PAGE = 10

HERE = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(HERE, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.pdf'}

DEFAULT_REMINDER_TEMPLATE = (
    "Hello {name},\n"
    "This is a friendly reminder from PhysioWay that you have an "
    "appointment scheduled on {date} at {time}.\n"
    "If you need to reschedule or have any questions, please contact us.\n"
    "We look forward to seeing you and supporting your recovery.\n"
    "Kind regards,\nPhysioWay Team"
)


# ══════════════════════════════════════════════════════════
#  AUTH HELPERS
# ══════════════════════════════════════════════════════════
def is_admin():
    return session.get('role') == 'admin'


def current_doctor_id():
    return session.get('doctor_id')


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_admin():
            flash('Admin access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════
#  DB INIT / MIGRATIONS
# ══════════════════════════════════════════════════════════
_initialized = False


def run_migrations():
    cur = mysql.connection.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT NOT NULL,
            session_datetime VARCHAR(50) NOT NULL DEFAULT '',
            description TEXT,
            is_first TINYINT(1) NOT NULL DEFAULT 0,
            sort_order INT NOT NULL DEFAULT 0,
            INDEX idx_patient (patient_id),
            CONSTRAINT fk_sessions_patient FOREIGN KEY (patient_id)
              REFERENCES patient(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            `key` VARCHAR(64) PRIMARY KEY,
            `value` TEXT NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            stored_filename VARCHAR(255) NOT NULL,
            mime_type VARCHAR(100) NOT NULL,
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_doc_patient (patient_id),
            CONSTRAINT fk_doc_patient FOREIGN KEY (patient_id)
              REFERENCES patient(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    cur.execute("INSERT IGNORE INTO settings (`key`,`value`) VALUES (%s,%s)",
                ('reminder_template', DEFAULT_REMINDER_TEMPLATE))
    cur.execute("INSERT IGNORE INTO settings (`key`,`value`) VALUES (%s,%s)",
                ('reminder_delta_minutes', '120'))

    cur.execute("""
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='patient'
          AND COLUMN_NAME='lastsession'
    """)
    has_old_cols = cur.fetchone()[0] > 0

    if has_old_cols:
        cur.execute("SELECT COUNT(*) FROM sessions")
        sessions_populated = cur.fetchone()[0] > 0

        if not sessions_populated:
            cur.execute("SELECT id, description, lastsession, nextsession "
                        "FROM patient")
            for pid, desc, lastsess, nextsess in cur.fetchall():
                ls = (lastsess or '').strip()
                d = desc or ''
                if ls or d.strip():
                    cur.execute(
                        "INSERT INTO sessions "
                        "(patient_id,session_datetime,description,is_first,sort_order) "
                        "VALUES (%s,%s,%s,1,0)",
                        (pid, ls, d))
                if nextsess:
                    for idx, dt in enumerate(
                            [s.strip() for s in nextsess.split(',') if s.strip()],
                            start=1):
                        cur.execute(
                            "INSERT INTO sessions "
                            "(patient_id,session_datetime,description,is_first,sort_order) "
                            "VALUES (%s,%s,'',0,%s)",
                            (pid, dt, idx))
            mysql.connection.commit()
            print("✓ Copied legacy session data into sessions table")

        for col in ('description', 'lastsession', 'nextsession'):
            try:
                cur.execute(f"ALTER TABLE patient DROP COLUMN {col}")
            except Exception as e:
                print(f"Drop {col}: {e}")
        print("✓ Dropped legacy patient columns")

    cur.execute("SELECT COUNT(*) FROM doctors WHERE role='admin'")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO doctors (username,password_hash,full_name,role) "
            "VALUES (%s,%s,%s,%s)",
            ('admin', generate_password_hash('admin123'),
             'Administrator', 'admin'))
        print("✓ Default admin created — admin / admin123")

    mysql.connection.commit()
    cur.close()


@app.before_request
def before_request_hook():
    global _initialized
    if not _initialized:
        try:
            run_migrations()
        except Exception as e:
            print(f"Init error: {e}")
        _initialized = True

    if request.endpoint in ('login', 'static', None):
        return
    if 'doctor_id' not in session:
        return redirect(url_for('login'))


# ══════════════════════════════════════════════════════════
#  SETTINGS HELPERS
# ══════════════════════════════════════════════════════════
def get_setting(key, default=''):
    cur = mysql.connection.cursor()
    cur.execute("SELECT `value` FROM settings WHERE `key`=%s", (key,))
    row = cur.fetchone()
    cur.close()
    return row[0] if row else default


def set_setting(key, value):
    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO settings (`key`,`value`) VALUES (%s,%s) "
        "ON DUPLICATE KEY UPDATE `value`=VALUES(`value`)",
        (key, value))
    mysql.connection.commit()
    cur.close()


# ══════════════════════════════════════════════════════════
#  PATIENT / SESSION HELPERS
# ══════════════════════════════════════════════════════════
def get_sessions(patient_id):
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id, session_datetime, description, is_first, sort_order "
        "FROM sessions WHERE patient_id=%s "
        "ORDER BY is_first DESC, sort_order ASC, id ASC", (patient_id,))
    rows = cur.fetchall()
    cur.close()
    return rows


def sync_sessions(patient_id, datetimes, descriptions):
    """Replace all sessions for a patient. Index 0 = first session."""
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM sessions WHERE patient_id=%s", (patient_id,))
    for idx, (dt, desc) in enumerate(zip(datetimes, descriptions)):
        dt = (dt or '').strip()
        desc = desc or ''
        if not dt and not desc.strip():
            continue
        is_first = 1 if idx == 0 else 0
        cur.execute(
            "INSERT INTO sessions "
            "(patient_id,session_datetime,description,is_first,sort_order) "
            "VALUES (%s,%s,%s,%s,%s)",
            (patient_id, dt, desc, is_first, idx))
    mysql.connection.commit()
    cur.close()


def recalc_paid(patient_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT COALESCE(SUM(amount),0) FROM payments "
                "WHERE patient_id=%s", (patient_id,))
    total = cur.fetchone()[0]
    cur.execute("UPDATE patient SET paidfees=%s WHERE id=%s",
                (total, patient_id))
    mysql.connection.commit()
    cur.close()


# ══════════════════════════════════════════════════════════
#  DOCUMENT HELPERS
# ══════════════════════════════════════════════════════════
def get_documents(patient_id):
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id, filename, stored_filename, mime_type, uploaded_at "
        "FROM documents WHERE patient_id=%s ORDER BY uploaded_at DESC",
        (patient_id,))
    rows = cur.fetchall()
    cur.close()
    return rows


def save_uploaded_documents(patient_id, files):
    """Persist a list of uploaded FileStorage objects under a patient.
    Skips empty inputs and unsupported extensions."""
    saved = 0
    for f in files:
        if not f or not f.filename:
            continue
        original = secure_filename(f.filename) or 'file'
        ext = os.path.splitext(original)[1].lower()
        if ext not in ALLOWED_EXT:
            flash(f'"{original}" was skipped (only images and PDFs allowed).',
                  'warning')
            continue
        stored = f"{uuid.uuid4().hex}{ext}"
        try:
            f.save(os.path.join(UPLOAD_DIR, stored))
        except Exception as e:
            print(f"Save failed for {original}: {e}")
            continue
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO documents "
            "(patient_id, filename, stored_filename, mime_type) "
            "VALUES (%s,%s,%s,%s)",
            (patient_id, original, stored,
             f.mimetype or 'application/octet-stream'))
        mysql.connection.commit()
        cur.close()
        saved += 1
    return saved


def remove_document_file(stored_filename):
    if not stored_filename:
        return
    path = os.path.join(UPLOAD_DIR, stored_filename)
    try:
        if os.path.isfile(path):
            os.remove(path)
    except Exception as e:
        print(f"Remove file {stored_filename}: {e}")


def remove_patient_files(patient_id):
    """Delete all on-disk files for a patient before the row is removed."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT stored_filename FROM documents WHERE patient_id=%s",
                (patient_id,))
    for (stored,) in cur.fetchall():
        remove_document_file(stored)
    cur.close()


# ══════════════════════════════════════════════════════════
#  WHATSAPP HELPERS
# ══════════════════════════════════════════════════════════
def extract_number_from_details(details):
    key = "+961"
    if not details:
        return None
    idx = details.find(key)
    if idx == -1:
        return None
    start = idx + len(key)
    length = 7 if start < len(details) and details[start] == "3" else 8
    num = details[start:start + length].strip()
    return num or None

def patient_phone(patient_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT details FROM patient WHERE id=%s", (patient_id,))
    row = cur.fetchone()
    cur.close()
    if not row:
        return None
    return extract_number_from_details(row[0])


def render_reminder_body(name, dt):
    template = get_setting('reminder_template', DEFAULT_REMINDER_TEMPLATE)
    return (template
            .replace('{name}', name or '')
            .replace('{date}', dt.strftime('%B %d, %Y') if dt else '')
            .replace('{time}', dt.strftime('%I:%M %p') if dt else ''))


def send_reminder_for(patient_id, name, session_dt_str):
    number = patient_phone(patient_id)
    if not number:
        return False
    try:
        fmt = '%Y-%m-%dT%H:%M' if 'T' in session_dt_str else '%Y-%m-%d'
        dt = datetime.strptime(session_dt_str, fmt)
    except ValueError:
        dt = None
    body = render_reminder_body(name, dt)
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        return send_whatsapp("961" + number, body, script_dir=here)
    except Exception as e:
        print(f"WA send failed: {e}")
        return False


# ── background reminder job ─────────────────────────────
def check_and_send_reminders():
    with app.app_context():
        try:
            delta = int(get_setting('reminder_delta_minutes', '120'))
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT s.patient_id, p.name, s.session_datetime
                FROM sessions s JOIN patient p ON p.id = s.patient_id
                WHERE s.session_datetime <> ''
            """)
            sessions_rows = cur.fetchall()
            now = datetime.now()
            until = now + timedelta(minutes=delta)
            for pid, name, ss in sessions_rows:
                try:
                    fmt = '%Y-%m-%dT%H:%M' if 'T' in ss else '%Y-%m-%d'
                    dt = datetime.strptime(ss, fmt)
                except ValueError:
                    continue
                if not (now <= dt <= until):
                    continue
                cur.execute(
                    "SELECT id FROM reminders_sent "
                    "WHERE patient_id=%s AND session_datetime=%s",
                    (pid, ss))
                if cur.fetchone():
                    continue
                if send_reminder_for(pid, name, ss):
                    cur.execute(
                        "INSERT IGNORE INTO reminders_sent "
                        "(patient_id, session_datetime) VALUES (%s, %s)",
                        (pid, ss))
                    mysql.connection.commit()
            cur.close()
        except Exception as e:
            print(f"Reminder-check error: {e}")


if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(func=check_and_send_reminders,
                      trigger='interval', minutes=5,
                      next_run_time=datetime.now() + timedelta(seconds=10))
    scheduler.start()
    atexit.register(scheduler.shutdown)


# ══════════════════════════════════════════════════════════
#  AUTH ROUTES
# ══════════════════════════════════════════════════════════
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password']

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM doctors WHERE username=%s", (username,))
    doc = cur.fetchone()
    cur.close()

    if doc and check_password_hash(doc[2], password):
        session['doctor_id'] = doc[0]
        session['username']  = doc[1]
        session['full_name'] = doc[3]
        session['role']      = doc[4]
        return redirect(url_for('index'))

    flash('Invalid username or password.', 'danger')
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ══════════════════════════════════════════════════════════
#  PATIENT ROUTES
# ══════════════════════════════════════════════════════════
@app.route('/')
def index():
    q = (request.args.get('q') or '').strip()
    try:
        page = max(1, int(request.args.get('page', 1)))
    except ValueError:
        page = 1
    offset = (page - 1) * PER_PAGE

    cur = mysql.connection.cursor()
    where = "WHERE 1=1 "
    params = []
    if not is_admin():
        where += "AND p.doctor_id=%s "
        params.append(current_doctor_id())
    if q:
        where += "AND p.name LIKE %s "
        params.append(f"%{q}%")

    cur.execute(
        "SELECT COUNT(*) FROM patient p LEFT JOIN doctors d "
        "ON p.doctor_id=d.id " + where, tuple(params))
    total = cur.fetchone()[0]
    total_pages = max(1, ceil(total / PER_PAGE))

    cur.execute(
        "SELECT p.id, p.name, p.details, p.casetype, p.totalfees, "
        "       p.paidfees, p.doctor_id, d.full_name "
        "FROM patient p LEFT JOIN doctors d ON p.doctor_id=d.id "
        + where + "ORDER BY p.name ASC LIMIT %s OFFSET %s",
        tuple(params) + (PER_PAGE, offset))
    data = cur.fetchall()
    cur.close()
    return render_template('index.html', data=data, q=q,
                           page=page, total_pages=total_pages, total=total)


@app.route('/edit_patient', methods=['GET', 'POST'])
def edit_patient():
    pid = request.values.get('id')
    if not pid:
        flash('Patient ID required.', 'warning')
        return redirect(url_for('index'))

    cur = mysql.connection.cursor()
    if is_admin():
        cur.execute(
            "SELECT id, name, details, casetype, totalfees, paidfees, doctor_id "
            "FROM patient WHERE id=%s", (pid,))
    else:
        cur.execute(
            "SELECT id, name, details, casetype, totalfees, paidfees, doctor_id "
            "FROM patient WHERE id=%s AND doctor_id=%s",
            (pid, current_doctor_id()))
    data = cur.fetchone()
    if not data:
        flash('Patient not found.', 'warning')
        cur.close()
        return redirect(url_for('index'))

    sessions_rows = get_sessions(pid)

    cur.execute("SELECT id, amount, payment_date FROM payments "
                "WHERE patient_id=%s ORDER BY payment_date DESC", (pid,))
    payments = cur.fetchall()

    cur.execute("SELECT session_datetime, sent_at FROM reminders_sent "
                "WHERE patient_id=%s ORDER BY sent_at DESC", (pid,))
    reminder_rows = cur.fetchall()
    reminded_sessions = [r[0].strip() for r in reminder_rows]

    doctors = []
    if is_admin():
        cur.execute("SELECT id, full_name FROM doctors ORDER BY full_name")
        doctors = cur.fetchall()

    documents = get_documents(pid)

    cur.close()
    return render_template('patient.html', data=data,
                           sessions=sessions_rows, payments=payments,
                           reminder_rows=reminder_rows,
                           reminded_sessions=reminded_sessions,
                           doctors=doctors,
                           documents=documents,
                           today=date.today().isoformat())


@app.route('/view_patient')
def view_patient():
    pid = request.values.get('id')
    if not pid:
        flash('Patient ID required.', 'warning')
        return redirect(url_for('index'))

    cur = mysql.connection.cursor()
    if is_admin():
        cur.execute(
            "SELECT p.id, p.name, p.details, p.casetype, p.totalfees, "
            "       p.paidfees, p.doctor_id, d.full_name "
            "FROM patient p LEFT JOIN doctors d ON p.doctor_id=d.id "
            "WHERE p.id=%s", (pid,))
    else:
        cur.execute(
            "SELECT p.id, p.name, p.details, p.casetype, p.totalfees, "
            "       p.paidfees, p.doctor_id, d.full_name "
            "FROM patient p LEFT JOIN doctors d ON p.doctor_id=d.id "
            "WHERE p.id=%s AND p.doctor_id=%s",
            (pid, current_doctor_id()))
    data = cur.fetchone()
    if not data:
        flash('Patient not found.', 'warning')
        cur.close()
        return redirect(url_for('index'))

    sessions_rows = get_sessions(pid)

    cur.execute("SELECT id, amount, payment_date FROM payments "
                "WHERE patient_id=%s ORDER BY payment_date DESC", (pid,))
    payments = cur.fetchall()

    cur.execute("SELECT session_datetime, sent_at FROM reminders_sent "
                "WHERE patient_id=%s ORDER BY sent_at DESC", (pid,))
    reminder_rows = cur.fetchall()
    reminded_sessions = [r[0].strip() for r in reminder_rows]

    documents = get_documents(pid)

    cur.close()
    return render_template('view_patient.html', data=data,
                           sessions=sessions_rows, payments=payments,
                           reminder_rows=reminder_rows,
                           reminded_sessions=reminded_sessions,
                           documents=documents)


# ── document serving / deletion ──────────────────────────
def _authorize_document(doc_id):
    """Return (patient_id, filename, stored_filename, mime_type) or None."""
    cur = mysql.connection.cursor()
    if is_admin():
        cur.execute(
            "SELECT d.patient_id, d.filename, d.stored_filename, d.mime_type "
            "FROM documents d WHERE d.id=%s", (doc_id,))
    else:
        cur.execute(
            "SELECT d.patient_id, d.filename, d.stored_filename, d.mime_type "
            "FROM documents d JOIN patient p ON p.id = d.patient_id "
            "WHERE d.id=%s AND p.doctor_id=%s",
            (doc_id, current_doctor_id()))
    row = cur.fetchone()
    cur.close()
    return row


@app.route('/document/<int:doc_id>')
def serve_document(doc_id):
    row = _authorize_document(doc_id)
    if not row:
        abort(404)
    _, original, stored, mime = row
    return send_from_directory(UPLOAD_DIR, stored,
                               mimetype=mime,
                               download_name=original,
                               as_attachment=False)


@app.route('/document/<int:doc_id>/download')
def download_document(doc_id):
    row = _authorize_document(doc_id)
    if not row:
        abort(404)
    _, original, stored, mime = row
    return send_from_directory(UPLOAD_DIR, stored,
                               mimetype=mime,
                               download_name=original,
                               as_attachment=True)


@app.route('/delete_document', methods=['POST'])
def delete_document():
    doc_id = request.form['document_id']
    row = _authorize_document(doc_id)
    if not row:
        flash('Document not found.', 'warning')
        return redirect(url_for('index'))
    pid, _, stored, _ = row
    remove_document_file(stored)
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM documents WHERE id=%s", (doc_id,))
    mysql.connection.commit()
    cur.close()
    flash('Document deleted.', 'success')
    return redirect(url_for('edit_patient', id=pid))


@app.route('/add_new', methods=['GET', 'POST'])
def add_new():
    if request.method == 'GET':
        doctors = []
        if is_admin():
            cur = mysql.connection.cursor()
            cur.execute("SELECT id, full_name FROM doctors ORDER BY full_name")
            doctors = cur.fetchall()
            cur.close()
        return render_template('newpatient.html',
                               today=date.today().isoformat(),
                               doctors=doctors)

    name        = request.form['name']
    details     = request.form['details']
    casetype    = request.form['casetype']
    totalfees   = request.form['totalfees']
    initial_pay = float(request.form.get('initial_payment') or 0)
    pay_date    = request.form.get('payment_date') or date.today().isoformat()

    if is_admin():
        doctor_id = request.form.get('doctor_id') or None
    else:
        doctor_id = current_doctor_id()

    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO patient "
        "(name, details, casetype, totalfees, paidfees, doctor_id) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (name, details, casetype, totalfees, 0, doctor_id))
    pid = cur.lastrowid

    if initial_pay > 0:
        cur.execute("INSERT INTO payments (patient_id, amount, payment_date) "
                    "VALUES (%s,%s,%s)", (pid, initial_pay, pay_date))
        cur.execute("UPDATE patient SET paidfees=%s WHERE id=%s",
                    (initial_pay, pid))
    mysql.connection.commit()
    cur.close()

    datetimes    = request.form.getlist('session_datetime[]')
    descriptions = request.form.getlist('session_description[]')
    sync_sessions(pid, datetimes, descriptions)

    save_uploaded_documents(pid, request.files.getlist('documents[]'))

    return redirect(url_for('view_patient', id=pid))


@app.route('/update_patient', methods=['POST'])
def update_patient():
    pid         = request.form['id']
    name        = request.form['name']
    details     = request.form['details']
    casetype    = request.form['casetype']
    totalfees   = request.form['totalfees']

    cur = mysql.connection.cursor()
    if is_admin():
        doctor_id = request.form.get('doctor_id') or None
        cur.execute(
            "UPDATE patient SET name=%s, details=%s, casetype=%s, "
            "totalfees=%s, doctor_id=%s WHERE id=%s",
            (name, details, casetype, totalfees, doctor_id, pid))
    else:
        cur.execute(
            "UPDATE patient SET name=%s, details=%s, casetype=%s, "
            "totalfees=%s WHERE id=%s AND doctor_id=%s",
            (name, details, casetype, totalfees, pid, current_doctor_id()))
    mysql.connection.commit()
    cur.close()

    datetimes    = request.form.getlist('session_datetime[]')
    descriptions = request.form.getlist('session_description[]')
    sync_sessions(pid, datetimes, descriptions)

    save_uploaded_documents(pid, request.files.getlist('documents[]'))

    return redirect(url_for('edit_patient', id=pid))


@app.route('/delete_patient', methods=['POST'])
def delete_patient():
    pid = request.form['patient_id']
    cur = mysql.connection.cursor()
    if is_admin():
        cur.execute("SELECT id FROM patient WHERE id=%s", (pid,))
    else:
        cur.execute("SELECT id FROM patient WHERE id=%s AND doctor_id=%s",
                    (pid, current_doctor_id()))
    if not cur.fetchone():
        cur.close()
        return redirect(url_for('index'))
    cur.close()

    remove_patient_files(pid)

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM patient WHERE id=%s", (pid,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('index'))


# ── payment CRUD ─────────────────────────────────────────
@app.route('/add_payment', methods=['POST'])
def add_payment():
    patient_id   = request.form['patient_id']
    amount       = request.form['amount']
    payment_date = request.form['payment_date']

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO payments (patient_id,amount,payment_date) "
                "VALUES (%s,%s,%s)", (patient_id, amount, payment_date))
    mysql.connection.commit()
    cur.close()
    recalc_paid(patient_id)
    return redirect(url_for('edit_patient', id=patient_id))


@app.route('/delete_payment', methods=['POST'])
def delete_payment():
    payment_id = request.form['payment_id']
    patient_id = request.form['patient_id']

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM payments WHERE id=%s", (payment_id,))
    mysql.connection.commit()
    cur.close()
    recalc_paid(patient_id)
    return redirect(url_for('edit_patient', id=patient_id))


# ── manual reminder ──────────────────────────────────────
@app.route('/send_reminder', methods=['POST'])
def send_reminder():
    patient_id = request.form['patient_id']
    session_dt = request.form['session_datetime']

    cur = mysql.connection.cursor()
    cur.execute("SELECT name FROM patient WHERE id=%s", (patient_id,))
    row = cur.fetchone()
    cur.close()
    name = row[0] if row else None

    if name and send_reminder_for(patient_id, name, session_dt):
        cur = mysql.connection.cursor()
        cur.execute("INSERT IGNORE INTO reminders_sent "
                    "(patient_id,session_datetime) VALUES (%s,%s)",
                    (patient_id, session_dt))
        mysql.connection.commit()
        cur.close()

    return redirect(url_for('edit_patient', id=patient_id))


# ── expenses CRUD ────────────────────────────────────────
@app.route('/expenses')
def expenses():
    cur = mysql.connection.cursor()
    if is_admin():
        cur.execute("SELECT e.*,d.full_name FROM expenses e "
                    "LEFT JOIN doctors d ON e.doctor_id=d.id "
                    "ORDER BY e.expense_date DESC")
    else:
        cur.execute("SELECT e.*,d.full_name FROM expenses e "
                    "LEFT JOIN doctors d ON e.doctor_id=d.id "
                    "WHERE e.doctor_id=%s ORDER BY e.expense_date DESC",
                    (current_doctor_id(),))
    data = cur.fetchall()

    if is_admin():
        cur.execute("SELECT COALESCE(SUM(amount),0) FROM expenses")
    else:
        cur.execute("SELECT COALESCE(SUM(amount),0) FROM expenses "
                    "WHERE doctor_id=%s", (current_doctor_id(),))
    total = cur.fetchone()[0]
    cur.close()
    return render_template('expenses.html', data=data, total=total,
                           today=date.today().isoformat())


@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'GET':
        return render_template('new_expense.html',
                               today=date.today().isoformat())

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO expenses (description,amount,expense_date,doctor_id) "
                "VALUES (%s,%s,%s,%s)",
                (request.form['description'], request.form['amount'],
                 request.form['expense_date'], current_doctor_id()))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('expenses'))


@app.route('/delete_expenses', methods=['POST'])
def delete_expenses():
    ids = request.form.getlist('delete_ids')
    if ids:
        cur = mysql.connection.cursor()
        fmt = ','.join(['%s'] * len(ids))
        if is_admin():
            cur.execute(f"DELETE FROM expenses WHERE id IN ({fmt})",
                        tuple(ids))
        else:
            cur.execute(f"DELETE FROM expenses WHERE id IN ({fmt}) "
                        f"AND doctor_id=%s",
                        tuple(ids) + (current_doctor_id(),))
        mysql.connection.commit()
        cur.close()
    return redirect(url_for('expenses'))


# ── calendar ─────────────────────────────────────────────
@app.route('/calendar')
def calendar():
    cur = mysql.connection.cursor()
    if is_admin():
        cur.execute("""
            SELECT p.id, p.name, s.session_datetime
            FROM sessions s JOIN patient p ON p.id = s.patient_id
            WHERE s.session_datetime <> ''
        """)
    else:
        cur.execute("""
            SELECT p.id, p.name, s.session_datetime
            FROM sessions s JOIN patient p ON p.id = s.patient_id
            WHERE s.session_datetime <> '' AND p.doctor_id=%s
        """, (current_doctor_id(),))
    rows = cur.fetchall()
    cur.close()
    events = [{
        "title": name,
        "start": dt,
        "url": url_for('edit_patient', id=pid),
    } for pid, name, dt in rows]
    return render_template('calendar.html', events=events)


# ══════════════════════════════════════════════════════════
#  ANALYTICS
# ══════════════════════════════════════════════════════════
@app.route('/analytics')
def analytics():
    cur  = mysql.connection.cursor()
    did  = current_doctor_id()

    if is_admin():
        cur.execute("""
            SELECT DATE_FORMAT(py.payment_date,'%Y-%m') m, SUM(py.amount)
            FROM payments py GROUP BY m ORDER BY m""")
    else:
        cur.execute("""
            SELECT DATE_FORMAT(py.payment_date,'%%Y-%%m') m, SUM(py.amount)
            FROM payments py JOIN patient p ON p.id=py.patient_id
            WHERE p.doctor_id=%s GROUP BY m ORDER BY m""", (did,))
    rev_rows = cur.fetchall()

    if is_admin():
        cur.execute("""
            SELECT DATE_FORMAT(expense_date,'%Y-%m') m, SUM(amount)
            FROM expenses GROUP BY m ORDER BY m""")
    else:
        cur.execute("""
            SELECT DATE_FORMAT(expense_date,'%%Y-%%m') m, SUM(amount)
            FROM expenses WHERE doctor_id=%s GROUP BY m ORDER BY m""",
                    (did,))
    exp_rows = cur.fetchall()

    if is_admin():
        cur.execute("""
            SELECT p.name, DATE_FORMAT(py.payment_date,'%Y-%m') m,
                   SUM(py.amount)
            FROM payments py JOIN patient p ON p.id=py.patient_id
            GROUP BY p.name,m ORDER BY m,p.name""")
    else:
        cur.execute("""
            SELECT p.name, DATE_FORMAT(py.payment_date,'%%Y-%%m') m,
                   SUM(py.amount)
            FROM payments py JOIN patient p ON p.id=py.patient_id
            WHERE p.doctor_id=%s GROUP BY p.name,m ORDER BY m,p.name""",
                    (did,))
    detail_rows = cur.fetchall()

    if is_admin():
        cur.execute("""
            SELECT DATE_FORMAT(expense_date,'%Y-%m'), description, amount
            FROM expenses ORDER BY expense_date DESC""")
    else:
        cur.execute("""
            SELECT DATE_FORMAT(expense_date,'%%Y-%%m'), description, amount
            FROM expenses WHERE doctor_id=%s
            ORDER BY expense_date DESC""", (did,))
    expense_detail_rows = cur.fetchall()

    doctor_stats = []
    if is_admin():
        cur.execute("""
            SELECT d.full_name,
              COALESCE((SELECT SUM(py.amount) FROM payments py
                        JOIN patient p ON p.id=py.patient_id
                        WHERE p.doctor_id=d.id),0),
              COALESCE((SELECT SUM(e.amount) FROM expenses e
                        WHERE e.doctor_id=d.id),0)
            FROM doctors d ORDER BY d.full_name""")
        for r in cur.fetchall():
            rev = float(r[1])
            exp = float(r[2])
            doctor_stats.append((r[0], rev, exp, rev - exp))

    cur.close()

    rev_dict = {r[0]: float(r[1]) for r in rev_rows}
    exp_dict = {r[0]: float(r[1]) for r in exp_rows}
    months   = sorted(set(list(rev_dict) + list(exp_dict)))
    revenues = [rev_dict.get(m, 0) for m in months]
    costs    = [exp_dict.get(m, 0) for m in months]
    profits  = [rev_dict.get(m, 0) - exp_dict.get(m, 0) for m in months]

    return render_template('analytics.html',
        months=months, revenues=revenues, costs=costs,
        profits=profits,
        total_revenue=sum(revenues), total_cost=sum(costs),
        total_profit=sum(revenues) - sum(costs),
        detail_rows=detail_rows,
        expense_detail_rows=expense_detail_rows,
        doctor_stats=doctor_stats)


# ══════════════════════════════════════════════════════════
#  ADMIN — DOCTOR MANAGEMENT
# ══════════════════════════════════════════════════════════
@app.route('/manage_doctors')
@admin_required
def manage_doctors():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT d.*,
          (SELECT COUNT(*) FROM patient p WHERE p.doctor_id=d.id) AS pcnt,
          COALESCE((SELECT SUM(py.amount) FROM payments py
                    JOIN patient p ON p.id=py.patient_id
                    WHERE p.doctor_id=d.id),0) AS rev
        FROM doctors d ORDER BY d.full_name""")
    doctors = cur.fetchall()
    cur.close()
    return render_template('manage_doctors.html', doctors=doctors)


@app.route('/add_doctor', methods=['GET', 'POST'])
@admin_required
def add_doctor():
    if request.method == 'GET':
        return render_template('add_doctor.html')

    username  = request.form['username']
    full_name = request.form['full_name']
    password  = request.form['password']
    role      = request.form.get('role', 'doctor')

    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM doctors WHERE username=%s", (username,))
    if cur.fetchone():
        flash('Username already exists.', 'danger')
        cur.close()
        return redirect(url_for('add_doctor'))

    cur.execute(
        "INSERT INTO doctors (username,password_hash,full_name,role) "
        "VALUES (%s,%s,%s,%s)",
        (username, generate_password_hash(password), full_name, role))
    mysql.connection.commit()
    cur.close()
    flash(f'Doctor "{full_name}" created.', 'success')
    return redirect(url_for('manage_doctors'))


@app.route('/delete_doctor', methods=['POST'])
@admin_required
def delete_doctor():
    doc_id = request.form['doctor_id']
    if int(doc_id) == current_doctor_id():
        flash("You can't delete yourself.", 'warning')
        return redirect(url_for('manage_doctors'))

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM doctors WHERE id=%s", (doc_id,))
    mysql.connection.commit()
    cur.close()
    flash('Doctor deleted.', 'success')
    return redirect(url_for('manage_doctors'))


@app.route('/reset_password', methods=['POST'])
@admin_required
def reset_password():
    doc_id   = request.form['doctor_id']
    new_pass = request.form['new_password']

    cur = mysql.connection.cursor()
    cur.execute("UPDATE doctors SET password_hash=%s WHERE id=%s",
                (generate_password_hash(new_pass), doc_id))
    mysql.connection.commit()
    cur.close()
    flash('Password reset successfully.', 'success')
    return redirect(url_for('manage_doctors'))


# ══════════════════════════════════════════════════════════
#  ADMIN — REMINDER SETTINGS
# ══════════════════════════════════════════════════════════
@app.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings_view():
    if request.method == 'POST':
        set_setting('reminder_template',
                    request.form.get('reminder_template', '').strip())
        try:
            delta = max(1, int(request.form.get('reminder_delta_minutes', '120')))
        except ValueError:
            delta = 120
        set_setting('reminder_delta_minutes', str(delta))
        flash('Settings saved.', 'success')
        return redirect(url_for('settings_view'))
    return render_template('settings.html',
        reminder_template=get_setting('reminder_template',
                                      DEFAULT_REMINDER_TEMPLATE),
        reminder_delta_minutes=get_setting('reminder_delta_minutes', '120'))


@app.route('/test_db_connection')
def test_db_connection():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT 1")
        cur.close()
        return "Connected!"
    except Exception as e:
        return f"Failed: {e}"


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
