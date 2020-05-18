class Config(object):
  DEBUG = False
  TESTING = False
  MAPS_API_KEY = "AIzaSyCpBaOeKIFy7F7S261eOkZcBuke3Y-d_Y8"

class DevConfig(Config):
  DEBUG = True
  HOST = '127.0.0.1'
  PORT = 3361

class TestConfig(Config):
  TESTING = True
