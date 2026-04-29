from flask import (Flask, render_template, request,
                   redirect, url_for, session, flash)
from flask_mysqldb import MySQL
from datetime import date, datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from apscheduler.schedulers.background import BackgroundScheduler
import atexit, os
import config
from twilio.rest import Client

app = Flask(__name__)
app.config.from_object(config)
app.secret_key = config.SECRET_KEY

sid   = "SID"
token = "TOKEN"
twilio_client = Client(sid, token)

mysql = MySQL(app)


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


# ── auto-create admin & enforce login on every request ───
_admin_checked = False


@app.before_request
def before_request_hook():
    global _admin_checked

    # create default admin once
    if not _admin_checked:
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT COUNT(*) FROM doctors WHERE role='admin'")
            if cur.fetchone()[0] == 0:
                cur.execute(
                    "INSERT INTO doctors (username,password_hash,full_name,role) "
                    "VALUES (%s,%s,%s,%s)",
                    ('admin',
                     generate_password_hash('admin123'),
                     'Administrator', 'admin'))
                mysql.connection.commit()
                print("✓ Default admin created — admin / admin123")
            cur.close()
        except Exception:
            pass
        _admin_checked = True

    # allow unauthenticated access to login & static
    if request.endpoint in ('login', 'static', None):
        return

    if 'doctor_id' not in session:
        return redirect(url_for('login'))


# ══════════════════════════════════════════════════════════
#  WHATSAPP HELPERS
# ══════════════════════════════════════════════════════════
def extract_number(user):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id,details FROM patient WHERE name=%s", (user,))
        data = cursor.fetchone()
        if not data:
            return None
        details = data[1] or ""
        key, start, result = "+961", 0, ""
        while True:
            idx = details.find(key, start)
            if idx == -1:
                break
            result = details[idx+len(key):idx+len(key)+8]
            start = idx + 1
        return result or None
    except Exception as e:
        print(f"extract_number error: {e}")
        return None
    finally:
        cursor.close()


def sendwtsp(number, appointment_date=None, appointment_time=None):
    body = (
        f"Hello,\nThis is a friendly reminder from PhysioWay that you have "
        f"an appointment scheduled on {appointment_date or '[Date]'} at "
        f"{appointment_time or '[Time]'}.\nIf you need to reschedule or have "
        f"any questions, please contact us at 03931372.\nWe look forward to "
        f"seeing you and supporting your recovery.\nKind regards,\nPhysioWay Team"
    )
    msg = twilio_client.messages.create(
        to=f"whatsapp:+961{number}",
        from_="whatsapp:+14155238886", body=body)
    print(f"WhatsApp sent to +961{number} — SID: {msg.sid}")

'''
# ── background reminder job ─────────────────────────────
def check_and_send_reminders():
    with app.app_context():
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT id,name,nextsession,lastsession FROM patient")
            patients = cur.fetchall()
            now, two_h = datetime.now(), datetime.now() + timedelta(hours=2)

            for pid, name, nxt, first in patients:
                sessions = []
                if nxt:
                    sessions.extend(s.strip() for s in nxt.split(',') if s.strip())
                if first:
                    sessions.append(first.strip())

                for ss in sessions:
                    try:
                        fmt = '%Y-%m-%dT%H:%M' if 'T' in ss else '%Y-%m-%d'
                        dt = datetime.strptime(ss, fmt)
                    except ValueError:
                        continue
                    if not (now <= dt <= two_h):
                        continue
                    cur.execute(
                        "SELECT id FROM reminders_sent "
                        "WHERE patient_id=%s AND session_datetime=%s",
                        (pid, ss))
                    if cur.fetchone():
                        continue
                    number = extract_number(name)
                    if not number:
                        continue
                    try:
                        sendwtsp(number,
                                 dt.strftime('%B %d, %Y'),
                                 dt.strftime('%I:%M %p'))
                        cur.execute(
                            "INSERT INTO reminders_sent "
                            "(patient_id,session_datetime) VALUES (%s,%s)",
                            (pid, ss))
                        mysql.connection.commit()
                    except Exception as e:
                        print(f"Reminder fail {name}: {e}")
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

'''
# ══════════════════════════════════════════════════════════
#  DB HELPERS
# ══════════════════════════════════════════════════════════
def get_all_patients(doctor_id=None):
    try:
        cur = mysql.connection.cursor()
        if doctor_id:
            cur.execute(
                "SELECT id,name,nextsession,lastsession FROM patient "
                "WHERE doctor_id=%s", (doctor_id,))
        else:
            cur.execute(
                "SELECT id,name,nextsession,lastsession FROM patient")
        return cur.fetchall()
    finally:
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


def patient_name_by_id(patient_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT name FROM patient WHERE id=%s", (patient_id,))
    row = cur.fetchone()
    cur.close()
    return row[0] if row else None


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
#  MAIN ROUTES
# ══════════════════════════════════════════════════════════
@app.route('/')
def index():
    cur = mysql.connection.cursor()
    if is_admin():
        cur.execute(
            "SELECT p.*, d.full_name FROM patient p "
            "LEFT JOIN doctors d ON p.doctor_id=d.id "
            "ORDER BY p.name ASC")
    else:
        cur.execute(
            "SELECT p.*, d.full_name FROM patient p "
            "LEFT JOIN doctors d ON p.doctor_id=d.id "
            "WHERE p.doctor_id=%s ORDER BY p.name ASC",
            (current_doctor_id(),))
    data = cur.fetchall()
    cur.close()
    return render_template('index.html', data=data)


@app.route('/edit_patient', methods=['GET', 'POST'])
def edit_patient():
    name = (request.form['patient_name'] if request.method == 'POST'
            else request.args.get('name'))

    cur = mysql.connection.cursor()
    if is_admin():
        cur.execute("SELECT * FROM patient WHERE name=%s", (name,))
    else:
        cur.execute("SELECT * FROM patient WHERE name=%s AND doctor_id=%s",
                    (name, current_doctor_id()))
    data = cur.fetchone()
    if not data:
        flash('Patient not found.', 'warning')
        return redirect(url_for('index'))

    appt_sessions = data[6].split(",") if data[6] else []

    cur.execute("SELECT id,amount,payment_date FROM payments "
                "WHERE patient_id=%s ORDER BY payment_date DESC", (data[0],))
    payments = cur.fetchall()

    cur.execute("SELECT session_datetime,sent_at FROM reminders_sent "
                "WHERE patient_id=%s ORDER BY sent_at DESC", (data[0],))
    reminder_rows = cur.fetchall()
    reminded_sessions = [r[0].strip() for r in reminder_rows]

    doctors = []
    if is_admin():
        cur.execute("SELECT id,full_name FROM doctors ORDER BY full_name")
        doctors = cur.fetchall()

    cur.close()
    return render_template('patient.html', data=data,
                           sessions=appt_sessions, payments=payments,
                           reminder_rows=reminder_rows,
                           reminded_sessions=reminded_sessions,
                           doctors=doctors,
                           today=date.today().isoformat())


@app.route('/add_new', methods=['GET', 'POST'])
def add_new():
    if request.method == 'GET':
        doctors = []
        if is_admin():
            cur = mysql.connection.cursor()
            cur.execute("SELECT id,full_name FROM doctors ORDER BY full_name")
            doctors = cur.fetchall()
            cur.close()
        return render_template('newpatient.html',
                               today=date.today().isoformat(),
                               doctors=doctors)

    name        = request.form['name']
    details     = request.form['details']
    casetype    = request.form['casetype']
    description = request.form['description']
    lastsession = request.form['firstsession']
    nextsession = ",".join(request.form.getlist('nextsession[]'))
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
        "(name,details,casetype,description,lastsession,"
        "nextsession,totalfees,paidfees,doctor_id) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (name, details, casetype, description,
         lastsession, nextsession, totalfees, 0, doctor_id))
    pid = cur.lastrowid

    if initial_pay > 0:
        cur.execute("INSERT INTO payments (patient_id,amount,payment_date) "
                    "VALUES (%s,%s,%s)", (pid, initial_pay, pay_date))
        cur.execute("UPDATE patient SET paidfees=%s WHERE id=%s",
                    (initial_pay, pid))

    mysql.connection.commit()
    cur.close()
    return redirect(url_for('index'))


@app.route('/update_patient', methods=['POST'])
def update_patient():
    patient_id  = request.form['id']
    name        = request.form['name']
    details     = request.form['details']
    casetype    = request.form['casetype']
    description = request.form['description']
    lastsession = request.form['firstsession']
    nextsession = ",".join(request.form.getlist('nextsession[]'))
    totalfees   = request.form['totalfees']

    cur = mysql.connection.cursor()

    if is_admin():
        doctor_id = request.form.get('doctor_id') or None
        cur.execute(
            "UPDATE patient SET name=%s,details=%s,casetype=%s,"
            "description=%s,lastsession=%s,nextsession=%s,"
            "totalfees=%s,doctor_id=%s WHERE id=%s",
            (name, details, casetype, description, lastsession,
             nextsession, totalfees, doctor_id, patient_id))
    else:
        cur.execute(
            "UPDATE patient SET name=%s,details=%s,casetype=%s,"
            "description=%s,lastsession=%s,nextsession=%s,"
            "totalfees=%s WHERE id=%s AND doctor_id=%s",
            (name, details, casetype, description, lastsession,
             nextsession, totalfees, patient_id, current_doctor_id()))

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
    return redirect(url_for('edit_patient',
                            name=patient_name_by_id(patient_id)))


@app.route('/delete_payment', methods=['POST'])
def delete_payment():
    payment_id = request.form['payment_id']
    patient_id = request.form['patient_id']

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM payments WHERE id=%s", (payment_id,))
    mysql.connection.commit()
    cur.close()
    recalc_paid(patient_id)
    return redirect(url_for('edit_patient',
                            name=patient_name_by_id(patient_id)))


# ── manual reminder ──────────────────────────────────────
@app.route('/send_reminder', methods=['POST'])
def send_reminder():
    patient_id = request.form['patient_id']
    session_dt = request.form['session_datetime']
    name   = patient_name_by_id(patient_id)
    number = extract_number(name)

    if number:
        try:
            fmt = '%Y-%m-%dT%H:%M' if 'T' in session_dt else '%Y-%m-%d'
            dt  = datetime.strptime(session_dt, fmt)
            d_str, t_str = dt.strftime('%B %d, %Y'), dt.strftime('%I:%M %p')
        except ValueError:
            d_str, t_str = session_dt, ""
        try:
            sendwtsp(number, d_str, t_str)
            cur = mysql.connection.cursor()
            cur.execute("INSERT IGNORE INTO reminders_sent "
                        "(patient_id,session_datetime) VALUES (%s,%s)",
                        (patient_id, session_dt))
            mysql.connection.commit()
            cur.close()
        except Exception as e:
            print(f"Manual reminder failed: {e}")

    return redirect(url_for('edit_patient', name=name))


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


# ── bulk delete patients ─────────────────────────────────
@app.route('/delete_patients', methods=['POST'])
def delete_patients():
    ids = request.form.getlist('delete_ids')
    if ids:
        cur = mysql.connection.cursor()
        fmt = ','.join(['%s'] * len(ids))
        if is_admin():
            cur.execute(f"DELETE FROM patient WHERE id IN ({fmt})",
                        tuple(ids))
        else:
            cur.execute(f"DELETE FROM patient WHERE id IN ({fmt}) "
                        f"AND doctor_id=%s",
                        tuple(ids) + (current_doctor_id(),))
        mysql.connection.commit()
        cur.close()
    return redirect(url_for('index'))


# ── calendar ─────────────────────────────────────────────
@app.route('/calendar')
def calendar():
    data = (get_all_patients() if is_admin()
            else get_all_patients(current_doctor_id()))
    events = []
    for row in data:
        name, nxt, first = row[1], row[2], row[3]
        events.append({"title": name, "start": first,
                       "url": url_for('edit_patient', name=name)})
        if nxt:
            for s in [x.strip() for x in nxt.split(',') if x.strip()]:
                events.append({"title": name, "start": s,
                               "url": url_for('edit_patient', name=name)})
    return render_template('calendar.html', events=events)


# ══════════════════════════════════════════════════════════
#  ANALYTICS
# ══════════════════════════════════════════════════════════
@app.route('/analytics')
def analytics():
    cur  = mysql.connection.cursor()
    did  = current_doctor_id()

    # ── revenue by month ──
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

    # ── expenses by month ──
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

    # ── patient detail ──
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

    # ── expense detail ──
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

    # ── per-doctor stats (admin only) ──
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

    # ── merge months ──
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
    app.run(debug=True, host='0.0.0.0',port=5001)
