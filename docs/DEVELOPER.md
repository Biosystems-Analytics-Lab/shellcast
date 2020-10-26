## Code Structure
- main.py - This file is the root of the Python Flask application.
- app.yaml - This file contains all of the configuration needed to deploy the app to Google Cloud.
- .gcloudignore - This file is similar to a .gitignore file in the sense that it specifies all of the files that will __not__ be uploaded to Google Cloud during deployments.
- config-template.py - This is a template that should be copied to make a local config.py file.
- __templates__ - This folder contains all of the Jinja templates.
- __static__ - This folder contains all of the static content that is served like CSS and JS files.
- __models__ - This folder contains all of the ORM models that are used to interact with the database.
- __routes__ - This folder contains all of the routes that are registered with the Flask application.
- __tests__ - This folder contains all of the unit tests for the application.
- __db-scripts__ - This folder contains helpful SQL scripts that can be used to setup a new database and populate it with initial records.

## Development Environment Setup

### Install Google Cloud SDK
The Google Cloud SDK is principally a command line tool that allows you to interact with Google Cloud from your local machine and perform various tasks. You can download and install the Google Cloud SDK by following [these instructions](https://cloud.google.com/sdk/docs).

### Download Cloud SQL proxy
You can download and setup the Cloud SQL proxy by following [these instructions](https://cloud.google.com/sql/docs/mysql/quickstart-proxy-test#install-proxy). Take note of where you download the proxy script. You will need to run it often, so keep it in a place that's easy to reference.

### Clone this repository
Clone this repository to your machine by running `git clone https://github.ncsu.edu/ssaia/shellcast.git`.

### Setup Python virtual environment
1. Make sure that you have Python 3 installed on your machine.
2. From the root directory of the repository, create a virtual environment by running `python3 -m venv venv`.
3. Activate the virtual environment by running `source venv/bin/activate` if on a Linux or Mac machine. If on a Windows machine, run `venv\Scripts\activate.bat`.  Now "python" will refer to the virtual environment's copy of Python 3. You can deactivate the virtual environment by running `deactivate` (Linux/Mac/Windows).
4. Install the app and testing dependencies by running `pip install -r requirements.txt` and then `pip install -r requirements-test.txt`.

### Make a Unix socket directory
To use the Cloud SQL proxy for local development and testing of the web app, a directory is needed for a Unix socket. From the root directory of the repository, make a new directory named "cloudsql" by running `mkdir cloudsql`.

### Make a configuration file based on the template file
The web app uses a configuration file named "config.py" to store various configuration options. Some of these are quite sensitive (e.g. database credentials), so they shouldn't be saved in version control. Because of this, a "config.py" file isn't in the Git repository but rather a "config-template.py" file which provides all of the necessary structure for the "config.py" file with all of the non-sensitive values already populated.
1. On your machine in the root of the repository, simply make a copy of config-template.py and name it "config.py". This file will automatically be ignored by Git because it is in the .gitignore.
2. You will now need to populate several values into config.py like the AWS Access Key ID, AWS Secret Access Key, Google Maps JavaScript API key, the database username, and the database password. Any values that you need to add are indicated by "ADD_VALUE_HERE". You can get these values through another communication channel.

### Setup Google service account credentials for Firebase Admin SDK
Since Firebase authentication is used for managing users, the web app uses the Firebase Admin SDK to verify user ID tokens sent from the front end. The Admin SDK uses the concept of [Application Default Credentials](https://cloud.google.com/docs/authentication/production#providing_credentials_to_your_application) to implicitly find service account credentials in its environment so that it can access Firebase services. Service account credentials are already present when the app is deployed on GCP environments like App Engine so the Admin SDK can find them no problem. When developing locally, you have do a little work to help the Admin SDK with credentials. [This article](https://medium.com/google-cloud/firebase-separating-configuration-from-code-in-admin-sdk-d2bcd2e87de6) paints a pretty clear picture of what is going on with the credentials while on App Engine vs. developing locally (and what you need to do to set them up correctly).

So what you need to do at this point is:
1. Generate and download a private key file for the Firebase service account
  - Go to the Firebase console and click on Settings > Service Accounts (or just click [here](https://console.firebase.google.com/u/1/project/ncsu-shellcast/settings/serviceaccounts/adminsdk))
  - Click generate new private key and store the file securely on your machine.  If you save it inside of the repo as `firebase-admin-sdk-credentials.json`, then it should be ignored by both .gitignore and .gcloudignore.  If you store it outside of the repo, then you won't have to worry about it being pushed to GitHub when you commit or Google Cloud when you deploy.  You do __NOT__ want to push this file to either of those places because it contains extremely sensitive information.
2. Now that you have the credentials file, you just have to create an environment variable called `GOOGLE_APPLICATION_CREDENTIALS` which stores the absolute path to the file and the Admin SDK will implicitly find it as if running in App Engine.  On Linux/Mac you can run `export GOOGLE_APPLICATION_CREDENTIALS="/path/to/firebase-admin-sdk-credentials.json"`.  On Windows in Powershell you can run `$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\firebase-admin-sdk-credentials.json"`.

## Common Development Tasks

### Use the Cloud SQL proxy (TCP and Unix socket)
By using the Cloud SQL proxy, you can connect to the Google Cloud SQL database instances using any tool that can connect with a TCP connection or a Unix socket (you can't use Unix sockets on Windows).  The Cloud SQL proxy also allows the web application to reach the Cloud SQL database for use with local development and testing.
- To use the Cloud SQL proxy with a TCP connection, run `<PATH TO PROXY SCRIPT>/cloud_sql_proxy -instances=ncsu-shellcast:us-east1:ncsu-shellcast-database=tcp:3306`.
- To use the Cloud SQL proxy with a Unix socket, you need to make a directory for the Unix socket and then run `<PATH TO PROXY SCRIPT>/cloud_sql_proxy -dir=<PATH TO UNIX SOCKET DIRECTORY> -instances=ncsu-shellcast:us-east1:ncsu-shellcast-database`.

### Run the application locally
1. Make sure the Python virtual environment is activated.
2. Make sure the Cloud SQL proxy is started with a Unix socket (run `<PATH TO PROXY SCRIPT>/cloud_sql_proxy -dir=./cloudsql -instances=ncsu-shellcast:us-east1:ncsu-shellcast-database`).
3. Run the Python app by running `python main.py`.
4. Now you can navigate to [http://localhost:3361](http//:localhost:3361) in your browser to see the web app.

### Run unit tests
1. Make sure the Python virtual environment is activated.
2. Make sure the Cloud SQL proxy is started with a Unix socket (run `<PATH TO PROXY SCRIPT>/cloud_sql_proxy -dir=./cloudsql -instances=ncsu-shellcast:us-east1:ncsu-shellcast-database`).
3. Run the tests by running `python -m pytest -v`. You should see the test output in the console.
4. If you'd like to see code coverage information as well, then you can run `python -m pytest -v --cov`.  You can then also see more in-depth coverage information by running `coverage html` which will generate web pages in the "htmlcov" directory.  If you open "htmlcov/index.html" in a web browser, then you can click through all of the Python files that were measured and see the exact lines that were run or missed.

### Deploy the app to Google App Engine
1. Make sure that you are signed in and using the correct project (ncsu-shellcast) by running `gcloud info`.
2. From the root directory of the repository, you can deploy the application to Google App Engine by running `gcloud app deploy`.
