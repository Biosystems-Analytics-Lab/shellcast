from email_validator import validate_email, EmailNotValidError
import re

class ProfileInfoValidator():
  def __init__(self, json, possibleServiceProviders):
    self.json = json
    self.email = json.get('email')
    self.phone_number = json.get('phone_number')
    self.service_provider_id = json.get('service_provider_id')
    self.possibleServiceProviders = possibleServiceProviders

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
      return True
    try:
      valid = validate_email(self.email)
      # Update with the normalized form.
      self.email = valid.email
    except EmailNotValidError as e:
      print(str(e))
      return self.addError('Email is not valid.')
    return True

  def validate_phone_number(self):
    if (self.phone_number and not self.service_provider_id):
      return self.addError('When providing a phone number, a service provider is required.')
    if (not re.search(r'^\d{10}$', self.phone_number)):
      return self.addError('Phone number must be 10 digits.')
    return True

  def validate_service_provider_id(self):
    if (self.service_provider_id and not self.phone_number):
      return self.addError('When providing a service provider, a phone number is required.')
    if (not int(self.service_provider_id) in self.possibleServiceProviders):
      return self.addError('The given service provider does not exist in the database.')
    return True
