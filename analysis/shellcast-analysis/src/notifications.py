import glob
import logging
import os
import os.path
from email.message import EmailMessage

from cryptography.fernet import Fernet
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy import create_engine, text

from constants import PQPF_DATA_DIR
from management import NotificationConfig
from utils import error_log

logger = logging.getLogger(__name__)


class Cipher:
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.key_file = os.path.join(os.path.dirname(config.token_file), 'encryption.key')

    def get_or_create_encryption_key(self):
        """Get the encryption key from file or create a new one."""
        # Try to read from file first
        if os.path.exists(self.key_file):
            try:
                with open(self.key_file, 'rb') as f:
                    key = f.read()
                    logger.info("Encryption key loaded from file")
                    return key
            except Exception as e:
                logger.error(f"Error reading encryption key file: {e}")
                # If there's an error reading the file, we'll generate a new key

        # Generate a new key if not found in file
        key = Fernet.generate_key()
        try:
            # Save the key to file
            with open(self.key_file, 'wb') as f:
                f.write(key)
            logger.info(f"Generated and saved new encryption key to {self.key_file}")
        except Exception as e:
            logger.error(f"Error saving encryption key: {e}")
            raise

        return key

    def encrypt_token_data(self, token_data):
        """Encrypt token data using Fernet encryption."""
        key = self.get_or_create_encryption_key()
        f = Fernet(key)
        return f.encrypt(token_data.encode())

    def decrypt_token_data(self, encrypted_data):
        """Decrypt token data using Fernet encryption."""
        key = self.get_or_create_encryption_key()
        f = Fernet(key)
        return f.decrypt(encrypted_data).decode()


class NotificationDataFilter:
    """ 
    Filter users based on their email/text preferences and probability thresholds.
    """

    def __init__(self, db_connection_string):
        self.connection_string = db_connection_string

    def get_users_data(self):
        """Get users' data from the database."""
        return self.execute_stored_procedure(self.connection_string, "get_users_data")

    def execute_stored_procedure(self, procedure_name, *args):
        """
        Execute a stored procedure using SQLAlchemy

        Args:
            procedure_name: Name of the stored procedure
            *args: Variable arguments to pass to the stored procedure

        Returns:
            Result of the stored procedure
        """
        try:
            engine = create_engine(self.connection_string)
            with engine.connect() as conn:
                # Create the CALL statement
                if args:
                    params = ",".join(["%s" for _ in args])
                    query = text(f"CALL {procedure_name}({params})")
                    result = conn.execute(query, args)
                else:
                    query = text(f"CALL {procedure_name}()")
                    result = conn.execute(query)

                # Fetch all results if any
                if result:
                    return result.fetchall()
            engine.dispose()
            return

        except Exception as e:
            error_log(e)
            raise

    # def probabilityToRisk(closureValue):
    #     flag = ""
    #     if closureValue == 1:
    #         flag = "Very Low"
    #     elif closureValue == 2:
    #         flag = "Low"
    #     elif closureValue == 3:
    #         flag = "Moderate"
    #     elif closureValue == 4:
    #         flag = "High"
    #     elif closureValue == 5:
    #         flag = "Very High"
    #     return flag

    @staticmethod
    def filter_users_by_preferences(users_data):
        """
        Filter users based on their email/text preferences and probability thresholds

        Args:
            users_data: List of tuples containing user data
            (user_id, email, phone, prob_pref, email_pref, text_pref, threshold,
             lease_id, area_id, user_code, prob_1d_perc, prob_2d_perc, prob_3d_perc)

        Returns:
            List of filtered user data tuples
        """
        filtered_users = []

        for user in users_data:
            # Unpack relevant fields
            (
                _,
                email,
                phone,
                prob_pref,
                email_pref,
                text_pref,
                threshold,
                lease_id,
                area_id,
                user_code,
                prob_1d_perc,
                prob_2d_perc,
                prob_3d_perc,
            ) = user

            # Check if user has either email or text notifications enabled
            has_notification_enabled = email_pref == 1 or text_pref == 1

            # Check if probability preference meets any of the threshold conditions
            meets_probability_threshold = (
                    prob_pref is not None  # Ensure prob_pref is not None
                    and (
                            prob_1d_perc >= prob_pref
                            or prob_2d_perc >= prob_pref
                            or prob_3d_perc >= prob_pref
                    )
            )

            # Include user if they have notifications enabled and meet probability thresholds
            if has_notification_enabled and meets_probability_threshold:
                filtered_users.append(user)

        return filtered_users


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
                "example@example.com": {
                    "CMU_U38": {
                        "leases": ["1234567890", "1234567891"],
                        "prob_1d_perc": 1 to 5,
                        "prob_2d_perc": 1 to 5,
                        "prob_3d_perc": 1 to 5
                    }
                }
            }
        """
        # Organize user data by user's email
        user_data_by_email = {}
        for data in self.data:
            # Get user email
            if data[4] == 1:
                user_email = data[1]
                if user_email not in user_data_by_email:
                    # A user can have multiple CMUs
                    user_data_by_email[user_email] = []
                    # Each CMU can have a list of leases and each CMU has 3 probabilities
                    cmu = {user_data_by_email[9]: {
                        "leases": [],
                        "prob_1d_perc": user_data_by_email[10],
                        "prob_2d_perc": user_data_by_email[11],
                        "prob_3d_perc": user_data_by_email[12]
                    }
                    }
                    user_data_by_email[user_email].append(cmu)
                else:
                    user_data_by_email[data[9]].append(data[7])
        return user_data_by_email

    def __call__(self):
        try:
            results = []
            organized_user_data = self.organize_data_by_email_preference()
            if organized_user_data:
                for user_email, cmu_data in organized_user_data.items():
                    template = ''
                    if len(cmu_data) > 0:
                        subject = self.notification_config.subject_template.format(self.state,
                                                                                   cmu_data[0].get("leases")[
                                                                                       0] + "or more")
                        for cmu in cmu_data:
                            template += "\n\nLease: {}-{}\n  Today: {}\n  Tomorrow: {}\n  In 2 days: {}\n".format(
                                ", ".join(cmu.get("leases")),
                                cmu,
                                cmu.get("prob_1d_perc"),
                                cmu.get("prob_2d_perc"),
                                cmu.get("prob_3d_perc"))
                        content = self.notification_config.lease_template + template + self.notification_config.notification_footer
                        if len(subject) > 0 and len(content) > 0:
                            results.append({"email": user_email, "subject": subject, "content": content})
                return results
        except Exception as e:
            logger.error(f"An error occurred in main: {e}")
            raise

    def email_notification_content_generator(self):
        """Main function to handle Gmail operations"""
        pass
        # 0. user id
        # 1. u.email,
        # 2. u.phone_number,
        # 3. u.service_provider_id,
        # 4. u.email_pref,
        # 5. u.text_pref,
        # 6. u.prob_pref == 3 or 4 or 5,
        # 7. l.lease_id,
        # 8. l.grow_area_name,
        # 9. l.cmu_name,
        # 10. cp.prob_1d_perc,
        # 11. cp.prob_2d_perc,
        # 12. cp.prob_3d_perc


# For each state
# Get SHA closure probabilities
# Get UserLease
# If NC >
# Get user_id, lease_id, deleted from user_leases where deleted is false
# Get unique lease_id from user_leases and join leases table to find cmu_name
# Get cmu_probabilities for cmu
# Check latest cmu_probabilities are today's
# If it is true Get today's cmu_probabilities
# Join all cmu_probablities, leases, user_leases
#
# [{user_id: [{"lease_id": "id", "cmu_name": "cmu_name", "prob1d": "low", "prob2d": "moderate", "high"}]}, ...]
#
# textAddress = '{}@{}'.format(user.phone_number, user.service_provider.sms_gateway)
# def get_gmail_service():
# """Get Gmail API service using service account credentials"""
# try:
#     if not os.path.exists(credential_json_path):
#         raise FileNotFoundError(
#             f"Service account credential file not found at {credential_json_path}"
#         )

#     # Load service account credentials from the credential file
#     credentials = service_account.Credentials.from_service_account_file(
#         credential_json_path,
#         scopes=SCOPES,
#         subject=SENDER  # Impersonate the sender email address
#     )

#     # Build and return the service
#     return build("gmail", "v1", credentials=credentials)
# except Exception as e:
#     logger.error(f"Error creating Gmail service: {e}")
#     logger.error(
#         "Please ensure you have downloaded the correct service account key file and set up domain-wide delegation"
#     )
#     raise
class GmailServices:
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.cipher = Cipher(config)

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
        creds = None
        # The file token_2.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        if os.path.exists(self.config.token_file):
            try:
                with open(self.config.token_file, 'rb') as token:
                    encrypted_data = token.read()
                    token_data = self.cipher.decrypt_token_data(encrypted_data)
                    creds = Credentials.from_authorized_user_info(eval(token_data), self.config.scopes)
            except Exception as e:
                logger.error(f"Error reading encrypted token file: {e}")
                # If there's an error reading the token, we'll proceed to create new credentials

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config.gmail_api_credential_file, self.config.scopes)
                creds = flow.run_local_server(port=0)

            # Save the encrypted credentials for the next run
            try:
                token_data = creds.to_json()
                encrypted_data = self.cipher.encrypt_token_data(token_data)
                with open(self.config.token_file, 'wb') as token:
                    token.write(encrypted_data)
            except Exception as e:
                logger.error(f"Error saving encrypted token file: {e}")
                raise

        try:
            # Build and return the Gmail service
            service = build('gmail', 'v1', credentials=creds)
            return service
        except HttpError as error:
            logging.error(f'An error occurred: {error}')
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
        try:
            message = EmailMessage()
            message["To"] = to_addresses
            message["From"] = self.config.sender
            message["Subject"] = subject
            message.set_content(content)

            # Encode the message
            encoded_message = message.as_bytes()
            create_message = {"raw": encoded_message}

            # Send the message
            send_message = (
                service.users().messages().send(userId="me", body=create_message).execute()
            )
            logger.info(f"Message Id: {send_message['id']}")
            return send_message

        except HttpError as error:
            logger.error(f"An error occurred while sending email: {error}")
            raise


# if u.email_pref == true and prob_pref >= cp.prob_1d_perc or cp.prob_2d_perc or cp.prob_3d_perc
class EmailNotification:
    """Email notification configuration"""

    def __init__(self, notification_config, state):
        self.config = notification_config
        self.state = state

    def send(self):
        queryset = NotificationDataFilter(self.config)
        content_generator = NotificationEmailContentGenerator(self.config, self.state, queryset)
        contents = content_generator()
        g_services = GmailServices(self.config)
        service = g_services.get_authenticated_gmail_service()
        for content in contents:
            g_services.gmail_send_message(service, content["email"], content["subject"], content["content"])


class DevEmailNotificationFL:
    """Email notification configuration"""

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
            # Send to each receiver individually
            for receiver in self.receivers:
                message = EmailMessage()
                message["From"] = self.sender
                message["To"] = receiver
                message["Subject"] = "FL ShellCast PQPF Analysis Results"
                message.set_content("Please find attached the latest PQPF analysis results.")

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
                encoded_message = message.as_bytes()
                create_message = {"raw": encoded_message}
                send_message = (
                    service.users().messages().send(userId="me", body=create_message).execute()
                )
                logger.info(f"Message Id: {send_message['id']} sent to {receiver}")

        except HttpError as error:
            logger.error(f"An error occurred while sending email with attachments: {error}")
            raise

    def send(self):
        """Main function to handle Gmail operations"""
        try:
            g_services_instance = GmailServices(self.config_notification)
            g_services = g_services_instance.get_authenticated_gmail_service()

            attachment_paths = self.get_fl_pqpf_csv_files()
            if len(attachment_paths) > 0:
                self.dev_send_email_with_attachments(g_services, attachment_paths)
            else:
                logger.info("No FL PQPF CSV files found")

        except Exception as e:
            logger.error(f"An error occurred in email_notification_content_generator: {e}")
            raise

        # if config["FL.Developer"]["SEND_EMAIL_TO_DEVELOPER"].lower() == "true":
        #     attachment_paths = _get_fl_pqpf_csv_files()
        #     email_list = [email.strip() for email in config["FL.Developer"]["EMAIL_RECEIVER"].split(",")]
        #     for email in email_list:
        #         self.dev_send_email_with_attachments(
        #             service,
        #             email,
        #             "FL ShellCast PQPF Analysis Results",
        #             "Please find attached the latest PQPF analysis results.",
        #             attachment_paths
        #         )
