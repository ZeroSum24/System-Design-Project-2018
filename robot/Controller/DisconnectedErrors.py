"""Exceptions that should be thrown when a motor or sensor disconnects"""

# Known exceptions produced when motors or sensors disconnect
EXCEPTIONS = (OSError, FileNotFoundError)

class DisconnectedError(Exception):
    """Can be raised when a component disconnects"""

class MotorDisconnectedError(DisconnectedError):
    """A Motor has disconnected"""

class SonarDisconnectedError(DisconnectedError):
    """The Sonar has disconnected"""

class ReflectivityDisconnectedError(DisconnectedError):
    """The Reflectivity sensor has disconnected"""

class ColorDisconnectedError(DisconnectedError):
    """The Color sensor has disconnected"""
