
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
	SECRET_KEY = os.environ.get('SECRET_KEY')
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
		'sqlite:///' + os.path.join(basedir, 'app.db')
	SQLALCHEMY_TRACK_MODIFICATIONS = False

	MAIL_SERVER = os.environ.get('MAIL_SERVER')
	MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
	MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
	MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
	MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
	ADMINS = ['nikola@example.com']

	POSTS_PER_PAGE = 10

	LANGUAGES = ['en', 'es']

	# Microsoft translator API key
	MS_TRANSLATOR_KEY = os.getenv('MS_TRANSLATOR_KEY')

	# Elasticsearch connection URL for the service
	ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')

	# Redis service config, if not specified we'll use local redis
	REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'