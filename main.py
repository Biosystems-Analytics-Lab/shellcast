import datetime

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def indexPage():
  regions = [{"id": "A1", "prob1Day": 0, "prob2Day": 35, "prob3Day": 75},
              {"id": "A2", "prob1Day": 2, "prob2Day": 37, "prob3Day": 77}]

  return render_template('index.html.jinja', regions=regions)

@app.route('/about')
def aboutPage():
  return render_template('about.html.jinja')

@app.route('/notifications')
def notificationsPage():
  return render_template('notifications.html.jinja')

if __name__ == '__main__':
  # This is used when running locally only. When deploying to Google App
  # Engine, a webserver process such as Gunicorn will serve the app. This
  # can be configured by adding an `entrypoint` to app.yaml.
  # Flask's development server will automatically serve static files in
  # the "static" directory. See:
  # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
  # App Engine itself will serve those files as configured in app.yaml.
  app.run(host='127.0.0.1', port=8080, debug=True)
