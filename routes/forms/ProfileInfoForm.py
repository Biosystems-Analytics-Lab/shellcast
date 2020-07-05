from wtforms import Form, StringField, validators

PHONE_NUMBER_LENGTH = 10

class ProfileInfoForm(Form):
  email = StringField('Email', [validators.Email(message='That\'s not a valid email address.')])
  phone_number = StringField('Phone number', [
    validators.Regexp(r'^\d{10}$', message='Phone number must be exactly 10 digits.')
  ])

  @staticmethod
  def from_json(json):
    return ProfileInfoForm(**json)
