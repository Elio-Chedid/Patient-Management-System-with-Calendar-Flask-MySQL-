# 🩺 Patient Management System with Calendar (Flask + MySQL)

This is a web-based Patient Management System built using **Flask**, **MySQL**, and **FullCalendar.js**. It allows users to:

- Add, edit, and delete patients
- Track session history and financial details
- View and manage sessions via an interactive calendar
- Store multiple session dates (with time) for each patient

---

## 🛠 Features

- 📋 Patient List View with Search, Sort, and Delete options
- 📝 Add / Edit Patient with:
  - Personal details
  - Case type & description
  - Session history
  - Total and paid fees
- 📅 FullCalendar integration to visualize upcoming sessions
- 🕒 Support for multiple session timestamps stored as strings
- 🎨 Clean and responsive Bootstrap UI

---

## 🚀 Tech Stack

| Tech        | Description                      |
|-------------|----------------------------------|
| Python      | Flask Web Framework              |
| MySQL       | Relational Database              |
| Jinja2      | HTML Templating Engine           |
| Bootstrap 5 | Responsive UI Framework          |
| FullCalendar| JS Library for Interactive Calendar |

---


## 🧪 Setup Instructions

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/patient-calendar-flask.git
cd patient-calendar-flask
Create a virtual environment (optional but recommended)


python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies


pip install -r requirements.txt
Configure MySQL

Create a database named william

Import your patient table with the following structure:


CREATE TABLE `patient` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` TEXT NOT NULL,
  `details` TEXT NOT NULL,
  `casetype` TEXT NOT NULL,
  `description` TEXT NOT NULL,
  `lastsession` TEXT,
  `nextsession` TEXT,
  `totalfees` FLOAT,
  `paidfees` FLOAT
);
Update your database config in app.py


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'your_user'
app.config['MYSQL_PASSWORD'] = 'your_password'
app.config['MYSQL_DB'] = 'william'
Run the app


python app.py
Then open http://127.0.0.1:5000 in your browser.

🗓 Calendar Functionality
The nextsession field can store multiple dates as a comma-separated string:


2025-09-04T15:40, 2025-09-06T11:20, 2025-09-10T15:00
These dates are parsed and rendered as calendar events using FullCalendar.

✅ TODO (Suggestions)
Add login/authentication

Implement search/filter functionality

Validate and format session dates on input

Add export/reporting options (PDF/Excel)

📄 License
This project is open-source and free to use under the MIT License.

