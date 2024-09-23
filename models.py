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


import os
import sqlite3
import sys
from datetime import datetime

class Db:
    _db_path = ""

    def __init__(self, db_path = None):
        if db_path is not None:
            self._db_path = db_path
            self.make_db_path()
            self.create_database()


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
    def log_encounter_audit(self, action, record_id, user_id, resultant_value):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self.db_connect() as conn:
                cursor = conn.cursor()
                query = f"INSERT INTO encounters_audit_log (action, record_id, timestamp, user_id,  resultant_value) VALUES ('{action}', '{record_id}', '{user_id}', '{timestamp}', '{resultant_value}' )"
                cursor.execute(query)
                conn.commit()
        except sqlite3.Error as e:
            print(f"Database error writing audit log: {e}", file=sys.stderr)

    # Function to export data as a zipped dict
    def zip_encounters(self, id=None, aid_station=None, include_deleted=False, only_deleted=False):
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