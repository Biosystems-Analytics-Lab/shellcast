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

@pages.route('/preferences')
def preferencesPage():
  return render_template('preferences.html.jinja')

@pages.route('/signin')
def signinPage():
  return render_template('signin.html.jinja')
