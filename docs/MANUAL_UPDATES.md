# MANUAL_UPDATES.md

This document is intended to explain how to perform simple, manual updates to ShellCast.  This is basically a subset of the [DEVELOPER.md](/docs/DEVELOPER.md) documentation with descriptions of a few, more common tasks.  This is geared towards readers with some knowledge of command terminals and Git.

## Table of Contents

1. [Setup](#1-setup)

2. [Uploading Changes to GitHub](#2-uploading-changes-to-github)

3. [Uploading Changes to Google App Engine](#3-uploading-changes-to-google-app-engine)

4. [Updating Web Pages](#4-updating-web-pages)

5. [Adding New Web Pages and Navigation Links](#5-adding-new-web-pages-and-navigation-links)

6. [Updating Shellfish Growing Unit Boundaries](#6-updating-shellfish-growing-unit-boundaries)

7. [Turning Notifications Off and On](#7-turning-notifications-off-and-on)

8. [Changing Notification Schedule](#8-changing-notification-schedule)

9. [Updating ShellCast Leases](#9-updating-shellcast-leases)

10. [Contact Information](#9-contact-information)

## 1. Setup

1. Download the GitHub repository to your machine by running `git clone https://github.ncsu.edu/biosystemsanalyticslab/shellcast.git` (for NCSU GitHub) or `git clone https://github.com/Biosystems-Analytics-Lab/shellcast.git` (GitHub).
2. Set up adding and push to the NCSU GitHub Enterprise **and** GitHub (public) repos as described in the [Mirroring code updates on GitHub public repo section](/docs/DEVELOPER.md#54-mirroring-code-updates-on-github-public-repo) of the DEVELOPER.md documentation.
3. Download and install the Google Cloud SDK by following [these instructions](https://cloud.google.com/sdk/docs).
4. Complete the steps under the [Make a configuration file based on the template file](/docs/DEVELOPER.md#46-make-a-configuration-file-based-on-the-template-file) section of the DEVELOPER.md documentation.

## 2. Uploading Changes to GitHub

1. From the root of your local repository, run `git pull` to make sure you have the most recent version of the GitHub repository.
2. Run `git add .` to stage all of the changes made in all files.
3. Run `git commit` which will open a text editor where you can write a commit message (describe what changes you've made).
4. Run `git push all` to push the changes to GitHub. Make sure you have set your remotes to add and push to the NCSU Enterprise GitHub **and** GitHub (public) repos as outlined in the [Mirroring code updates on GitHub public repo section](/docs/DEVELOPER.md#54-mirroring-code-updates-on-github-public-repo) of the DEVELOPER.md documentation.

## 3. Uploading Changes to Google App Engine

1. From the root of your local repository, run `gcloud app deploy`.  Now any changes should be visible on the public website.  If the changes don't seem to be showing, then your browser is probably caching the old files.

## 4. Updating Web Pages

Nearly all of the HTML used for the content of the web pages is contained in the templates/ directory as Jinja templates.  However, HTML that needs to be generated dynamically is not present in these files and is instead embedded in JavaScript files.  If you want to edit any of the following dynamic elements, look in the listed JS file to find the HTML otherwise look at the template for the page you want to edit.

Dynamic HTML element file locations:
- The map legend, day selector, and lease and grow area info popup HTML can be found in static/index/index.js.
- The lease information form and lease search results HTML can be found in static/preferences/preferences.js.

After you have found and made an edit:
1. [Upload the changes to GitHub](#2-uploading-changes-to-github).
2. [Upload the changes to Google App Engine](#3-uploading-changes-to-google-app-engine).

## 5. Adding New Web Pages and Navigation Links

1. First, you need to create a template for the web page in the templates/ directory.  The template file is essentially the new web page's content except for things that are common to all pages such as the navigation bar and footer (these are specified in base.html.jinja but you don't need to mess with that file for now).  You can duplicate an existing template such as `about.html.jinja` as a starting point and rename it to `<name of the new page>.html.jinja`.  Delete all of the HTML in the `{% block content %}...{% endblock %}` section and replace it with what you want to be shown on the page.  Also be sure to update the `{% block title %}...{% endblock %}` section with the title of the new page (this is what will be shown on the tab in a web browser).  Also you can remove, reuse, or replace the CSS file tag in the `{% block additional_head %}...{% endblock %}` section depending if you need additional styling for the new page.  (CSS files for each of the existing pages are in the static/<name of page>/ directories if you need to take a look at them.)
2. Next you need to add a route to the Flask application so that the page can be served to a client that requests it.  Open routes/pages.py and copy and paste an existing route like the following:
  ```
  @pages.route('/about')
  def aboutPage():
    return render_template('about.html.jinja')
  ```
Then change the route from `'/about'` to `'/<name of the new page>'`, the function name from `aboutPage()` to `<name of the new page>Page()`, and the template file path from `'about.hmtl.jinja'` to `<name of the new template file>`.

3. Next you need to add a navigation link for the new page.  Open templates/base.html.jinja and find the following line:
  ```
  {% set navItems = [("index", "/", "Map"), ("about", "/about", "About Us"), ("how-it-works", "/how-it-works", "How ShellCast Works")] %}
  ```
This is a list of tuples containing the 3 pieces of information needed to make each of the nav links in the nav bar.  The first string in each tuple is the name of the page (the part of the template file name before `.html.jinja`).  The second string is the route to the page (this is what you used as the route in step 2).  The third string is the actual text that will be shown as a link in the nav bar.  You just need to add another tuple to the end of the list (the order that the items appear in the navItems list is the order that they will appear as nav links in the nav bar).

4. Finally, [upload the changes to GitHub](#2-uploading-changes-to-github) and [to Google App Engine](#3-uploading-changes-to-google-app-engine).

## 6. Updating Shellfish Growing Unit Boundaries

static/cmu_bounds.geojson contains the NCDMF growing units and their boundaries.  To modify the growing units' boundaries, simply replace that file with an updated version while keeping the file name the same.

1. [Upload the changes to GitHub](#2-uploading-changes-to-github).
2. [Upload the changes to Google App Engine](#3-uploading-changes-to-google-app-engine).

## 7. Turning Notifications Off and On

You can turn off notifications by deleting the notification cron job.  In cron.yaml, comment out the /sendNotifications cron job.  The file should go from this:
```
cron:
- description: "Send notifications daily"
  url: /sendNotifications
  schedule: every day 07:00
  timezone: America/New_York
```
to this:
```
cron:
# - description: "Send notifications daily"
#   url: /sendNotifications
#   schedule: every day 07:00
#   timezone: America/New_York
```
Now [upload the changes to Google App Engine](#3-uploading-changes-to-google-app-engine).

You can find more information on Google App Engine cron jobs [here](https://cloud.google.com/appengine/docs/flexible/python/scheduling-jobs-with-cron-yaml).

To turn notifications back on, uncomment the cron job, and [upload the changes to Google App Engine](#3-uploading-changes-to-google-app-engine).

## 8. Changing Notification Schedule

You can change the time at which notifications are sent by modifying the /sendNotifications cron job configuration in cron.yaml.  See [this page](https://cloud.google.com/appengine/docs/flexible/python/scheduling-jobs-with-cron-yaml#defining_the_cron_job_schedule) for information on how to format the schedule for a Google App Engine cron job.

You will need to change cron.yaml from this:
```
cron:
- description: "Send notifications daily"
  url: /sendNotifications
  schedule: every day 07:00
  timezone: America/New_York
```
to this:
```
cron:
- description: "Send notifications daily"
  url: /sendNotifications
  schedule: <SCHEDULE FORMAT>
  timezone: America/New_York
```

Only the "schedule:" line needs to be changed unless you are also changing the timezone that is used to interpret the schedule.

Now [upload the changes to GitHub](#2-uploading-changes-to-github) and [upload the changes to Google App Engine](#3-uploading-changes-to-google-app-engine). Be sure to push changes to both the NCSU GitHub Enterprise **and** the GitHub (public) repos as decribed in the [Mirroring code updates on GitHub (public) repo section](/docs/DEVELOPER.md#54-mirroring-code-updates-on-github-public-repo) of the DEVELOPER.md documentation.

## 9. Updating ShellCast Leases

Check out the instructions in [ANALYSIS.md](/docs/ANALYSIS.md/#8-updating-leases) for more details on how to update ShellCast leases.

## 10. Contact Information

If you have any questions, feedback, or suggestions please submit issues [through the NCSU Enterprise GitHub](https://github.ncsu.edu/biosystemsanalyticslab/shellcast/issues) or [through GitHub (public)](https://github.com/Biosystems-Analytics-Lab/shellcast/issues). You can also reach out to Sheila Saia (ssaia at ncsu dot edu) or Natalie Nelson (nnelson4 at ncsu dot edu).
