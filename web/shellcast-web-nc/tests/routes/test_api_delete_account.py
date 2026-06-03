from models.User import User


def test_delete_account(client, db_session, add_mock_fb_user):
    # check to make sure that there are no users in the database
    results = db_session.query(User).all()
    assert len(results) == 0

    # add two mock Firebase users
    add_mock_fb_user(dict(uid="blah1", email="blah1@gmail.com"), "validUser1")
    user1 = User(
        firebase_uid="blah1",
        email="blah1@gmail.com",
        phone_number="1234567890",
        email_pref=True,
        text_pref=True,
        text_consent=True,
        prob_pref=3,
    )
    add_mock_fb_user(dict(uid="blah2", email="blah2@gmail.com"), "validUser2")
    user2 = User(
        firebase_uid="blah2",
        email="blah2@gmail.com",
        phone_number="1234567890",
        email_pref=True,
        text_pref=True,
        text_consent=True,
        prob_pref=3,
    )
    db_session.add(user1)
    db_session.add(user2)
    db_session.commit()

    # make sure they're both in the db
    res = client.get("/user-info", headers={"Authorization": "validUser1"})
    assert res.status_code == 200
    res = client.get("/user-info", headers={"Authorization": "validUser2"})
    assert res.status_code == 200
    results = db_session.query(User).all()
    assert len(results) == 2

    # delete the first user
    res = client.get("/delete-account", headers={"Authorization": "validUser1"})
    assert res.status_code == 200
    users = db_session.query(User).all()
    assert users[0].firebase_uid is None
    assert users[0].email is None
    assert users[0].phone_number is None
    assert users[0].email_pref is User.DEFAULT_email_pref
    assert users[0].text_pref is User.DEFAULT_text_pref
    assert users[0].text_consent is User.DEFAULT_text_consent
    assert users[0].prob_pref == User.DEFAULT_prob_pref
    assert users[0].deleted is True

    assert users[1].firebase_uid == "blah2"
    assert users[1].email == "blah2@gmail.com"
    assert users[1].phone_number == "1234567890"
    assert users[1].email_pref is True
    assert users[1].text_pref is True
    assert users[1].text_consent is True
    assert users[1].prob_pref == 3
    assert users[1].deleted is False

    # delete the second user
    res = client.get("/delete-account", headers={"Authorization": "validUser2"})
    assert res.status_code == 200
    users = db_session.query(User).all()
    assert users[0].firebase_uid is None
    assert users[0].email is None
    assert users[0].phone_number is None
    assert users[0].email_pref is User.DEFAULT_email_pref
    assert users[0].text_pref is User.DEFAULT_text_pref
    assert users[0].text_consent is User.DEFAULT_text_consent
    assert users[0].prob_pref == User.DEFAULT_prob_pref
    assert users[0].deleted is True

    assert users[1].firebase_uid is None
    assert users[1].email is None
    assert users[1].phone_number is None
    assert users[1].email_pref is User.DEFAULT_email_pref
    assert users[1].text_pref is User.DEFAULT_text_pref
    assert users[1].text_consent is User.DEFAULT_text_consent
    assert users[1].prob_pref == User.DEFAULT_prob_pref
    assert users[1].deleted is True


def test_delete_nonexistent_user(client, add_mock_fb_user):
    # add two mock Firebase users
    add_mock_fb_user(dict(uid="blah1", email="blah1@gmail.com"), "validUser1")
    add_mock_fb_user(dict(uid="blah2", email="blah2@gmail.com"), "validUser2")

    # try to delete another user
    res = client.get("/delete-account", headers={"Authorization": "validUser3"})
    # user_required should prevent delete_account from running and return 401
    # from running and just return a 401
    assert res.status_code == 401
