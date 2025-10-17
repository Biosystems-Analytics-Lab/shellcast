#!/usr/bin/env python3
"""
Test script for EmailNotification class to send test email from shellcastapp@ncsu.edu
Usage: python test_email_notification.py [state] [user_id] [user_email]
Example: python test_email_notification.py sc 1 mshukun@ncsu.edu
"""

import argparse
import logging
import os
import sys
from datetime import datetime

# Add the parent directory to the Python path to import from src
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from management import DirectoryConfig, NotificationConfig
from notifications import (
    EmailNotification,
    GmailServices,
    NotificationEmailContentGenerator,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_test_data(state, user_id, user_email):
    """Create test data for specified state, user_id, and email"""
    # Mock data that would come from the database
    test_data = [
        {
            "user_id": user_id,
            "email": user_email,
            "phone": None,
            "prob_pref": 3,  # Moderate threshold
            "email_pref": 1,  # Email enabled
            "text_pref": 0,  # Text disabled
            "threshold": 4,
            "lease_id": f"TEST{user_id:03d}",
            "area_id": f"{state.upper()}001",
            "user_code": f"TEST_USER_{user_id}",
            "prob_1d_perc": 4,  # High probability today
            "prob_2d_perc": 3,  # Moderate probability tomorrow
            "prob_3d_perc": 2,  # Low probability in 2 days
        }
    ]
    return test_data


def test_email_content_generation(state, user_id, user_email):
    """Test the email content generation without sending"""
    logger.info("Testing email content generation...")

    try:
        # Initialize configurations
        dir_config = DirectoryConfig(state, "gcp.mysql")
        notification_config = NotificationConfig(state)

        # Create test data
        test_data = create_test_data(state, user_id, user_email)

        # Test content generation
        content_generator = NotificationEmailContentGenerator(
            notification_config, state, test_data
        )

        # Generate email content
        contents = content_generator()

        if contents:
            logger.info(f"Generated {len(contents)} email content(s)")
            for content in contents:
                logger.info(f"Email to: {content['email']}")
                logger.info(f"Subject: {content['subject']}")
                logger.info(f"Content preview: {content['content'][:200]}...")
                logger.info(f"User ID: {content['user_id']}")
        else:
            logger.warning("No email content generated")

        return contents

    except Exception as e:
        logger.error(f"Error in content generation test: {e}")
        raise


def test_gmail_service(state):
    """Test Gmail service authentication"""
    logger.info("Testing Gmail service authentication...")

    try:
        # Initialize notification config
        notification_config = NotificationConfig(state)

        # Test Gmail service
        gmail_services = GmailServices(notification_config)
        service = gmail_services.get_authenticated_gmail_service()

        logger.info("Gmail service authentication successful")
        return service

    except Exception as e:
        logger.error(f"Error in Gmail service test: {e}")
        raise


def test_send_email(state, user_id, user_email):
    """Test sending actual email"""
    logger.info("Testing actual email sending...")

    try:
        # Initialize configurations
        dir_config = DirectoryConfig(state, "gcp.mysql")
        notification_config = NotificationConfig(state)

        # Create test data
        test_data = create_test_data(state, user_id, user_email)

        # Generate email content
        content_generator = NotificationEmailContentGenerator(
            notification_config, state, test_data
        )
        contents = content_generator()

        if not contents:
            logger.error("No email content generated")
            return False

        # Set up Gmail service
        gmail_services = GmailServices(notification_config)
        service = gmail_services.get_authenticated_gmail_service()

        # Send email
        content = contents[0]  # Get the first (and only) email content
        logger.info(
            f"Sending email to {content['email']} with subject: {content['subject']}"
        )

        response = gmail_services.gmail_send_message(
            service, content["email"], content["subject"], content["content"]
        )

        logger.info(f"Email sent successfully! Message ID: {response['id']}")
        return True

    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Test EmailNotification class with configurable parameters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_email_notification.py sc 1 mshukun@ncsu.edu
  python test_email_notification.py nc 5 test@example.com
  python test_email_notification.py fl 10 user@test.org
        """,
    )

    parser.add_argument(
        "state",
        help="State abbreviation (e.g., sc, nc, fl)",
        choices=["sc", "nc", "fl"],
        type=str.lower,
    )

    parser.add_argument("user_id", help="User ID for the test", type=int)

    parser.add_argument("user_email", help="Email address to send test email to")

    return parser.parse_args()


def main():
    """Main test function"""
    # Parse command line arguments
    args = parse_arguments()

    state = args.state.upper()
    user_id = args.user_id
    user_email = args.user_email

    logger.info("Starting EmailNotification test...")
    logger.info(
        f"Test configuration: User ID={user_id}, State={state}, From=shellcastapp@ncsu.edu, To={user_email}"
    )

    try:
        # Test 1: Content generation
        logger.info("\n=== Test 1: Email Content Generation ===")
        contents = test_email_content_generation(state, user_id, user_email)

        # Test 2: Gmail service authentication
        logger.info("\n=== Test 2: Gmail Service Authentication ===")
        service = test_gmail_service(state)

        # Test 3: Send actual email
        logger.info("\n=== Test 3: Send Actual Email ===")
        success = test_send_email(state, user_id, user_email)

        if success:
            logger.info("\n✅ All tests completed successfully!")
        else:
            logger.error("\n❌ Email sending failed!")

    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
