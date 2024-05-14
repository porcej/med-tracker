#!/usr/bin/env python
# -*- coding: ascii -*-

"""
App to track runners in aid stations for the MCM

Changelog:
    - 2023-10-28 - Initial Commit
    - 2024-05-14
"""

__author__ = "Joseph Porcelli (porcej@gmail.com)"
__version__ = "0.0.5"
__copyright__ = "Copyright (c) 2024 Joseph Porcelli"
__license__ = "MIT"

from pprint import pprint
import datetime
from io import BytesIO
import os
import pandas as pd
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
    if int(id) <= len(app.config['USERS']):
        user = User()
        user.id = id;
        user.username = app.config['USERS'][int(id)]
    return user


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

app.config['USERS'] = app.config['AID_STATIONS'][:]
app.config['MANAGERS'] = [
    'Med Tracking',
]
app.config['ADMINS'] = [
    'porcej'
]

# Add admins to managers and managers to users
app.config['MANAGERS'].extend(app.config['ADMINS'])
app.config['USERS'].extend(app.config['MANAGERS'])

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

    # Encounters Table - Holds a list of all encounters
    cursor.execute('''CREATE TABLE IF NOT EXISTS encounters (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      aid_station TEXT,
                      bib TEXT,
                      first_name TEXT,
                      last_name TEXT,
                      age INTEGER,
                      sex TEXT,
                      runner_type TEXT,
                      time_in TEXT,
                      time_out TEXT,
                      presentation TEXT,
                      vitals TEXT,
                      iv TEXT,
                      na TEXT,
                      kplus TEXT,
                      cl TEXT,
                      tco TEXT,
                      bun TEXT,
                      cr TEXT,
                      glu TEXT,
                      treatments TEXT,
                      disposition TEXT,
                      hospital TEXT,
                      notes TEXT,
                      registered INTEGER DEFAULT 1 NOT NULL
                   )''')

    # Vitals Table - Holds a List of all Vitasl
    cursor.execute('''CREATE TABLE IF NOT EXISTS vitals (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      encounter_id INTEGER,
                      vital_time TEXT,
                      temp TEXT,
                      resp TEXT,
                      pulse TEXT,
                      bp TEXT,
                      notes TEXT
                   )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS persons (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      bib TEXT,
                      first_name TEXT,
                      last_name TEXT,
                      age INTEGER,
                      sex TEXT,
                      runner INTEGER
                   )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS presentation (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      code TEXT,
                      description TEXT
                   )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS disposition (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      code TEXT,
                      description TEXT
                   )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT NOT NULL,
                      password TEXT NOT NULL,
                      role TEXT
                   )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS aid_stations (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT NOT NULL
                   )''')



    print("Database created!", file=sys.stderr)
    conn.commit()
    conn.close()


# Function to export data as a zipped dict
def zip_encounters(id=None, aid_station=None):
    where_clause = None
    if id is not None or aid_station is not None:
        if id is not None:
            where_clause = f'ID={id}'
        if aid_station is not None:
            where_clause = f'aid_station={aid_station}'

        print(f'WHERE CLAUSE ***************  {where_clause} ************')

    data = zip_table(table_name='encounters', where_clause=where_clause)
    return data


# Function to export data as a zipped dict
def zip_vitals(encounter_id=None, id=None):
    where_clause = None
    if encounter_id is not None and id is not None:
        where_clause = f'ENCOUNTER_ID={encounter_id} AND ID={id}'
    elif encounter_id is None and id is None:
        return {'data': []}
    else:
        if encounter_id is not None:
            where_clause = f'ENCOUNTER_ID={encounter_id}'
        if id is not None:
            where_clause = f'id={id}'

    data = zip_table(table_name='vitals', where_clause=where_clause)
    return data


# Function to export participant data as a zipped dict
def zip_table(table_name, where_clause=None):
    if where_clause is None:
        where_clause = ""
    else:
        where_clause = f' WHERE {where_clause}'
    with sqlite3.connect(app.config['DATABASE']) as conn:
        cursor = conn.cursor()
        select_statement = f'SELECT * FROM {table_name}{where_clause if where_clause else ""}'
        print(f'SELECT STATMENT ===== {select_statement} ====')
        cursor.execute(select_statement)
        rows = cursor.fetchall()
        # Get the column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in cursor.fetchall()]
        # Convert the data to a list of dictionaries
    data_list = []
    for row in rows:
        data_dict = dict(zip(columns, row))
        data_list.append(data_dict)
    return {'data': data_list}

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
        if request.form.get("username") in app.config['USERS']:
            if app.config['PASSWORD'] == request.form.get("password"):
                user = User()
                user.username = request.form.get("username")
                user.id = app.config['USERS'].index(user.username);
                login_user(user, remember='y')
                return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'error')
        # Redirect the user back to the home
        # (we'll create the home route in a moment)
    return render_template("login.html", aid_stations=app.config['USERS'])

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
    is_admin = current_user.username in app.config['ADMINS']

    conn = db_connect()
    cursor = conn.cursor()

    active_encounters_by_station = {}
    synopsis = {'total': {}, 'stations': {}}

    for aid_station in app.config['AID_STATIONS']:

        # Active Encounters (have a start time and not an end time)
        cursor.execute('''SELECT * FROM encounters
                          WHERE ( time_out IS NULL OR time_out="")
                          AND aid_station=?
                          ORDER BY time_in
                       ''', (aid_station,))
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

        # Closed Encounters with Transport Only
        cursor.execute('''SELECT COUNT(*) FROM encounters
                          WHERE hospital IS NOT NULL
                          AND hospital<>""
                          AND aid_station=?
                          ORDER BY time_in
                       ''', (aid_station,))
        synopsis['stations'][aid_station]['transported'] = cursor.fetchone()[0]


    # All encounter recoreds
    cursor.execute('''SELECT COUNT(*) FROM encounters
                      ORDER BY time_in
                   ''')
    synopsis['total']['encounters'] = cursor.fetchone()[0]

    # Active Encounters (have a start time and not an end time)
    cursor.execute('''SELECT COUNT(*) FROM encounters
                      WHERE time_in IS NOT NULL
                      AND ( time_out IS NULL OR time_out="")
                      ORDER BY time_in
                   ''')
    synopsis['total']['active'] = cursor.fetchone()[0]

    # Closed Encounters Only (have an end time)
    cursor.execute('''SELECT COUNT(*) FROM encounters
                      WHERE time_out IS NOT NULL
                      AND time_out<>""
                      ORDER BY time_in
                   ''')
    synopsis['total']['discharged'] = cursor.fetchone()[0]

    
    # Closed Encounters with Transport Only
    cursor.execute('''SELECT COUNT(*) FROM encounters
                      WHERE hospital IS NOT NULL
                      AND hospital<>""
                      ORDER BY time_in
                   ''')
    synopsis['total']['transported'] = cursor.fetchone()[0]

    return render_template("dashboard.html", \
                           aid_stations=app.config['AID_STATIONS'], \
                           active_encounters=active_encounters_by_station, \
                           synopsis=synopsis, \
                           is_admin=is_admin)


@app.route('/encounters')
@login_required
def encounters():
    is_admin = current_user.username in app.config['ADMINS']
    is_manager = current_user.username in app.config['MANAGERS']
    return render_template('encounters.html',
            aid_stations=app.config['AID_STATIONS'], \
            is_manager=is_manager, \
            is_admin=is_admin)


# *====================================================================*
#         ADMIN
# *====================================================================*
# Route for uploading xlsx file and removing all rows
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.username not in app.config['ADMINS']:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        if 'remove-people' in request.form:
            remove_all_rows('persons')
            return f'All removed all runners.'
        elif 'remove-encounters' in request.form:
            remove_all_rows('encounters')
            return f'All removed all encounters.'
        elif 'export-people' in request.form:
            return export_to_xlsx('persons')
        elif 'export-encounters' in request.form:
            return export_to_xlsx('encounters')
        elif 'file' in request.files:
            file = request.files['file']
            if file.filename.endswith('.xlsx'):
                df = pd.read_excel(file)
                df['runner'] = 'Runner'  # Set runner field to "Runner"
                save_to_database(df)
                return 'File uploaded and data loaded into database successfully!'
            else:
                return 'Only xlsx files are allowed!'
    return render_template('admin.html')

# Save DataFrame to SQLite database
def save_to_database(df):
    with sqlite3.connect(app.config['DATABASE']) as conn:
        df.to_sql('persons', conn, if_exists='replace', index=False)

# Remove all rows from the table
def remove_all_rows(table):
    with sqlite3.connect(app.config['DATABASE']) as conn:
        conn.execute(f'DELETE FROM {table}')

# Export SQLite table to xlsx file
def export_to_xlsx(table):
    with sqlite3.connect(app.config['DATABASE']) as conn:
        df = pd.read_sql_query(f'SELECT * FROM {table}', conn)
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name=table)
    writer.close()
    output.seek(0)
    return send_file(output, download_name=f'{table}.xlsx', as_attachment=True)

# *====================================================================*
#         API
# *====================================================================*
@app.route('/api/participants/', methods=['GET'])
@login_required
def api_participants():
    data = zip_table("persons")
    return jsonify(data)

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
            with sqlite3.connect(app.config['DATABASE']) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                conn.commit()
            
            new_data = zip_encounters(id=id)
            return jsonify(new_data)

        # Handle Creating a new record
        if action.lower() == 'create':
            col_elem = data.keys()
            val_elem = []
            for col in col_elem:
                val_elem.append(f"'{data[col]}'")

            query = f"INSERT INTO encounters ( {', '.join(col_elem) }) VALUES ({ ', '.join(val_elem) })"
            with sqlite3.connect(app.config['DATABASE']) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                id = cursor.lastrowid
                conn.commit()
            new_data = zip_encounters(id=id)
            return jsonify(new_data)

        # Handle Remove
        if action.lower() == 'remove':
            with sqlite3.connect(app.config['DATABASE']) as conn:
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM encounters WHERE id={id}")
                conn.commit()
            
            new_data = zip_encounters(id=id)
            return jsonify(new_data)

    # Handle Get Request
    if request.method == "GET":
        with sqlite3.connect(app.config['DATABASE']) as conn:
            data = zip_encounters(aid_station=aid_station)
        return jsonify(data)

    return jsonify("Oh no, you should never be here...")


# *====================================================================*
#         Utilities
# *====================================================================*
# Parses a time string in the format HH:mm and returns a number rep
def parse_time(str):
    try:
        return int(str.replace(":",""))
    except:
        return -1

if __name__ == '__main__':
    create_database()
    app.run(debug=True, host="0.0.0.0", port="8080")
    
