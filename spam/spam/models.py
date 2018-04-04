from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from spam.database import Base
from spam import db
from datetime import datetime

# Staff table will include the people that work in the company
class Staff(db.Model):
    __tablename__ = 'staff'
    id = db.Column(Integer, primary_key=True)
    # Name of the person
    name = db.Column(String(120),unique=True, index=True, nullable=False)
    # Email of the person (to match in the report form)
    email = db.Column(String(120),unique=True, nullable=False)
    # Which desk the person works in
    location_id = db.Column(Integer, ForeignKey('location.id'))
    #relationship forms the link for the ORM
    problem = db.relationship('Problem', backref='problem')


    def __init__(self, name=None, email=None, location_id=None):
        self.name = name
        self.email = email
        self.location_id = location_id

    def __repr__(self):
        return '<Staff %r>' % (self.name)

# Locations in the map
class Location(db.Model):
    __tablename__ = 'location'
    id = db.Column(Integer, primary_key=True)
    # How the path planner percieves nodes
    map_node = db.Column(String(50), unique=True, nullable=False)
    # Human readable name of that location
    location_name = db.Column(String(50), unique=True, nullable=False)
    # Whether it is a desk (where mail can be delivered) or not (i.e. junction)
    is_desk = db.Column(Boolean, default=True)
    #uselist=false restricts to one-one
    staff = db.relationship('Staff', backref='staff')

    def __init__(self, map_node=None, location_name=None, is_desk=True):
        self.map_node = map_node
        self.location_name = location_name
        self.is_desk = is_desk

    def __repr__(self):
        return '<Location %r>' % (self.location_name)

# Notifications
class Problem(db.Model):
    __tablename__ = 'problem'
    id = db.Column(Integer, primary_key=True)
    # Who reported the problem
    origin = db.Column(Integer, ForeignKey('staff.id'), nullable=False)
    # The desctription of the problem
    message = db.Column(String(200), nullable=False)
    # The time that it was submitted
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow())
    # Whether it has been resolved
    solved = db.Column(Boolean, default=False)
    # Identifies the notifications considered urgent.
    # All notifications coming from the robot should be marked urgent.
    is_urgent = db.Column(Boolean, default=False)

    def __init__(self, origin=None, message=None, is_urgent=False, solved=False, timestamp=datetime.utcnow()):
        self.origin = origin
        self.message = message
        self.timestamp = timestamp
        self.is_urgent = is_urgent
        self.solved= solved

    def __repr__(self):
        return '<Problem %r>' % (self.id)
