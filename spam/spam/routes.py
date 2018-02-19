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
from spam import router
from flask_mqtt import Mqtt
#spam = Flask(__name__) # create the spamlication instance :)
#spam.config.from_pyfile('spam.cfg') # load config from this file , spam.py
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

mqtt = Mqtt(spam)
battery_info = 0
location_info = "Loading Bay"
connection_status = False
path_planning = []

db = SQLAlchemy(spam)

# Definition of environment variable for Notifications
unseen_notifications=0

def add_unseen_notification():
    global unseen_notifications
    unseen_notifications += 1
def get_unseen_notification():
    return unseen_notifications
def zero_unseen_notification():
    global unseen_notifications
    unseen_notifications = 0

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
    zero_unseen_notification()
    signal_to_solve = request.args.get('solve_id', default = -1, type = int)

    if signal_to_solve != -1:
        problem_to_solve = db.session.query(Problem).filter(Problem.id == signal_to_solve).one()
        problem_to_solve.solved = True
        db.session.commit()

    notifications= Problem.query.filter(Problem.solved == False).all()
    for notification in notifications:
        notification.origin = Staff.query.filter(Staff.id == notification.origin).one().name
    return render_template('notifications.html', notifications=notifications)

@spam.route('/settings')
def settings():
    return redirect('/admin')

#TODO: match these up with index.html
@spam.route('/view', methods=['GET', 'POST'])
def mail_delivery():
    error = None
    if request.method == 'POST':
        submit=[]
        path_planning={}
        for i in range(1,6):
            try:
                where_to = request.form.get('inputSlot'+str(i))
                if( Location.query.filter(Location.id == where_to).one().map_node not in path_planning.keys()):
                    path_planning[Location.query.filter(Location.id == where_to).one().map_node]=[i]
                else:
                    path_planning[Location.query.filter(Location.id == where_to).one().map_node].append(i)

                submit.append(Location.query.filter(Location.id == where_to).one())
            except:
                # When nothing is selected
                pass
        #Use path planner
        print ("This is path planning:")
        print (path_planning)
        print(router.build_route(path_planning))

        return render_template('echo_submit.html', submit=submit, desks=get_desks_list(), unseen_notifications=get_unseen_notification())
    #else
    return render_template('recipients.html', error=error, desks=get_desks_list(), unseen_notifications=get_unseen_notification())

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
      add_unseen_notification()
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

@spam.route('/status')
def status():
    return render_template('status.html')

@mqtt.on_connect()
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("topic/connection_established")
    client.subscribe("topic/battery")
    client.subscribe("topic/location")

@mqtt.on_message()
def on_message(client, userdata, msg):
    #This should recieve the message from the ev3 and from the status
    #page update the information for both location and battery regardless of
    #which one has changed
    print("Msg Recieved Cap")
    if msg.topic == "connection_established":
    #Msg is published to the UI to establish ev3 connection has been brokered
        connection_status = True
        print("Connected -- Woap Woap")
    elif msg.topic == "location":
        location_info = msg.decode()
    elif msg.topic == "battery":
        battery_info = msg.decode()
    return render_template('echo_ev3.html', ev3_info=[connection_status, location_info, battery_info])

def database_map_nodes_lookup():
    # looks up the map nodes from the databse and adds in the map nodes from
    # the database. Poll the database for these map nodes

    #add look-up part
    map_nodes = []
    return build_route(map_nodes)

@mqtt.on_log()
def handle_logging(client, userdata, level, buf):
    print(level, buf)

def publish_path_planning(path_str):
    mqtt.publish("path_directions", path_str)

def publish_emergency_commands(emrg_cmd_str):
    mqtt.publish("emergency_commands", emrg_cmd_str)


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
            desks.append(location)
    return desks
