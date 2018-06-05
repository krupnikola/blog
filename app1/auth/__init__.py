from flask import Blueprint

bp = Blueprint('auth', __name__)


from app1.auth import routes