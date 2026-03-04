def test_index(client):
    res = client.get("/")
    assert res.status_code == 200


def test_about(client):
    res = client.get("/about")
    assert res.status_code == 200


def test_preferences(client):
    res = client.get("/preferences")
    assert res.status_code == 200


def test_signin(client):
    res = client.get("/signin")
    assert res.status_code == 200


def test_faqs(client):
    res = client.get("/faqs")
    assert res.status_code == 200


def test_feedback(client):
    res = client.get("/feedback")
    assert res.status_code == 200


def test_how_it_works(client):
    res = client.get("/how-it-works")
    assert res.status_code == 200


def test_map(client):
    res = client.get("/map")
    assert res.status_code == 200


def test_notification_service(client):
    res = client.get("/notification-service")
    assert res.status_code == 200
