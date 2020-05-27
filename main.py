import datetime
from flask import Flask, render_template, jsonify

from models import db

from routes.pages import pages
from routes.areaData import areaData

from config import Config, DevConfig

def createApp(configObj):
  """
  Returns a Flask app configured with the given configuration object.
  """
  app = Flask(__name__)
  app.config.from_object(configObj)

  # register blueprints
  app.register_blueprint(pages)
  app.register_blueprint(areaData)

  # initialize database connection
  db.init_app(app)

  return app

app = None

# if running the file directly
if __name__ == '__main__':
  # setup for running locally (development configuration)
  app = createApp(DevConfig())
  # run the app locally
  app.run(host=DevConfig.HOST, port=DevConfig.PORT, debug=True)
else: # else the app is being run from a WSGI application such as gunicorn
  # setup for production configuration
  app = createApp(Config())
