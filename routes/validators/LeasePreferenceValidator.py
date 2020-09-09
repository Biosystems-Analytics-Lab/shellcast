import re

class LeasePreferenceValidator():
  """
  Validates form data submitted for profile information.
  NOTE: This validator assumes that a complete set of the data is given for
  each field.  i.e. If there are 3 fields (email_pref, text_pref, prob_pref),
  the current values for each field must be given even if only one field is 
  actually being updated.
  """

  def __init__(self, json):
    self.email_pref = json.get('email_pref')
    self.text_pref = json.get('text_pref')
    self.prob_pref = json.get('prob_pref')

    self.errors = []

  def addError(self, message):
    self.errors.append(message)
    return False

  def validate(self):
    validators = [self.validateEmailPref, self.validateTextPref, self.validateProbPref]
    valid = True
    for validator in validators:
      if (not validator()):
        valid = False
    return valid

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
