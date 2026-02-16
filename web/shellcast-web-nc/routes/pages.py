from datetime import datetime, timedelta, timezone

import pytz
from flask import Blueprint, render_template
from models import db
from models.CMUProbability import CMUProbability

# the number of seconds in one hour
SECONDS_IN_HOURS = 3600

pages = Blueprint("shellcast-nc", __name__)


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


def temp_remove_verizon(serviceProviders):
    """Temporarily remove Verizon from the list of service providers"""
    verizon_idx = None
    for idx, item in enumerate(serviceProviders):
        if item.name == "Verizon":
            verizon_idx = idx
            break
    if verizon_idx is not None:
        serviceProviders.pop(verizon_idx)
    return serviceProviders


@pages.route("/preferences")
def preferences_page():
    prob_options = [3, 4, 5]
    return render_template(
        "preferences.html",
        probOptions=prob_options,
    )


@pages.route("/signin")
def signin_page():
    return render_template("signin.html")


@pages.route("/feedback")
def feedback_page():
    return render_template("feedback.html")
