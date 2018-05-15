from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask_bootstrap import Bootstrap
from flask_moment import Moment



app = Flask(__name__, template_folder='templates')
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
mail = Mail(app)
# protection of login required views, here is specified what route to trigger if user is not authenticated
login.login_view = 'login'
# bootstrap support integration
bootstrap = Bootstrap(app)
# integration of Moment.js functionalities
moment = Moment(app)


# email setup 

# first check that we ar enot in debug mode
if not app.debug:
    # second check if the email server is configured, if not we can not send emails
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        # making a new file handler that logs messages to an email
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            # fake "from" mail address for sending emails
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            # list of addresses to send to, and an email subject
            toaddrs=app.config['ADMINS'], subject='Microblog Failure',
            credentials=auth, secure=secure)
        # set level of message logging
        mail_handler.setLevel(logging.ERROR)
        # adding defined handler to logger
        app.logger.addHandler(mail_handler)


    if not os.path.exists('logs'):
        os.mkdir('logs')
    # making a new file handler that logs messages to a file on disk 
    file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240,
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    # adding second handler to logger
    app.logger.addHandler(file_handler)


    # global logging level set for entire logger
    app.logger.setLevel(logging.INFO)
    # message to log every time the app(=server) starts
    app.logger.info('Microblog startup')



from app1 import routes, models, errors
