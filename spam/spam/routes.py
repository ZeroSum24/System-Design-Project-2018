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
from spam import db
from spam.models import Staff, Location, Problem

# Definition of environment variable for Notifications
UNSEEN_NOTIFICATIONS=0

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


@spam.route('/notifications')
def notifications():
    UNSEEN_NOTIFICATIONS = 0
    return render_template('notifications.html')

@spam.route('/settings')
def settings():
    return redirect('/admin')

#TODO: match these up with index.html
@spam.route('/view', methods=['GET', 'POST'])
def mail_delivery():
    error = None
    if request.method == 'POST':
        # for u,a in db_session.query(Staff.name, Location.physical).filter(Staff.id==Location.staff_id).all():
        #     l.append(u)
        #     l.append(a)
        return render_template('echo_submit.html', submit=submit, desks=get_desks_list(), unseen_notifications=UNSEEN_NOTIFICATIONS)
    #else
    return render_template('recipients.html', error=error, desks=get_desks_list(), unseen_notifications=UNSEEN_NOTIFICATIONS)

@spam.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
      try:
        origin= Staff.query.filter_by(email = request.form['email_problem']).one()
      except:
        return render_template("report.html",desks=get_desks_list(), result=-1)
      problem = Problem(origin=origin.id, message=request.form['description_problem'])
      db.session.add(problem)
      db.session.commit()
      UNSEEN_NOTIFICATIONS += 1
      return render_template("report.html",desks=get_desks_list(), result=1)
    else:
      return render_template('report.html', desks=get_desks_list(), result=0)

@spam.route('/test')
def test():
    from spam.database import db_session
    from spam.models import Staff, Location, Problem

    l1 = Location(map_node='A', location_name='Desk Apple', is_desk=True)
    l2 = Location(map_node='B', location_name='Desk Bumblebee', is_desk=True)
    l3 = Location(map_node='C', location_name='Junction A', is_desk=False)

    u1 = Staff('Administrator', 'admin@localhost.com')
    u2 = Staff('Joao Catarino', 'joao@somewhere.com', 1)
    u3 = Staff('Rosina', 'roz@thisorthat.com', 2)

    p1 = Problem(origin=2, message="My mail didn't arrive please solve it.")
    p2 = Problem(origin=1, message="Robot is out of lines.", is_urgent=True)

    db_session.add(l1)
    db_session.add(l2)
    db_session.add(l3)
    db_session.commit()

    db_session.add(u1)
    db_session.add(u2)
    db_session.add(u3)
    db_session.commit()

    db_session.add(p1)
    db_session.add(p2)
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
