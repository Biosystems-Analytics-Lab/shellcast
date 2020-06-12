import pytest

from models.TextDisclaimer import TextDisclaimer

def test_valid(dbSession, genRandomString):
  validDisclaimer1 = TextDisclaimer(webapp_page='/index', disclaimer_text='This is my disclaimer text. This application is not indicative of whether or not a lease or grow area will actually be closed. It simply provides a prediction.')

  dbSession.add(validDisclaimer1)
  dbSession.commit()

  assert validDisclaimer1.id == 1

  res = TextDisclaimer.query.all()

  assert len(res) == 1
  assert res[0].webapp_page == validDisclaimer1.webapp_page
  assert res[0].disclaimer_text == validDisclaimer1.disclaimer_text

  additionalDisclaimers = [
    TextDisclaimer(webapp_page='/' + genRandomString(length=12), disclaimer_text=genRandomString(length=143)),
    TextDisclaimer(webapp_page='/' + genRandomString(length=49), disclaimer_text=genRandomString(length=77)),
    TextDisclaimer(webapp_page='/' + genRandomString(length=24), disclaimer_text=genRandomString(length=230))
  ]

  dbSession.add_all(additionalDisclaimers)
  dbSession.commit()

  assert additionalDisclaimers[0].id == 2
  assert additionalDisclaimers[1].id == 3
  assert additionalDisclaimers[2].id == 4

  res = TextDisclaimer.query.all()

  assert len(res) == len(additionalDisclaimers) + 1

def test_asDict(genRandomString):
  disclaimer = TextDisclaimer(webapp_page=genRandomString(length=31), disclaimer_text='blah')

  dictForm = disclaimer.asDict()

  assert dictForm['webapp_page'] == disclaimer.webapp_page
  assert dictForm['disclaimer_text'] == disclaimer.disclaimer_text

def test_repr(genRandomString):
  disclaimer = TextDisclaimer(webapp_page=genRandomString(length=31), disclaimer_text='blah')

  stringForm = disclaimer.__repr__()

  assert 'TextDisclaimer' in stringForm
  assert disclaimer.webapp_page in stringForm
  assert disclaimer.disclaimer_text in stringForm
