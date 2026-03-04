from models.CMU import CMU


def test_valid(db_session):
    validUnit1 = CMU(cmu_name="U001")

    db_session.add(validUnit1)
    db_session.commit()

    assert validUnit1.id == 1

    res = CMU.query.all()

    assert len(res) == 1
    assert res[0].cmu_name == validUnit1.cmu_name

    additionalUnits = [CMU(cmu_name="U023"), CMU(cmu_name="U004"), CMU(cmu_name="U128")]

    db_session.add_all(additionalUnits)
    db_session.commit()

    assert additionalUnits[0].id == 2
    assert additionalUnits[1].id == 3
    assert additionalUnits[2].id == 4

    res = CMU.query.all()

    assert len(res) == len(additionalUnits) + 1


def test_asDict(gen_random_string):
    unit = CMU(cmu_name="U001")

    dictForm = unit.as_dict()

    assert dictForm["cmu_name"] == unit.cmu_name


def test_repr(gen_random_string):
    unit = CMU(cmu_name="U007")

    stringForm = unit.__repr__()

    assert "CMU" in stringForm
    assert unit.cmu_name in stringForm
