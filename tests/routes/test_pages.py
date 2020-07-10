import pytest

def test_index(client):
  res = client.get('/')
  assert res.status_code == 200

def test_about(client):
  res = client.get('/about')
  assert res.status_code == 200

def test_preferences(client):
  res = client.get('/preferences')
  assert res.status_code == 200

def test_signin(client):
  res = client.get('/signin')
  assert res.status_code == 200
