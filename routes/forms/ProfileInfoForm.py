from wtforms import Form, StringField, SelectField, validators, ValidationError

PHONE_NUMBER_LENGTH = 10

class ProfileInfoForm(Form):
  email = StringField('Email', [validators.Email(message='That\'s not a valid email address.')])
  phone_number = StringField('Phone number', [
    validators.Optional(), validators.Regexp(r'^\d{10}$', message='Phone number must be exactly 10 digits.')
  ])
  service_provider_id = SelectField('Service provider', coerce=int, choices=[('', '-- Select one --')])

  def validate_phone_number(self, field):
    if field.data and not self.service_provider_id.data:
      raise ValidationError('When providing a phone number, a service provider is required')

  def validate_service_provider_id(self, field):
    if field.data and not self.phone_number.data:
      raise ValidationError('When providing a service provider, a phone number is required')

  @staticmethod
  def from_json(json):
    return ProfileInfoForm(**json)
