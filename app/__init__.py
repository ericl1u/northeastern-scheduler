from flask import Flask
from flask_caching import Cache
from flask_compress import Compress
from flasgger import Swagger
from flask_login import LoginManager
# from celery import Celery
import os

app = Flask(__name__)

app.config.from_object(os.environ['APP_SETTINGS'])

cache = Cache(app)
cache.clear()
cache.init_app(app)

lm = LoginManager(app)

# celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
# celery.conf.update(app.config)

Swagger(app)
Compress(app)

from app import views
from app import logging
