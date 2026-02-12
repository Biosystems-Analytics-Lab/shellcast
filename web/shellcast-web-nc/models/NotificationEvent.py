from models import db
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import functions


class NotificationEvent(db.Model):
    """
    Model for tracking notification events (SMS and Email).
    Supports both inbound (user replies) and outbound (sent notifications) messages.
    """

    __tablename__ = "notification_events"

    # Template names for text_content_template (outbound SMS)
    TEMPLATE_SMS_CLOSURE_ALERT = "sms_closure_alert"
    TEMPLATE_SMS_SMOKE_TEST = "sms_smoke_test"

    id = Column(Integer, primary_key=True)
    state = Column(String(2), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_type = Column(String(10), nullable=False)  # 'email' or 'text'

    # Recipient info (one will be NULL depending on type)
    email_address = Column(String(100))
    phone_number = Column(String(15))

    # Message content
    text_content_template = Column(Text)  # Template name for SMS
    email_content = Column(Text)  # Full email content

    # Status tracking
    send_success = Column(Boolean, default=True)

    # SMS and Email message tracking
    message_id = Column(String(100))  # Bandwidth message ID or SES message ID
    message_direction = Column(String(10))  # 'inbound' or 'outbound'
    delivery_status = Column(
        String(20)
    )  # 'RECEIVED', 'QUEUED', 'SENDING', 'SENT', 'FAILED', 'DELIVERED', etc.
    delivery_time = Column(DateTime)
    error_code = Column(String(20))

    created = Column(DateTime, server_default=functions.now())

    @classmethod
    def log_sms_outbound(
        cls,
        state,
        user_id,
        phone_number,
        template_name,
        message_id=None,
        send_success=True,
    ):
        """Log an outbound SMS notification"""
        return cls(
            state=state,
            user_id=user_id,
            notification_type="text",
            phone_number=phone_number,
            text_content_template=template_name,
            message_id=message_id,
            message_direction="outbound",
            delivery_status="QUEUED" if send_success else "FAILED",
            send_success=send_success,
        )

    @classmethod
    def log_sms_inbound(cls, state, user_id, phone_number, message_id=None):
        """Log an inbound SMS (user reply like STOP, HELP)"""
        return cls(
            state=state,
            user_id=user_id,
            notification_type="text",
            phone_number=phone_number,
            message_id=message_id,
            message_direction="inbound",
            delivery_status="RECEIVED",
            send_success=True,
        )

    @classmethod
    def log_email(
        cls,
        state,
        user_id,
        email_address,
        email_content,
        message_id=None,
        send_success=True,
    ):
        """Log an email notification"""
        return cls(
            state=state,
            user_id=user_id,
            notification_type="email",
            email_address=email_address,
            email_content=email_content,
            message_id=message_id,
            message_direction="outbound",
            delivery_status="SENT" if send_success else "FAILED",
            send_success=send_success,
        )

    def update_delivery_status(self, status, error_code=None):
        """Update delivery status from callback"""
        from datetime import datetime, timezone

        self.delivery_status = status
        if status == "DELIVERED":
            self.delivery_time = datetime.now(timezone.utc)
        if error_code:
            self.error_code = error_code

    def asDict(self):
        return {
            "id": self.id,
            "state": self.state,
            "user_id": self.user_id,
            "notification_type": self.notification_type,
            "email_address": self.email_address,
            "phone_number": self.phone_number,
            "message_id": self.message_id,
            "message_direction": self.message_direction,
            "delivery_status": self.delivery_status,
            "send_success": self.send_success,
            "created": self.created.isoformat() if self.created else None,
        }

    def __repr__(self):
        return f"<NotificationEvent: {self.id}, {self.notification_type}, {self.delivery_status}>"
