#!/usr/bin/env python
# -*- coding: ascii -*-

"""
Some models to store data

Changelog:
    - 2023-10-28 - Initial Commit
"""

__author__ = "Joseph Porcelli (porcej@gmail.com)"
__version__ = "0.0.1"
__copyright__ = "Copyright (c) 2023 Joseph Porcelli"
__license__ = "MIT"

import datetime
import os
import re
import sqlite3
import sys
from openpyxl import load_workbook
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, abort
from flask_login import current_user, LoginManager, login_user, logout_user, login_required, UserMixin
from urllib.parse import urlsplit
from werkzeug.utils import secure_filename


# Initialize the app
app = Flask(__name__)
app.secret_key = "your_secret_key"  # Change this to a secure secret key

login_manager = LoginManager()
login_manager.login_view  = 'login'
login_manager.init_app(app)

# Setup some user stuff here
class FakeUser(UserMixin):
    id = 1
    username = "Admin User"
    password = ""

@login_manager.user_loader
def load_user(id):
    fakeuser = FakeUser()
    return fakeuser


# *====================================================================*
#         APP CONFIG
# *====================================================================*
app.config['PASSWORD'] = "mcm2023"
app.config['DATABASE'] = 'db/data.db'
app.config['AID_STATIONS'] = [
    "Aid Station 1", 
    "Aid Station 2", 
    "Aid Station 3", 
    "Aid Station 4/6", 
    "Aid Station 5", 
    "Aid Station 7", 
    "Aid Station 8", 
    "Aid Station 9", 
    "Aid Station 10", 
    "Med Alpha", 
    "Med Bravo", 
    "Med Charlie", 
    "Med Delta", 
    "Med Echo"
]
app.config['AID_STATION_MAP'] = {
    "AS1": "Aid Station 1", 
    "AS2": "Aid Station 2", 
    "AS3": "Aid Station 3", 
    "AS46": "Aid Station 4/6", 
    "AS5": "Aid Station 5", 
    "AS7": "Aid Station 7", 
    "AS8": "Aid Station 8", 
    "AS9": "Aid Station 9", 
    "AS10": "Aid Station 10", 
    "mA": "Med Alpha", 
    "mB": "Med Bravo", 
    "mC": "Med Charlie", 
    "mD": "Med Delta", 
    "mE": "Med Echo"
}


# *====================================================================*
#         INITIALIZE DB & DB access
# *====================================================================*
# This should be a recursive walk for the database path... TODO
if not os.path.exists('db'):
    os.makedirs('db')


# Function to connect to SQLLite Database
def db_connect():
    return sqlite3.connect(app.config['DATABASE'])


# Function to create an SQLite database and table to store data
def create_database():
    conn =  db_connect()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS encounters (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      aid_station TEXT,
                      bib TEXT,
                      first_name TEXT,
                      last_name TEXT,
                      time_in TEXT,
                      time_out TEXT,
                      disposition TEXT,
                      hospital TEXT,
                      notes TEXT
                   )''')

    print("Database created!", file=sys.stderr)
    conn.commit()
    conn.close()

# *====================================================================*
#         ROUTES
# *====================================================================*


# *--------------------------------------------------------------------*
#         Authentication & User Management
# *--------------------------------------------------------------------*
@app.route("/login", methods=["GET", "POST"])
def login():
    # if current_user.is_authenticated:
    #     return redirect(url_for('upload_fiel'))

    # If a post request was made, find the user by 
    # filtering for the username
    if request.method == "POST":
        if app.config['USERNAME'] == request.form.get("username"):
            if app.config['PASSWORD'] == request.form.get("password"):
                user = FakeUser()
                user.username = app.config['USERNAME'] 
                user.password = app.config['PASSWORD']
                # user.user_id = 1;
                login_user(user, remember='y')
                next_page = request.args.get('next')
                # if not next_page or urlsplit(next_page).netloc != '':
                    # next_page = url_for('upload_file')
                return redirect(next_page)
        # Redirect the user back to the home
        # (we'll create the home route in a moment)
    return render_template("login.html", aid_stations=app.config['AID_STATIONS'])

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))





if __name__ == '__main__':
    create_database()
    app.run(debug=True, host="0.0.0.0", port="8080")
    
