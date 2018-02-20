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
import pickle

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
db = SQLAlchemy(spam)

# GLOBAL VARIABLES
battery_info_volts = 40
# Delivery Status should assume one of these >> "Delivering", "Returning", "Parked", "Interrupted"
delivery_status = "Delivering"
location_info = "Going from C to D"
connection_status = False
path_planning_result = []
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
    global connection_status
    global battery_info_volts
    zero_unseen_notification()
    signal_to_solve = request.args.get('solve_id', default = -1, type = int)

    if signal_to_solve != -1:
        problem_to_solve = db.session.query(Problem).filter(Problem.id == signal_to_solve).one()
        problem_to_solve.solved = True
        db.session.commit()

    notifications= Problem.query.filter(Problem.solved == False).all()
    for notification in notifications:
        notification.origin = Staff.query.filter(Staff.id == notification.origin).one().name
    return render_template('notifications.html', notifications=notifications, battery_level=battery_calculate(battery_info_volts), connection_status=connection_status)

@spam.route('/settings')
def settings():
    return redirect('/admin')

#TODO: match these up with index.html
@spam.route('/view', methods=['GET', 'POST'])
def mail_delivery():
    error = None
    global connection_status
    global battery_info_volts
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
        publish_path_planning(router.build_route(path_planning))

        return render_template('echo_submit.html', submit=submit, desks=get_desks_list(), unseen_notifications=get_unseen_notification(), battery_level=battery_calculate(battery_info_volts), connection_status=connection_status)
    #else
    return render_template('recipients.html', error=error, desks=get_desks_list(), unseen_notifications=get_unseen_notification(), battery_level=battery_calculate(battery_info_volts), connection_status=connection_status)

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
    global connection_status
    global location_info
    global battery_info_volts
    global delivery_status
    return render_template('status.html', battery_level=battery_calculate(battery_info_volts), connection_status=connection_status, location_info=location_info, delivery_status= delivery_status)

@mqtt.on_connect()
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("connection_status")
    client.subscribe("battery_info_volts")
    client.subscribe("location_info")
    client.subscribe("delivery_status")
    client.subscribe("problem")


#Receiving information from the robot.
@mqtt.on_message()
def on_message(client, userdata, msg):
    #This should recieve the message from the ev3 and from the status
    #page update the information for both location and battery regardless of
    #which one has changed
    print("Msg Recieved Cap")
    if msg.topic == "connection_status":
    #Msg is published to the UI to establish ev3 connection has been brokered
        global connection_status
        connection_status = True
        print("Connected -- Woap Woap")
    elif msg.topic == "location_info":
        global location_info
        location_info = msg.payload.decode()
        print("location_info updated")
    elif msg.topic == "battery_info_volts":
        global battery_info_volts
        battery_info_volts = float(msg.payload.decode())
        print("battery_info_volts updated")
    elif msg.topic == "delivery_status":
        global delivery_status
        delivery_status = msg.payload.decode()
        print("delivery_status updated")
    elif msg.topic == "problem":
        add_unseen_notification()
        problem = Problem(origin=Staff.query.filter(Staff.email == "robot@spam.com").one().id, message=msg.payload.decode(), is_urgent=True)
        db.session.add(problem)
        db.session.commit()
        print("Problem reported by robot.")

def database_map_nodes_lookup():
    # looks up the map nodes from the databse and adds in the map nodes from
    # the database. Poll the database for these map nodes

    #add look-up part
    map_nodes = []
    return build_route(map_nodes)

@mqtt.on_log()
def handle_logging(client, userdata, level, buf):
    print(level, buf)

#Functions that send information to the robot
def publish_path_planning(path_direction):
    path_direction = pickle.dumps(path_direction)
    mqtt.publish("path_direction", path_direction)
    print(path_direction)

def publish_emergency_commands(emergency_command):
    mqtt.publish("emergency_command", emergency_command)
    print(emergency_command)


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

def battery_calculate(voltage_level):
    return int(voltage_level)
