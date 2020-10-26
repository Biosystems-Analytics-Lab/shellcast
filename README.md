# shellcast
ShellCast is a Python Flask web application that helps North Carolina shellfish growers make harvesting decisions based on predicted rainfall.  The live production version of the app can be found at [https://go.ncsu.edu/shellcast](https://go.ncsu.edu/shellcast).

## Third-party Services
Various third-party services are used as part of the ShellCast web app.

Google Cloud Platform
- App Engine - The web app is deployed on Google App Engine in a standard Python 3 environment.
- Cloud SQL - ShellCast uses a MySQL database for storing all persistent information.  The database is managed by Google Cloud SQL.
- Logging - All logs related to the App Engine and Cloud SQL instances are recorded with Google Logging.  Additional custom logs from within the app itself are also recorded.
- Firebase
  - Authentication - ShellCast uses Firebase authentication to manage user signup and login.

Google
- Maps API - ShellCast uses the Google Maps JavaScript API for displaying a map of the North Carolina coast with an overlay of the NCDMF growing areas and user leases.

Amazon Web Services
- Simple Email Service - ShellCast uses AWS SES to send closure notifications to users through email and text.

NCSU VCL
- Linux Server - ShellCast uses a custom Linux server to run the closure analysis code on a regular basis.

## Documentation
Instructions explaining how to perform a variety of tasks can be found in the following documents.

- docs/MANUAL_UPDATES.md explains how to make simple updates to ShellCast.
- docs/DEVELOPER.md explains the structure of the repository, how to setup a full development environment, and how to perform common development tasks.
- docs/DATABASE.md explains how to access, manage, and interact with the ShellCast database.
- docs/ANALYSIS.md explains the various analysis scripts and how to set up the analysis cron job on a virtual computing lab image.
- docs/LICENSE.md explains the ShellCast license.
- docs/CITATION.md explains how to cite and give attribution to ShellCast source code.
