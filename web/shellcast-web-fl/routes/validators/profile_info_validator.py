import re

from email_validator import EmailNotValidError, validate_email


class ProfileInfoValidator:
    """
    Validates form data submitted for profile information.
    NOTE: This validator assumes that a complete set of the data is given for
    each field.  i.e. If there are 6 fields (email, phone number,
    service provider, email preference, text preference, probability
    preference), the current values for each field must be given even if only
    one field is actually being updated.
    """

    def __init__(self, json):
        self.email = json.get("email")
        self.phone_number = json.get("phone_number")
        self.email_pref = json.get("email_pref")
        self.text_pref = json.get("text_pref")
        self.prob_pref = json.get("prob_pref")
        self.text_consent = json.get("text_consent")

        self.errors = []

    def add_error(self, message):
        self.errors.append(message)
        return False

    def validate(self):
        validators = [
            self._validate_email,
            self._validate_phone_number,
            self._validate_email_pref,
            self._validate_text_pref,
            self._validate_prob_pref,
            self._validate_text_consent,
        ]
        valid = True
        for validator in validators:
            if not validator():
                valid = False
        return valid

    def _validate_email(self):
        if not self.email_pref:
            # When email_pref is off, don't require or update email; leave as None so API preserves existing.
            self.email = None
            return True
        if not self.email or not str(self.email).strip():
            return self.add_error(
                "An email address is required when email notifications are enabled."
            )
        try:
            validated_email = validate_email(self.email)
            self.email = validated_email.normalized  # Update with the normalized form.
        except EmailNotValidError as e:
            print(str(e))
            return self.add_error("Email is not valid.")
        return True

    def _validate_phone_number(self):
        if not self.phone_number:
            self.phone_number = None
            return True
        if not re.search(r"^\d{10}$", self.phone_number):
            return self.add_error("The phone number must be 10 digits long.")
        return True

    def _validate_email_pref(self):
        if not isinstance(self.email_pref, bool):
            return self.add_error("Email preference must be true or false.")
        return True

    def _validate_text_pref(self):
        if not isinstance(self.text_pref, bool):
            return self.add_error("Text preference must be true or false.")
        return True

    def _validate_prob_pref(self):
        try:
            prob_pref_int = int(self.prob_pref)
        except Exception:
            return self.add_error("Probability preference must be an integer.")
        if prob_pref_int not in [3, 4, 5]:
            return self.add_error("Probability preference must be 3, 4, or 5.")
        return True

    def _validate_text_consent(self):
        if not isinstance(self.text_consent, bool):
            return self.add_error("Text consent must be true or false.")
        return True
