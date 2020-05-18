import pytest

import main

from config import TestConfig

@pytest.fixture
def client():
  main.app.config.from_object(TestConfig())

  with main.app.test_client() as client:
    yield client

def test_index(client):
  res = client.get('/')
  assert res.status_code == 200