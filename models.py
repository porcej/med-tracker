#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCM - Medical Tracker API

Tools to interact with Sierra Wireless's AirlinkOS API.

This module provides an OpenAPI compliant API for the MCM Medical Tracker App
"""

__author__ = "Joe Porcelli"
__copyright__ = "Copyright 2024, Joe Porcelli"
__license__ = "MIT"
__version__ = "0.0.1"
__email__ = "porcej@gmail.com"
__status__ = "Development"


import json
import os
import sqlite3
import sys
from datetime import datetime
from uuid import uuid4

class Db:
    _db_path = ""

    def __init__(self, db_path = None):
        if db_path is not None:
            self._db_path = db_path
            self.make_db_path()
            self.create_database()

    def add_db(self, db_path=None):
        self._db_path = db_path


    # *====================================================================*
    #         INITIALIZE DB & DB access
    # *====================================================================*
    def make_db_path(self):
        db_path = os.path.dirname(self._db_path)
        if db_path:
            os.makedirs(db_path, exist_ok=True)

    # Function to connect to SQLLite Database
    def db_connect(self):
        try:
            conn = sqlite3.connect(self._db_path)
            return conn
        except sqlite3.Error as e:
            print(f"Database error: {e}", file=sys.stderr)
            return None


    # Function to create an SQLite database and table to store data
    def create_database(self):
        with self.db_connect() as conn:
            cursor = conn.cursor()

            # Encounters Table - Holds a list of all encounters
            cursor.execute('''CREATE TABLE IF NOT EXISTS encounters (
                              id INTEGER PRIMARY KEY AUTOINCREMENT,
                              uuid TEXT UNIQUE NOT NULL,
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
                              delete_flag INTEGER DEFAULT 0,
                              delete_reason TEXT,
                              critical_flag INTEGER DEFAULT 0,
                              num_encounters INTEGER DEFAULT 1
                           )''')

            cursor.execute('''SELECT COUNT(*) AS CNTREC FROM pragma_table_info('encounters') WHERE name='uuid' ''')
            if cursor.fetchall()[0][0] == 0:
                print("Updating encounters table... adding UUID", file=sys.stderr)
                cursor.execute('''ALTER TABLE encounters ADD uuid TEXT UNIQUE NOT NULL ''')

            cursor.execute('''SELECT COUNT(*) AS CNTREC FROM pragma_table_info('encounters') WHERE name='delete_flag' ''')
            if cursor.fetchall()[0][0] == 0:
                print("Updating encounters table... adding delete flag", file=sys.stderr)
                cursor.execute('''ALTER TABLE encounters ADD delete_flag INTEGER DEFAULT 0 ''')
                cursor.execute('''ALTER TABLE encounters ADD delete_reason TEXT DEFAULT '' ''')

            cursor.execute('''SELECT COUNT(*) AS CNTREC FROM pragma_table_info('encounters') WHERE name='critical_flag' ''')
            if cursor.fetchall()[0][0] == 0:
                print("Updating encounters table... adding critical_flag", file=sys.stderr)
                cursor.execute('''ALTER TABLE encounters ADD critical_flag INTEGER DEFAULT 0 ''')

            cursor.execute('''SELECT COUNT(*) AS CNTREC FROM pragma_table_info('encounters') WHERE name='num_encounters' ''')
            if cursor.fetchall()[0][0] == 0:
                print("Updating encounters table... adding num_encounters", file=sys.stderr)
                cursor.execute('''ALTER TABLE encounters ADD num_encounters INTEGER DEFAULT 0 ''')


                # Encounters Table - Holds a list of all encounters
            cursor.execute('''CREATE TABLE IF NOT EXISTS encounters_audit_log (
                              id INTEGER PRIMARY KEY AUTOINCREMENT,
                              uuid TEXT NOT NULL,
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

            cursor.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
                              id INTEGER PRIMARY KEY AUTOINCREMENT,
                              room TEXT NOT NULL,
                              assignment TEXT NOT NULL,
                              username TEXT NOT NULL,
                              content TEXT NOT NULL DEFAULT ' ',
                              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                           )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS encounter_transactions (
                              id INTEGER PRIMARY KEY AUTOINCREMENT,
                              uuid TEXT UNIQUE NOT NULL,
                              encounter_uuid TEXT NOT NULL,
                              user TEXT NOT NULL DEFAULT 'API',
                              data TEXT,
                              synced INTEGER DEFAULT 0,
                              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                           )''')

            print("Database created!", file=sys.stderr)
            conn.commit()

    # Function to log server sync

    def log_transaction(self, encounter_uuid, user, data, created_at, transaction_uuid=None, synced=0):
        table_name = "encounter_transactions"

        if transaction_uuid is None:
            transaction_uuid = str(uuid4())

        if not isinstance(data, str):
            data = json.dumps(data)
        
        query = f"INSERT INTO {table_name} (uuid, encounter_uuid, user, data, synced, created_at) VALUES (?, ?, ?, ?, ?, ?)"

        try:
            with self.db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (transaction_uuid, encounter_uuid, user, data, synced, created_at))
                conn.commit()
                return transaction_uuid
        except sqlite3.Error as e:
            print(f"Database error recording transaction {query}: {e}", file=sys.stderr)
            return None

    # Check if we have this update
    def check_if_synced(self, uuid):
        table_name = 'encounter_transactions'
        query = f"SELECT uuid FROM {table_name} WHERE uuid ='{uuid}'"
        try:
            with self.db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                data = cursor.fetchall()
                if len(data) > 0:
                    return True
                else:
                    return False
        except sqlite3.Error as e:
            print(f"Database error checking if synced {query}: {e}", file=sys.stderr)
            return False

    # Function to update sync status
    def update_sync_status(self, log_id, sync_status):
        table_name = 'encounter_transactions'
        query = f"UPDATE {table_name} SET synced = {sync_status} WHERE uuid = '{log_id}'"
        try:
            with self.db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                conn.commit()
        except sqlite3.Error as e:
            print(f'Database error updating sync status "{query}": {e}', file=sys.stderr)
            return None

    # Function to return all chat messages in a chatroom
    def get_sync_transactions(self, unsynced_only=True):
        table_name = 'encounter_transactions'

        if unsynced_only:
            query = f"SELECT * FROM {table_name} WHERE synced = 0 ORDER BY created_at"
        else:
            query = f"SELECT * FROM {table_name} ORDER BY created_at"

        try:
            
            with self.db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                # Get the column names
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [column[1] for column in cursor.fetchall()]
                data_list = []
            for row in rows:
                data_dict = dict(zip(columns, row))
                data_list.append(data_dict)
            return data_list
        except sqlite3.Error as e:
            print(f"Database error getting transaction to sync {query}: {e}", file=sys.stderr)
            return None

    # Function to return all chat messages in a chatroom
    def get_chat_messages(self, room):
        table_name = 'chat_messages'
        try:
            query = f"SELECT * FROM {table_name} WHERE room = ? ORDER BY created_at"
            with self.db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (room,))
                rows = cursor.fetchall()
                # Get the column names
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [column[1] for column in cursor.fetchall()]
                data_list = []
            for row in rows:
                data_dict = dict(zip(columns, row))
                data_list.append(data_dict)
            return data_list
        except sqlite3.Error as e:
            print(f"Database error reading messages for {room}: {e}", file=sys.stderr)
            return None

    # Adds a chat message to the db
    def add_chat_message(self, room, assignment, username, content, created_at):
        query = f"INSERT INTO chat_messages (room, assignment, username, content, created_at) VALUES ('{room}', '{assignment}', '{username}', '{content}', '{created_at}')"
        try:
            with self.db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                conn.commit()

        except sqlite3.Error as e:
            print(f"Database error executing query {query}: {e}", file=sys.stderr)
            return None

    # Function to execute query and return the last row ID after executing seaid query
    def execute_query(self, query, values=None):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self.db_connect() as conn:
                cursor = conn.cursor()
                if values is None:
                    cursor.execute(query)
                else:
                    cursor.execute(query, values)
                id = cursor.lastrowid
                conn.commit()
                return id
        except sqlite3.Error as e:
            print(f"Database error executing query {query}: {e}", file=sys.stderr)
            return None


    # Function to log audit transactions
    def log_encounter_audit(self, action, uuid, user_id, resultant_value):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self.db_connect() as conn:
                cursor = conn.cursor()
                query = f"INSERT INTO encounters_audit_log (action, uuid, user_id, timestamp, resultant_value) VALUES (?, ?, ?, ?, ?)"
                values = (action, uuid, user_id, timestamp, resultant_value)
                cursor.execute(query, values)
                conn.commit()
        except sqlite3.Error as e:
            print(f"Database error writing audit log -{query}: {e}", file=sys.stderr)

    # Function to export data as a zipped dict
    def zip_encounters(self, id=None, uuid=None, aid_station=None, include_deleted=False, only_deleted=False):
        where_clauses = []
        if id is not None:
            where_clauses.append(f'ID={id}')
        if uuid is not None:
            where_clauses.append(f"uuid='{uuid}'")
        if aid_station is not None:
            where_clauses.append(f"aid_station='{aid_station}'")
        if include_deleted is False:
            where_clauses.append('delete_flag!=1')
        if only_deleted:
            where_clauses.append('delete_flag=1')

        where_clause = ' AND '.join(where_clauses)

        data = self.zip_table(table_name='encounters', where_clause=where_clause)
        return data


    # Function to export data as a zipped dict
    def zip_vitals(self, encounter_id=None, id=None):
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

        data = self.zip_table(table_name='vitals', where_clause=where_clause)
        return data


    # Function to export participant data as a zipped dict
    def zip_table(self, table_name, where_clause=None):
        if where_clause is None:
            where_clause = ""

        if len(where_clause) > 0:
            where_clause = f' WHERE {where_clause}'
        with self.db_connect() as conn:
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