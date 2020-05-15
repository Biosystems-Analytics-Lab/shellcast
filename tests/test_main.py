import pytest

import main

@pytest.fixture
def client():
  main.app.config['TESTING'] = True

  with main.app.test_client() as client:
    yield client

def test_index(client):
  res = client.get('/')
  assert res.status_code == 200