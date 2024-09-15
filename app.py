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


from config import Config
from datetime import datetime
from io import BytesIO
import os
import pandas as pd
import re
import sqlite3
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, abort
from flask_login import current_user, LoginManager, login_user, logout_user, login_required, UserMixin
from urllib.parse import urlsplit
from werkzeug.utils import secure_filename

from flask_socketio import SocketIO, emit, join_room, leave_room


# Initialize the app
app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager()
login_manager.login_view  = 'login'
login_manager.init_app(app)

socketio = SocketIO()
socketio.init_app(app)

# Setup some user stuff here
class User(UserMixin):
    def __init__(self, name, id, role, person='', active=True):
        self.id = id
        self.name = name
        self.role = role
        self.person = person
        self.active = active

    def get_id(self):
        return self.id

    def get_person(self):
        return self.person

    def user_stamp(self):
        return f'{self.name}-{self.person}'

    def set_person(self, person):
        self.person = person

    @property
    def is_active(self):
        return self.active

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_manager(self):
        return self.role == 'manager'
    

@login_manager.user_loader
def load_user(id):
    return Config.USERS[int(id)]


# *====================================================================*
#         APP CONFIG
# *====================================================================*
idx = 0
Config.AID_STATIONS = []
Config.USERS = []
for n, u in Config.USER_ACCOUNTS.items():

    # Create a userid for each user
    u['id'] = idx

    # Assume users are all aid stations
    if (u['role'] == 'user'):
        Config.AID_STATIONS.append(n)

    # Set password if no password is provided
    if (u['password'] is None or u['password'] == ''):
        u['password'] = Config.USER_PASSWORD
    Config.USERS.append(User(name=n, id=idx, role=u['role']))
    idx += 1

# *====================================================================*
#         INITIALIZE DB & DB access
# *====================================================================*
# This should be a recursive walk for the database path... TODO
if not os.path.exists('db'):
    os.makedirs('db')

# Function to connect to SQLLite Database
def db_connect():
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        return conn
    except sqlite3.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
        return None


# Function to create an SQLite database and table to store data
def create_database():
    with db_connect() as conn:
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
                          participant INTEGER,
                          active_duty INTEGER,
                          time_in TEXT,
                          time_out TEXT,
                          presentation TEXT,
                          vitals TEXT,
                          iv TEXT,
                          iv_fluid_count INTEGER,
                          oral_fluid INTEGER,
                          food INTEGER,
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
                          delete_flag INTEGER,
                          delete_reason TEXT

                       )''')

        cursor.execute('''SELECT COUNT(*) AS CNTREC FROM pragma_table_info('encounters') WHERE name='delete_flag' ''')
        if cursor.fetchall()[0][0] == 0:
            print("Updating encounters table", file=sys.stderr)
            cursor.execute('''ALTER TABLE encounters ADD delete_flag INTEGER DEFAULT 0 ''')
            cursor.execute('''ALTER TABLE encounters ADD delete_reason TEXT DEFAULT '' ''')

            # Encounters Table - Holds a list of all encounters
        cursor.execute('''CREATE TABLE IF NOT EXISTS encounters_audit_log (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          action TEXT,
                          record_id TEXT,
                          timestamp TEXT,
                          user_id TEXT,
                          resultant_value TEXT
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
                          participant INTEGER,
                          active_duty INTEGER
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

# Function to execute query and return the last row ID after executing seaid query
def execute_query(query, values=None):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with db_connect() as conn:
            cursor = conn.cursor()
            if values is None:
                cursor.execute(query)
            else:
                cursor.execute(query, values)
            id = cursor.lastrowid
            conn.commit()
            return id
    except sqlite3.Error as e:
        print(f"Database error executing query: {e}", file=sys.stderr)
        return None


# Function to log audit transactions
def log_encounter_audit(action, record_id, user_id, resultant_value):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with db_connect() as conn:
            cursor = conn.cursor()
            query = f"INSERT INTO encounters_audit_log (action, record_id, timestamp, user_id,  resultant_value) VALUES ('{action}', '{record_id}', '{user_id}', '{timestamp}', '{resultant_value}' )"
            cursor.execute(query)
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database error writing audit log: {e}", file=sys.stderr)

# Function to export data as a zipped dict
def zip_encounters(id=None, aid_station=None, include_deleted=False, only_deleted=False):
    where_clauses = []
    if id is not None:
        where_clauses.append(f'ID={id}')
    if aid_station is not None:
        where_clauses.append(f"aid_station='{aid_station}'")
    if include_deleted is False:
        where_clauses.append('delete_flag!=1')
    if only_deleted:
        where_clauses.append('delete_flag=1')

    where_clause = ' AND '.join(where_clauses)

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

    if len(where_clause) > 0:
        where_clause = f' WHERE {where_clause}'
    with db_connect() as conn:
        cursor = conn.cursor()
        select_statement = f'SELECT * FROM {table_name}{where_clause if where_clause else ""}'
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
    try:
        if current_user.is_authenticated:
            print("Current user is at login page but is authenticated", file=sys.stderr)
            return redirect(url_for('dashboard'))

        username = request.form.get('username')
        password = request.form.get('password')
        person = request.form.get('person')

        # If a post request was made, find the user by 
        # filtering for the username
        if request.method == "POST":
            if username in Config.USER_ACCOUNTS.keys():
                if password == Config.USER_ACCOUNTS[username]['password']:
                    user = Config.USERS[Config.USER_ACCOUNTS[username]['id']]
                    user.set_person(person)
                    login_user(user, remember='y')
                    return redirect(url_for('dashboard'))
            flash('Invalid username or password', 'error')
            # Redirect the user back to the home
            # (we'll create the home route in a moment)
        return render_template("login.html", aid_stations=Config.USER_ACCOUNTS.keys())
    except Exception as e:
        flash('An unexpected error occurred.', 'error')

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

    for aid_station in Config.AID_STATIONS:

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
                        WHERE disposition IS NOT NULL
                          AND disposition like 'Transport%'
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
                      WHERE disposition IS NOT NULL
                      AND disposition like 'Transport%'
                      ORDER BY time_in
                   ''')
    synopsis['total']['transported'] = cursor.fetchone()[0]

    return render_template("dashboard.html", \
                           aid_stations=Config.AID_STATIONS, \
                           active_encounters=active_encounters_by_station, \
                           synopsis=synopsis, \
                           is_admin=current_user.is_admin)


@app.route('/encounters')
@login_required
def encounters():
    return render_template('encounters.html',
            username=current_user.name, \
            aid_stations=Config.AID_STATIONS, \
            is_manager=current_user.is_manager, \
            is_admin=current_user.is_admin)


# *====================================================================*
#         Chat
# *====================================================================*
@app.route('/chat')
def chat():
    """Chat room. The user's name and room must be stored in
    the session."""
    name = current_user.name
    room = 'chat'
    # if name == '' or room == '':
    #     return redirect(url_for('.index'))
    return render_template('chat.html', name=name, room=room, is_admin=current_user.is_admin)



# *====================================================================*
#         ADMIN
# *====================================================================*
# Route for uploading xlsx file and removing all rows
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        if 'remove-people' in request.form:
            remove_all_rows('persons')
            return f'All removed all runners.'
        elif 'remove-encounters' in request.form:
            remove_all_rows('encounters')
            send_sio_msg('remove_encounter', 'File Uploaded')
            return f'All removed all encounters.'
        elif 'export-people' in request.form:
            return export_to_xlsx('persons')
        elif 'export-encounters' in request.form:
            return export_to_xlsx('encounters')
        elif 'participants-file' in request.files:
            file = request.files['participants-file']
            if file.filename.endswith('.xlsx'):
                df = pd.read_excel(file)
                df['participant'] = 1
                save_to_database(df, 'persons')
                return 'File uploaded and data loaded into database successfully!'
            else:
                return 'Only xlsx files are allowed!'
        elif 'encounters-file' in request.files:
            file = request.files['encounters-file']
            if file.filename.endswith('.xlsx'):
                df = pd.read_excel(file)
                save_to_database(df, 'encounters')
                send_sio_msg('new_encounter', 'File Uploaded')
                return 'File uploaded and data loaded into database successfully!'
            else:
                return 'Only xlsx files are allowed!'
        else:
            return 'I am not a teapot.'

    return render_template('admin.html')

# Save DataFrame to SQLite database
def save_to_database(df, table):
    with sqlite3.connect(Config.DATABASE_PATH) as conn:
        df.to_sql(table, conn, if_exists='replace', index=False)

# Remove all rows from the table
def remove_all_rows(table):
    with sqlite3.connect(Config.DATABASE_PATH) as conn:
        conn.execute(f'DELETE FROM {table}')

# Export SQLite table to xlsx file
def export_to_xlsx(table):
    with sqlite3.connect(Config.DATABASE_PATH) as conn:
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
            matches = re.search(pattern, key)
            if matches:
                id = int(matches.group(1))
                field_key = matches.group(2)
                data[field_key] = request.form[key]

        # Handle Editing an existing record
        if action.lower() == 'edit':
            data_keys = data.keys()
            query = f"UPDATE encounters SET {' ,'.join(f'{n} = :{n}' for n in data_keys)} WHERE id={id}"
            execute_query(query, data)

            new_data = zip_encounters(id=id)
            jnew_data = jsonify(new_data)
            log_encounter_audit(action=action.lower(), record_id=id, user_id=current_user.user_stamp(), resultant_value=jnew_data)
            send_sio_msg('edit_encounter', jnew_data)
            return jnew_data

        # Handle Creating a new record
        if action.lower() == 'create':
            data_keys = data.keys()
            query = f"INSERT INTO encounters ( {', '.join(data_keys) }) VALUES (:{', :'.join(data_keys) })"
            id = execute_query(query, data)

            new_data = zip_encounters(id=id)
            jnew_data = jsonify(new_data)
            log_encounter_audit(action=action.lower(), record_id=id, user_id=current_user.user_stamp(), resultant_value=jnew_data.get_data().decode('UTF-8'))
            send_sio_msg('new_encounter', jnew_data)
            return jnew_data

        # Handle Remove
        if action.lower() == 'remove':
            query = f"UPDATE encounters SET delete_flag=1 WHERE id={id}"
            execute_query(query)
            
            new_data = zip_encounters(id=id)
            jnew_data = jsonify(new_data)
            log_encounter_audit(action=action.lower(), record_id=id, user_id=current_user.user_stamp(), resultant_value=jnew_data)
            send_sio_msg('remove_encounter', jnew_data)
            return jnew_data

    # Handle Get Request
    if request.method == "GET":
        with sqlite3.connect(Config.DATABASE_PATH) as conn:
            data = zip_encounters(aid_station=aid_station)
        return jsonify(data)

    return jsonify("Oh no, you should never be here...")





# *====================================================================*
#         SocketIO API
# *====================================================================*
# Handler for a message recieved over 'connect' channel
@socketio.on('connect', namespace="/api")
def test_connect():
    emit('after connect',  {'data':'Lets dance'})

def send_sio_msg(msg_type, msg, room=None):
    broadcast = room is None
    socketio.emit(msg_type, namespace='/api')

# *====================================================================*
#         SocketIO Chat
# *====================================================================*
@socketio.on('joined', namespace='/chat')
def joined(message):
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    room = 'chat'
    join_room(room)
    emit('status', {'msg': current_user.name + ' has entered the room.'}, room=room)


@socketio.on('text', namespace='/chat')
def text(message):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    room = 'chat'
    emit('message', {'msg': current_user.name + ':' + message['msg']}, room=room)


@socketio.on('left', namespace='/chat')
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    room = 'chat'
    leave_room(room)
    emit('status', {'msg': current_user.name + ' has left the room.'}, room=room)




if __name__ == '__main__':
    create_database()
    socketio.run(app, debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)

    
