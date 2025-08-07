from flask import Flask, render_template, request, redirect, url_for, make_response
from flask_mysqldb import MySQL
import config

app = Flask(__name__)
app.config.from_object(config)

mysql = MySQL(app)


def get_all_patients():
    try:
        
        cursor = mysql.connection.cursor() 
        cursor.execute("SELECT id, name, nextsession,lastsession FROM patient")
        patients = cursor.fetchall()
        return patients
    finally:
        cursor.close()
        

@app.route('/test_db_connection')
def test_db_connection():
    try:
        # Attempt to get a cursor or connect
        cur = mysql.connection.cursor()
        cur.execute("SELECT 1") # A simple query to test connection
        cur.close()
        return "Successfully connected to the database!"
    except Exception as e:
        return f"Failed to connect to the database: {e}"
    
@app.route('/')
def index():
    cur=mysql.connection.cursor()
    cur.execute("select * from patient ORDER BY name ASC")
    data=cur.fetchall()
    return render_template('index.html',data=data)

@app.route('/edit_patient', methods=['GET','POST'])
def edit_patient():
    if request.method=='POST':
        name=request.form['patient_name']
    if request.method=='GET':
        name=request.args.get('name')
    cur=mysql.connection.cursor()  
    cur.execute("select * from patient where name = %s",(name,))
    data=cur.fetchone()
    return render_template('patient.html',data=data)

@app.route('/add_new',methods=['GET','POST'])
def add_new():
    if request.method=='GET':
        return render_template('newpatient.html')
    else:
        name=request.form['name']
        details=request.form['details']
        casetype=request.form['casetype']
        description=request.form['description']
        lastsession=request.form['lastsession']
        nextsession=request.form['nextsession']
        totalfees=request.form['totalfees']
        paidfees=request.form['paidfees']
        cur1=mysql.connection.cursor() 
        cur1.execute("INSERT INTO patient (name, details, casetype, description, lastsession, nextsession, totalfees, paidfees) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",(name,details,casetype,description,lastsession,nextsession,totalfees,paidfees))
        mysql.connection.commit()
        return redirect(url_for('index'))
    
@app.route('/update_patient',methods=['POST'])
def update_patient():
    name=request.form['name']
    details=request.form['details']
    casetype=request.form['casetype']
    description=request.form['description']
    lastsession=request.form['lastsession']
    nextsession=request.form['nextsession']
    totalfees=request.form['totalfees']
    paidfees=request.form['paidfees']
    cur1=mysql.connection.cursor() 
    cur1.execute("UPDATE patient set name=%s,details=%s,casetype=%s,description=%s,lastsession=%s,nextsession=%s,totalfees=%s,paidfees=%s where name=%s",(name,details,casetype,description,lastsession,nextsession,totalfees,paidfees,name))
    mysql.connection.commit()
    return redirect(url_for('index'))

@app.route('/delete_patients', methods=['POST'])
def delete_patients():
    ids_to_delete = request.form.getlist('delete_ids')
    
    if ids_to_delete:
        cur = mysql.connection.cursor()
        format_strings = ','.join(['%s'] * len(ids_to_delete))
        cur.execute(f"DELETE FROM patient WHERE id IN ({format_strings})", tuple(ids_to_delete))
        mysql.connection.commit()
        cur.close()
    
    return redirect(url_for('index'))


@app.route('/calendar')
def calendar():
    data = get_all_patients()  # each row: [id, name, ..., nextsession, ...]
    events = []

    for row in data:
        name = row[1]
        sessions = row[2]
        fsession=row[3]
        events.append({"title":name,"start":fsession,"url":url_for('edit_patient',name=name)}) 
        if sessions:
            # Split by comma and strip spaces
            session_list = [s.strip() for s in sessions.split(',') if s.strip()]
            for session in session_list:
                events.append({
                    "title": name,
                    "start": session,  # expects string like '2025-08-03T11:30'
                    "url":url_for('edit_patient',name=name)
                })

    return render_template('calendar.html', events=events)


    
    
    
    
    
if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')