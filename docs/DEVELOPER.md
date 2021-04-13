# DEVELOPER.md

This document is intended to help a developer get up and running with ShellCast.

_Please note that some steps in this document will only work on a Unix machine (Linux/Mac). There are certainly work arounds for Windows, but I did not thoroughly look into these and document them._

## Table of Contents

1. [Code Structure](#1-code-structure)

2. [Notable Technologies Used](#2-notable-technologies-used)

3. [General Notes](#3-general-notes)

4. [Development Environment Setup](#4-development-environment-setup)

5. [Common Development Tasks](#5-common-development-tasks)

6. [Testing](#6-testing)

7. [Contact Information](#7-contact-information)

## 1. Code Structure

- main.py - The root of the Python Flask application.
- app.yaml - Configuration for deploying the app to Google Cloud.
- cron.yaml - Configuration for cron jobs running on Google App Engine.
- config-template.py - Template that should be copied to make a local config.py file.
- .gcloudignore - This file is similar to a .gitignore file in the sense that it specifies all of the files that will __not__ be uploaded to Google Cloud during deployments.
- .coveragerc - Configuration for the pytest-cov code coverage library.
- requirements.txt - Dependencies for the Python app.
- requirements-test.txt - Dependencies for unit tests.
- __templates__ - Contains all of the Jinja templates used to render each page of the site.
- __static__ - Contains all of the static content for each web page (CSS, JS, images, etc).
- __models__ - Contains all of the Object Relational Mapping (ORM) models that are used to interact with the database.
- __routes__ - Contains all of the routes that are registered with the Flask application.
- __tests__ - Contains all of the unit tests for the application.
- __db-scripts__ - Contains helpful SQL scripts that can be used to setup a new database and populate it with initial records.
- __analysis__ - Contains all of the code related to calculating probabilities and uploading them to the database.  This code is logically separate from the rest of the codebase and is hosted on a Linux VM due to its dependency on R code.  For more information about the analysis code see the [ANALYSIS.md documentation](docs/ANALYSIS.md).
- __docs__ - Contains all of the documentation for the ShellCast application.

## 2. Notable Technologies Used

- [Flask](https://flask.palletsprojects.com/en/1.1.x/) - Flask is a lightweight web app framework written in Python.  It is used for all of the backend logic of the web app.
- [SQLAlchemy](https://www.sqlalchemy.org/) - SQLAlchemy is a Python framework used to interact with databases.  It is used in this project mainly for its ORM functionality.
- [Jinja](https://jinja.palletsprojects.com/en/2.11.x/) - Jinja is a templating language.  It is used to build templates for the pages of the site.

## 3. General Notes

- The GitHub repository and the deployment on Google Cloud App Engine are not necessarily in sync with each other i.e. there is no automation pipeline set up that will automatically deploy new commits to App Engine.  You must explicitly deploy to GAE by following the [Deploy the app to Google App Engine instructions](#53-deploy-the-app-to-google-app-engine).

- The NCSU Enterprise GitHub repo is mirrored on a GitHub public repo to share ShellCast code openly. See [Mirroring code updates on GitHub public repo](#54-mirroring-code-updates-on-GitHub-public-repo) for more information on how to add and push changes to ShellCast.


## 4. Development Environment Setup

### 4.1 Install and initialize Google Cloud SDK

The Google Cloud SDK is principally a command line tool that allows you to interact with Google Cloud from your local machine and perform various tasks. You can download, install, and initialize the Google Cloud SDK by following [these instructions](https://cloud.google.com/sdk/docs/quickstart).

### 4.2 Download Cloud SQL proxy

You can download and setup the Cloud SQL proxy by following [these instructions](https://cloud.google.com/sql/docs/mysql/quickstart-proxy-test#install-proxy). Take note of where you download the proxy script. You will need to run it often, so keep it in a place that's easy to reference.

### 4.2 Clone the GitHub repository

Clone the GitHub repository to your machine by running `git clone https://github.ncsu.edu/biosystemsanalyticslab/shellcast.git`.  It's recommended that you clone the repository to a relatively shallow path in your file system.  If the path to the repo is too long, then it can cause issues with Unix sockets (see [Use the Cloud SQL proxy (TCP and Unix socket)](#51-use-the-cloud-sql-proxy-tcp-and-unix-socket)).

### 4.3 Setup Python virtual environment

1. Make sure that you have Python 3.7 or higher installed on your machine.
2. From the root directory of your local repository, create a virtual environment by running `python3 -m venv venv`.
3. Activate the virtual environment by running `source venv/bin/activate` if on a Linux or Mac machine. If on a Windows machine, run `venv\Scripts\activate.bat`.  Now "python" will refer to the virtual environment's copy of Python 3. You can deactivate the virtual environment by running `deactivate` (Linux/Mac/Windows).
4. Install the app and testing dependencies by running `pip install -r requirements.txt` and then `pip install -r requirements-test.txt`.  If you get errors that mention `error: invalid command 'bdist_wheel'`, then try running `pip install wheel` first.

### 4.4 Make a Unix socket directory

_This step cannot be performed on a Windows machine. This step is ultimately needed to connect to the database through the Unix socket option of the Cloud SQL proxy. To work around this, I would look into changing the SQLALCHEMY_DATABASE_URI property of your config.py file (see the section below) for the DevConfig and TestConfig objects. You should be able to change the URI so that it connects through a TCP connection in the Dev and Test configurations while still connecting through a Unix socket once deployed to GCP (that's when the regular Config object (production) configuration is used)._

To use the Cloud SQL proxy for local development and testing of the web app, a directory is needed for a Unix socket. From the root directory of your local repository, make a new directory named "cloudsql" by running `mkdir cloudsql`.

### 4.5 Make a configuration file based on the template file

The web app uses a configuration file named "config.py" to store various configuration options. Some of these are quite sensitive (e.g. database credentials), so they shouldn't be saved in version control. Because of this, a "config.py" file isn't in the repository but rather a "config-template.py" file which provides all of the necessary structure for the "config.py" file with all of the non-sensitive values already populated.
1. On your machine in the root of your local repository, simply make a copy of config-template.py and name it "config.py". This file will automatically be ignored by Git because it is in the .gitignore.
2. You will now need to populate several values into config.py like the AWS Access Key ID, AWS Secret Access Key, Google Maps JavaScript API key, the database username, and the database password. Any values that you need to add are indicated by "ADD_VALUE_HERE". Since these values are extremely sensitive, they are not stored in this repository. If you are working on ShellCast as a developer, you can get the values by contacting a ShellCast administrator. If you are adapting the code to another project, you can add in new values that you create.

### 4.6 Setup Google service account credentials for Firebase Admin SDK

Since Firebase authentication is used for managing users, the web app uses the Firebase Admin SDK to verify user ID tokens sent from the front end. The Admin SDK uses the concept of [Application Default Credentials](https://cloud.google.com/docs/authentication/production#providing_credentials_to_your_application) to implicitly find service account credentials in its environment so that it can access Firebase services. Service account credentials are already present when the app is deployed on GCP environments like App Engine so the Admin SDK can find them no problem. When developing locally, you have do a little work to help the Admin SDK with credentials. [This article](https://medium.com/google-cloud/firebase-separating-configuration-from-code-in-admin-sdk-d2bcd2e87de6) paints a pretty clear picture of what is going on with the credentials while on App Engine vs. developing locally (and what you need to do to set them up correctly).

So what you need to do at this point is:
1. Generate and download a private key file for the Firebase service account
  - Go to the Firebase console and click on Settings > Service Accounts (or just click [here](https://console.firebase.google.com/u/1/project/ncsu-shellcast/settings/serviceaccounts/adminsdk))
  - Click generate new private key and store the file securely on your machine.  If you save it inside of the repo as `firebase-admin-sdk-credentials.json`, then it should be ignored by both .gitignore and .gcloudignore.  If you store it outside of the repo, then you won't have to worry about it being pushed to GitHub when you commit or Google Cloud when you deploy.  You do __NOT__ want to push this file to either of those places because it contains extremely sensitive information.
2. Now that you have the credentials file, you just have to create an environment variable called `GOOGLE_APPLICATION_CREDENTIALS` which stores the absolute path to the file and the Admin SDK will implicitly find it as if running in App Engine.  On Linux/Mac you can run `export GOOGLE_APPLICATION_CREDENTIALS="/path/to/firebase-admin-sdk-credentials.json"`.  On Windows in Powershell you can run `$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\firebase-admin-sdk-credentials.json"`.

## 5. Common Development Tasks

### 5.1 Use the Cloud SQL proxy (TCP and Unix socket)

By using the Cloud SQL proxy, you can connect to the Google Cloud SQL database instances using any tool that can connect with a TCP connection or a Unix socket (NOTE: you can't use Unix sockets on Windows).  The Cloud SQL proxy also allows the web application to reach the Cloud SQL database for use with local development and testing.
- To use the Cloud SQL proxy with a TCP connection, run `<PATH TO PROXY SCRIPT>/cloud_sql_proxy -instances=ncsu-shellcast:us-east1:ncsu-shellcast-database=tcp:3306`.
- To use the Cloud SQL proxy with a Unix socket, you need to make a directory for the Unix socket and then run `<PATH TO PROXY SCRIPT>/cloud_sql_proxy -instances=ncsu-shellcast:us-east1:ncsu-shellcast-database -dir=<PATH TO UNIX SOCKET DIRECTORY>`.  If you're having issues with the Unix socket being created correctly, then make sure your `cloudsql/` directory (and thus your local shellcast repository) is not too deep in your file system.  Unix sockets have a limit on the length of their paths, so make sure the path to your local shellcast repository is relatively shallow.

### 5.2 Run the application locally

1. Make sure the Python virtual environment is activated and that you are in the root of your local repository.
2. Make sure the Cloud SQL proxy is started with a Unix socket (see [Use the Cloud SQL proxy](#51-use-the-cloud-sql-proxy-tcp-and-unix-socket)).
3. Run the Python app by running `python main.py`.
4. Now you can navigate to [http://localhost:3361](http//:localhost:3361) in your browser to see the web app.

### 5.3 Deploy the app to Google App Engine

1. Make sure that you are signed in and using the correct project (ncsu-shellcast) by running `gcloud info`.
2. From the root directory of your local repository, you can deploy the application to Google App Engine by running `gcloud app deploy`.

### 5.4 Mirroring code updates on GitHub public repo

1. The NCSU GitHub Enterprise repo of ShellCast at https://github.ncsu.edu/biosystemsanalyticslab/shellcast is also mirrored on the public GitHub site at https://github.com/Biosystems-Analytics-Lab/shellcast. Mirroring is set up through git add and git push remotes as explained [here](https://jigarius.com/blog/multiple-git-remote-repositories).
2. When adding and pushing changes to the remote NCSU Enterprise GitHub repo, use `git push all`. This will make sure both remote locations are up-to-date.

We created the GitHub public repo and initiated remote mirroring after realizng the public view of the NCSU Enterprise GitHub repo was only public with NCSU authentication (i.e., public to only folks affiliated with NCSU).

## 6. Testing

[pytest](https://docs.pytest.org/en/latest/) is used for unit testing.  [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/) is used to generate code coverage reports.  The unit tests use pytest fixtures quite extensively.  See the [pytest fixtures documentation](https://docs.pytest.org/en/stable/fixture.html) for more information.  All of the fixtures are specified in tests/conftest.py.

### 6.1 Run unit tests

1. Make sure the Python virtual environment is activated and that you are in the root of your local repository.
2. Make sure the Cloud SQL proxy is started with a Unix socket (see [Use the Cloud SQL proxy](#51-use-the-cloud-sql-proxy-tcp-and-unix-socket)).
3. Run the tests by running `python -m pytest -v`. You should see the test output in the console.

### 6.2 Generate code coverage report

1. Perform steps 1 and 2 from the [Run unit tests](#61-run-unit-tests) section.
2. Run `python -m pytest -v --cov` to see coverage information.
3. Running `coverage html` afterwards will generate web pages in a "htmlcov" directory.  If you open "htmlcov/index.html" in a web browser, then you can click through all of the Python files that were measured and see the exact lines that were executed or missed.

### 6.3 Running specific tests

Oftentimes you will not want to run the entire test suite.  You can run a specific directory of test files, a specific test file, or even a specific test within a file.
- To run a directory of test files use `python -m pytest -v <PATH TO TEST DIRECTORY>`.
- To run a specific test file use `python -m pytest -v <PATH TO TEST FILE>`.
- To run a specific test within a file use `python -m pytest -v <PATH TO TEST FILE>::<NAME OF TEST FUNCTION>`.

## 6.4 Frontend Development Notes

The frontend of ShellCast consists of the HTML generated from the Jinja templates in the templates/ directory and the JS, CSS, and other files in the static/ directory.  The frontend also uses several CSS and JS libraries.

### 6.5 Third-party libraries

- [Bootstrap](https://getbootstrap.com/) - Bootstrap is used for many of the UI components for the site.
- [NCSU Bootstrap CSS](https://brand.ncsu.edu/bootstrap/v4/docs/4.1/content/reboot/) - NC State's custom CSS for Bootstrap is used to provide a foundation for the styling of the site.
- [Bootstrap Table](https://bootstrap-table.com/) - Bootstrap Table is used to build the tables on the index page.
- [Firebase JS](https://firebase.google.com/docs/web/setup) - Firebase is used to handle user authentication.
- [Firebase UI](https://firebase.google.com/docs/auth/web/firebaseui) - Firebase UI provides a drop-in UI for authentication flows.

### 6.6 Templates

All of the HTML for each web page is specified in a Jinja template for that web page.  Note that the templates do not contain any HTML that needs to be dynamically generated.  That HTML is specified within the JS file for the page that needs the dynamic content.

- [templates/base.html.jinja](/templates/base.html.jinja) serves as a base for most of the other templates meaning that they build off of base.html.jinja.  base.html.jinja contains HTML for the navigation bar, footer, and disclaimer/privacy policy modal.
- [templates/index.html.jinja](/templates/index.html.jinja) is the template for the index (map) page.
- [templates/about.html.jinja](/templates/about.html.jinja) is the template for the About Us page.
- [templates/how-it-works.html.jinja](/templates/how-it-works.html.jinja) is the template for the How ShellCast Works page.
- [templates/preferences.html.jinja](/templates/preferences.html.jinja) is the template for the Preferences page.
- [templates/signin.html.jinja](/templates/signin.html.jinja) is the template for the sign in page.

### 6.7 JavaScript and CSS

The JS and CSS files for each page are grouped together in directories in [static/](/static/) that correspond to each template.  The [static/commmon/](/static/common/) directory contains JS and CSS that is common to all web pages (such as authentication code).  (I realize that renaming common/ to base/ to match the template naming or vice versa would have been smart, but that's just the way things were named initially and were never renamed.)

Several ES6 features of JavaScript are used throughout the JS files such as: the let/const keywords for declaring variables, arrow functions, and async/await syntax for asynchronous programming.  At the bottom of most of the JS files, you will find an immediately invoked function expression (IIFE) which basically serves as a setup/main function that runs as soon as that JS file is loaded.

## 7. Contact Information

If you have any questions, feedback, or suggestions please submit issues [through the NCSU Enterprise GitHub](https://github.ncsu.edu/biosystemsanalyticslab/shellcast/issues) or [through GitHub (public)](https://github.com/Biosystems-Analytics-Lab/shellcast/issues). You can also reach out to Sheila Saia (ssaia at ncsu dot edu) or Natalie Nelson (nnelson4 at ncsu dot edu).
