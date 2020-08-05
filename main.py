import os
import logging

from flask import Flask, render_template, jsonify

import firebase_admin

from models import db

from routes.pages import pages
from routes.api import api
from routes.cron import cron

from config import Config, DevConfig

# check if running on Google App Engine
# (just checking for one of the environment variables found here: https://cloud.google.com/appengine/docs/standard/python3/runtime#environment_variables)
if ('GAE_APPLICATION' in os.environ):
  # integrate Python logging module with Google Cloud Logging (captures INFO level and higher by default)
  import google.cloud.logging
  gcloudLoggingClient = google.cloud.logging.Client()
  gcloudLoggingClient.get_default_handler()
  gcloudLoggingClient.setup_logging()

  logging.info('Running on Google App Engine')

# initialize Firebase Admin SDK
firebase_admin.initialize_app()

def createApp(configObj):
  """
  Returns a Flask app configured with the given configuration object.
  """
  app = Flask(__name__)
  app.config.from_object(configObj)

  # register blueprints
  app.register_blueprint(pages)
  app.register_blueprint(api)
  app.register_blueprint(cron)

  # initialize database connection
  db.init_app(app)

  return app

app = None

# if running the file directly
if __name__ == '__main__':
  logging.info('Starting app with development configuration')
  # setup for running locally (development configuration)
  app = createApp(DevConfig())
  # run the app locally
  app.run(host=DevConfig.HOST, port=DevConfig.PORT, debug=True)
else: # else the app is being run from a WSGI application such as gunicorn
  logging.info('Starting app with production configuration')

  # setup for production configuration
  app = createApp(Config())
