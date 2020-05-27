import pytest

from main import createApp

from config import TestConfig

@pytest.fixture
def client():
  app = createApp(TestConfig())

  with app.test_client() as client:
    yield client

def test_index(client):
  res = client.get('/')
  assert res.status_code == 200

def test_about(client):
  res = client.get('/about')
  assert res.status_code == 200

def test_notifications(client):
  res = client.get('/notifications')
  assert res.status_code == 200

def test_areaData(client):
  res = client.get('/areaData')
  assert res.status_code == 200
  json = res.get_json()
  assert len(json) == 73
  assert json['A01']['prob1Day'] == 16