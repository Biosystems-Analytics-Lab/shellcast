import unittest
from main import createApp
from config import TestConfig, Config
from main import createApp

class TestFoo(unittest.TestCase):

    def setUp(self):
        self.app = createApp(TestConfig)
        print(Config.SQLALCHEMY_DATABASE_URI)
        print('here')

    def test_Print(self):
        print('here')

    # app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI

    # def test_foo_with_client(self, client):
    #     # Use the client here
    #     # Example request to a route returning "hello world" (on a hypothetical app)
    #     response = client.get('/leases')
    #     print(response)








