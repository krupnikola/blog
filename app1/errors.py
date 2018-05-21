from flask import render_template
from app1 import app, db



@app.errorhandler(404)
def not_found_error(error):
	# there are two return values, one is a regular template rendering and the other one is ERROR CODE!
	return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
	# this command drops everything that is in the db session and has not been committed when the error happened
	# so the next session starts clean
	# command opposite od db.session.commit()
	db.session.rollback()
	return render_template('500.html'), 500
