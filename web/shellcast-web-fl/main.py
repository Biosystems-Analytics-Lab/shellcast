import json
import logging
import os

import firebase_admin
import requests
from firebase_admin import auth
from flask import Flask, request, Response
from gcloud import storage

from config import Config, DevConfig
from models import db
from routes.api import api
from routes.cron import cron
from routes.pages import pages

# check if running on Google App Engine
# (just checking for one of the environment variables found here:
# https://cloud.google.com/appengine/docs/standard/python3/runtime#environment_variables)
if 'GAE_APPLICATION' in os.environ:
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

    # application to convert the probability to risk factor in html.jinja
    @app.context_processor
    def my_utility_processor():
        def probabilityToRisk(closureValue):
            flag = ""
            if (closureValue == 1):
                flag = "Very Low"
            elif (closureValue == 2):
                flag = "Low"
            elif (closureValue == 3):
                flag = "Moderate"
            elif (closureValue == 4):
                flag = "High"
            elif (closureValue == 5):
                flag = "Very High"
            return flag

        return dict(probabilityToRisk=probabilityToRisk)

    @app.route('/__/auth', methods=['POST', 'GET'])
    def proxy_to_firebase():
        id_token = request.headers.get('Authorization', '').split(' ').pop()
        try:
            auth.verify_id_token(id_token)
        except ValueError:
            firebase_url = 'https://ncsu-shellcast.firebaseio.com' + request.full_path
            resp = requests.request(
                method=request.method,
                url=firebase_url,
                headers={key: value for (key, value) in request.headers if key != 'Host'},
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False)
            excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
            headers = [(name, value) for (name, value) in resp.raw.headers.items()
                       if name.lower() not in excluded_headers]
            response = Response(resp.content, resp.status_code, headers)
            return response

    @app.route('/cmusGeoJson', methods=['GET'])
    def get_cmus_geosjson():
        storage_client = storage.Client()
        blob = storage_client.bucket(app.config['GCLOUD_STORAGE_BUCKET']).get_blob('fl_cmus.geojson')
        cmus_geojson_str = blob.download_as_string()
        cmus_geojson = json.loads(cmus_geojson_str)
        return cmus_geojson

    return app


app = None

# if running the file directly
if __name__ == '__main__':
    logging.info('Starting app with development configuration')
    # setup for running locally (development configuration)
    app = createApp(DevConfig())
    # run the app locally
    app.run(host=DevConfig.HOST, port=DevConfig.PORT, debug=True)
else:  # else the app is being run from a WSGI application such as gunicorn
    logging.info('Starting app with production configuration')

    # setup for production configuration
    app = createApp(Config())
