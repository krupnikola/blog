from flask import Flask, request, current_app
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
from flask_babel import Babel, lazy_gettext as _l
from elasticsearch import Elasticsearch
from redis import Redis
import rq




db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
# protection of login required views, here is specified what route to trigger if user is not authenticated
login.login_view = 'auth.login'
login.login_message = _l('Please log in to access this page.')
# bootstrap support integration
bootstrap = Bootstrap()
# integration of Moment.js functionality
moment = Moment()
babel = Babel()
mail = Mail()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)
    # Elasticsearch instance, we add it as an attribute to flask app instance and it is conditional, the service
    # will run if the el-variable is set
    app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
        if app.config['ELASTICSEARCH_URL'] else None

    # similar as elastic service, we create it as an app attribute
    app.redis = Redis.from_url(app.config['REDIS_URL'])
    # task queue initialised via Queue class from the rq module, name of the worker is microblog-tasks
    # in order for this to run, Redis service must run on the OS
    app.task_queue = rq.Queue('microblog-tasks', connection=app.redis)


    from app1.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app1.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app1.main import bp as main_bp
    app.register_blueprint(main_bp)

    # email setup

    # first check that we are not in debug mode
    if not app.debug and not app.testing:
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

    return app


# this function is invoked for each request to select a language
# 'accept_languages' object client sends through web browser with each request
# and we collect it here and select a language based on that
@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])


from app1 import models
