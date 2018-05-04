from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager


app = Flask(__name__, template_folder='templates')
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
# protection of login required views, here is specified what route to trigger if user is not authenticated
login.login_view = 'login'

from app1 import routes, models
