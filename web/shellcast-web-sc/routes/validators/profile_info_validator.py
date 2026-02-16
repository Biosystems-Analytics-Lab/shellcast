"""
Profile Information Validator

This module provides validation for user profile information including
email, phone number, and notification preferences.
"""

import re

from email_validator import EmailNotValidError, validate_email


class ProfileInfoValidator:
    """
    Validates form data submitted for profile information.

    This validator assumes that a complete set of data is given for each field.
    If there are 6 fields (email, phone number, email
    preference, text preference, probability preference), the current values
    for each field must be given even if only one field is actually being
    updated.
    """

    # Valid probability preference values
    VALID_PROB_VALUES = [3, 4, 5]

    def __init__(self, json_data):
        """
        Initialize the validator with JSON data.

        Args:
            json_data (dict): JSON data containing profile information
        """
        self.email = json_data.get("email")
        self.phone_number = json_data.get("phone_number")
        self.email_pref = json_data.get("email_pref")
        self.text_pref = json_data.get("text_pref")
        self.prob_pref = json_data.get("prob_pref")
        self.text_consent = json_data.get("text_consent")
        self.errors = []

    def add_error(self, message):
        """
        Add an error message to the errors list.

        Args:
            message (str): Error message to add

        Returns:
            bool: False to indicate validation failure
        """
        self.errors.append(message)
        return False

    def validate(self):
        """
        Run all validation methods.

        Returns:
            bool: True if all validations pass, False otherwise
        """
        validators = [
            self._validate_email,
            self._validate_phone_number,
            self._validate_email_pref,
            self._validate_text_pref,
            self._validate_prob_pref,
            self._validate_text_consent,
        ]

        is_valid = True
        for validator in validators:
            if not validator():
                is_valid = False

        return is_valid

    def _validate_email(self):
        """
        Validate email address format and normalization.

        Returns:
            bool: True if email is valid, False otherwise
        """
        # Only require email if email preference is checked
        if self.email_pref and not self.email:
            return self.add_error(
                "An email address is required when email notifications are enabled."
            )

        # If email preference is not checked, email is optional
        if not self.email_pref:
            self.email = None
            return True

        # Validate email format if provided
        try:
            validated_email = validate_email(self.email)
            # Update with normalized form
            self.email = validated_email.email
        except EmailNotValidError as e:
            print(f"Email validation error: {e}")
            return self.add_error("Email is not valid.")

        return True

    def _validate_phone_number(self):
        """
        Validate phone number format (10 digits).

        Returns:
            bool: True if phone number is valid or empty, False otherwise
        """
        # Only require phone number if text preference is checked
        if self.text_pref and not self.phone_number:
            return self.add_error(
                "A phone number is required when text notifications are enabled."
            )

        # If text preference is not checked, phone number is optional
        if not self.text_pref:
            self.phone_number = None
            return True

        # Validate phone number format if provided
        if not re.search(r"^\d{10}$", self.phone_number):
            return self.add_error("The phone number must be 10 digits long.")

        return True

    def _validate_email_pref(self):
        """
        Validate email preference is a boolean value.

        Returns:
            bool: True if email preference is valid, False otherwise
        """
        if not isinstance(self.email_pref, bool):
            return self.add_error("Email preference must be true or false.")
        return True

    def _validate_text_pref(self):
        """
        Validate text preference is a boolean value.

        Returns:
            bool: True if text preference is valid, False otherwise
        """
        if not isinstance(self.text_pref, bool):
            return self.add_error("Text preference must be true or false.")
        return True

    def _validate_prob_pref(self):
        """
        Validate probability preference is a valid integer value.

        Returns:
            bool: True if probability preference is valid, False otherwise
        """
        try:
            prob_pref_int = int(self.prob_pref)
        except (ValueError, TypeError):
            return self.add_error("Probability preference must be an integer.")

        if prob_pref_int not in self.VALID_PROB_VALUES:
            valid_values = ", ".join(map(str, self.VALID_PROB_VALUES))
            return self.add_error(
                f"Probability preference must be one of: {valid_values}."
            )

        return True

    def _validate_text_consent(self):
        """
        Validate text consent is a boolean value.

        Returns:
            bool: True if text consent is valid, False otherwise
        """
        if not isinstance(self.text_consent, bool):
            return self.add_error("Text consent must be true or false.")
        return True
