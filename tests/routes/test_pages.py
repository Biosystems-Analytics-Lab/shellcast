import pytest

def test_index(client):
  res = client.get('/')
  assert res.status_code == 200

def test_about(client):
  res = client.get('/about')
  assert res.status_code == 200

def test_notifications(client):
  res = client.get('/notifications')
  assert res.status_code == 200
