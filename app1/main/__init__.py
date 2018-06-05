from flask import Blueprint

bp = Blueprint('main', __name__)

from app1.main import routes