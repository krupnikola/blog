# konfiguracioni fajl treba da bude lociran izvan applikacije

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
# loaduje environment promenljive iz fajla ".env", izmesten je ispred Config klase jer ce ona zatraziti
# ove promenljive preko os.environ.get
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
	# ako postoji environ variable imena SECRET_KEY onda ce procitati iz operativnog sistema, a ako ne onda koristi hardkodovanu
	SECRET_KEY = os.environ.get('SECRET_KEY')
	# URL that defines type and location of the database, napravili smo apsolutnu putanju do baze
	# opet smo ostavili mogucnost da ako postoji environ variable koja sadrzi DATABASE_URL da to uzmemo
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
		'sqlite:///' + os.path.join(basedir, 'app.db')
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	# ispisuje query-je onako kako ih sqlalchemy salje bazi interno
	# SQLALCHEMY_ECHO = True

	# email notification configuration
	MAIL_SERVER = os.environ.get('MAIL_SERVER')
	MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
	# encrypted connection flag, true if defined in the environment
	MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
	MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
	MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
	ADMINS = ['nikola@example.com']

	# pagination setting
	POSTS_PER_PAGE = 10

	# supported languages list for Babel
	LANGUAGES = ['en', 'es']

	# Microsoft translator API key
	MS_TRANSLATOR_KEY = os.getenv('MS_TRANSLATOR_KEY')

	# Elasticsearch connection URL for the service
	ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')