from email_validator import validate_email, EmailNotValidError
import re

from models import db
from models.PhoneServiceProvider import PhoneServiceProvider

class ProfileInfoValidator():
  """
  Validates form data submitted for profile information.
  NOTE: This validator assumes that a complete set of the data is given for
  each field.  i.e. If there are 3 fields (email, phone number, service provider),
  the current values for each field must be given even if only one field is 
  actually being updated.
  """

  def __init__(self, json):
    self.email = json.get('email')
    self.phone_number = json.get('phone_number')
    self.service_provider_id = json.get('service_provider_id')

    self.errors = []

  def addError(self, message):
    self.errors.append(message)
    return False

  def validate(self):
    validators = [self.validateEmail, self.validatePhoneNumber, self.validateServiceProviderId]
    valid = True
    for validator in validators:
      if (not validator()):
        valid = False
    return valid

  def validateEmail(self):
    if (not self.email):
      return self.addError('An email address is always required.')
    try:
      validatedEmail = validate_email(self.email)
      self.email = validatedEmail.email # Update with the normalized form.
    except EmailNotValidError as e:
      print(str(e))
      return self.addError('Email is not valid.')
    return True

  def validatePhoneNumber(self):
    if (not self.phone_number):
      self.phone_number = None
      self.service_provider_id = None
      return True
    if (not re.search(r'^\d{10}$', self.phone_number)):
      return self.addError('The phone number must be 10 digits long.')
    if (self.phone_number and not self.service_provider_id):
      return self.addError('When providing a phone number, a service provider is required.')
    return True

  def validateServiceProviderId(self):
    if (not self.service_provider_id and not self.phone_number):
      self.phone_number = None
      self.service_provider_id = None
      return True
    possibleServiceProviders = list(map(lambda x: x[0], db.session.query(PhoneServiceProvider.id).all()))
    if (not self.service_provider_id or not int(self.service_provider_id) in possibleServiceProviders):
      return self.addError('The given service provider does not exist in the database.')
    return True
