class Config(object):
  DEBUG = False
  TESTING = False
  MAPS_API_KEY = "REDACTED"

class DevConfig(Config):
  DEBUG = True
  HOST = '127.0.0.1'
  PORT = 3361

class TestConfig(Config):
  TESTING = True
