import sqlalchemy


class Config(object):
  """
  The configuration used for a production environment.
  """
  # analysis path
  # ANALYSIS_PATH = 'ANALYSIS_DIR_PATH_HERE'
  # data path
  # DATA_PATH = 'DATA_DIR_PATH_HERE'
  # whether or not to log debugging output from Flask
  DEBUG = False
  # whether or not to setup Flask in testing mode
  TESTING = False
  # AWS Access Key ID
  AWS_ACCESS_KEY_ID = 'REDACTED'
  # AWS Secret Access Key
  AWS_SECRET_ACCESS_KEY = 'REDACTED'
  # AWS SES region
  AWS_REGION = 'us-east-1'
  # Google Maps JavaScript API Key
  MAPS_API_KEY = 'REDACTED'
  # For Windows TCP database connection
  DB_HOST = '127.0.0.1'
  DB_PORT = '3306'
  # the username to use to access the database
  DB_USER = 'root'
  # the password for the user
  DB_PASS = 'L3tm3sql!'
  # the name of the database
  DB_NAME = 'shellcast_sc'
  # the path prefix to the location of the Unix socket used to connect to the Cloud SQL database
  DB_UNIX_SOCKET_PATH_PREFIX = '/cloudsql/'
  # the name of the Cloud SQL instance to connect to
  CLOUD_SQL_INSTANCE_NAME = 'ncsu-shellcast:us-east1:ncsu-shellcast-database'
  # whether or not to track modifications in SQLAlchemy
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  # various configuration options for SQLAlchemy
  SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 5, # max number of permanent connections in the connection pool
    'max_overflow': 2, # number of additional connections that can be created over the pool_size
    'pool_timeout': 30, # max number of seconds to wait to get a new connection from the pool
    'pool_recycle': 1800, # max number of seconds a connection can persist
  }
  # the URI used to connect to the database
  @property
  def SQLALCHEMY_DATABASE_URI(self):
    return 'mysql+pymysql://{}:{}@/{}?unix_socket={}{}'.format(self.DB_USER, self.DB_PASS, self.DB_NAME, self.DB_UNIX_SOCKET_PATH_PREFIX, self.CLOUD_SQL_INSTANCE_NAME)

  # @property
  # def SQLALCHEMY_DATABASE_URI(self):
  #   uri = sqlalchemy.engine.url.URL.create(
  #     drivername="mysql+pymysql",
  #     username=Config.DB_USER,
  #     password=Config.DB_PASS,
  #     host=Config.DB_HOST,
  #     port=Config.DB_PORT,
  #     database=Config.DB_NAME
  #   )
  #   return uri.render_as_string(hide_password=False)


class DevConfig(Config):
  """
  The configuration used for local development.
  """
  # whether or not to log debugging output from Flask
  DEBUG = True
  # the IP address of the web server
  HOST = '127.0.0.1'
  # the port that the web server should listen on
  PORT = 3361
  # the name of the database
  DB_NAME = 'shellcast_sc'
  # the path prefix to the location of the Unix socket used to connect to the Cloud SQL database
  DB_UNIX_SOCKET_PATH_PREFIX = './cloudsql/'


class TestConfig(Config):
    """
    The configuration used for unit testing.
    """
    # whether or not to setup Flask in testing mode
    TESTING = True
    # Use SQLite in-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # Disable CSRF protection in tests
    WTF_CSRF_ENABLED = False
    # Use a simple secret key for testing
    SECRET_KEY = 'test-secret-key'
    # Override MySQL-specific options for SQLite
    SQLALCHEMY_ENGINE_OPTIONS = {}


class TestConfigMySQL(Config):
    """
    The configuration used for integration testing with MySQL.
    This ensures tests run against the same database type as production.
    """
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
    
    # Use test database (same type as production)
    DB_NAME = 'shellcast_sc_test'
    
    # Override the database URI to use test database
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        # Use local MySQL for testing (not Cloud SQL)
        return f'mysql+pymysql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
    
    # Keep production-like engine options for realistic testing
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 2,  # Smaller pool for testing
        'max_overflow': 1,
        'pool_timeout': 10,
        'pool_recycle': 1800,
    }
