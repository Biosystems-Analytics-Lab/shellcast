from models.User import User


def test_user(db_session):
    user = User(
        firebase_uid="3sH9so5Y3DP72QA1XqbWw9J6I8o1",
        email="asdf@adf.com",
        phone_number="1234567890",
    )

    db_session.add(user)
    db_session.commit()

    assert user.id == 1

    res = User.query.all()

    assert len(res) == 1
    assert res[0].firebase_uid == user.firebase_uid
    assert res[0].email == user.email
    assert res[0].phone_number == user.phone_number
    assert res[0].email_pref is False
    assert res[0].text_pref is False
    assert res[0].prob_pref == user.prob_pref
    assert res[0].email_consent is False
    assert res[0].text_consent is False
    assert res[0].email_verification_sent is False
    assert res[0].text_verification_sent is False
    assert res[0].deleted is False


def test_as_dict(gen_random_string):
    user = User(
        firebase_uid=gen_random_string(length=28),
        email=gen_random_string(length=13),
        phone_number=gen_random_string(length=11),
    )

    dict_form = user.as_dict()

    assert dict_form["firebase_uid"] == user.firebase_uid
    assert dict_form["phone_number"] == user.phone_number
    assert dict_form["email"] == user.email
    assert dict_form["email_pref"] == user.email_pref
    assert dict_form["email_consent"] == user.email_consent
    assert dict_form["text_pref"] == user.text_pref
    assert dict_form["text_consent"] == user.text_consent
    assert dict_form["prob_pref"] == user.prob_pref
    assert dict_form["email_verification_sent"] == user.email_verification_sent
    assert dict_form["text_verification_sent"] == user.text_verification_sent


def test_repr(gen_random_string):
    user = User(
        firebase_uid=gen_random_string(length=28),
        email=gen_random_string(length=13),
        phone_number=gen_random_string(length=11),
    )

    string_form = user.__repr__()

    assert "User" in string_form
    assert user.email in string_form
