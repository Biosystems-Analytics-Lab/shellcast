import base64
import glob
import logging
import os
import os.path
from datetime import datetime
from email.message import EmailMessage

import pandas as pd
import utils
from constants import PQPF_DATA_DIR
from cryptography.fernet import Fernet
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from itsdangerous import URLSafeTimedSerializer
from management import DirectoryConfig, NotificationConfig
from sqlalchemy import create_engine
from utils import execute_stored_procedure

logger = logging.getLogger(__name__)

PROB_CATS = {1: "Very Low", 2: "Low", 3: "Moderate", 4: "High", 5: "Very High"}


def generate_unsubscribe_token(user_id, email, secret_key):
    """
    Generate a secure unsubscribe token for a user.

    Args:
        user_id (int): The user's ID
        email (str): The user's email address
        secret_key (str): Secret key for token signing

    Returns:
        str: A secure, time-limited unsubscribe token
    """
    serializer = URLSafeTimedSerializer(secret_key)
    token_data = {
        "uid": user_id,
        "email": email,
        "timestamp": datetime.now().isoformat(),
    }
    return serializer.dumps(token_data, salt="email-unsubscribe")


def filter_users_by_preferences(users_data, prob_1d_only=False, state=None):
    """
    Filter users based on their email/text preferences and probability thresholds

    Args:
        users_data: List of tuples containing user data
        (user_id, email, phone, prob_pref, email_pref, text_pref, threshold,
         lease_id, area_id, user_code, prob_1d_perc, prob_2d_perc, prob_3d_perc)
        prob_1d_only: States where has only today's prediction (e.g. FL) to be true
        state: State code (FL, SC, NC) to determine consent requirements
    Returns:
        List of filtered user data tuples
    """
    logger.info(f"Starting to filter {len(users_data)} users")
    filtered_users = []

    for user in users_data:
        # Check if user has email notifications enabled
        # For SC and FL: both email_pref AND email_consent must be true
        # For NC: only email_pref needs to be true (consent not implemented yet)
        if state and state.upper() in ["SC", "FL"]:
            email_enabled = (
                user.get("email_pref") == 1 and user.get("email_consent") == 1
            )
        else:
            # NC or unknown state - only check email_pref
            email_enabled = user.get("email_pref") == 1

        # Text notifications are not implemented yet, so skip text checks
        has_notification_enabled = email_enabled

        logger.debug(
            f"User {user.get('user_id')} notification preferences - email_pref: "
            f"{user.get('email_pref')}, email_consent: {user.get('email_consent')}, "
            f"state: {state}, email_enabled: {email_enabled}"
        )

        # Check if probability preference meets any of the threshold conditions
        if prob_1d_only:
            meets_probability_threshold = (
                user["prob_pref"] is not None  # Ensure prob_pref is not None
                and user["prob_1d_perc"] >= user["prob_pref"]
            )
            logger.debug(
                f"User {user.get('user_id')} 1D probability check - pref: "
                f"{user.get('prob_pref')}, actual: {user.get('prob_1d_perc')}"
            )
        else:
            meets_probability_threshold = user[
                "prob_pref"
            ] is not None and (  # Ensure prob_pref is not None
                user["prob_1d_perc"] >= user["prob_pref"]
                or user["prob_2d_perc"] >= user["prob_pref"]
                or user["prob_3d_perc"] >= user["prob_pref"]
            )
            logger.debug(
                f"User {user.get('user_id')} "
                f"3D probability check - pref: {user.get('prob_pref')}, "
                f"1D: {user.get('prob_1d_perc')}, "
                f"2D: {user.get('prob_2d_perc')}, "
                f"3D: {user.get('prob_3d_perc')}"
            )

        # Include user if they have notifications enabled and meet probability thresholds
        if has_notification_enabled and meets_probability_threshold:
            filtered_users.append(user)
            logger.debug(f"User {user.get('user_id')} added to filtered list")

    logger.info(f"Filtering complete. {len(filtered_users)} users meet the criteria")
    return filtered_users


class Cipher:
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.key_file = os.path.join(
            os.path.dirname(config.token_file), "encryption.key"
        )
        logger.info("Initialized Cipher with key file")

    def get_or_create_encryption_key(self):
        """Get the encryption key from file or create a new one."""
        # Try to read from file first
        if os.path.exists(self.key_file):
            try:
                with open(self.key_file, "rb") as f:
                    key = f.read()
                    logger.info("Encryption key loaded from file")
                    return key
            except Exception as e:
                logger.error(f"Error reading encryption key file: {e}")
                # If there's an error reading the file, we'll generate a new key

        # Generate a new key if not found in file
        logger.info("Generating new encryption key")
        key = Fernet.generate_key()
        try:
            # Save the key to file
            with open(self.key_file, "wb") as f:
                f.write(key)
            logger.info(f"Generated and saved new encryption key to {self.key_file}")
        except Exception as e:
            logger.error(f"Error saving encryption key: {e}")
            raise

        return key

    def encrypt_token_data(self, token_data):
        """Encrypt token data using Fernet encryption."""
        logger.debug("Starting token encryption")
        key = self.get_or_create_encryption_key()
        f = Fernet(key)
        encrypted_data = f.encrypt(token_data.encode())
        logger.debug("Token encryption completed successfully")
        utils.done_str
        return encrypted_data

    def decrypt_token_data(self, encrypted_data):
        """Decrypt token data using Fernet encryption."""
        logger.debug("Starting token decryption")
        key = self.get_or_create_encryption_key()
        f = Fernet(key)
        decrypted_data = f.decrypt(encrypted_data).decode()
        logger.debug("Token decryption completed successfully")
        return decrypted_data


class NotificationEmailContentGenerator:
    def __init__(self, notification_config: NotificationConfig, state, data):
        """
        Args:
            List of tuples containing user data
        (user_id, email, phone, prob_pref, email_pref, text_pref, threshold,
         lease_id, area_id, user_code, prob_1d_perc, prob_2d_perc, prob_3d_perc)
        """
        self.notification_config = notification_config
        self.state = state
        self.data = data

    def organize_data_by_email_preference(self):
        """Organize user data by user's email

        Returns:
            Dictionary of user data organized by user's email
            e.g. {
                "example@example.com": [
                    {"lease": "234567", "user_id": 1, "prob_1d_perc": 1, "prob_2d_perc": 1,
                    "prob_3d_perc": 3},
                    {"lease": "234890", "user_id": 1, "prob_1d_perc": 1, "prob_2d_perc": 1,
                    "prob_3d_perc": 3},
                ]
            }
        """
        # Organize user data by user's email
        user_data_by_email = {}
        for data in self.data:
            # Check if email preference is enabled and email exists
            # For SC and FL: both email_pref AND email_consent must be true
            # For NC: only email_pref needs to be true (consent not implemented yet)
            if self.state and self.state.upper() in ["SC", "FL"]:
                email_ok = (
                    data.get("email_pref") == 1
                    and data.get("email_consent") == 1
                    and data.get("email")
                )
            else:
                # NC or unknown state - only check email_pref
                email_ok = data.get("email_pref") == 1 and data.get("email")

            if email_ok:
                email = data["email"]
                lease_id = data.get("lease_id")

                # Use setdefault to initialize the list if email is new
                user_leases = user_data_by_email.setdefault(email, [])

                # Safely get probability values using .get()
                prob_1d_perc = data.get("prob_1d_perc")
                prob_2d_perc = data.get("prob_2d_perc")
                prob_3d_perc = data.get("prob_3d_perc")

                # Skip if no lease_id
                if not lease_id:
                    continue

                lease_data = None
                # Case 1: Only 1D probability exists (e.g. FL)
                if (
                    prob_1d_perc is not None
                    and prob_2d_perc is None
                    and prob_3d_perc is None
                ):
                    lease_data = {
                        "lease": lease_id,
                        "user_id": data.get("user_id"),
                        "prob_1d_perc": prob_1d_perc,
                        "prob_days": 1,
                    }
                # Case 2: All three probabilities exist
                elif (
                    prob_1d_perc is not None
                    and prob_2d_perc is not None
                    and prob_3d_perc is not None
                ):
                    lease_data = {
                        "lease": lease_id,
                        "user_id": data.get("user_id"),
                        "prob_1d_perc": prob_1d_perc,
                        "prob_2d_perc": prob_2d_perc,
                        "prob_3d_perc": prob_3d_perc,
                        "prob_days": 3,
                    }

                # Append if lease_data was created in one of the specific cases
                if lease_data:
                    user_leases.append(lease_data)

        return user_data_by_email

    def __call__(self):
        try:
            results = []
            organized_user_data = self.organize_data_by_email_preference()

            if not organized_user_data:
                return results

            for user_email, leases_data in organized_user_data.items():
                first = leases_data[0]

                # Generate subject
                subject = self.notification_config.subject_template.format(
                    self.state, first.get("lease")
                )
                if len(leases_data) > 1:
                    subject += " and more"

                # Generate message based on probability days
                message = self._generate_message(first)
                if not message:
                    continue

                # Generate unsubscribe link for SC and FL
                if self.state.upper() in ["SC", "FL"]:
                    unsubscribe_link = self._generate_unsubscribe_link(
                        first.get("user_id"), user_email
                    )
                    content = (
                        message
                        + self.notification_config.notification_footer
                        + "<br><br>"
                        + unsubscribe_link
                    )
                else:
                    content = message + self.notification_config.notification_footer

                # Add to results if both subject and content are valid
                if subject and content:
                    results.append(
                        {
                            "email": user_email,
                            "subject": subject,
                            "content": content,
                            "user_id": first.get("user_id"),
                        }
                    )

            return results
        except Exception as e:
            logger.error(f"An error occurred in main: {e}")
            raise

    def _generate_message(self, lease_data):
        """Generate message content based on probability days."""
        if lease_data.get("prob_days") == 1:  # FL
            return (
                f"{self.notification_config.lease_template_today_only}<br><br>"
                f"<strong>Lease:</strong> {lease_data.get('lease')}<br>"
                f"&nbsp;&nbsp;&nbsp;&nbsp;<strong>Today:</strong> {PROB_CATS.get(int(lease_data.get('prob_1d_perc')))}\n"
            )
        elif lease_data.get("prob_days") == 3:
            return (
                f"{self.notification_config.lease_template}<br><br>"
                f"<strong>Lease:</strong> {lease_data.get('lease')}<br>"
                f"&nbsp;&nbsp;&nbsp;&nbsp;<strong>Today:</strong> {PROB_CATS.get(int(lease_data.get('prob_1d_perc')))}<br>"
                f"&nbsp;&nbsp;&nbsp;&nbsp;<strong>Tomorrow:</strong> {PROB_CATS.get(int(lease_data.get('prob_2d_perc')))}<br>"
                f"&nbsp;&nbsp;&nbsp;&nbsp;<strong>In 2 days:</strong> {PROB_CATS.get(int(lease_data.get('prob_3d_perc')))}\n"
            )
        return ""

    def _generate_unsubscribe_link(self, user_id, email):
        """Generate unsubscribe link for the user with state-specific URL."""
        try:
            token = generate_unsubscribe_token(
                user_id, email, self.notification_config.secret_key
            )
            base_url = self.notification_config.web_base_url
            unsubscribe_url = f"{base_url}/u/{token}"
            return (
                f"To unsubscribe from these notifications, <a href='{unsubscribe_url}'>Unsubscribe</a> or \n"
                f"visit <a href='{base_url}'>go.ncsu.edu/shellcast</a> Preferences page."
            )
        except Exception as e:
            logger.error(f"Error generating unsubscribe link for user {user_id}: {e}")
            # Fallback to preferences page if token generation fails
            base_url = self.notification_config.web_base_url
            return f"To unsubscribe from these notifications, <a href='{base_url}/preferences'>visit here</a>"


class GmailServices:
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.cipher = Cipher(config)
        logger.info("Initialized GmailServices")

    def get_authenticated_gmail_service(self):
        """Gets Gmail API service with proper authentication and token handling.

        This function implements the OAuth2 flow for desktop applications:
        1. Checks for existing token
        2. Refreshes token if expired
        3. Create a new token through user authentication if needed
        4. Saves token for future use

        Returns:
            Gmail API service object
        """
        logger.info("Starting Gmail service authentication")
        creds = None
        # The file token_2.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self.config.token_file):
            try:
                with open(self.config.token_file, "rb") as token:
                    encrypted_data = token.read()
                    token_data = self.cipher.decrypt_token_data(encrypted_data)
                    creds = Credentials.from_authorized_user_info(
                        eval(token_data), self.config.scopes
                    )
                logger.info("Successfully loaded credentials from token file")
            except Exception as e:
                logger.error(f"Error reading encrypted token file: {e}")

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                logger.info("No valid credentials found, starting OAuth flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config.gmail_api_credential_file, self.config.scopes
                )
                creds = flow.run_local_server(port=0)

            # Save the encrypted credentials for the next run
            try:
                token_data = creds.to_json()
                encrypted_data = self.cipher.encrypt_token_data(token_data)
                with open(self.config.token_file, "wb") as token:
                    token.write(encrypted_data)
                logger.info("Successfully saved new credentials")
            except Exception as e:
                logger.error(f"Error saving encrypted token file: {e}")
                raise

        try:
            # Build and return the Gmail service
            service = build("gmail", "v1", credentials=creds)
            logger.info("Successfully built Gmail service")
            return service
        except HttpError as error:
            logger.error(f"An error occurred while building Gmail service: {error}")
            raise

    def gmail_send_message(self, service, to_addresses, subject, content):
        """Create and send an email message
        Args:
            service: Gmail API service instance
            to_addresses: List of email addresses to send to
            subject: Email subject
            content: Email content
        Returns: Message object, including message id
        """
        logger.info(
            f"Preparing to send email to {to_addresses} with subject: {subject}"
        )
        try:
            message = EmailMessage()
            message["To"] = to_addresses
            message["From"] = self.config.sender
            message["Subject"] = subject

            # Set both plain text and HTML content
            # Convert HTML to plain text for text version
            import re

            plain_text = re.sub(r"<[^>]+>", "", content)  # Remove HTML tags
            plain_text = plain_text.replace("&nbsp;", " ")  # Replace HTML entities

            message.set_content(plain_text)
            message.add_alternative(content, subtype="html")

            # Encode the message
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {"raw": encoded_message}

            # Send the message
            send_message = (
                service.users()
                .messages()
                .send(userId="me", body=create_message)
                .execute()
            )
            logger.info(f"Message sent successfully. Message Id: {send_message['id']}")
            return send_message

        except HttpError as error:
            logger.error(f"An error occurred while sending email: {error}")
            raise


class NotificationLogManager:
    def __init__(self, connection_string):
        self.logs = []
        self.connection_string = connection_string

    def add_log(
        self,
        user_id,
        address,
        notification_text,
        notification_type,
        send_success,
        response_text="",
    ):
        """Add a notification log to memory"""
        log = {
            "user_id": user_id,
            "address": address,
            "notification_text": notification_text,
            "notification_type": notification_type,
            "send_success": send_success,
            "response_text": response_text,
        }
        self.logs.append(log)

    def save_to_db(self):
        """Save all logs to database in batch"""
        if not self.logs:
            return

        try:
            engine = create_engine(self.connection_string)
            with engine.begin() as conn:
                # Convert logs to DataFrame
                df = pd.DataFrame(self.logs)
                # Save to database
                df.to_sql("notification_log", con=conn, if_exists="append", index=False)
            # Clear logs after successful save
            self.logs = []
        except Exception as e:
            logger.error(f"Error saving notification logs to database: {e}")
            raise


class EmailNotification:
    """Email notification configuration"""

    def __init__(
        self,
        dir_config: DirectoryConfig,
        notification_config: NotificationConfig,
        state: str,
        prob_only_today=False,
    ):
        self.dir_config = dir_config
        self.notification_config = notification_config
        self.state = state
        self.prob_only_today = prob_only_today
        self.log_manager = NotificationLogManager(self.dir_config.connect_str)
        logger.info(f"Initialized EmailNotification for state: {state}")

    def send(self):
        logger.info("[Send Notifications]")
        try:
            user_data = execute_stored_procedure(
                self.dir_config.connect_str, self.notification_config.stored_procedure
            )
            logger.info(f"Retrieved {len(user_data)} users from database")

            logger.info("Filtering users based on preferences")
            filtered_data = filter_users_by_preferences(
                user_data, self.prob_only_today, self.state
            )

            if len(filtered_data) > 0:
                logger.info("Generating email content")
                content_generator_inst = NotificationEmailContentGenerator(
                    self.notification_config, self.state, filtered_data
                )
                contents = content_generator_inst()
                logger.info(f"Generated {len(contents)} email contents")

                logger.info("Setting up Gmail service")
                g_services = GmailServices(self.notification_config)
                service = g_services.get_authenticated_gmail_service()

                logger.info("Starting to send emails")
                for content in contents:
                    logger.debug(f"Sending email to {content['email']}")
                    try:
                        response = g_services.gmail_send_message(
                            service,
                            content["email"],
                            content["subject"],
                            content["content"],
                        )
                        # Log successful send
                        self.log_manager.add_log(
                            user_id=content["user_id"],
                            address=content["email"],
                            notification_text=content["content"],
                            notification_type="Email",
                            send_success=1,
                            response_text=str(response),
                        )
                    except Exception as e:
                        # Log failed send
                        self.log_manager.add_log(
                            user_id=content["user_id"],
                            address=content["email"],
                            notification_text=content["content"],
                            notification_type="Email",
                            send_success=0,
                            response_text=str(e),
                        )
                        logger.error(f"Failed to send email to {content['email']}: {e}")

                # Save all logs to database
                self.log_manager.save_to_db()
                logger.info("Email notification process completed successfully")
            else:
                logger.info("No notifications today")
            logger.info(utils.done_str)

        except Exception as e:
            logger.error(f"An error occurred during email notification process: {e}")
            raise


class DevEmailNotificationFL:
    """Sending emails to developers with attachments for FL ShellCast
    This email is to assess the accuracy of the FL ShellCast model.

    Args:
        config_dirs: DirectoryConfig instance
        config_notification: NotificationConfig instance
    """

    def __init__(self, config_dirs, config_notification):
        self.config_dirs = config_dirs
        self.config_notification = config_notification
        self.sender = self.config_notification.sender
        self.receivers = self.config_notification.dev_email_receivers.split(", ")
        self.send_yes_no = self.config_notification.dev_send_email

    @staticmethod
    def get_fl_pqpf_csv_files():
        """Get FL PQPF CSV files that contain 'lease' or 'tmp' in their filenames

        Returns:
            List of file paths for CSV files matching the criteria
        """
        matching_files = []

        for file in glob.glob(os.path.join(PQPF_DATA_DIR, "fl/outputs", "*.csv")):
            if any(keyword in file.lower() for keyword in ["lease", "tmp"]):
                matching_files.append(file)
        return matching_files

    def dev_send_email_with_attachments(self, service, attachment_paths):
        """Send an email with attachments
        Args:
            service: Gmail API service instance
            attachment_paths: List of paths to attachment files
        """
        try:
            # Send it to each receiver individually
            for receiver in self.receivers:
                message = EmailMessage()
                message["From"] = self.sender
                message["To"] = receiver
                message["Subject"] = "FL ShellCast PQPF Analysis Results"
                message.set_content(
                    "Please find attached the latest PQPF analysis results."
                )

                # Add attachments
                for attachment_path in attachment_paths:
                    with open(attachment_path, "rb") as f:
                        file_data = f.read()
                        file_name = os.path.basename(attachment_path)
                        message.add_attachment(
                            file_data,
                            maintype="application",
                            subtype="octet-stream",
                            filename=file_name,
                        )

                # Encode and send the message
                encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

                create_message = {"raw": encoded_message}
                send_message = (
                    service.users()
                    .messages()
                    .send(userId="me", body=create_message)
                    .execute()
                )
                logger.debug(f"Message Id: {send_message['id']} sent to {receiver}")

        except HttpError as error:
            logger.error(
                f"An error occurred while sending email with attachments: {error}"
            )
            raise

    def send(self):
        """Main function to handle Gmail operations"""
        try:
            g_services_instance = GmailServices(self.config_notification)
            g_services = g_services_instance.get_authenticated_gmail_service()

            attachment_paths = self.get_fl_pqpf_csv_files()
            if len(attachment_paths) > 0:
                self.dev_send_email_with_attachments(g_services, attachment_paths)
                logger.info("Email sent to developers successfully")
            else:
                logger.info("No FL PQPF CSV files found")

        except Exception as e:
            logger.error(
                f"An error occurred in email_notification_content_generator: {e}"
            )
            raise
