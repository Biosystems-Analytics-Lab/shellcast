from datetime import datetime, timezone, timedelta

import pytz
from flask import Blueprint, render_template
from models import db
from models.CMUProbability import CMUProbability
from models.PhoneServiceProvider import PhoneServiceProvider

# the number of seconds in one hour
SECONDS_IN_HOURS = 3600

pages = Blueprint('shellcast-sc', __name__)


@pages.route('/')
def indexPage():
    return render_template('index.html')


@pages.route('/map')
def mapPage():
    lastGrowingUnitProb = db.session.query(CMUProbability).order_by(CMUProbability.id.desc()).first()
    templateVals = {
        'lastUpdated': 'No calculations run yet',
        'hoursAgo': '?',
        'day1': '?',
        'day2': '?',
        'day3': '?'
    }
    if (lastGrowingUnitProb):
        local = pytz.timezone('US/Eastern')
        local_dt = local.localize(lastGrowingUnitProb.created, is_dst=None)
        lastUpdatedTimeUTC = local_dt.astimezone(pytz.utc)
        curTimeUTC = datetime.now(timezone.utc)
        duration = curTimeUTC - lastUpdatedTimeUTC
        durationSecs = duration.total_seconds()
        templateVals['hoursAgo'] = int(divmod(durationSecs, SECONDS_IN_HOURS)[0])
        lastUpdatedTimeEST = lastUpdatedTimeUTC.astimezone(local)

        templateVals['hoursAgo'] = int(divmod(durationSecs, SECONDS_IN_HOURS)[0])
        templateVals['lastUpdated'] = lastUpdatedTimeEST.strftime('%B %d, %Y %I:%M %p')  # ex: July 24, 2020 04:14 PM
        templateVals['day1'] = lastUpdatedTimeEST.strftime('%B %d (%A)')
        templateVals['day2'] = (lastUpdatedTimeEST + timedelta(days=1)).strftime('%B %d (%A)')
        templateVals['day3'] = (lastUpdatedTimeEST + timedelta(days=2)).strftime('%B %d (%A)')
    return render_template('map.html', **templateVals)


@pages.route('/about')
def aboutPage():
    return render_template('about.html')


@pages.route('/how-it-works')
def howItWorksPage():
    return render_template('how-it-works.html')


@pages.route('/faqs')
def faqsPage():
    return render_template('faqs.html')


def temp_remove_verizon(serviceProviders):
    """ Temporarily remove Verizon from the list of service providers
    """
    verizon_idx = None
    for idx, item in enumerate(serviceProviders):
        if item.name == 'Verizon':
            verizon_idx = idx
            break
    if verizon_idx is not None:
        serviceProviders.pop(verizon_idx)
    return serviceProviders


@pages.route('/preferences')
def preferencesPage():
    serviceProviders = db.session.query(PhoneServiceProvider.id, PhoneServiceProvider.name).all()
    probOptions = [3, 4, 5]
    return render_template('preferences.html', serviceProviders=temp_remove_verizon(serviceProviders),
                           probOptions=probOptions)


@pages.route('/signin')
def signinPage():
    return render_template('signin.html')


@pages.route('/feedback')
def feedbackPage():
    return render_template('feedback.html')
