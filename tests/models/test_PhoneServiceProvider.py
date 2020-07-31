import pytest

from models.PhoneServiceProvider import PhoneServiceProvider

def test_PhoneServiceProvider(dbSession):
  validProvider1 = PhoneServiceProvider(name='Verizon', mms_gateway='vzwpix.com')

  dbSession.add(validProvider1)
  dbSession.commit()

  assert validProvider1.id == 1

  res = PhoneServiceProvider.query.all()

  assert len(res) == 1
  assert res[0].name == validProvider1.name
  assert res[0].mms_gateway == validProvider1.mms_gateway

def test_asDict(genRandomString):
  provider = PhoneServiceProvider(name='Verizon', mms_gateway='vzwpix.com')

  dictForm = provider.asDict()

  assert dictForm['name'] == provider.name
  assert dictForm['mms_gateway'] == provider.mms_gateway

def test_repr(genRandomString):
  provider = PhoneServiceProvider(name='Verizon', mms_gateway='vzwpix.com')

  stringForm = provider.__repr__()

  assert 'PhoneServiceProvider' in stringForm
  assert provider.name in stringForm
  assert provider.mms_gateway in stringForm
