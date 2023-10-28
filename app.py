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

from pprint import pprint
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
class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(id):
    if int(id) <= len(app.config['AID_STATIONS']):
        user = User()
        user.id = id;
        user.username = app.config['AID_STATIONS'][int(id)]
    return user


# *====================================================================*
#         APP CONFIG
# *====================================================================*
app.config['PASSWORD'] = ""
app.config['DATABASE'] = 'db/data.db'
app.config['CENSUS_TEMPALTE'] = 'static/Medical Census Roster Sheet_22OCT2023.xlsx'
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
    "Med Echo",
    "Med Tracking"
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


# Function to export data as a zipped dict
def zip_data(cursor, id=None, aid_station=None):
    where_clause = ""
    if id is not None or aid_station is not None:
        where_clause = " WHERE"
        if id is not None:
            where_clause = f"{where_clause} ID={id}"
        if aid_station is not None:
            where_clause = f"{where_clause} aid_station='{aid_station}'"

    cursor.execute(f"SELECT * FROM encounters {where_clause}")
    rows = cursor.fetchall()

    # Get the column names
    cursor.execute(f"PRAGMA table_info(encounters)")
    columns = [column[1] for column in cursor.fetchall()]

    # Convert the data to a list of dictionaries
    data_list = []
    for row in rows:
        data_dict = dict(zip(columns, row))
        data_list.append(data_dict)

    return {'data': data_list}



# Function to fetch a sqlite table as a JSON string
def load_data(table_name, id=None):
    # Connect to the SQLite database
    conn = db_connect()
    cursor = conn.cursor()
    data = zip_data(cursor, table_name, id)
    conn.close()
    return data



# *====================================================================*
#         ROUTES
# *====================================================================*


# *--------------------------------------------------------------------*
#         Authentication & User Management
# *--------------------------------------------------------------------*
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        print("Current user is at login page but is authenticated", file=sys.stderr)
        return redirect(url_for('dashboard'))

    # If a post request was made, find the user by 
    # filtering for the username
    if request.method == "POST":
        if request.form.get("username") in app.config['AID_STATIONS']:
            if app.config['PASSWORD'] == request.form.get("password"):
                user = User()
                user.username = request.form.get("username")
                user.id = app.config['AID_STATIONS'].index(user.username);
                login_user(user, remember='y')
                return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'error')
        # Redirect the user back to the home
        # (we'll create the home route in a moment)
    return render_template("login.html", aid_stations=app.config['AID_STATIONS'])

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# *--------------------------------------------------------------------*
#         End User Routes (Web Pages)
# *--------------------------------------------------------------------*
@app.route('/')
@login_required
def dashboard():
    conn = db_connect()
    cursor = conn.cursor()

    active_encounters_by_station = {}
    synopsis = {'total': {}, 'stations': {}}

    for aid_station in app.config['AID_STATIONS']:
        cursor.execute('''SELECT * FROM encounters
                          WHERE time_in IS NOT NULL
                          AND ( time_out IS NULL OR time_out="")
                          AND aid_station=?
                          ORDER BY time_in
                       ''', (aid_station,))
        active_encounters = cursor.fetchall()
        active_encounters_by_station[aid_station] = cursor.fetchall()


        # Generate Synopsis data set
        synopsis['stations'][aid_station] = {}

        # All Encounters
        cursor.execute("SELECT COUNT(*) FROM encounters WHERE aid_station=?", (aid_station,))
        synopsis['stations'][aid_station]['encounters'] = cursor.fetchone()[0]

        # Active Encounters (have a start time and not an end time)
        cursor.execute('''SELECT COUNT(*) FROM encounters
                          WHERE time_in IS NOT NULL
                          AND ( time_out IS NULL OR time_out="")
                          AND aid_station=?
                          ORDER BY time_in
                       ''', (aid_station,))
        synopsis['stations'][aid_station]['active'] = cursor.fetchone()[0]

        # Closed Encounters Only (have an end time)
        cursor.execute('''SELECT COUNT(*) FROM encounters
                          WHERE time_out IS NOT NULL
                          AND time_out<>""
                          AND aid_station=?
                          ORDER BY time_in
                       ''', (aid_station,))
        synopsis['stations'][aid_station]['discharged'] = cursor.fetchone()[0]

        
                # Closed Encounters Only (have an end time)
        cursor.execute('''SELECT COUNT(*) FROM encounters
                          WHERE hospital IS NOT NULL
                          AND hospital<>""
                          AND aid_station=?
                          ORDER BY time_in
                       ''', (aid_station,))
        synopsis['stations'][aid_station]['transported'] = cursor.fetchone()[0]

    return render_template("dashboard.html", \
                           aid_stations=app.config['AID_STATIONS'], \
                           active_encounters=active_encounters_by_station, \
                           synopsis=synopsis)


@app.route('/encounters')
@login_required
def encounters():
    return render_template('encounters.html')


# *====================================================================*
#         API
# *====================================================================*
@app.route('/api/encounters', methods=['GET', 'POST'])
@app.route('/api/encounters/<aid_station>', methods=['GET', 'POST'])
@login_required
def api_encounters(aid_station=None):
    if aid_station is not None:
        aid_station = aid_station.replace("_", " ")
        aid_station = aid_station.replace("--", "/")

    if request.method == 'POST':
        
        # Validate the post request
        if 'action' not in request.form:
            return jsonify({ 'error': 'Ahhh I dont know what to do, please provide an action'})

        action = request.form['action']

        pattern = r'\[(\d+)\]\[([a-zA-Z_]+)\]'
        data = {}
        id = 0
        query = ""

        for key in request.form.keys():
            print(f"Key: {key}", file=sys.stderr)
            matches = re.search(pattern, key)
            if matches:
                id = int(matches.group(1))
                field_key = matches.group(2)
                data[field_key] = request.form[key]

        # Handle Editing an existing record
        if action.lower() == 'edit':

            set_elem = []
            for col in data.keys():
                set_elem.append(f" {col}='{data[col]}'")

            query = f"UPDATE encounters SET {', '.join(set_elem)} WHERE ID={id}"

            print(f"Query: {query}", file=sys.stderr)

            conn = db_connect()
            cursor = conn.cursor()
            cursor.execute(query)
            new_data = zip_data(cursor, id=id)
            conn.commit()
            conn.close()
            return jsonify(new_data)

        # Handle Creating a new record
        if action.lower() == 'create':
            col_elem = data.keys()
            val_elem = []
            for col in col_elem:
                val_elem.append(f"'{data[col]}'")

            query = f"INSERT INTO encounters ( {', '.join(col_elem) }) VALUES ({ ', '.join(val_elem) })"
            conn = db_connect()
            cursor = conn.cursor()
            cursor.execute(query)
            new_data = zip_data(cursor, id=cursor.lastrowid)
            conn.commit()
            conn.close()
            return jsonify(new_data)


        # Handle Remove
        if action.lower() == 'remove':
            conn = db_connect()
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM encounters WHERE id={id}")
            conn.commit()
            
            new_data = zip_data(cursor)
            conn.close()
            return jsonify(new_data)

    # Handle Get Request
    if request.method == "GET":
        if aid_station is None:
            conn = db_connect()
            cursor = conn.cursor()
            data = zip_data(cursor)
            conn.close()
            return jsonify(data)
        
        conn = db_connect()
        cursor = conn.cursor()
        data = zip_data(cursor, aid_station=aid_station)
        conn.close()
        return jsonify(data)


    return jsonify("This fun thing")



# *====================================================================*
#         Utilities
# *====================================================================*
def parse_time(str):
    return int(str.replace(":",""))



if __name__ == '__main__':
    create_database()
    app.run(debug=True, host="0.0.0.0", port="8080")
    
