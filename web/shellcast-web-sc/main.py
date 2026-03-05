import logging
import os
import sys

import firebase_admin
import requests
from firebase_admin import auth
from flask import Flask, Response, request

# Load environment variables from .env (local and, if deployed, on GAE).
# With override=True, .env wins over app.yaml env_variables when both exist.
try:
    from dotenv import load_dotenv

    load_dotenv(override=True)
except ImportError:
    pass  # dotenv not available, continue without it

from models import db  # noqa: E402
from routes.api import api  # noqa: E402
from routes.cron import cron  # noqa: E402
from routes.pages import pages  # noqa: E402

# check if running on Google App Engine
# (just checking for one of the environment variables found here:
# https://cloud.google.com/appengine/docs/standard/python3/runtime#environment_variables)
RUNNING_ON_GAE = "GAE_APPLICATION" in os.environ or os.getenv("GAE_ENV", "").startswith(
    "standard"
)
if RUNNING_ON_GAE:
    # integrate Python logging module with Google Cloud Logging (captures INFO level and higher by default)
    import google.cloud.logging  # noqa: E402

    gcloudLoggingClient = google.cloud.logging.Client()
    gcloudLoggingClient.get_default_handler()
    gcloudLoggingClient.setup_logging()

    logging.info("Running on Google App Engine")

# initialize Firebase Admin SDK
firebase_admin.initialize_app()


def create_app(config=None):
    """
    Returns a Flask app configured from env (or from config object when provided for tests).
    """
    app = Flask(__name__)

    # Allow GAE, local, and webhook Host headers (avoids "Host validation failed" / SecurityError).
    # Webhooks (e.g. Bandwidth → /api/bandwidth/callback) may send a different Host; these patterns cover common cases.
    app.config["TRUSTED_HOSTS"] = [
        ".appspot.com",
        "localhost",
        "127.0.0.1",
        ".run.app",  # Cloud Run if used as proxy
    ]

    if config is not None:
        # Test/config-based setup
        app.config.from_object(config)
        uri = getattr(config, "SQLALCHEMY_DATABASE_URI", None)
        if callable(uri):
            uri = config.SQLALCHEMY_DATABASE_URI
        if uri is not None:
            app.config["SQLALCHEMY_DATABASE_URI"] = uri
    else:
        # Provide safe local defaults for development if not set
        os.environ.setdefault("HOST", "127.0.0.1")
        os.environ.setdefault("PORT", "8080")
        os.environ.setdefault("SECRET_KEY", "dev-secret-key")

        # Validate required environment variables
        # DB_HOST / DB_PORT are required for local TCP connections.
        # CLOUD_SQL_INSTANCE_NAME is required on GAE for Unix socket connections.
        required_vars = [
            "HOST",
            "PORT",
            "SECRET_KEY",
            "EMAIL_SECRET_KEY",
            "DB_USER",
            "DB_PASS",
            "DB_NAME",
            "DB_POOL_SIZE",
            "DB_MAX_OVERFLOW",
            "DB_POOL_TIMEOUT",
            "DB_POOL_RECYCLE",
        ]
        if RUNNING_ON_GAE:
            required_vars.append("CLOUD_SQL_INSTANCE_NAME")
        else:
            required_vars.extend(["DB_HOST", "DB_PORT"])

        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        if missing_vars:
            error_msg = (
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
            )
            error_msg += "Please set these variables in your .env file or environment."
            print(f"ERROR: {error_msg}", file=sys.stderr)
            raise ValueError(error_msg)

        # Configure Flask app directly from environment variables
        app.config.update(
            {
                # Flask Configuration
                "DEBUG": os.environ.get("DEBUG", "false").lower() == "true",
                "TESTING": os.environ.get("TESTING", "false").lower() == "true",
                "SECRET_KEY": os.environ.get("SECRET_KEY"),
                "EMAIL_SECRET_KEY": os.environ.get("EMAIL_SECRET_KEY"),
                # Database Configuration
                "DB_HOST": os.environ.get("DB_HOST"),
                "DB_PORT": os.environ.get("DB_PORT"),
                "DB_USER": os.environ.get("DB_USER"),
                "DB_PASS": os.environ.get("DB_PASS"),
                "DB_NAME": os.environ.get("DB_NAME"),
                # Cloud SQL Configuration
                "DB_UNIX_SOCKET_PATH_PREFIX": os.environ.get(
                    "DB_UNIX_SOCKET_PATH_PREFIX", "/cloudsql/"
                ),
                "CLOUD_SQL_INSTANCE_NAME": os.environ.get("CLOUD_SQL_INSTANCE_NAME"),
                # SQLAlchemy Configuration
                "SQLALCHEMY_TRACK_MODIFICATIONS": os.environ.get(
                    "SQLALCHEMY_TRACK_MODIFICATIONS", "false"
                ).lower()
                == "true",
                "SQLALCHEMY_ENGINE_OPTIONS": {
                    "pool_size": int(os.environ.get("DB_POOL_SIZE")),
                    "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW")),
                    "pool_timeout": int(os.environ.get("DB_POOL_TIMEOUT")),
                    "pool_recycle": int(os.environ.get("DB_POOL_RECYCLE")),
                },
            }
        )

        # Database URI: use env override (e.g. tests with sqlite) or build from settings.
        # - On GAE: connect via Unix socket /cloudsql/<instance_name>
        # - Local dev: connect via TCP host:port from .env (no proxy required if DB is reachable)
        if os.environ.get("SQLALCHEMY_DATABASE_URI"):
            app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
                "SQLALCHEMY_DATABASE_URI"
            )
        else:
            if RUNNING_ON_GAE:
                # Use Unix socket provided by App Engine standard.
                socket_path = "{}{}".format(
                    app.config["DB_UNIX_SOCKET_PATH_PREFIX"],
                    app.config["CLOUD_SQL_INSTANCE_NAME"],
                )
                app.config["SQLALCHEMY_DATABASE_URI"] = (
                    "mysql+pymysql://{}:{}@/{}?unix_socket={}&ssl_disabled=true".format(
                        app.config["DB_USER"],
                        app.config["DB_PASS"],
                        app.config["DB_NAME"],
                        socket_path,
                    )
                )
            else:
                # Local TCP connection (DB_HOST:DB_PORT) – uses values from .env
                host = app.config["DB_HOST"]
                port = app.config["DB_PORT"]
                if port:
                    hostport = f"{host}:{port}"
                else:
                    hostport = host
                app.config["SQLALCHEMY_DATABASE_URI"] = (
                    "mysql+pymysql://{}:{}@{}/{}".format(
                        app.config["DB_USER"],
                        app.config["DB_PASS"],
                        hostport,
                        app.config["DB_NAME"],
                    )
                )

    # Set Gmail redirect URI if provided
    app.config["GMAIL_REDIRECT_URI"] = os.environ.get("GMAIL_REDIRECT_URI")

    # register blueprints
    app.register_blueprint(pages)
    app.register_blueprint(api)
    app.register_blueprint(cron)

    # initialize database connection
    db.init_app(app)

    # application to convert the probability to risk factor in html.jinja
    @app.context_processor
    def my_utility_processor():
        def probability_to_risk(closure_value):
            flag = ""
            if closure_value == 1:
                flag = "Very Low"
            elif closure_value == 2:
                flag = "Low"
            elif closure_value == 3:
                flag = "Moderate"
            elif closure_value == 4:
                flag = "High"
            elif closure_value == 5:
                flag = "Very High"
            return flag

        return dict(probability_to_risk=probability_to_risk)

    @app.route("/__/auth", methods=["POST", "GET"])
    def proxy_to_firebase():
        id_token = request.headers.get("Authorization", "").split(" ").pop()
        try:
            auth.verify_id_token(id_token)
        except ValueError:
            firebase_url = "https://ncsu-shellcast.firebaseio.com" + request.full_path
            resp = requests.request(
                method=request.method,
                url=firebase_url,
                headers={
                    key: value for (key, value) in request.headers if key != "Host"
                },
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False,
            )
            excluded_headers = [
                "content-encoding",
                "content-length",
                "transfer-encoding",
                "connection",
            ]
            headers = [
                (name, value)
                for (name, value) in resp.raw.headers.items()
                if name.lower() not in excluded_headers
            ]
            response = Response(resp.content, resp.status_code, headers)
            return response

    return app


# Alias for tests that use createApp(config)
createApp = create_app

app = None

# if running the file directly
if __name__ == "__main__":
    logging.info("Starting app with development configuration")
    app = create_app()
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT") or 0),
        debug=os.environ.get("DEBUG", "false").lower() == "true",
    )
else:
    # run from WSGI (e.g. gunicorn on GAE); entrypoint in app.yaml: gunicorn -b :$PORT main:app
    logging.info("Starting app with production configuration")
    app = create_app()
    application = app  # alias for runtimes that expect "application"
