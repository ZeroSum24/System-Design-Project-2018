#from .spam import app
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

spam = Flask(__name__)
spam.config.from_object(Config)
db = SQLAlchemy(spam)
migrate = Migrate(spam, db)

from spam import routes, models
