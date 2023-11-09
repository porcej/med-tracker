#!/usr/bin/env python
# -*- coding: ascii -*-

"""
App to track runners in aid stations for the MCM

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
app.config['CENSUS_PATH'] = 'census'
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
    "Med Echo"
]
app.config['AID_STATION_MAP'] = {
    "Aid Station 1": "AS1", 
    "Aid Station 2": "AS2", 
    "Aid Station 3": "AS3", 
    "Aid Station 4/6": "AS46", 
    "Aid Station 5": "AS5", 
    "Aid Station 7": "AS7", 
    "Aid Station 8": "AS8", 
    "Aid Station 9": "AS9", 
    "Aid Station 10": "AS10", 
    "Med Alpha": "A", 
    "Med Bravo": "B", 
    "Med Charlie": "C", 
    "Med Delta": "D", 
    "Med Echo": "E"
}
app.config['USERS'] = app.config['AID_STATIONS'][:]
app.config['USERS'].append('Med Tracking')


# *====================================================================*
#         INITIALIZE DB & DB access
# *====================================================================*
# This should be a recursive walk for the database path... TODO
if not os.path.exists('db'):
    os.makedirs('db')

if not os.path.exists(app.config['CENSUS_PATH']):
    os.makedirs(app.config['CENSUS_PATH'])

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
                      presentation TEXT,
                      hospital TEXT,
                      notes TEXT,
                      runner_type TEXT,

                      age INTEGER,
                      sex TEXT,
                      iv_access INTEGER DEFAULT 0 NOT NULL,
                      registered INTEGER DEFAULT 1 NOT NULL

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
                           synopsis=synopsis)


@app.route('/encounters')
@login_required
def encounters():
    return render_template('encounters.html')


@app.route('/census')
@login_required
def census_list():
    files = [f for f in os.listdir(app.config['CENSUS_PATH']) if f.lower().endswith('.xlsx')]
    sorted_files = sorted(files, reverse=True)

    return render_template('census_list.html', files=sorted_files)


@app.route('/download/<file_name>')
@login_required
def download_file(file_name):
    file_path = os.path.join(app.config['CENSUS_PATH'], file_name)
    if os.path.isfile(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        abort(404)


@app.route('/gen-census')
@login_required
def generate_census_report():
    start_time = 0
    end_time = 0
    aid_station = current_user.username
    try:
        start_time = int(request.args.get('report_start_time'))
        end_time = int(request.args.get('report_end_time'))
    except:
        abort(418, 'This server is a teapot, not a coffee machine. - Please provide a start and end time for the census and try again.')

    if end_time < start_time:
        abort(418, 'This server is a teapot, not a coffee machine. - Start time should be before the end time.')

    # Connect to the db
    conn = db_connect()
    cursor = conn.cursor()
    # Get the aid station data
    cursor.execute(f"SELECT bib, time_in, time_out, hospital FROM encounters WHERE aid_station='{aid_station}'")
    aid_station_data = cursor.fetchall()
    conn.close()

    current_encounters = []
    past_encounters = []
    transported_encounters = []
    for row in aid_station_data:
        time_in =  parse_time(row[1])
        time_out = parse_time(row[2])
        hospital = row[3]
        if start_time <= time_out<= end_time:
            past_encounters.append(row[0])
            if hospital is not None and hospital != "":
                transported_encounters.append(row[0])
        else:
            if start_time <= time_in <= end_time:
                current_encounters.append(row[0])


    filename = fill_census_report(str(end_time), aid_station, current_encounters, past_encounters, transported_encounters)


    return redirect(url_for('download_file', file_name=filename))



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

# Fills out a a census report
def fill_census_report(end_time, aid_station, current_encounters, past_encounters, transport_encounters):
    end_time = "{:0>4}".format(end_time)
    filename = f"{end_time}{app.config['AID_STATION_MAP'][aid_station]}.xlsx"
    file_path = os.path.join(app.config['CENSUS_PATH'], filename)

    current_encounter_cells = [f"A{x}" for x in range(7, 16)] + \
                              [f"B{x}" for x in range(7, 16)] + \
                              [f"A{x}" for x in range(48, 57)] + \
                              [f"B{x}" for x in range(48, 57)]

    closed_encounter_cells = [f"A{x}" for x in range(19, 28)] + \
                             [f"B{x}" for x in range(19, 28)] + \
                             [f"A{x}" for x in range(60, 69)] + \
                             [f"B{x}" for x in range(60, 69)]

    transport_encounter_cells = [f"A{x}" for x in range(31, 35)] + \
                                [f"B{x}" for x in range(31, 35)] + \
                                [f"A{x}" for x in range(72, 76)] + \
                                [f"B{x}" for x in range(72, 76)]

    wb = load_workbook(app.config['CENSUS_TEMPALTE'])
    wb.save(file_path)

    sheet = wb["Census Roster Sheet"] # wb.active

    # Write the Census Time
    sheet['C4'] = end_time

    # Write current encounters
    for encounter in current_encounters:
        sheet[current_encounter_cells.pop(0)] = encounter
    wb.save(file_path)

    # Write closed encounters
    for encounter in past_encounters:
        sheet[closed_encounter_cells.pop(0)] = encounter
    wb.save(file_path)

    # Write transport
    for encounter in transport_encounters:
        sheet[transport_encounter_cells.pop(0)] = encounter
    wb.save(file_path)

    return filename


if __name__ == '__main__':
    create_database()
    app.run(debug=True, host="0.0.0.0", port="8080")
    
