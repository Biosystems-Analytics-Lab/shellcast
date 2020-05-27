import datetime
from flask import Flask, render_template, jsonify

from models import db

from routes.pages import pages
from routes.areaData import areaData

from config import Config, DevConfig

app = Flask(__name__)

app.register_blueprint(pages)
app.register_blueprint(areaData)

def initialize(configObj):
  app.config.from_object(configObj)
  db.init_app(app)

# if running the file directly
if __name__ == '__main__':
  # setup for running locally (development configuration)
  initialize(DevConfig())
  # run the app locally
  app.run(host=DevConfig.HOST, port=DevConfig.PORT, debug=True)
else: # else the app is being run from a WSGI application such as gunicorn
  # setup for production configuration
  initialize(Config())
