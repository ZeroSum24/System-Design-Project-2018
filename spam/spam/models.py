from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from spam.database import Base
from spam import db
from datetime import datetime

#TODO: figure out what data type and data robot_location and robot_id need
#TODO: write a database blueprint to build the data automatically every time the code gets reset in production
#TODO: add Flask-Migrate ? (probably wont need, as the database structure wont change while containing real data)
#I dont really like the naming convention here
class Staff(db.Model):
    __tablename__ = 'staff'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(120),unique=True, index=True, nullable=False)
    email = db.Column(String(120),unique=True, nullable=False)
    location_id = db.Column(Integer, ForeignKey('location.id'))
    #relationship forms the link for the ORM
    problem = db.relationship('Problem', backref='problem')


    def __init__(self, name=None, email=None, location_id=None):
        self.name = name
        self.email = email
        self.location_id = location_id

    def __repr__(self):
        return '<Staff %r>' % (self.name)

class Location(db.Model):
    __tablename__ = 'location'
    id = db.Column(Integer, primary_key=True)
    map_node = db.Column(String(50), unique=True, nullable=False)
    location_name = db.Column(String(50), unique=True, nullable=False)
    is_desk = db.Column(Boolean, default=True)
    #uselist=false restricts to one-one
    staff = db.relationship('Staff', backref='staff')

    def __init__(self, map_node=None, location_name=None):
        self.map_node = map_node
        self.location_name = location_name

    def __repr__(self):
        return '<Location %r>' % (self.location_name)

class Problem(db.Model):
    __tablename__ = 'problem'
    id = db.Column(Integer, primary_key=True)
    origin = db.Column(Integer, ForeignKey('staff.id'), nullable=False)
    message = db.Column(String(200), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    solved = db.Column(Boolean, default=False)

    def __init__(self, origin=None, message=None):
        self.origin = origin
        self.message = message
        self.solved= False

    def __repr__(self):
        return '<Problem %r>' % (self.id)
