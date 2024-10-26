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
from io import BytesIO
import json
import os
import pandas as pd
import re
import sqlite3
import sys
from uuid import uuid4, UUID
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, abort, Blueprint, g
from flask_login import current_user, LoginManager, login_user, logout_user, login_required, UserMixin
from urllib.parse import urlsplit
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO, emit, join_room, leave_room
import time
import socketio as socketioClient
import threading

from models import Db

from api import api_bp

sync_mode = 'server'

remote_sio = socketioClient.Client()
try:
    if (Config.UPSTREAM_ENDPOINT != "") and Config.SYNC_ENABLED:
        sync_mode = 'client'
except:
    pass

print(f" * Syncing is {'enabled' if Config.SYNC_ENABLED else 'disabled'}.")
print(f" * Starting syncing as {sync_mode}.", file=sys.stderr)


# Initialize the app
app = Flask(__name__)
app.config.from_object(Config)
jwt = JWTManager(app)

login_manager = LoginManager()
login_manager.login_view  = 'auth_bp.login'
login_manager.init_app(app)

socketio = SocketIO()
socketio.init_app(app, cors_allowed_origins="*")

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
    try:
        return Config.USERS[int(id)]
    except: 
        return None


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
db = Db(Config.DATABASE_PATH)


# *====================================================================*
#         ROUTES
# *====================================================================*

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')
internal_api_bp = Blueprint('internal_api_bp', __name__, url_prefix='/api/internal')
chat_bp = Blueprint('chat_bp', __name__, url_prefix='/chat')
admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')
main_bp = Blueprint('main_bp', __name__)

# *--------------------------------------------------------------------*
#         Authentication & User Management
# *--------------------------------------------------------------------*
@auth_bp.route("/login", methods=["GET", "POST"])
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
                    return redirect(url_for('main_bp.dashboard'))
            flash('Invalid username or password', 'error')
            # Redirect the user back to the home
            # (we'll create the home route in a moment)
        return render_template("login.html", aid_stations=Config.USER_ACCOUNTS.keys())
    except Exception as e:
        flash('An unexpected error occurred.', 'error')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth_bp.login'))



# *--------------------------------------------------------------------*
#         End User Routes (Web Pages)
# *--------------------------------------------------------------------*
@main_bp.route('/')
@login_required
def dashboard():
    conn = db.db_connect()
    cursor = conn.cursor()

    active_encounters_by_station = {}
    synopsis = {'total': {}, 'stations': {}}

    for aid_station in Config.AID_STATIONS:

        # Active Encounters (have a start time and not an end time)
        cursor.execute('''SELECT * FROM encounters
                          WHERE ( time_out IS NULL OR time_out="")
                          AND aid_station=?
                          AND delete_flag != 1
                          ORDER BY time_in
                       ''', (aid_station,))
        active_encounters_by_station[aid_station] = cursor.fetchall()

        # Generate Synopsis data set
        synopsis['stations'][aid_station] = {}

        # All Encounters
        cursor.execute("SELECT COUNT(*) FROM encounters WHERE aid_station=? AND delete_flag !=1 ", (aid_station,))
        synopsis['stations'][aid_station]['encounters'] = cursor.fetchone()[0]

        # Active Encounters (have a start time and not an end time)
        cursor.execute('''SELECT COUNT(*) FROM encounters
                          WHERE time_in IS NOT NULL
                          AND ( time_out IS NULL OR time_out="")
                          AND aid_station=?
                          AND delete_flag <> 1
                       ''', (aid_station,))
        synopsis['stations'][aid_station]['active'] = cursor.fetchone()[0]

        # Closed Encounters Only (have an end time)
        cursor.execute('''SELECT COUNT(*) FROM encounters
                          WHERE time_out IS NOT NULL
                          AND time_out<>""
                          AND aid_station=?
                          AND delete_flag <> 1
                       ''', (aid_station,))
        synopsis['stations'][aid_station]['discharged'] = cursor.fetchone()[0]

        # Closed Encounters with Transport Only
        cursor.execute('''SELECT COUNT(*) FROM encounters
                        WHERE disposition IS NOT NULL
                          AND disposition like 'Transport%'
                          AND aid_station=?
                          AND delete_flag <> 1
                       ''', (aid_station,))
        synopsis['stations'][aid_station]['transported'] = cursor.fetchone()[0]


    # All encounter recoreds
    cursor.execute('''SELECT COUNT(*) FROM encounters
                      WHERE delete_flag <> 1
                   ''')
    synopsis['total']['encounters'] = cursor.fetchone()[0]

    # Active Encounters (have a start time and not an end time)
    cursor.execute('''SELECT COUNT(*) FROM encounters
                      WHERE time_in IS NOT NULL
                      AND ( time_out IS NULL OR time_out="")
                      AND delete_flag <> 1
                   ''')
    synopsis['total']['active'] = cursor.fetchone()[0]

    # Closed Encounters Only (have an end time)
    cursor.execute('''SELECT COUNT(*) FROM encounters
                      WHERE time_out IS NOT NULL
                      AND time_out<>""
                      AND delete_flag != 1
                   ''')
    synopsis['total']['discharged'] = cursor.fetchone()[0]

    
    # Closed Encounters with Transport Only
    cursor.execute('''SELECT COUNT(*) FROM encounters
                      WHERE disposition IS NOT NULL
                      AND disposition like 'Transport%'
                      AND delete_flag != 1
                   ''')
    synopsis['total']['transported'] = cursor.fetchone()[0]

    return render_template("dashboard.html", \
                           aid_stations=Config.AID_STATIONS, \
                           active_encounters=active_encounters_by_station, \
                           synopsis=synopsis, \
                           is_admin=current_user.is_admin, \
                           active_page='dashboard')


@main_bp.route('/encounters')
@login_required
def encounters():
    return render_template('encounters.html',
            base_api_path=internal_api_bp.url_prefix, \
            username=current_user.name, \
            aid_stations=Config.AID_STATIONS, \
            is_manager=current_user.is_manager, \
            is_admin=current_user.is_admin, \
            active_page='encounters')

@main_bp.route('/lookup')
@login_required
def lookup():
    return render_template('lookup.html',
            base_api_path=internal_api_bp.url_prefix, \
            username=current_user.name, \
            aid_stations=Config.AID_STATIONS, \
            is_manager=current_user.is_manager, \
            is_admin=current_user.is_admin, \
            active_page='lookup')


# *====================================================================*
#         Chat
# *====================================================================*
@chat_bp.route('/')
def chat():
    """Chat room. The user's name and room must be stored in
    the session."""
    assignment = current_user.name
    username = current_user.get_person()
    return render_template('chat.html', assignment=assignment, username=username, is_admin=current_user.is_admin, active_page='chat')



# *====================================================================*
#         ADMIN
# *====================================================================*
# Route for uploading xlsx file and removing all rows
@admin_bp.route('/', methods=['GET', 'POST'])
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

    return render_template('admin.html', is_admin=current_user.is_admin, active_page='admin')

# Save DataFrame to SQLite database
def save_to_database(df, table):
    with db.db_connect() as conn:
        df.to_sql(table, conn, if_exists='replace', index=False)

# Remove all rows from the table
def remove_all_rows(table):
    with db.db_connect() as conn:
        conn.execute(f'DELETE FROM {table}')

# Export SQLite table to xlsx file
def export_to_xlsx(table):
    with db.db_connect() as conn:
        df = pd.read_sql_query(f'SELECT * FROM {table}', conn)
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name=table)
    writer.close()
    output.seek(0)
    return send_file(output, download_name=f'{table}.xlsx', as_attachment=True)


# *====================================================================*
#         Internal API - available at /data
# *====================================================================*
@internal_api_bp.route('/participants/', methods=['GET'])
@login_required
def data_participants():
    data = db.zip_table("persons")
    return jsonify(data)


# Parse a transaction request
def parse_transaction(payload):
    known_actions = ['create', 'edit', 'remove']
    pattern = r'\[(\d+)\]\[([a-zA-Z_]+)\]'
    transaction_parts = {
        'data': {},
    }
    
    # Check if data is string, if so unpack to object
    if isinstance(payload, str):
        payload = json.loads(payload)

    # Validate the post request
    if 'action' not in payload:
        e_msg = "Encounter post submitted without action."
        print(e_msg, file=sys.stderr)
        return { 'error': e_msg}

    transaction_parts['action'] = payload['action'].lower()
    if transaction_parts['action'] not in known_actions:
        e_msg = f"Encounter post submitted with unknown action {action}."
        print(e_msg, file=sys.stderr)
        return { 'error': e_msg}

    for key in payload.keys():
        tokens = re.findall(r'\[(.*?)\]', key)
        if len(tokens) == 2:
            [transaction_parts['encounter_uuid'], field_key] = tokens
            transaction_parts['data'][field_key] = payload[key]

    return transaction_parts

def transact_create(user, data, uuid=None):
    try: 
        uuidObj = UUID(uuid, version=4)
    except ValueError:
        uuid  = str(uuid4())
    data['uuid'] = uuid
    data_keys = data.keys()
    query = f"INSERT INTO encounters ( {', '.join(data_keys) }) VALUES (:{', :'.join(data_keys)})"
    db.execute_query(query, data)
    new_data = db.zip_encounters(uuid=uuid)
    send_sio_msg('new_encounter', new_data)
    return {'encounter_uuid': uuid, 'data': new_data, 'user': user}

def transact_edit(user, data, uuid):
    data_cols = ', '.join([f"{key} = ?" for key in data.keys()])
    data_vals = list(data.values())

    query = f"UPDATE encounters SET {data_cols} WHERE uuid = '{uuid}'"
    db.execute_query(query, data_vals)
    new_data = db.zip_encounters(uuid=uuid)
    send_sio_msg('edit_encounter', new_data)
    return {'encounter_uuid': uuid, 'data': new_data, 'user': user}

def transact_delete(user, uuid):
    query = f"UPDATE encounters SET delete_flag=1 WHERE uuid='{uuid}'"
    db.execute_query(query)
    new_data = db.zip_encounters(uuid=uuid, include_deleted=True)
    send_sio_msg('remove_encounter', new_data)
    return {'encounter_uuid': uuid, 'data': new_data, 'user': user}


def transaction(payload, user="API", encounter_uuid=None, created_at=None):
    parts = parse_transaction(payload)

    # If we had an error parsing, just return that message
    if 'error' in parts:
        return parts

    # If we have an encounter UUID, lets use it
    if encounter_uuid is not None:
        parts['encounter_uuid'] = encounter_uuid

    # Handle Creating a new record
    if parts['action'] == 'create':
        ret_val = transact_create(user=user, data=parts['data'], uuid=parts['encounter_uuid'])

     # Handle Editing an existing record
    elif parts['action'] == 'edit':
        ret_val = transact_edit(user=user, data=parts['data'], uuid=parts['encounter_uuid'])

    # Handle removing 
    elif parts['action'] == 'remove':
       ret_val = transact_delete(user=user, uuid=parts['encounter_uuid'])

    jnew_data = json.dumps(ret_val['data'])
    db.log_encounter_audit(action=parts['action'], uuid=ret_val['encounter_uuid'], user_id=user, resultant_value=jnew_data)
    return ret_val


@internal_api_bp.route('/encounters', methods=['GET', 'POST'])
@internal_api_bp.route('/encounters/<aid_station>', methods=['GET', 'POST'])
@login_required
def data_encounters(aid_station=None):
    if aid_station is not None:
        aid_station = aid_station.replace("_", " ")
        aid_station = aid_station.replace("--", "/")

    if request.method == 'POST':
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        payload = json.dumps(request.form)

        data = transaction(payload=payload, user=current_user.user_stamp())
        encounter_uuid = data['encounter_uuid']
        user = data['user']

        transaction_id = db.log_transaction(encounter_uuid=encounter_uuid, user=user, data=payload, created_at=created_at, transaction_uuid=None, synced=0)
        notify_sync_new_record()
        return jsonify( data['data'] )
       
    # Handle Get Request
    if request.method == "GET":
        with db.db_connect() as conn:
            data = db.zip_encounters(aid_station=aid_station)
        return jsonify(data)

    return jsonify("Oh no, you should never be here...")



app.register_blueprint(auth_bp)
app.register_blueprint(internal_api_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(main_bp)
app.register_blueprint(api_bp)

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
@socketio.on('join', namespace='/chat')
def handle_join(data):
    room = data['room']
    join_room(room)
    previous_messages = db.get_chat_messages(room)
    emit('previous_messages', previous_messages, room=request.sid)

@socketio.on('send_message', namespace='/chat')
def handle_send_message(data):
    room = data['room']
    assignment = current_user.name
    username = current_user.get_person()
    content = data['message']
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


    db.add_chat_message(room=room, assignment=assignment, username=username, content=content, created_at=created_at)
    message = {
        "assignment": assignment,
        "username": username,
        "content": content,
        "created_at": created_at
    }

    emit('receive_message', message, room=room)

@socketio.on('send_message_public', namespace='/chat')
def handle_send_message_public(data):
    room = data['room']
    assignment = data['assignment']
    username =  data['username']
    content = data['message']
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


    db.add_chat_message(room=room, assignment=assignment, username=username, content=content, created_at=created_at)
    message = {
        "assignment": assignment,
        "username": username,
        "content": content,
        "created_at": created_at
    }

    emit('receive_message', message, room=room)

# *====================================================================*
#         SocketIO Server Sync Actions
# *====================================================================*

# Send out a single sync message to Room for sync id
def notify_sync_new_record(room='encounters'):
    message_type = 'sync_encounters'
    namespace = "/sync"

    previous_encounters = db.get_sync_transactions()

    if len(previous_encounters) > 0:
        if sync_mode == 'client':
            if remote_sio.connected:
                remote_sio.emit(message_type, previous_encounters, namespace=namespace)
        elif sync_mode == 'server':
            emit(message_type, previous_encounters, room=room, namespace=namespace)

# Add a transaction from a remote host
def add_sync_transaction(message):
    msg_type = "encounter_sync_confirmation"
    data = message['data']
    user = message['user']
    created_at = message['created_at']
    e_uuid = message['encounter_uuid']
    uuid = message['uuid']

    transaction_uuid = db.log_transaction(encounter_uuid=e_uuid, user=user, data=data, created_at=created_at, transaction_uuid=uuid, synced=2)
    if transaction_uuid is not None:
        transaction(payload=data, user=user, encounter_uuid=e_uuid, created_at=created_at)
    
    if sync_mode == 'client':
        if remote_sio.connected:
            remote_sio.emit(msg_type, {'id': transaction_uuid}, namespace="/sync")
    else:
        emit(msg_type, {'id': transaction_uuid}, room="encounters", namespace="/sync")


# *====================================================================*
#         SocketIO Server Sync Server
# *====================================================================*
@socketio.on('join', namespace='/sync')
def handle_sync_join(data):
    key = data['key']
    room = data['room']
    if key == Config.UPSTREAM_KEY:
        join_room(room)
        notify_sync_new_record(room=request.sid)

# Handle a request to sync multiple encounters
@socketio.on('sync_encounters', namespace='/sync')
def handle_sync_encounters(data):
    if Config.SYNC_ENABLED:
        for item in data:
            add_sync_transaction(item)

# Handle Encounter Sync Confirmation (set sync_status 2)
@socketio.on('encounter_sync_confirmation', namespace='/sync')
def handle_sync_confirmation(data):
    db.update_sync_status(log_id=data['id'], sync_status=2)
# *====================================================================*
#         SocketIO Server Sync Client
# *====================================================================*

def connect_to_remote_server():
    """Attempt to connect to the remote server with retry on failure."""
    while not remote_sio.connected:
        try:
            remote_sio.connect(Config.UPSTREAM_ENDPOINT, namespaces=["/sync"])
            print("Successfully connected to the remote Socket.IO server.", file=sys.stderr)
        except socketioClient.exceptions.ConnectionError as e:
            print(f"SYNC Client connection failed: {e}. Retrying in 60 seconds...", file=sys.stderr)
            time.sleep(60)  # Wait before retrying

@remote_sio.event(namespace="/sync")
def connect():
    data = {
        'key': Config.UPSTREAM_KEY,
        'room': 'encounters'
    }
    remote_sio.emit('join', data, namespace="/sync")
    notify_sync_new_record()

@remote_sio.event(namespace="/sync")
def disconnect():
    print("Disconnected from the remote Socket.IO server. Attempting to reconnect...")
    # Start reconnection attempts in a separate thread
    threading.Thread(target=connect_to_remote_server, daemon=True).start()

# Handle a request to sync multiple encounters
@remote_sio.on('sync_encounters', namespace='/sync')
def remote_handle_sync_encounters(data):
    if Config.SYNC_ENABLED:
        for encounter in data:
            add_sync_transaction(encounter)

# Handle Encounter Sync Confirmation (set sync_status 2)
@remote_sio.on('encounter_sync_confirmation', namespace='/sync')
def remote_handle_sync_confirmation(data):
    db.update_sync_status(log_id=data['id'], sync_status=2)

if sync_mode == 'client':
    # Connect initially to the remote server in a separate thread
    threading.Thread(target=connect_to_remote_server, daemon=True).start()



if __name__ == '__main__':
    # create_database()
    socketio.run(app, debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)

    
