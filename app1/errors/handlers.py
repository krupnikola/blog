from flask import render_template
from app1 import db
from app1.errors import bp


# new detail is the decorator which now doesn't need to come from app instance itself but from the
# blueprint
@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500