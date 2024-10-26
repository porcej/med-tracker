#!/usr/bin/env python
# -*- coding: ascii -*-

"""
App to allow access to 

Changelog:
    - 2024-10-26 - Initial Commit

"""

__author__ = "Joseph Porcelli (porcej@gmail.com)"
__version__ = "0.0.5"
__copyright__ = "Copyright (c) 2024 Joseph Porcelli"
__license__ = "MIT"


from flask import Flask, render_template, request, session, redirect, url_for, flash
from config import Config



# Initialize Flask app
app = Flask(__name__)

app.config.from_object(Config)


# *--------------------------------------------------------------------*
#         Authentication & User Management
# *--------------------------------------------------------------------*
@app.route("/", methods=["GET", "POST"])
def index():
    # try:
        # If a post request was made, find the user by 
        # filtering for the username
    if request.method == "POST":
        assignment = request.form.get('assignment')
        username = request.form.get('username')
        if assignment in Config.USER_ACCOUNTS.keys():
            session['assignment'] = assignment
            session['username'] = username
            return redirect(url_for('chat'))
        flash('Invalid assignment or name', 'error')

    return render_template("pub_chat_index.html", assignments=Config.USER_ACCOUNTS.keys())
    # except Exception as e:
    #     flash('An unexpected error occurred.', 'error')


@app.route("/chat")
def chat():
    if ('username' not in session) or ('assignment' not in session):
        return redirect(url_for('index'))
    return render_template('pub_chat.html', username=session['username'], assignment=session['assignment'], server_port=Config.PORT)

@app.route("/logout")
def end_session():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # create_database()
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.CHAT_PORT)

    
