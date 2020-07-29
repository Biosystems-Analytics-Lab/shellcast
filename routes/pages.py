from flask import Blueprint, render_template, current_app
from models import db
from models.SGAMinMaxProbability import SGAMinMaxProbability

from datetime import datetime, timezone
import pytz

# the number of seconds in one hour
SECONDS_IN_HOURS = 3600

pages = Blueprint('', __name__)
@pages.route('/')
def indexPage():
  lastGrowAreaProb = db.session.query(SGAMinMaxProbability).order_by(SGAMinMaxProbability.id.desc()).first()
  if (lastGrowAreaProb):
    lastUpdatedTimeUTC = lastGrowAreaProb.updated.replace(tzinfo=timezone.utc)
    curTimeUTC = datetime.now(timezone.utc)
    duration = curTimeUTC - lastUpdatedTimeUTC
    durationSecs = duration.total_seconds()
    durationHours = int(divmod(durationSecs, SECONDS_IN_HOURS)[0])
    lastUpdatedTimeESTFormatted = lastUpdatedTimeUTC.astimezone(pytz.timezone('US/Eastern')).strftime("%B %d, %Y %I:%M %p") # ex: July 24, 2020 04:14 PM
    return render_template('index.html.jinja', mapsAPIKey=current_app.config['MAPS_API_KEY'], lastUpdated=lastUpdatedTimeESTFormatted, hoursAgo=durationHours)
  else:
    return render_template('index.html.jinja', mapsAPIKey=current_app.config['MAPS_API_KEY'], lastUpdated="No calculations run yet", hoursAgo="?")

@pages.route('/about')
def aboutPage():
  return render_template('about.html.jinja')

@pages.route('/preferences')
def preferencesPage():
  return render_template('preferences.html.jinja')

@pages.route('/signin')
def signinPage():
  return render_template('signin.html.jinja')
