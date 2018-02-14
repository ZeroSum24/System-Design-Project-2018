# all the imports
import os
from spam import spam
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
import socket
from sys import argv
from flask_sqlalchemy import SQLAlchemy
from spam.database import db_session
from spam.database import init_db
from spam.models import Staff, Location, Problem

# spam = Flask(__name__) # create the spamlication instance :)
# #spam.config.from_pyfile('spam.cfg') # load config from this file , spam.py
# # got rid of envar override because yolo
# spam.config.from_object(__name__) # load config from this file , spam.py
#
# # Load default config and override config from an environment variable
# spam.config.update(dict(
#     EMAIL='admin@admin.com',
#     PASSWORD='default',
#     SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/test.db',
#     SQLALCHEMY_ECHO = False,
#     SECRET_KEY = '\xfb\x12\xdf\xa1@i\xd6>V\xc0\xbb\x8fp\x16#Z\x0b\x81\xeb\x16',
#     DEBUG = True
# ))
# spam.config.from_envvar('SPAM_SETTINGS', silent=True)
db = SQLAlchemy(spam)

#database functions
# def connect_db():
#     """Connects to the specific database."""
#     rv = sqlite3.connect(spam.config['DATABASE'])
#     rv.row_factory = sqlite3.Row
#     return rv

#this cli contexct is for the flask shell
@spam.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')
#g is a is a general purpose variable associated with the current spamlication context.
# def get_db():
#     """Opens a new database connection if there is none yet for the
#     current spamlication context.
#     """
#     if not hasattr(g, 'sqlite_db'):
#         g.sqlite_db = connect_db()
#     return g.sqlite_db


@spam.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()



@spam.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['inputEmail'] != spam.config['EMAIL']:
            error = 'Invalid email'
        elif request.form['inputPassword'] != spam.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('mail_delivery'))

    #else
    return render_template('login.html', error=error)

@spam.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))

#TODO: match these up with index.html
@spam.route('/view', methods=['GET', 'POST'])
def mail_delivery():
    error = None

    desks=[]
    for location in Location.query.all():
        desks.append(location.location_name)

    if request.method == 'POST':
        # for u,a in db_session.query(Staff.name, Location.physical).filter(Staff.id==Location.staff_id).all():
        #     l.append(u)
        #     l.append(a)
        return render_template('echo_submit.html', submit=submit, desks=get_desks_list())
    #else
    return render_template('recipients.html', error=error, desks=get_desks_list())

@spam.route('/report')
def report():
    return render_template('report.html', desks=get_desks_list())

@spam.route('/test')
def test():
    from spam.database import db_session
    from spam.models import User
    u = User('admin', 'admin@localhost')
    db_session.add(u)
    db_session.commit()



#TODO: need database editing thingymijig
        #technically extension, but hey, once I get the db working it'll be fine
#<a class="nav-link" href="#">Status</a>
#<a class="nav-link" href="#">Settings</a>
#<a class="nav-link" href="#">Help</a>
#<a class="nav-link" href="#">Logout</a>

#TODO: get a bluetooth connection cycle going - probably
    #<span class="badge badge-pill badge-success">Robot Connected</span>
#TODO: get external post requests working
@spam.route('/slots', methods=['GET', 'POST'])
def receive_http():
    error=None
    if request.method == 'POST':
        return render_template('login.html', error=error)
    #else
    return render_template('login.html', error=error)

# Function that produces a list of Desk names by going into the database.
def get_desks_list():
    desks=[]
    for location in Location.query.all():
        if location.is_desk:
            desks.append(location.location_name)
    return desks
