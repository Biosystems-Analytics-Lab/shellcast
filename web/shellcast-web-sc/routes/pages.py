from datetime import datetime, timedelta, timezone

import pytz
from flask import Blueprint, current_app, render_template
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from models import db
from models.CMUProbability import CMUProbability
from models.User import User

# the number of seconds in one hour
SECONDS_IN_HOURS = 3600

pages = Blueprint("shellcast-sc", __name__)


@pages.route("/")
def index_page():
    return render_template("index.html")


@pages.route("/map")
def map_page():
    last_growing_unit_prob = (
        db.session.query(CMUProbability).order_by(CMUProbability.id.desc()).first()
    )
    template_vals = {
        "lastUpdated": "No calculations run yet",
        "hoursAgo": "?",
        "day1": "?",
        "day2": "?",
        "day3": "?",
    }
    if last_growing_unit_prob:
        local = pytz.timezone("US/Eastern")
        local_dt = local.localize(last_growing_unit_prob.created, is_dst=None)
        last_updated_time_utc = local_dt.astimezone(pytz.utc)
        cur_time_utc = datetime.now(timezone.utc)
        duration = cur_time_utc - last_updated_time_utc
        duration_secs = duration.total_seconds()
        template_vals["hoursAgo"] = int(divmod(duration_secs, SECONDS_IN_HOURS)[0])
        last_updated_time_est = last_updated_time_utc.astimezone(local)

        template_vals["hoursAgo"] = int(divmod(duration_secs, SECONDS_IN_HOURS)[0])
        template_vals["lastUpdated"] = last_updated_time_est.strftime(
            "%B %d, %Y %I:%M %p"
        )  # ex: July 24, 2020 04:14 PM
        template_vals["day1"] = last_updated_time_est.strftime("%B %d (%A)")
        template_vals["day2"] = (last_updated_time_est + timedelta(days=1)).strftime(
            "%B %d (%A)"
        )
        template_vals["day3"] = (last_updated_time_est + timedelta(days=2)).strftime(
            "%B %d (%A)"
        )
    return render_template("map.html", **template_vals)


@pages.route("/about")
def about_page():
    return render_template("about.html")


@pages.route("/how-it-works")
def how_it_works_page():
    return render_template("how-it-works.html")


@pages.route("/notification-service")
def notification_service_page():
    return render_template("notification-service.html")


@pages.route("/faqs")
def faqs_page():
    return render_template("faqs.html")


@pages.route("/preferences")
def preferences_page():
    prob_options = [3, 4, 5]
    return render_template(
        "preferences.html",
        probOptions=prob_options,
        text_notifications_ui_enabled=current_app.config[
            "TEXT_NOTIFICATIONS_UI_ENABLED"
        ],
        text_notifications_disabled_message=current_app.config[
            "TEXT_NOTIFICATIONS_DISABLED_MESSAGE"
        ],
    )


@pages.route("/signin")
def signin_page():
    return render_template("signin.html")


@pages.route("/feedback")
def feedback_page():
    return render_template("feedback.html")


@pages.route("/u/<token>")
def one_click_unsubscribe(token):
    """
    One-click unsubscribe without exposing email. Token encodes user id and is time-limited.
    """
    serializer = URLSafeTimedSerializer(current_app.config["EMAIL_SECRET_KEY"])
    try:
        data = serializer.loads(
            token, salt="email-unsubscribe", max_age=60 * 60 * 24 * 60
        )
        user_id = data.get("uid")
    except SignatureExpired:
        return (
            render_template(
                "unsubscribed.html",
                success=False,
                message="This unsubscribe link has expired.",
            ),
            400,
        )
    except BadSignature:
        return (
            render_template(
                "unsubscribed.html", success=False, message="Invalid unsubscribe link."
            ),
            400,
        )

    if not user_id:
        return (
            render_template(
                "unsubscribed.html", success=False, message="Invalid unsubscribe link."
            ),
            400,
        )

    user = db.session.query(User).filter_by(id=user_id, deleted=False).first()
    if not user:
        return (
            render_template(
                "unsubscribed.html", success=False, message="User not found."
            ),
            404,
        )

    # Update user's email preferences and consent
    now = datetime.now(timezone.utc)
    user.email_pref = False
    user.email_opt_out_date = now
    user.touch_updated(now)
    try:
        db.session.add(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return (
            render_template(
                "unsubscribed.html",
                success=False,
                message="An error occurred while unsubscribing.",
            ),
            500,
        )

    return render_template(
        "unsubscribed.html",
        success=True,
        message="You have been unsubscribed successfully.",
    )
