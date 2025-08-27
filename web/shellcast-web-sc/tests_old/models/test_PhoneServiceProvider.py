import pytest

from models.PhoneServiceProvider import PhoneServiceProvider

def test_PhoneServiceProvider(dbSession):
  validProvider1 = PhoneServiceProvider(name='Verizon', mms_gateway='vzwpix.com', sms_gateway='vtext.com')

  dbSession.add(validProvider1)
  dbSession.commit()

  assert validProvider1.id == 1

  res = PhoneServiceProvider.query.all()

  assert len(res) == 1
  assert res[0].name == validProvider1.name
  assert res[0].mms_gateway == validProvider1.mms_gateway
  assert res[0].sms_gateway == validProvider1.sms_gateway

def test_asDict():
  provider = PhoneServiceProvider(name='Verizon', mms_gateway='vzwpix.com', sms_gateway='vtext.com')

  dictForm = provider.asDict()

  assert dictForm['name'] == provider.name
  assert dictForm['mms_gateway'] == provider.mms_gateway
  assert dictForm['sms_gateway'] == provider.sms_gateway

def test_repr():
  provider = PhoneServiceProvider(name='Verizon', mms_gateway='vzwpix.com', sms_gateway='vtext.com')

  stringForm = provider.__repr__()

  assert 'PhoneServiceProvider' in stringForm
  assert provider.name in stringForm
  assert provider.mms_gateway in stringForm
  assert provider.sms_gateway in stringForm
