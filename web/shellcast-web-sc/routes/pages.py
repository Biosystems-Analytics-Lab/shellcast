from datetime import datetime, timezone, timedelta

import pytz
from flask import Blueprint, render_template, current_app
from models import db
from models.CMUProbability import CMUProbability
from models.User import User
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

# the number of seconds in one hour
SECONDS_IN_HOURS = 3600

pages = Blueprint("shellcast-sc", __name__)


@pages.route("/")
def indexPage():
    return render_template("index.html")


@pages.route("/map")
def mapPage():
    lastGrowingUnitProb = (
        db.session.query(CMUProbability).order_by(CMUProbability.id.desc()).first()
    )
    templateVals = {
        "lastUpdated": "No calculations run yet",
        "hoursAgo": "?",
        "day1": "?",
        "day2": "?",
        "day3": "?",
    }
    if lastGrowingUnitProb:
        local = pytz.timezone("US/Eastern")
        local_dt = local.localize(lastGrowingUnitProb.created, is_dst=None)
        lastUpdatedTimeUTC = local_dt.astimezone(pytz.utc)
        curTimeUTC = datetime.now(timezone.utc)
        duration = curTimeUTC - lastUpdatedTimeUTC
        durationSecs = duration.total_seconds()
        templateVals["hoursAgo"] = int(divmod(durationSecs, SECONDS_IN_HOURS)[0])
        lastUpdatedTimeEST = lastUpdatedTimeUTC.astimezone(local)

        templateVals["hoursAgo"] = int(divmod(durationSecs, SECONDS_IN_HOURS)[0])
        templateVals["lastUpdated"] = lastUpdatedTimeEST.strftime(
            "%B %d, %Y %I:%M %p"
        )  # ex: July 24, 2020 04:14 PM
        templateVals["day1"] = lastUpdatedTimeEST.strftime("%B %d (%A)")
        templateVals["day2"] = (lastUpdatedTimeEST + timedelta(days=1)).strftime(
            "%B %d (%A)"
        )
        templateVals["day3"] = (lastUpdatedTimeEST + timedelta(days=2)).strftime(
            "%B %d (%A)"
        )
    return render_template("map.html", **templateVals)


@pages.route("/about")
def aboutPage():
    return render_template("about.html")


@pages.route("/how-it-works")
def howItWorksPage():
    return render_template("how-it-works.html")


@pages.route("/notification-service")
def notificationServicePage():
    return render_template("notification-service.html")


@pages.route("/faqs")
def faqsPage():
    return render_template("faqs.html")


@pages.route("/preferences")
def preferencesPage():
    probOptions = [3, 4, 5]
    return render_template(
        "preferences.html",
        probOptions=probOptions,
    )


@pages.route("/signin")
def signinPage():
    return render_template("signin.html")


@pages.route("/feedback")
def feedbackPage():
    return render_template("feedback.html")


@pages.route("/unsubscribe")
def unsubscribePage():
    return render_template("unsubscribe.html")


@pages.route("/u/<token>")
def oneClickUnsubscribe(token):
    """
    One-click unsubscribe without exposing email. Token encodes user id and is time-limited.
    """
    serializer = URLSafeTimedSerializer(current_app.config["EMAIL_SECRET_KEY"])
    try:
        data = serializer.loads(token, salt="email-unsubscribe", max_age=60 * 60 * 24 * 60)
        user_id = data.get("uid")
    except SignatureExpired:
        return render_template("unsubscribed.html", success=False, message="This unsubscribe link has expired."), 400
    except BadSignature:
        return render_template("unsubscribed.html", success=False, message="Invalid unsubscribe link."), 400

    if not user_id:
        return render_template("unsubscribed.html", success=False, message="Invalid unsubscribe link."), 400

    user = db.session.query(User).filter_by(id=user_id, deleted=False).first()
    if not user:
        return render_template("unsubscribed.html", success=False, message="User not found."), 404

    # Update user's email preferences and consent
    user.email_consent = False
    user.email_pref = False
    user.email_opt_out_date = datetime.now(timezone.utc)
    try:
        db.session.add(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return render_template("unsubscribed.html", success=False, message="An error occurred while unsubscribing."), 500

    return render_template("unsubscribed.html", success=True, message="You have been unsubscribed successfully.")
