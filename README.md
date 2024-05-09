# ShellCast
ShellCast is a Python Flask web application that helps North Carolina shellfish growers make harvesting decisions based on predicted rainfall.  The live production version of the app can be found at [https://go.ncsu.edu/shellcast](https://go.ncsu.edu/shellcast). A public version of this repository is also available at https://github.com/Biosystems-Analytics-Lab/shellcast.

Please note that this repository is participating in a study into sustainability of open source projects. Data will be gathered about this repository for approximately the next 12 months, starting from May 17, 2021.

Data collected will include number of contributors, number of PRs, time taken to close/merge these PRs, and issues closed.

For more information, please visit [our informational page](https://sustainable-open-science-and-software.github.io/) or download our [participant information sheet](https://sustainable-open-science-and-software.github.io/assets/PIS_sustainable_software.pdf).

## Table of Contents

1. [Third-Party Services](#1-third-party-services)

2. [Architecture Overview](#2-architecture-overview)

3. [Documentation Overview](#3-documentation-overview)

4. [Contact Information](#4-contact-information)

## 1. Third-Party Services

Various third-party services are used as part of the ShellCast web app.

Google Cloud Platform
- App Engine - The web app is deployed on Google App Engine in a standard Python 3 environment.
- Cloud SQL - ShellCast uses a MySQL database for storing all persistent information.  The database is managed by Google Cloud SQL.
- Logging - All logs related to the App Engine and Cloud SQL instances are recorded with Google Logging.  Additional custom logs from within the app itself are also recorded.
- Firebase
  - Authentication - ShellCast uses Firebase authentication to manage user signup and login.

Amazon Web Services
- Simple Email Service - ShellCast uses AWS SES to send closure notifications to users through email and text.

NCSU Enterprise GitHub
- Available through https://github.ncsu.edu/login
- The NCSU Enterprise GitHub repo is also mirrored to add and push to a remote GitHub (public) repo at https://github.com/Biosystems-Analytics-Lab/shellcast. See [docs/DEVELOPER.md](/docs/DEVELOPER.md) for more information.

## 2. Architecture Overview

![A diagram showing the data flow of the ShellCast application.](docs/images/architecture_diagram.png)

1. Download NOAA PQPF and daily quality controlled rainfall estimates from FTP server every morning.
2. The analysis server calculates closure probabilities for growing units based on the rainfall forecasts and rainfall closure thresholds for those growing units. See [docs/ANALYSIS.md](/docs/ANALYSIS.md) for more information.
3. The calculated probabilities for every growing unit are uploaded to the database every morning.
4. The database is a MySQL 5.7 instance hosted on Google Cloud SQL. See [docs/DATABASE.md](/docs/DATABASE.md) for more information.
5. Calculated probabilities are retrieved by the web server
6. The web server is a Python Flask application hosted on Google App Engine. See [docs/DEVELOPER.md](/docs/DEVELOPER.md) for more information.
7. As requests are made from a web browser, the web server responds to those requests.
8. A user can access the ShellCast website using any modern web browser on a computer, phone, or tablet.
9. User information and preferences are propagated back to the database.
10. Notifications are sent to users every morning based on their notification preferences. Notifications are sent using Amazon Web Services Simple Email Service.
11. Email notifications show a detailed list of a user's leases that may close soon. Email notifications are sent using the user's email address.
12. Text notifications consist of a short message with a link back to ShellCast site. Text notifications are sent using the user's phone number and the SMS gateway for the user's phone service provider.

## 3. Documentation Overview

Instructions explaining how to perform a variety of tasks can be found in the following documents in the `docs` directory [here](/docs/).

- [docs/ANALYSIS.md](/docs/ANALYSIS.md) explains the various analysis scripts and how to set up the analysis cron job on a virtual computing lab image.
- [docs/CITATION.md](/docs/CITATION.md) explains how to cite and give attribution to ShellCast source code.
- [docs/DATABASE.md](/docs/DATABASE.md) explains how to access, manage, and interact with the ShellCast database.
- [docs/DEVELOPER.md](/docs/DEVELOPER.md) explains the structure of the repository, how to setup a full development environment, and how to perform common development tasks.
- [docs/LICENSE.md](/docs/LICENSE.md) explains the ShellCast license.
- [docs/MANUAL_UPDATES.md](/docs/MANUAL_UPDATES.md) explains how to make simple updates to ShellCast.

## 4. Contact Information

If you have any questions, feedback, or suggestions please submit issues [through the NCSU Enterprise GitHub](https://github.ncsu.edu/biosystemsanalyticslab/shellcast/issues) or [through GitHub (public)](https://github.com/Biosystems-Analytics-Lab/shellcast/issues). You can also reach out to Makiko Shukunobe (mshukun at ncsu dot edu) or Natalie Nelson (nnelson4 at ncsu dot edu). 
