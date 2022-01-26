from flask import Blueprint, render_template, current_app
from models import db
from models.CMUProbability import CMUProbability
from models.PhoneServiceProvider import PhoneServiceProvider

from datetime import datetime, timezone, timedelta
import pytz

# the number of seconds in one hour
SECONDS_IN_HOURS = 3600

pages = Blueprint('', __name__)
@pages.route('/')
def indexPage():
  lastGrowingUnitProb = db.session.query(CMUProbability).order_by(CMUProbability.id.desc()).first()
  templateVals = {
    'mapsAPIKey': current_app.config['MAPS_API_KEY'],
    'lastUpdated': 'No calculations run yet',
    'hoursAgo': '?',
    'day1': '?',
    'day2': '?',
    'day3': '?'
  }
  if (lastGrowingUnitProb):
    lastUpdatedTimeUTC = lastGrowingUnitProb.updated.replace(tzinfo=timezone.utc)
    curTimeUTC = datetime.now(timezone.utc)
    duration = curTimeUTC - lastUpdatedTimeUTC
    durationSecs = duration.total_seconds()
    templateVals['hoursAgo'] = int(divmod(durationSecs, SECONDS_IN_HOURS)[0])
    lastUpdatedTimeEST = lastUpdatedTimeUTC.astimezone(pytz.timezone('US/Eastern'))
    templateVals['lastUpdated'] = lastUpdatedTimeEST.strftime('%B %d, %Y %I:%M %p') # ex: July 24, 2020 04:14 PM
    templateVals['day1'] = lastUpdatedTimeEST.strftime('%B %d (%A)')
    templateVals['day2'] = (lastUpdatedTimeEST + timedelta(days=1)).strftime('%B %d (%A)')
    templateVals['day3'] = (lastUpdatedTimeEST + timedelta(days=2)).strftime('%B %d (%A)')
  return render_template('index.html.jinja', **templateVals)

@pages.route('/about')
def aboutPage():
  return render_template('about.html.jinja')

@pages.route('/how-it-works')
def howItWorksPage():
  return render_template('how-it-works.html.jinja')

@pages.route('/faqs')
def faqsPage():
  return render_template('faqs.html.jinja')

@pages.route('/preferences')
def preferencesPage():
  serviceProviders = db.session.query(PhoneServiceProvider.id, PhoneServiceProvider.name).all()
  probOptions = [3, 4, 5]
  return render_template('preferences.html.jinja', serviceProviders=serviceProviders, probOptions=probOptions)

@pages.route('/signin')
def signinPage():
  return render_template('signin.html.jinja')

@pages.route('/feedback')
def feedbackPage():
  return render_template('feedback.html.jinja')
