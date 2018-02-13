# all the imports
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
import socket
from sys import argv

app = Flask(__name__) # create the application instance :)
app.config.from_object(__name__) # load config from this file , spam.py

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'spam.db'),
    SECRET_KEY='development key',
    EMAIL='admin@admin.com',
    PASSWORD='default'
))
app.config.from_envvar('SPAM_SETTINGS', silent=True)


#database functions TODO: swtich to sqlalchemy
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
    #else
    return render_template('recipients.html', error=error)

@app.route('/report')
def report():
    return render_template('report.html')

@app.route('/status')
def status():
    return render_template('status.html')


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
