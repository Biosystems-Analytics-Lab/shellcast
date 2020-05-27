class Config(object):
  """
  The configuration used for a production environment.
  """
  # whether or not to log debugging output from Flask
  DEBUG = False
  # whether or not to setup Flask in testing mode
  TESTING = False
  # Google Maps JavaScript API Key
  MAPS_API_KEY = ''
  # the username to use to access the database
  DB_USER = ''
  # the password for the user
  DB_PASS = ''
  # the name of the database
  DB_NAME = 'shellcast'
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
  DB_NAME = 'shellcast'
  # the path prefix to the location of the Unix socket used to connect to the Cloud SQL database
  DB_UNIX_SOCKET_PATH_PREFIX = './cloudsql/'


class TestConfig(Config):
  """
  The configuration used for unit testing.
  """
  # whether or not to setup Flask in testing mode
  TESTING = True
