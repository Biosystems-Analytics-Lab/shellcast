from flask import Blueprint, render_template, current_app
from models.ClosureProbability import ClosureProbability

import logging

pages = Blueprint('', __name__)
@pages.route('/')
def indexPage():
  return render_template('index.html.jinja', mapsAPIKey=current_app.config['MAPS_API_KEY'])

@pages.route('/about')
def aboutPage():
  return render_template('about.html.jinja')

@pages.route('/notifications')
def notificationsPage():
  return render_template('notifications.html.jinja')

@pages.route('/signin')
def signinPage():
  return render_template('signin.html.jinja')

@pages.route('/super-special-extra-secret-test-route')
def test():
  print('Test print: blah blah')
  logging.debug('Test logging.debug: superfluous stuff')
  logging.info('Test logging.info: normal stuff')
  logging.warning('Test logging.warning: potentially bad stuff')
  logging.error('Test logging.error: bad stuff')
  logging.exception('Test logging.exception: worse stuff')
  logging.critical('Test logging.critical: absolutely terrible stuff')
  return 'This is just a testing route.  How\'d you find this?'

