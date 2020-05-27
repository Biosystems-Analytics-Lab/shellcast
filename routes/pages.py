from flask import Blueprint, render_template, current_app
from models.ClosureProbability import ClosureProbability

pages = Blueprint('', __name__)
@pages.route('/')
def indexPage():
  return render_template('index.html.jinja', mapsAPIKey=current_app.config['MAPS_API_KEY'])


@pages.route('/test')
def test():
  print(ClosureProbability.query.all())
  return 'blah'

@pages.route('/about')
def aboutPage():
  return render_template('about.html.jinja')

@pages.route('/notifications')
def notificationsPage():
  return render_template('notifications.html.jinja')

