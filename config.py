# konfiguracioni fajl treba da bude lociran izvan applikacije

import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
	# ako postoji environ variable imena SECRET_KEY onda ce procitati is operativnog sistema, a ako ne onda koristi hardkodovanu
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
	# URL that defines type and location of the database, napravili smo apsolutnu putanju do baze
	# opet smo ostavili mogucnost da ako postoji environ variable koaj sadrzi DATABASE_URL da to uzmemo
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
		'sqlite:///' + os.path.join(basedir, 'app.db')
	SQLALCHEMY_TRACK_MODIFICATIONS = False

	#email notification configuration
	MAIL_SERVER = os.environ.get('MAIL_SERVER')
	MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
	#encrypted connection flag, true if defined in the environment
	MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
	MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
	MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
	ADMINS = ['etfnik@gmail.com']