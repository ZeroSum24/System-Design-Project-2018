# all the imports
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
import socket
from sys import argv
import graph # this is the module for path planning. Will later be route.py
from flask_mqtt import Mqtt


app = Flask(__name__) # create the application instance :)
app.config.from_object(__name__) # load config from this file , spam.py

broker_aws_host = "18.219.135.123" #this is a static ip to aws_1_broker

app.config['MQTT_BROKER_IP'] = broker_aws_host  # use the free broker from HIVEMQ
app.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection
app.config['MQTT_USERNAME'] = ''  # set the username here if you need authentication for the broker
app.config['MQTT_PASSWORD'] = ''  # set the password here if the broker demands authentication
app.config['MQTT_KEEPALIVE'] = 5  # set the time interval for sending a ping to the broker to 5 seconds
app.config['MQTT_TLS_ENABLED'] = False  # set TLS to disabled for testing purposes

mqtt = Mqtt(app)
battery_info = 0
location_info = "Loading Bay"
connection_status = False
path_planning = []

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'spam.db'),
    SECRET_KEY='development key',
    EMAIL='admin@admin.com',
    PASSWORD='default'
))
app.config.from_envvar('SPAM_SETTINGS', silent=True)

#database functions TODO: switch to sqlalchemy
def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv
#to avoid piping into sqlite3 directly
def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')
#g is a is a general purpose variable associated with the current application context.
def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db
@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()



@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['inputEmail'] != app.config['EMAIL']:
            error = 'Invalid email'
        elif request.form['inputPassword'] != app.config['PASSWORD']:
            error = 'Invalid password'
            #TODO: allow the user to reattempt even if they have got the wrong password
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('mail_delivery'))
    #else
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))

#TODO: match these up with index.html
@app.route('/view', methods=['GET', 'POST'])
def mail_delivery():
    error = None
    if request.method == 'POST':
        #flash('You were logged in')
        #s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #s.connect(('localhost', 8888))
        #template expecting list
        submit = ["ff","mv","mgsd"]

            #TODO:this wont work anymore
            #submit = [request.form['slot1'], request.form['slot2'], request.form['slot3'], request.form['slot4'], request.form['slot5']]
        #s.send(', '.join(submit).encode())
        return render_template('echo_submit.html', submit=submit)
    #TODO *insert path planning here* but need to see how the database works for this to go ahead
    path_planning = database_map_nodes_lookup()
    publish_path_planning(path_planning)
    #else
    return render_template('recipients.html', error=error)

@app.route('/report')
def report():
    return render_template('report.html')

@app.route('/status')
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

#TODO: need database editing thingymijig
        #technically extension, but hey, once I get the db working it'll be fine
#<a class="nav-link" href="#">Status</a>
#<a class="nav-link" href="#">Settings</a>
#<a class="nav-link" href="#">Help</a>
#<a class="nav-link" href="#">Logout</a>

#TODO: add the 'user' things for reporting wrong mail
#TODO: get a bluetooth connection cycle going - probably
    #<span class="badge badge-pill badge-success">Robot Connected</span>
#TODO: get external post requests working
@app.route('/slots', methods=['GET', 'POST'])
def receive_http():
    error=None
    if request.method == 'POST':
        return render_template('login.html', error=error)
    #else
    return render_template('login.html', error=error)
