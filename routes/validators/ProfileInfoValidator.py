from email_validator import validate_email, EmailNotValidError
import re

from models import db
from models.PhoneServiceProvider import PhoneServiceProvider

class ProfileInfoValidator():
  """
  Validates form data submitted for profile information.
  NOTE: This validator assumes that a complete set of the data is given for
  each field.  i.e. If there are 6 fields (email, phone number,
  service provider, email preference, text preference, probability
  preference), the current values for each field must be given even if only
  one field is actually being updated.
  """

  def __init__(self, json):
    self.email = json.get('email')
    self.phone_number = json.get('phone_number')
    self.service_provider_id = json.get('service_provider_id')
    self.email_pref = json.get('email_pref')
    self.text_pref = json.get('text_pref')
    self.prob_pref = json.get('prob_pref')

    self.errors = []

  def addError(self, message):
    self.errors.append(message)
    return False

  def validate(self):
    validators = [
      self.validateEmail, self.validatePhoneNumber, self.validateServiceProviderId,
      self.validateEmailPref, self.validateTextPref, self.validateProbPref
    ]
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

  def validateEmailPref(self):
    if (self.email_pref != True and self.email_pref != False):
      return self.addError('Email preference must be true or false.')
    return True

  def validateTextPref(self):
    if (self.text_pref != True and self.text_pref != False):
      return self.addError('Text preference must be true or false.')
    return True

  def validateProbPref(self):
    try:
      probPrefInt = int(self.prob_pref)
    except Exception:
      return self.addError('Probability preference must be an integer.')
    if (probPrefInt < 0 or probPrefInt > 100):
      return self.addError('Probability preference must be between 0 and 100.')
    return True