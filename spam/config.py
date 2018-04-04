import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    EMAIL='admin@admin.com'
    PASSWORD='default'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'spam.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    DEBUG = True

    MAIL_SERVER = "box.spamrobot.ml"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    #MAIL_DEBUG = app.debug
    MAIL_USERNAME = "notification@spamrobot.ml"
    MAIL_PASSWORD = "spamnotification"
    #MAIL_DEFAULT_SENDER = "!spam"
    #MAIL_MAX_EMAILS = None
    #MAIL_SUPPRESS_SEND = app.testing
    #MAIL_ASCII_ATTACHMENTS = False

   # MQTT_BROKER_URL = localhost # use the free broker from HIVEMQ
   # MQTT_BROKER_PORT = 1883  # default port for non-tls connection
   # MQTT_USERNAME = ''  # set the username here if you need authentication for the broker
   # MQTT_PASSWORD = ''  # set the password here if the broker demands authentication
   # MQTT_KEEPALIVE = 5  # set the time interval for sending a ping to the broker to 5 seconds
   # MQTT_TLS_ENABLED = False  # set TLS to disabled for testing purposes
