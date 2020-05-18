import datetime
from flask import Flask, render_template

from config import Config, DevConfig

app = Flask(__name__)
app.config.from_object(Config())

@app.route('/')
def indexPage():
  regions = [{"id": "A1", "prob1Day": 0, "prob2Day": 35, "prob3Day": 75},
              {"id": "A2", "prob1Day": 2, "prob2Day": 37, "prob3Day": 77}]

  return render_template('index.html.jinja', mapsAPIKey=Config.MAPS_API_KEY, regions=regions)

@app.route('/about')
def aboutPage():
  return render_template('about.html.jinja')

@app.route('/notifications')
def notificationsPage():
  return render_template('notifications.html.jinja')

if __name__ == '__main__':
  app.config.from_object(DevConfig())
  # This is used when running locally only. When deploying to Google App
  # Engine, a webserver process such as Gunicorn will serve the app. This
  # can be configured by adding an `entrypoint` to app.yaml.
  # Flask's development server will automatically serve static files in
  # the "static" directory. See:
  # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
  # App Engine itself will serve those files as configured in app.yaml.
  app.run(host=DevConfig.HOST, port=DevConfig.PORT, debug=True)
