import datetime
from flask import Flask, render_template, jsonify

from config import Config, DevConfig

app = Flask(__name__)
app.config.from_object(Config())

@app.route('/')
def indexPage():
  return render_template('index.html.jinja', mapsAPIKey=Config.MAPS_API_KEY)

@app.route('/about')
def aboutPage():
  return render_template('about.html.jinja')

@app.route('/notifications')
def notificationsPage():
  return render_template('notifications.html.jinja')

@app.route('/areaData')
def areaData():
  growingAreas = {
    "A01": {
      "prob1Day": 16,
      "prob2Day": 35,
      "prob3Day": 75
    },
    "A02": {
      "prob1Day": 76,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "A03": {
      "prob1Day": 74,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "B01": {
      "prob1Day": 88,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "B02": {
      "prob1Day": 91,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "B03": {
      "prob1Day": 96,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "B04": {
      "prob1Day": 25,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "B05": {
      "prob1Day": 48,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "B06": {
      "prob1Day": 73,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "B07": {
      "prob1Day": 100,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "B08": {
      "prob1Day": 18,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "B09": {
      "prob1Day": 28,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "B10": {
      "prob1Day": 19,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "C01": {
      "prob1Day": 88,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "C02": {
      "prob1Day": 45,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "C03": {
      "prob1Day": 53,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "C04": {
      "prob1Day": 16,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "D01": {
      "prob1Day": 26,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "D02": {
      "prob1Day": 37,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "D03": {
      "prob1Day": 4,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "D04": {
      "prob1Day": 49,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "E01": {
      "prob1Day": 49,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "E02": {
      "prob1Day": 28,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "E03": {
      "prob1Day": 66,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "E04": {
      "prob1Day": 59,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "E05": {
      "prob1Day": 59,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "E06": {
      "prob1Day": 70,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "E07": {
      "prob1Day": 8,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "E08": {
      "prob1Day": 88,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "E09": {
      "prob1Day": 54,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "F01": {
      "prob1Day": 92,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "F02": {
      "prob1Day": 78,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "F03": {
      "prob1Day": 3,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "F04": {
      "prob1Day": 64,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "F05": {
      "prob1Day": 6,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "F06": {
      "prob1Day": 72,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "F07": {
      "prob1Day": 49,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "F08": {
      "prob1Day": 55,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "F09": {
      "prob1Day": 3,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "G01": {
      "prob1Day": 64,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "G02": {
      "prob1Day": 6,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "G03": {
      "prob1Day": 72,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "G04": {
      "prob1Day": 49,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "G05": {
      "prob1Day": 55,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "G06": {
      "prob1Day": 3,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "G07": {
      "prob1Day": 88,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "G08": {
      "prob1Day": 42,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "G09": {
      "prob1Day": 16,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "G10": {
      "prob1Day": 28,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "G11": {
      "prob1Day": 43,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "G12": {
      "prob1Day": 77,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "H01": {
      "prob1Day": 67,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "H02": {
      "prob1Day": 87,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "H03": {
      "prob1Day": 30,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "H04": {
      "prob1Day": 36,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "H05": {
      "prob1Day": 52,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "H06": {
      "prob1Day": 15,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "I01": {
      "prob1Day": 92,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "I02": {
      "prob1Day": 52,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "I03": {
      "prob1Day": 45,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "I04": {
      "prob1Day": 45,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "I05": {
      "prob1Day": 24,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "I06": {
      "prob1Day": 57,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "I07": {
      "prob1Day": 9,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "I08": {
      "prob1Day": 20,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "I09": {
      "prob1Day": 6,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "I10": {
      "prob1Day": 55,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "I11": {
      "prob1Day": 83,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "I12": {
      "prob1Day": 62,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "I13": {
      "prob1Day": 75,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "I14": {
      "prob1Day": 10,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "I15": {
      "prob1Day": 32,
      "prob2Day": 37,
      "prob3Day": 77
    },
    "I16": {
      "prob1Day": 78,
      "prob2Day": 37,
      "prob3Day": 77
    }
  }
  return jsonify(growingAreas)

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
