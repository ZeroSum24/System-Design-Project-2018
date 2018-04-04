# All the imports needed
from spam import spam
from flask import request, session, redirect, url_for, \
     render_template, flash
from flask_sqlalchemy import SQLAlchemy
from spam.database import db_session
from spam.database import init_db
from spam import db
from spam.models import Staff, Location, Problem
from spam import router
from flask_mqtt import Mqtt
import json
from threading import Lock, Timer
from time import sleep, time
from spam.thread_decorator import thread
from spam import socketio, mail
import image_processing
from spam import assist
from flask_assistant import Assistant, tell, ask
from flask_mail import Message


# Variable assertion

mqtt = Mqtt(spam)
db = SQLAlchemy(spam)

# First brick is BRICK 30
# Second brick is BRICK 10


# GLOBAL VARIABLES
battery_info_volts = 0
battery_info_volts_2= 0
delivery_status = "State.LOADING" # Delivery Status should assume one of these >> "State.DELIVERING", "State.RETURNING", "State.LOADING", "State.STOPPING", "State.PANICKING"
location_info_lock = Lock()
location_info = "Nothing reported yet."
connection_status = False
connection_status_2 = False
path_planning_result = []
recipients = []
lock = Lock()
lock_2 = Lock()
current_slot = 1
seen = False
seen_2 = False
path_planning={}
go_button_pressed = False
manual_button_pressed = False
last_auto_state = None
qnt_delivered = 0
start_time_lock = Lock()
start_time = 0

# Definitions of environment variable for Notifications
unseen_notifications= 0
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


@thread
def polling_loop():
    # Function checks the first brick (30) of the robot is connects looping through
    # on a seperate thread
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
    # Function checks the second brick (10) of the robot is connects looping through
    # on a seperate thread
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


@spam.teardown_appcontext
def shutdown_session(exception=None):
    # Ends the database session if the app is closed
    db_session.remove()

def emit_to_auto_status(msg):
    # Sends live messages to the website using socketIO for the automatic mode
    # section
    global last_auto_state
    print ("Sending by socketIO: " + msg)
    socketio.emit("auto_status", msg, broadcast=True)
    last_auto_state = msg


@spam.route('/', methods=['GET', 'POST'])
def login():
    # Handles the login page for the website by rendering it and informing the
    # user whether they had the correct login or not
    error = None
    if request.method == 'POST':
        if request.form['inputEmail'] != spam.config['EMAIL']:
            error = 'Invalid email'
        elif request.form['inputPassword'] != spam.config['PASSWORD']:
            error = 'Invalid password'
        else:
            # informs the user they were correct and loads the first page
            # covering the automatic mode
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('automatic_mode'))

    return render_template('login.html', error=error)

@spam.route('/logout')
def logout():
    # Handles the logout button for the website if the user clicks on log-out
    # it renders the login page and informs them they were logged out
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))


@spam.route('/notifications')
def notifications():
    # Function handles the notifications to be displayed to the user on the
    # notification page
    global connection_status
    global connection_status_2
    global battery_info_volts
    global battery_info_volts_2
    zero_unseen_notification()

    # Covers when the receptionist clicks on the notification, setting it to
    # be solved on a click
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
    # Function renders the admin page of the database for the user when the
    # settings button on the UI is clicked
    return redirect('/admin')

@spam.route('/auto_view', methods=['GET', 'POST'])
def automatic_mode():
    # Handles the rendering of the automatic mode page
    global path_planning_result, path_planning, current_slot, last_auto_state, manual_button_pressed, start_time, recipients
    if request.method == 'GET':
        min_battery_level = min(battery_calculate(battery_info_volts), battery_calculate(battery_info_volts_2))

        # Sets the appropriate flags and wait times to ensure the communication
        # works between automatic mode and manual
        manual_button_pressed = False
        with start_time_lock:
            wait_time = 14 - (time() - start_time)
        if wait_time < 0:
            wait_time = 0
        timer = Timer(wait_time, lambda: mqtt.publish("go_manual","False"))
        timer.start()

        # Updates the view if there has been no previous letters
        if last_auto_state is None:
            last_auto_state = "Please insert the first letter."

        # Gets the requestes for the emergency_command and updates if the connection_status is working
        command = request.args.get('emergency_command', default = "", type = str)
        if command != "":
            if connection_status:
                mqtt.publish("emergency_command",command)

        return render_template('automode.html', min_battery_level=min_battery_level, people=get_people_list(), active="Mail Delivery", unseen_notifications=get_unseen_notification(), battery_level_2=battery_calculate(battery_info_volts_2), battery_level=battery_calculate(battery_info_volts), connection_status=connection_status, connection_status_2=connection_status_2, delivery_status=delivery_status, last_auto_state=last_auto_state)
    else:
        submit=[]

        try:
            # Adds the parcel location information to the path_planning by
            # quering the database for user then location information and appending
            # that to the path_planning

            who_to = request.form.get('inputSlot5')
            where_to = transform_into_desk(who_to)
            recipients.append(Staff.query.filter(who_to == Staff.id).one().email);

            if( Location.query.filter(Location.id == where_to).one().map_node not in path_planning.keys()):
                path_planning[Location.query.filter(Location.id == where_to).one().map_node]=[5]
            else:
                path_planning[Location.query.filter(Location.id == where_to).one().map_node].append(5)
        except:
            # Case where when no parcel  is selected
            pass

        # Colates the information about which desks the robot will visit for
        # the confirmation page
        for node in path_planning.keys():
            submit.append(Location.query.filter(Location.map_node == node).one())

        # Use path planner reset the variables for the next usage of the robot
        # and render confirmation of delivery page with the location details
        # displayed

        path_planning_go_button()

        current_slot = 1
        path_planning = {}
        last_auto_state = None
        print("To Manual -- Slots: " + str(path_planning) + ". Error current slot updated: " + str(current_slot))

        min_battery_level = min(battery_calculate(battery_info_volts), battery_calculate(battery_info_volts_2))
        return render_template('echo_submit.html', min_battery_level=min_battery_level, submit=submit, unseen_notifications=get_unseen_notification(), battery_level=battery_calculate(battery_info_volts), battery_level_2=battery_calculate(battery_info_volts_2), connection_status=connection_status, connection_status_2=connection_status_2)


@spam.route('/view', methods=['GET', 'POST'])
def mail_delivery():
    # Handles the manual mode view
    error = None
    global current_slot
    global connection_status
    global connection_status_2
    global battery_info_volts
    global battery_info_volts_2
    global path_planning_result
    global path_planning
    global last_auto_state
    global manual_button_pressed
    global recipients

    if request.method == 'POST':
        # Case where the robot parcel and letter form has been updated and submitted
        submit=[]
        path_planning={}

        # Adds each of the letters to the path_planning to be sent to the robot for beginning
        for i in range(1,6):
            try:
                # Looks up the location of each of the letter recepients and
                # updates the path_planning accordingly
                who_to = request.form.get('inputSlot'+str(i))
                recipients.append(Staff.query.filter(who_to == Staff.id).one().email);
                where_to = transform_into_desk(who_to)
                if( Location.query.filter(Location.id == where_to).one().map_node not in path_planning.keys()):
                    path_planning[Location.query.filter(Location.id == where_to).one().map_node]=[i]
                else:
                    path_planning[Location.query.filter(Location.id == where_to).one().map_node].append(i)

                submit.append(Location.query.filter(Location.id == where_to).one())
            except:
                # When no parcels or letters have been selected
                pass

        # Calls the send mail notifications function
        send_dispatch_mail()

        # Builds the path plan and publishes before rendering the confirmatio page
        print ("This is path planning:")
        print (path_planning)
        path_planning_result = router.build_route(path_planning)
        if connection_status and delivery_status == "State.LOADING":
            # Check the robot is connected and in the loading state ready to deliver
            publish_path_planning(path_planning_result)

        min_battery_level = min(battery_calculate(battery_info_volts), battery_calculate(battery_info_volts_2))
        return render_template('echo_submit.html', min_battery_level=min_battery_level, submit=submit, unseen_notifications=get_unseen_notification(), battery_level=battery_calculate(battery_info_volts), battery_level_2=battery_calculate(battery_info_volts_2), connection_status=connection_status, connection_status_2=connection_status_2)

    else:
        # Renders the Manual mode page with the correct variables (if by GET request)

        current_slot = 1
        path_planning = {}
        last_auto_state = None
        manual_button_pressed = True
        recipients.clear()

        # Resets the variables to be used to monitor the automatic mode for another session
        with start_time_lock:
            global start_time
            start_time = time()
        print("To Manual -- Slots: " + str(path_planning) + ". Error current slot updated: " + str(current_slot))

        # Handles the emergency_commands if they are called passing the information to the robot to react
        command = request.args.get('emergency_command', default = "", type = str)
        if command != "":
            if connection_status:
                mqtt.publish("emergency_command",command)

        min_battery_level = min(battery_calculate(battery_info_volts), battery_calculate(battery_info_volts_2))

        # Updates the image_processing loop with the infomation that manual_mode
        # has been selected and it is no longer needed
        mqtt.publish("go_manual","True")

        return render_template('recipients.html', min_battery_level=min_battery_level, active="Mail Delivery", error=error, people=get_people_list(), unseen_notifications=get_unseen_notification(), battery_level=battery_calculate(battery_info_volts), battery_level_2=battery_calculate(battery_info_volts_2), connection_status=connection_status, delivery_status=delivery_status, connection_status_2=connection_status_2)

@spam.route('/report', methods=['GET', 'POST'])
def report():
    # Renders the report page for when users wish to report an error that has
    # occured with the robot
    if request.method == 'POST':
      # The case where the report form has updated with information and sent

      # Checks whether the staff member is part of the office based on their
      # form added email address
      try:
        origin= Staff.query.filter_by(email = request.form['email_problem']).one()
      except:
        return render_template("report.html",desks=get_desks_list(), result=-1)
      problem = Problem(origin=origin.id, message=request.form['description_problem'])

      # Adds the problem as a notification to the database
      db.session.add(problem)
      db.session.commit()
      add_unseen_notification()
      return render_template("report.html",desks=get_desks_list(), result=1)
    else:
      return render_template('report.html', desks=get_desks_list(), result=0)

@spam.route('/status')
def status():
    # Renders the status page with all the neccessary variables collected
    # through communications
    global connection_status
    global connection_status_2
    global location_info
    global battery_info_volts
    global battery_info_volts_2
    global delivery_status
    global qnt_delivered
    min_battery_level = min(battery_calculate(battery_info_volts), battery_calculate(battery_info_volts_2))
    return render_template('status.html', qnt_delivered=qnt_delivered, min_battery_level=min_battery_level, unseen_notifications=get_unseen_notification(), active="Status", battery_level=battery_calculate(battery_info_volts), battery_level_2=battery_calculate(battery_info_volts_2), connection_status=connection_status, location_info=location_info, delivery_status= delivery_status, connection_status_2=connection_status_2)


# Functions that cover the robot's and servers communication
# ----------------------------------------------------------

@mqtt.on_connect()
def on_connect(client, userdata, flags, rc):
    # MQTT connection handler for subscribing to the correct topics to recieve
    # information from the robot.
    print("Connected with result code "+str(rc))
    client.subscribe("battery_info_volts")
    client.subscribe("location_info")
    client.subscribe("delivery_status")
    client.subscribe("problem")
    client.subscribe("request_route")
    client.subscribe("image_processing")
    client.subscribe("battery_info_volts_2")

    # Resets the robot's classifier for when the brick disconnects
    print("Resetting the classifier")
    mqtt.publish("go_manual", "True")
    mqtt.publish("go_manual", "False")


# MQTT message receipt handler for receiving information from the robot.
@mqtt.on_message()
def on_message(client, userdata, msg):
    # This recieves messages from each of the ev3 bricks. Each topic on recieving
    # has unique funtionality
    print("Msg Recieved Cap")
    global path_planning_result, location_info, path_planning, current_slot, go_button_pressed, manual_button_pressed, recipients

    if msg.topic == "location_info":
        # Allows the server to keep up-to-date with the robot's location and
        # delivery progress
        with location_info_lock:
            global qnt_delivered
            location_info = msg.payload.decode()
            instruction_info = path_planning_result.pop(0)
            # Updates the known location for the server when the instruction
            # "Report" has been selected and if the Dump command is called in
            # that time it updates the amount of letters which have been dumped
            while instruction_info[0] != "Report":
                if instruction_info[0] == "Dump":
                    qnt_delivered = qnt_delivered + len(instruction_info[1])
                instruction_info = path_planning_result.pop(0)
            print("HERE")
            print(location_info)
            print(instruction_info)
        print("location_info updated")

    elif msg.topic == "battery_info_volts":
        # Updates the connection status of the first ev3 brick (30) through
        # the seen flag
        global seen
        with lock:
            seen = True
        global battery_info_volts
        # Decodes and updates the varible with the voltage information from the
        # first ev3 brick (30)
        battery_info_volts = float(msg.payload.decode())
        print("battery_info_volts updated")

    elif msg.topic == "battery_info_volts_2":
        # Updates the connection status of the second ev3 brick (10) through
        # the seen_2 flag
        global seen_2
        with lock:
            seen_2 = True
        global battery_info_volts_2
        # Decodes and updates the varible with the voltage information from the
        # second ev3 brick (10)
        battery_info_volts_2 = float(msg.payload.decode())
        print("battery_info_volts_2 updated")

    elif msg.topic == "delivery_status":
        # Works the control loop on the first ev3 brick (10) to handle the robot state
        global delivery_status
        path_planning = {}
        delivery_status = msg.payload.decode()
        if delivery_status == "State.RETURNING":
            print("Returning")
        elif delivery_status == "State.LOADING":
            # Updates the automatic_mode view with an instruction to insert the
            # first letter to begin the cycle
            current_slot = 1
            emit_to_auto_status('Please insert first letter')
            go_button_pressed = False
            print("Loading")
        print("delivery_status updated")

    elif msg.topic == "problem":
        # Handles the case when the robot encounters an error and enters "Panic Mode"
        # it updates the database with the error information
        add_unseen_notification()
        problem = Problem(origin=Staff.query.filter(Staff.email == "notification@spamrobot.ml").one().id, message=msg.payload.decode(), is_urgent=True)
        db.session.add(problem)
        db.session.commit()
        print("Problem reported by robot.")

    elif msg.topic == "request_route":
        # When the robot requests the route it feeds the collected path_planning
        # nodes into the router module to calculate the optimal path plan for robot
        # which is then published to the robot

        print("Requested Route")
        with location_info_lock:
            print("Received Location:")
            print(msg.payload.decode())
            path_planning_result = router.return_from(*(msg.payload.decode().split('-')))
            print(path_planning_result)
            publish_path_planning(path_planning_result)

    elif msg.topic == "image_processing":
        # Handles the image processing on the server side for the robot, calling
        # the image processing module to classify the image and update it based
        # on that
        print("Image Recieved")

        if (delivery_status != "State.LOADING"):
            # Updates the automatic_mode view if the robot is not in the
            # loading state and exits
            emit_to_auto_status("The robot is not ready to load. Wait or click callback.")
            return

        # Saves the recieved bytearray for the second ev3 brick (10) onto disk
        # and reads as an image
        image_location = 'image_recieved.jpg'
        msg_handle = open(image_location, 'wb')
        msg_handle.write(msg.payload)
        msg_handle.close()

        # Calls the image processing module to process the image
        desk_from_image = 0
        qr_code = image_processing.scanImage(image_location)

        # Handles the response of the server based on the results of the classification

        if qr_code == "Fail":
            # Case Failed:
            # There is no recognised qr_code so it requests a new photo new photo

            print('QR codes: %s' % qr_code)
            if (go_button_pressed == False and manual_button_pressed == False):
                # Only requests a new photo where the robot hasn't started and
                # user is still in automatic mode
                client.publish("image_result", "False")

        else:
            # Case Classified:
            # First runs through error checking to ensure error
            # checking to ensure it has been classified correctly

            if (go_button_pressed == False and manual_button_pressed == False):
                # Check ensures the robot hasn't started and user is still in automatic mode

                try:
                    #Checks the desk is an integer and it corresponds to a user

                    desk_from_image = int(qr_code)
                    user_read = Staff.query.filter(Staff.id == desk_from_image).one()
                except:
                    # Exception occurs if the desk is not an integer or the user is no a staff member
                    # the website is updated with encouragement to remove the letter and the robot is instructed
                    # to drop the letter from the classifier

                    emit_to_auto_status("Couldn't find the recipient of this letter in the office.\nPlease remove the letter from slot {} and insert a new letter.".format(current_slot))
                    print("Error incorrect desk allocation - wrong number from QR Code")
                    client.publish("image_result", current_slot)
                    return
                try:
                    # Checks the user read from the qr_code is attached to a
                    # desk and updates the path_planning information
                    location_read = user_read.location_id
                    map_node_of_location = Location.query.filter(Location.id == location_read).one().map_node

                    # Adds the user's email for later notification
                    recipients.append(user_read.email);

                    # Updates the path planning with users location checking
                    # if their location has been added already or not
                    if (map_node_of_location not in path_planning.keys()):
                        path_planning[Location.query.filter(Location.id == location_read).one().map_node]=[current_slot]
                    else:
                        path_planning[Location.query.filter(Location.id == location_read).one().map_node].append(current_slot)
                except:
                    # Exception occurs if the office user does not already have
                    # a desk. The robot is requested to drop the letter and the
                    # user is encourage on the UI to remove it and continue loading
                    emit_to_auto_status("{} has not currently been allocated a desk. Remove letter from slot {} and insert a new letter".format(user_read.name, current_slot))
                    print("Error person without desk assigned.")
                    client.publish("image_result", current_slot)
                    return

                # Case Classified and Correct:
                # The robot is sent a messgae to drop the letter and the website
                # is updated with letter information and destination
                print ("This is path planning:")
                print ("Slots: " + str(path_planning))
                emit_to_auto_status("Letter on slot {} loaded to {} on {}. Insert next letter.".format(current_slot,user_read.name, Location.query.filter(Location.id == location_read).one().location_name))
                current_slot += 1
                client.publish("image_result", current_slot)

                # Checks in case the slots have been filled to finish off the process
                if (current_slot > 4):
                    emit_to_auto_status("Last letter was loaded to {} on {}. Press Deliver Mail when ready.".format(user_read.name, Location.query.filter(Location.id == location_read).one().location_name))
                    print("Slots have all been filled")


@mqtt.on_log()
def handle_logging(client, userdata, level, buf):
    # Function which logs the MQTT communication between the server and the robot
    print(level, buf)

# Functions which send image_processing commands to the robot
# ----------------------------------------------

def path_planning_go_button():
    # Function for the user interface buttion "Deliver Mail" on the UI
    # Once Go Button is pressed sends path planning off updating the relavent
    # flag
    global go_button_pressed, path_planning, path_planning_result

    print ("This is path planning:")
    print ("Slots: " + str(path_planning))
    go_button_pressed = True
    path_planning_result = router.build_route(path_planning)

    if connection_status and delivery_status == "State.LOADING":
        # Ensures the robot is connected and in the right state to begin
        # delivering with the path_planning information
        publish_path_planning(path_planning_result)

    send_dispatch_mail()

def send_dispatch_mail():
    # Function which emails every staff member who is due to recieve mail with
    # a notification
    global recipients
    for user in recipients:
        subject = 'Delivery out'
        msg = Message(subject, sender = ("!spam", "notification@spamrobot.ml"), recipients=[user])
        msg.body = u'Dear %s,\n!spam thinks you would like to know that your mail is on the way.\n\n!spam <3' % Staff.query.filter(Staff.email == user).one().name
        mail.send(msg)
    recipients.clear()


# Functions which  send information to the robot
# ----------------------------------------------

def publish_path_planning(path_direction):
    # Sends the path planning infromation to the robot
    path_direction = json.dumps(path_direction)
    mqtt.publish("path_direction", path_direction)
    print(path_direction)

def publish_emergency_commands(emergency_command):
    # Function which sends the selected emergency_command to the robot
    mqtt.publish("emergency_command", emergency_command)
    print(emergency_command)
    global path_planning_result

    if emergency_command == 'Callback':
        # If the command is a Callback it locks the location information whilst
        # it works out the route for the robot to return back to base
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
    # Queries the database to produce a list of all the map locations
    # that are desks and returns them
    desks=[]
    for location in Location.query.all():
        if location.is_desk:
            desks.append(location)
    return desks

def get_people_list():
    # Queries the database to produce a list of all the staff working in the office
    # that have been assigned a desk location and returns them
    people=[]
    for person in Staff.query.filter(Staff.location_id != None).all():
        people.append(person)
    return people

def transform_into_desk(who_to):
    return Staff.query.filter(Staff.id == who_to).one().staff.id

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


# Functions that interface with Google Assistant
# ----------------------------------------------

@assist.action('Battery')
def battery_chat():
    # Returns the battery information for each brick if they are both connected
    speech = ""
    if connection_status:
        speech = speech + "The battery of brick number 30 is {} percent.".format(battery_calculate(battery_info_volts))
    if connection_status_2:
        speech = speech + "The battery of brick number 10 is {} percent.".format(battery_calculate(battery_info_volts_2))
    if (not connection_status) and (not connection_status_2):
        speech = speech + "To see the battery levels, I need the bricks connected."
    return tell(speech)

@assist.action('Callback')
def callback_chat():
    # Function which allows the receptionist to use the callback command
    publish_emergency_commands('Callback')
    speech = "I am returning to the reception."
    return tell(speech)

@assist.action('Resume')
def resume_chat():
    # Function which allows the receptionist to use the resume command
    publish_emergency_commands('Resume')
    speech = "I resumed operations."
    return tell(speech)

@assist.action('Stop')
def stop_chat():
    # Function which allows the receptionist to use the stop command
    publish_emergency_commands('Stop')
    speech = "I stopped and I'm waiting for your instructions."
    return tell(speech)

@assist.action('Connection Status')
def connection_chat():
    # Returns the connection status of each brick depending on
    # their connection state
    speech = ""
    if connection_status and connection_status_2:
        speech = "Both bricks are connected."
    elif connection_status and not connection_status_2:
        speech = "Brick 30 is connected, however brick 10 is disconnected."

    elif connection_status_2 and not connection_status:
        speech = "Brick 10 is connected, however brick 30 is disconnected."
    else:
        speech = "Both bricks are disconnected."

    return tell(speech)

@assist.action('Deliver Mail - yes')
def deliver_yes_chat(user):
    # Function is used to set check the robot has the correct state to begin
    # delivering after updating the path_planning with the parcel information
    global delivery_status, manual_button_pressed, connection_status
    print (user)
    if not connection_status:
        # Checks the robot is connected
        speech = "Spam is not connected"
    else:
        if delivery_status != "State.LOADING":
            # Checks the robot is in a loading state and not already delivering
            speech = "Spam is not in loading mode"
        else:
            if manual_button_pressed:
                # Checks that the interface is in automatic mode
                speech = "Spam has to be in automatic mode"
            else:
                # Adds the parcel information to the path_planning and calls the
                # path_planning processing
                if user:
                    desk = None
                    try:
                        desk = Staff.query.filter(Staff.name.ilike(user)).one().staff.map_node
                    except:
                        speech = "I couldn't find user {} in the system.".format(user)
                        return tell(speech)
                    if(desk not in path_planning.keys()):
                        path_planning[desk]=[5]
                    else:
                        path_planning[desk].append(5)
                speech = "Delivering."
                path_planning_go_button()

    return tell(speech)

@assist.action('Deliver Mail')
def deliver__chat(user):
    # Function which acts on request the user wants to deliver the mail
    global delivery_status, manual_button_pressed, connection_status
    print (user)
    if not connection_status:
        # Checks the robot is connected
        speech = "Spam is not connected"
    else:
        if delivery_status != "State.LOADING":
            # Checks the robot is in a loading state and not already delivering
            speech = "Spam is not in loading mode"
        else:
            if manual_button_pressed:
                # Checks that the interface is in automatic mode
                speech = "Spam has to be in automatic mode"
            else:
                # Allows the receptionist to add a parcel to the delivery
                # if not already added
                if user:
                    speech = "Do you want to start delivery with a parcel for {}?".format(user)
                else:
                    speech = "Do you want to start delivery without a parcel recipient?"
    return ask(speech)

@assist.action('Desk Query')
def desk_chat(user):
    print (user)
    speech = ""
    try:
        desk = Staff.query.filter(Staff.name.ilike(user)).one().staff.location_name
        speech = "{} works in {}.".format(user, desk)
        return tell(speech)
    except:
        speech = "I couldn't find user {} in the system.".format(user)
        return tell(speech)

@assist.action('Location Status')
def location_chat():
    # Function which returns information on the robots current location
    if location_info == "Nothing reported yet.":
        # Handles the case the robot hasn't yet reported it's location
        return tell("I haven't reported any location yet. Check again later.")
    speech = "I was last seen in point {}".format(location_info[0])
    return tell(speech)

@assist.action('Notifications')
def notification_chat():
    # Function which lists the amount of notifications the receptionist may have
    # waiting and forwards that information to GoogleAssistant
    if unseen_notifications == 0:
        speech = "You have no new notifications. Hip hip hooray!"
        return tell(speech)
    elif unseen_notifications == 1:
        speech = "You have one new notification. Would you like me to read it?"
    else:
        speech = "You have {} new notifications. Would you like me to read them?".format(unseen_notifications)
    return ask(speech)

@assist.action('Notifications - yes')
def notification_yes_chat():
    # Function which reads any pending notifications the receptionist may have
    # waiting and forwards that information to GoogleAssistant
    speech = ""
    notifications = Problem.query.order_by('timestamp desc').limit(unseen_notifications)
    for notification in notifications:
        speech = speech + ("From {}: {}. ".format(Staff.query.filter(notification.origin == Staff.id).one().name, notification.message))
    return tell(speech)

@assist.action('Parcel Quantity')
def parcel_chat():
    # Informs the receptionist how many parcels have been delivered
    speech = "So far, I have delivered {} objects.".format(qnt_delivered)
    return tell(speech)

@assist.action('Robot State')
def state_chat():
    # Function which returns the correct speech information to inform the
    # receptionist depending on which state the robot is in
    speech = ""
    if delivery_status == "State.LOADING":
        speech = "The robot is Parked and Loading."
    elif delivery_status == "State.DELIVERING":
        speech = "The robot is Delivering mail."
    elif delivery_status == "State.RETURNING":
        speech = "The robot is Returning to reception."
    elif delivery_status == "State.STOPPING":
        speech = "The robot is Stopped and waiting for instructions."
    elif delivery_status == "State.PANICKING":
        speech = "The robot has stopped and needs help, please check the notifications."
    else:
        speech = "I couldn't find the robot's state."
    return tell(speech)

@assist.action('User Query')
def user_chat(desk):
    # Function which returns information about stored user values in the database
    print (desk)
    speech = ""
    try:
        # Searches for the desk in the database
        desk_obj = Location.query.filter(Location.location_name == desk).one()
    except:
        # Catches the exception created where the desk is not found and forwards
        # that to the GoogleAssistant
        speech = "I couldn't find desk {} in the system.".format(desk)
        return tell(speech)
    try:
        # Collates the names of everyone who works at a certain desk and forwards
        # that to the GoogleAssistant
        people = map(lambda x: x.name, desk_obj.staff)
        speech = "Here's who works on {}: ".format(desk) + ", ".join(str(x) for x in people)
        return tell(speech)
    except:
        # Handles the case that desk does not exist or no one is attached to a
        # desk by catching the exeption and forwarding that to GoogleAssistant
        speech = "No one works on desk {}.".format(desk)
        return tell(speech)
