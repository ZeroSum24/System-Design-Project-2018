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
import json
from threading import Lock
from time import sleep
from spam.thread_decorator import thread

import image_processing
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
battery_info_volts = 0
battery_info_volts_2= 0
# Delivery Status should assume one of these >> "State.DELIVERING", "State.RETURNING", "State.LOADING", "State.STOPPING", "State.PANICKING"
delivery_status = "State.LOADING"
location_info_lock = Lock()
location_info = "Nothing reported yet."
connection_status = False
connection_status_2 = False
path_planning_result = []
lock = Lock()
lock_2 = Lock()
current_slot = 1
seen = False
seen_2 = False
path_planning={}
go_button_pressed = False
# Definition of environment variable for Notifications
unseen_notifications=0
current_orientation = 0

def add_unseen_notification():
    global unseen_notifications
    unseen_notifications += 1
def get_unseen_notification():
    global unseen_notifications
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

@thread
def polling_loop():
    while True:
        sleep(7)
        with lock:
            global connection_status
            global seen
            connection_status = seen
            seen = False
polling_loop()

@thread
def polling_loop_2():
    while True:
        sleep(7)
        with lock_2:
            global connection_status_2
            global seen_2
            connection_status_2 = seen_2
            seen_2 = False
polling_loop_2()



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
            return redirect(url_for('automatic_mode'))

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
    global connection_status_2
    global battery_info_volts
    global battery_info_volts_2
    zero_unseen_notification()
    signal_to_solve = request.args.get('solve_id', default = -1, type = int)

    if signal_to_solve != -1:
        problem_to_solve = db.session.query(Problem).filter(Problem.id == signal_to_solve).one()
        problem_to_solve.solved = True
        db.session.commit()

    notifications= Problem.query.filter(Problem.solved == False).all()
    for notification in notifications:
        notification.origin = Staff.query.filter(Staff.id == notification.origin).one().name
    min_battery_level = min(battery_calculate(battery_info_volts), battery_calculate(battery_info_volts_2))
    return render_template('notifications.html',min_battery_level=min_battery_level, notifications=notifications,battery_level_2=battery_calculate(battery_info_volts_2) , battery_level=battery_calculate(battery_info_volts), connection_status=connection_status, connection_status_2=connection_status_2, unseen_notifications=get_unseen_notification())

@spam.route('/settings')
def settings():
    return redirect('/admin')

@spam.route('/auto_view', methods=['GET', 'POST'])
def automatic_mode():
    if request.method == 'GET':
        min_battery_level = min(battery_calculate(battery_info_volts), battery_calculate(battery_info_volts_2))
        return render_template('automode.html', min_battery_level=min_battery_level, desks=get_desks_list(), active="Mail Delivery", unseen_notifications=get_unseen_notification(), battery_level_2=battery_calculate(battery_info_volts_2), battery_level=battery_calculate(battery_info_volts), connection_status=connection_status, connection_status_2=connection_status_2, delivery_status=delivery_status)
    else:
        global path_planning_result, path_planning
        submit=[]

        try:
            print ("166")
            where_to = request.form.get('inputSlot5')
            print ("167")
            if( Location.query.filter(Location.id == where_to).one().map_node not in path_planning.keys()):
                print ("168")
                path_planning[Location.query.filter(Location.id == where_to).one().map_node]=[5]
            else:
                print ("169")
                path_planning[Location.query.filter(Location.id == where_to).one().map_node].append(5)
        except:
            # When nothing is selected
            print ("170")
            pass

        for node in path_planning.keys():
            submit.append(Location.query.filter(Location.map_node == node).one())

        #Use path planner
        print ("This is path planning:")
        print (path_planning)
        path_planning_result = router.build_route(path_planning)
        if connection_status and delivery_status == "State.LOADING":
            publish_path_planning(path_planning_result)

        min_battery_level = min(battery_calculate(battery_info_volts), battery_calculate(battery_info_volts_2))
        return render_template('echo_submit.html', min_battery_level=min_battery_level, submit=submit, desks=get_desks_list(), unseen_notifications=get_unseen_notification(), battery_level=battery_calculate(battery_info_volts), battery_level_2=battery_calculate(battery_info_volts_2), connection_status=connection_status, connection_status_2=connection_status_2)


@spam.route('/view', methods=['GET', 'POST'])
def mail_delivery():
    error = None
    global connection_status
    global connection_status_2
    global battery_info_volts
    global battery_info_volts_2
    global path_planning_result
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
        path_planning_result = router.build_route(path_planning)
        if connection_status and delivery_status == "State.LOADING":
            publish_path_planning(path_planning_result)

        min_battery_level = min(battery_calculate(battery_info_volts), battery_calculate(battery_info_volts_2))
        return render_template('echo_submit.html', min_battery_level=min_battery_level, submit=submit, desks=get_desks_list(), unseen_notifications=get_unseen_notification(), battery_level=battery_calculate(battery_info_volts), battery_level_2=battery_calculate(battery_info_volts_2), connection_status=connection_status, connection_status_2=connection_status_2)
    #else
    else:
        command = request.args.get('emergency_command', default = "", type = str)
        if command != "":
            if connection_status:
                mqtt.publish("emergency_command",command)
        min_battery_level = min(battery_calculate(battery_info_volts), battery_calculate(battery_info_volts_2))
        return render_template('recipients.html', min_battery_level=min_battery_level, active="Mail Delivery", error=error, desks=get_desks_list(), unseen_notifications=get_unseen_notification(), battery_level=battery_calculate(battery_info_volts), battery_level_2=battery_calculate(battery_info_volts_2), connection_status=connection_status, delivery_status=delivery_status, connection_status_2=connection_status_2)

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

@spam.route('/status')
def status():
    global connection_status
    global connection_status_2
    global location_info
    global battery_info_volts
    global battery_info_volts_2
    global delivery_status
    min_battery_level = min(battery_calculate(battery_info_volts), battery_calculate(battery_info_volts_2))
    return render_template('status.html', min_battery_level=min_battery_level, unseen_notifications=get_unseen_notification(), active="Status", battery_level=battery_calculate(battery_info_volts), battery_level_2=battery_calculate(battery_info_volts_2), connection_status=connection_status, location_info=location_info, delivery_status= delivery_status, connection_status_2=connection_status_2)

@mqtt.on_connect()
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("battery_info_volts")
    client.subscribe("location_info")
    client.subscribe("delivery_status")
    client.subscribe("problem")
    client.subscribe("request_route")
    client.subscribe("image_processing")
    client.subscribe("battery_info_volts_2")

#Receiving information from the robot.
@mqtt.on_message()
def on_message(client, userdata, msg):
    #This should recieve the message from the ev3 and from the status
    #page update the information for both location and battery regardless of
    #which one has changed
    print("Msg Recieved Cap")
    global path_planning_result, location_info, path_planning, current_slot, go_button_pressed
    if msg.topic == "location_info":
        with location_info_lock:
            location_info = msg.payload.decode()
            instruction_info = path_planning_result.pop(0)
            while instruction_info[0] != "Report":
                instruction_info = path_planning_result.pop(0)
            print("HERE")
            print(location_info)
            print(instruction_info)
        print("location_info updated")
    elif msg.topic == "battery_info_volts":
        global seen
        with lock:
            seen = True
        global battery_info_volts
        battery_info_volts = float(msg.payload.decode())
        print("battery_info_volts updated")
    elif msg.topic == "battery_info_volts_2":
        global seen_2
        with lock:
            seen_2 = True
        global battery_info_volts_2
        battery_info_volts_2 = float(msg.payload.decode())
        print("battery_info_volts_2 updated")
    elif msg.topic == "delivery_status":
        global delivery_status
        delivery_status = msg.payload.decode()
        if delivery_status == "State.RETURNING":
            print("Returning")
        elif delivery_status == "State.LOADING":
            current_slot = 1
            print("Loading")
        elif delivery_status != "State.LOADING":
            path_planning = {}
            print("Path Planning reset")
        print("delivery_status updated")
    elif msg.topic == "problem":
        add_unseen_notification()
        problem = Problem(origin=Staff.query.filter(Staff.email == "robot@spam.com").one().id, message=msg.payload.decode(), is_urgent=True)
        db.session.add(problem)
        db.session.commit()
        print("Problem reported by robot.")
    elif msg.topic == "request_route":
        print("Requested Route")
        with location_info_lock:
            print("Received Location:")
            print(msg.payload.decode())
            path_planning_result = router.return_from(*(msg.payload.decode().split('-')))
            print(path_planning_result)
            publish_path_planning(path_planning_result)
    elif msg.topic == "image_processing":
        print("Image Recieved")

        #put recieved bytearray back onto disk and read as image
        #TODO look into whether image on ev3 can be saved as a png
        if (delivery_status != "State.LOADING"):
            return

        image_location = 'image_recieved.jpg'
        msg_handle = open(image_location, 'wb')
        msg_handle.write(msg.payload)
        msg_handle.close()

        # image = pickle.loads(msg.payload)
        # qr_code = image_processing.scanImage(image)
        desk_from_image = 0
        qr_code = image_processing.scanImage(image_location)

        # if qr_code != "None":                 #Checks qr_code has been registered
        if qr_code != "[]":
            #pyzbar - for output: no (zbarlight ) None == [] ; yes (zbarlight [b'2'] == [Decoded(data=b'2', type='QRCODE')])
            # yes -- the qr_code is right
            # desk_from_image = int(qr_code[3]) # [b'2']  -- expected output example
            desk_from_image = int(qr_code[16])
            print("Type: " + qr_code[24:])
            print('QR codes: %s' % qr_code)

            # Input checking that the QR is not a desk we can't handle
            amount_of_desks = len(get_desks_list())
            if (desk_from_image < 1 or desk_from_image > amount_of_desks):

                print("Error incorrect desk allocation - wrong number from QR Code")
                client.publish("image_result", "False")
            else:
                # Adds the location to path planning, looks up the unique id of person in the database

                location_read = Staff.query.filter(Staff.id == desk_from_image).one().location_id
                map_node_of_location = Location.query.filter(Location.id == location_read).one().map_node
                if (map_node_of_location not in path_planning.keys()):
                    path_planning[Location.query.filter(Location.id == location_read).one().map_node]=[current_slot]
                else:
                    path_planning[Location.query.filter(Location.id == location_read).one().map_node].append(current_slot)

                print ("This is path planning:")
                print (path_planning)


                if (go_button_pressed == False):
                    current_slot += 1
                    client.publish("image_result", str(current_slot))

                    if (current_slot > 4):
                        print("Slots have all been filled")
                else:
                    return
        else:                                    # no -- no qr_code so get new photo
            print('QR codes: %s' % qr_code)

            if (go_button_pressed == False): # Breaks the communication between robot and server
                client.publish("image_result", "False")
            else:
                return
        # TODO need to include UI feedback for the path_planning being empty and the Go_button being pressed


@mqtt.on_log()
def handle_logging(client, userdata, level, buf):
    print(level, buf)

#Functions that send image_processing commands to the robot
def path_planning_go_button():
    #Once Go Button is pressed sends path planning off

    go_button_pressed = False
    path_planning_result = router.build_route(path_planning)
    if connection_status and delivery_status == "State.LOADING":
        publish_path_planning(path_planning_result)
    min_battery_level = min(battery_calculate(battery_info_volts), battery_calculate(battery_info_volts_2))
    return render_template('echo_submit.html', min_battery_level=min_battery_level, submit=submit, desks=get_desks_list(), unseen_notifications=get_unseen_notification(), battery_level=battery_calculate(battery_info_volts), battery_level_2=battery_calculate(battery_info_volts_2), connection_status=connection_status, connection_status_2=connection_status_2)

@spam.route('/reset_button')
def reset_button():
    #Once button is pressed sends a command moving the slot over one place and to dump each slot already loaded
    client.publish("shift_slot", str(current_slot))

#Functions that send information to the robot
def publish_path_planning(path_direction):
    path_direction = json.dumps(path_direction)
    mqtt.publish("path_direction", path_direction)
    print(path_direction)

def publish_emergency_commands(emergency_command):
    mqtt.publish("emergency_command", emergency_command)
    print(emergency_command)
    global path_planning_result
    if emergency_command == 'Callback':
        with location_info_lock:
            global location_info
            instruction = path_planning_result.pop(0)
            while instruction[0] != 'Report':
                instruction = path_planning_result.pop(0)
            location_info = instruction[1]
            print("HERE")
            print(location_info)
            print(instruction)

# Function that produces a list of Desk names by going into the database.
def get_desks_list():
    desks=[]
    for location in Location.query.all():
        if location.is_desk:
            desks.append(location)
    return desks

def battery_calculate(voltage_reading):
    max_volt = 9000000
    min_volt = 6500000
    if max_volt > voltage_reading > min_volt:
        percent = (voltage_reading - min_volt) / (max_volt - min_volt) * 100
    elif voltage_reading >= max_volt:
        percent = 100
    else:
        percent = 0
    return int(percent)
