This document is intended to explain how to perform simple, manual updates to ShellCast.

## Setup
1. Download the Git repository to your machine by running `git clone https://github.ncsu.edu/biosystemsanalyticslab/shellcast.git`.
2. Download and install the Google Cloud SDK by following [these instructions](https://cloud.google.com/sdk/docs).
3. Complete the steps under the [Make a configuration file based on the template file]() section of the DEVELOPER.md documentation.

## Uploading changes to GitHub
1. From the root of the repository, run `git pull` to make sure you have the most recent version of the repository.
2. Run `git add .` to stage all of the changes made in all files.
3. Run `git commit` which will open a text editor where you can write a commit message (describe what changes you've made).
4. Run `git push` to push the changes to GitHub.

## Uploading changes to Google App Engine
1. From the root of the repository, run `gcloud app deploy`.  Now any changes should be visible on the public website.  If the changes don't seem to be showing, then your browser is probably caching the old files.

## Updating web pages
Nearly all of the HTML used for the content of the web pages is contained in the templates/ directory as Jinja templates.  However, HTML that needs to be generated dynamically is not present in these files and is instead embedded in JavaScript files.  If you want to edit any of the following dynamic elements, look in the listed JS file to find the HTML otherwise look at the template for the page you want to edit.

Dynamic HTML element file locations:
- The map legend, day selector, and lease and grow area info popup HTML can be found in static/index/index.js.
- The lease information form and lease search results HTML can be found in static/preferences/preferences.js.

After you have found and made an edit:
1. [Upload the changes to GitHub](#uploading-changes-to-github).
2. [Upload the changes to Google App Engine](#uploading-changes-to-google-app-engine).

## Updating growing area boundaries
growing_area_bounds.geojson contains the NCDMF growing areas and their boundaries.  To modify the growing areas' boundaries, simply replace that file with an updated version while keeping the file name the same.

1. [Upload the changes to GitHub](#uploading-changes-to-github).
2. [Upload the changes to Google App Engine](#uploading-changes-to-google-app-engine).

## Turning off/on notifications
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
Now [upload the changes to Google App Engine](#uploading-changes-to-google-app-engine).

You can find more information on Google App Engine cron jobs [here](https://cloud.google.com/appengine/docs/flexible/python/scheduling-jobs-with-cron-yaml).

To turn notifications back on, uncomment the cron job, and [upload the changes to Google App Engine](#uploading-changes-to-google-app-engine).
