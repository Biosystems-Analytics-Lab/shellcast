from email_validator import validate_email, EmailNotValidError
import re

from models import db
from models.PhoneServiceProvider import PhoneServiceProvider

class ProfileInfoValidator():
  def __init__(self, json):
    self.email = json.get('email')
    self.phone_number = json.get('phone_number')
    self.service_provider_id = json.get('service_provider_id')

    self.errors = []

  def addError(self, message):
    self.errors.append(message)
    return False

  def validate(self):
    validators = [self.validate_email, self.validate_phone_number, self.validate_service_provider_id]
    for validator in validators:
      if (not validator()):
        return False
    return True

  def validate_email(self):
    if (not self.email):
      return self.addError('An email address is always required.')
    try:
      valid = validate_email(self.email)
      self.email = valid.email # Update with the normalized form.
    except EmailNotValidError as e:
      print(str(e))
      return self.addError('Email is not valid.')
    return True

  def validate_phone_number(self):
    if (not self.phone_number):
      self.phone_number = None
      self.service_provider_id = None
      return True
    if (self.phone_number and self.service_provider_id == None):
      return self.addError('When providing a phone number, a service provider is required.')
    if (not re.search(r'^\d{10}$', self.phone_number)):
      return self.addError('Phone number must be 10 digits.')
    return True

  def validate_service_provider_id(self):
    if (not self.service_provider_id and not self.phone_number):
      self.phone_number = None
      self.service_provider_id = None
      return True
    possibleServiceProviders = list(map(lambda x: x[0], db.session.query(PhoneServiceProvider.id).all()))
    if (not self.service_provider_id or not int(self.service_provider_id) in possibleServiceProviders):
      return self.addError('The given service provider does not exist in the database.')
    return True
