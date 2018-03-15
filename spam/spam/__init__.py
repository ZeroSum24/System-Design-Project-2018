#from .spam import app
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_socketio import SocketIO
from flask_assistant import Assistant, ask, tell

spam = Flask(__name__)
spam.config.from_object(Config)
db = SQLAlchemy(spam)
migrate = Migrate(spam, db)
admin = Admin(spam, name='Settings', template_mode='bootstrap3')
socketio = SocketIO(spam)
from spam.models import Staff, Location, Problem
admin.add_view(ModelView(Staff, db.session))
admin.add_view(ModelView(Problem, db.session))
admin.add_view(ModelView(Location, db.session))
assist = Assistant(app, route='/fulfillment')


from spam import routes, models
