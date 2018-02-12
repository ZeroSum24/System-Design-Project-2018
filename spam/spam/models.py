from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from spam.database import Base
from spam import db

#TODO: figure out what data type and data robot_location and robot_id need
#TODO: write a database blueprint to build the data automatically every time the code gets reset in production
#TODO: add Flask-Migrate ? (probably wont need, as the database structure wont change while containing real data)
#I dont really like the naming convention here
class Staff(db.Model):
    #__tablename__ = 'staff'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(120), nullable=False)
    robot_id = db.Column(String(120), unique=True)
    #relationship forms the link for the ORM
    location = relationship('Location', backref='location')

    def __init__(self, name=None, robot_id=None):
        self.name = name
        self.robot_id = robot_id

    def __repr__(self):
        return '<User %r>' % (self.name)

class Location(db.Model):
    #__tablename__ = 'location'
    id = db.Column(Integer, primary_key=True)
    robot = db.Column(String(50), unique=True)
    physical = db.Column(String(50), unique=True)
    #foreignkey indicates these values should be restrained to named remote values
    staff_id = db.Column(Integer, ForeignKey('staff.id'))
    #uselist=false restricts to one-one
    staff = relationship('Staff', uselist=False, backref='staff')

    def __init__(self, robot_location=None, physical_location=None):
        self.robot_location = robot_location
        self.physical_location = physical_location

    def __repr__(self):
        return '<Location %r>' % (self.physical_location)
