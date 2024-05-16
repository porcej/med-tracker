#!/usr/bin/env python
# -*- coding: ascii -*-

"""
Configureation File for APP

Changelog:
    - 2024-05-15 - Initial Commit

"""

import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'this is a secret key that you will never guess'

    # Database Stuff
    DATABASE_PATH = os.environ.get('DATABASE_URL') or 'db/data.db'

    # Admin Account
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or ''
    ADMIN_PASSWORD = os.environ.get('USER_PASSWORD') or ''

     # Users 
    USERS = [
        {
            'username': 'Aid S/F'
            'password': '',
            'role': 'user'
        },
        {
            'username': 'Aid 1',
            'password': '',
            'role': 'user'
        }, 
        {
            'username': 'Aid 2',
            'password': '',
            'role': 'user'
        }, 
        {
            'username': 'Aid 3',
            'password': '',
            'role': 'user'
        }, 
        {
            'username': 'Aid 4',
            'password': '',
            'role': 'user'
        },
        {
            'username': 'Med Tracking',
            'password': 'SomeManagerPassword',
            'role': 'manager'
        },
        {
            'username': 'admin',
            'password': 'RealHardToGuessAdminPassword',
            'role': 'admin'
        }
    ]
    USER_PASSWORD = os.environ.get('USER_PASSWORD') or ''


    # Threading stuff
    # Set this variable to "threading", "eventlet" or "gevent" to specify
    # different async modes, or leave it set to None for the application to choose
    # the best option based on installed packages.
    ASYNC_MODE = os.environ.get('ASYNC_MODE') or None

    # Web UI and general app Stuff
    if (os.environ.get('MED_TRACKER_DEBUG') in ['True', 'TRUE', 'true', '1']):
        DEBUG = True
    else:
        DEBUG = False

    HOST = os.environ.get('MED_TRACKER_HOST') or '0.0.0.0'

    PORT = int(os.environ.get('MED_TRACKER_PORT') or 8080)


    LOGGING_PATH = os.environ.get('LOGGING_PATH') or 'log'

    # Logging Levels:
    #
    # Log Level     | Use Value
    # --------------+-----------
    # CRITICAL      | 50
    # ERROR         | 40
    # WARNING       | 30
    # INFO          | 20
    # DEBUG         | 10
    # VERBOSE       | 1
    # NOTSET        | 0

    LOGGING_LEVEL = os.environ.get('LOGGING_LEVEL') or 1   # VERBOSE