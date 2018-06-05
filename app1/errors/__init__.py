from flask import Blueprint

bp = Blueprint('errors', __name__)

from app1.errors import handlers