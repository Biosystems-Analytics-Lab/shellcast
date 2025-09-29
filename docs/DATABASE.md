# DATABASE.md

This document is intended to help a developer understand the ShellCast database structure and make changes to the database.

## Table of Contents

1. [Database Design](#1-database-design)
2. [Create a Dedicated Database User for Google App Engine]()
2. [Connecting to Google Cloud SQL](#2-connecting-to-google-cloud-sql)
3. [Downloading Database Tables](#3-downloading-database-tables)
4. [Editing User Information and Leases](#4-editing-user-information-and-leases)
5. [Contact Information](#5-contact-information)

## 1. Database Design

ShellCast uses a MySQL 5.7 instance hosted on Google Cloud SQL.</br>
⚒️ _TODO: Upgrade to MySQL 8.0_

Database table descriptions as below. Each state has a slightly different set of table columns. The database table schema can be found in the `analysis/shellcast-analysis/db_scripts` directory in the sql files.

- users
  - Stores information about users.
  - User accounts and authentication are mainly handled by Firebase.  In our database, we simply create a user record when a new user registers through Firebase and store the Firebase UID in the record along with other information.
- user_leases
  - Stores the leases that users have added to their accounts.
  - Leases are associated with a particular user.  If two users create two of the exact same leases, then they will still be stored as two different records in the database.
- leases
  - Stores all of the leases registered with an organization in each state.  These are the leases that users can search for in the application and then add to their accounts.
  - The records in this table are "manually" added and should be updated periodically.
- cmus
  - Stores the conditional management units (CMU) or shellfish harvested area (SHA).
  - Records in this table are manually added and should be updated when any changes occur.
- cmu_probabilities
  - Stores calculated closure probabilities for each CMU.
  - These probabilities are calculated and added to the database on a daily basis. The probability for the CMU that a given lease belongs to is also the probability for that lease.
- notification_log
  - Stores a log of all notifications that are sent to users.
  - Each notification is associated with a user that the notification is sent to as well as the closure probability that triggered the notification.
- phone_service_providers
  - Stores information about phone service providers.
  - This table is used to determine the email-to-SMS gateway for a user's phone number.  This is used to send text notifications to users.

There are 3 "databases" in the Cloud SQL MySQL instance: `shellcast_fl`, `shellcast_nc`, and `shellcast_sc` production database that the live, public site uses.  `shellcast_dev` is the development database that is used when running the application on a local machine.  `shellcast_testing` is a database that is used for running the unit tests for the application.  `shellcast_testing` is wiped clean after every test. </br></br>
Alternatively, you can use locally installed MySQL or a Docker MySQL image for ShellCast analysis development. Modify the `config.ini` database connection variable and the database name in `[state]_main.py` to use the new database connection.

Database diagrams for each state are shown below:



__DB Name: shellcast_nc__
![shellcast_nc](/Users/makiko/CGAProjects/NCSUGitHubProjects/shellcast/docs/images/shellcast_nc_db.png)



__DB Name: shellcast_sc__
![shellcast_sc](/Users/makiko/CGAProjects/NCSUGitHubProjects/shellcast/docs/images/shellcast_sc_db.png)



__DB Name: shellcast_fl__
![`shellcast_fl`](images/shellcast_fl_db.png)

## 2. Create a Dedicated Database User for Google App Engine
1. Generate password </br>
_Example:_
  ```
  python -c "import secrets; print(secrets.token_urlsafe(16))"
  ```
2. Connect to your Cloud SQL instance
```
gcloud sql connect {SQL instance name} --user root"
```
3. Enter "root" user password after you see folowing.
```
Connecting to database with SQL user [root].Enter password:
```
4. Create user
```sql
-- Create a minimal privilege database user for shellcast-sc application
-- This user will have ONLY the privileges needed for the application to function

-- Create the user (replace 'your_secure_password' with a strong password)
CREATE USER '<user name>'@'%' IDENTIFIED BY '<user password>';

-- Grant only the essential privileges for application operation
-- SELECT: Read data
-- INSERT: Add new records
-- UPDATE: Modify existing records  
-- DELETE: Remove records
GRANT SELECT, INSERT, UPDATE ON <database name>.* TO '<user name'@'%';

-- Apply the changes
FLUSH PRIVILEGES;

-- Verify the user was created correctly
SELECT User, Host FROM mysql.user WHERE User = '<user name>';

-- Show the granted privileges
SHOW GRANTS FOR '<user name>'@'%';
```
5. Update "DB_USER" and "DB_PASSWORD" for app.yaml and .env

## 3. Connecting to Google Cloud SQL with MySQL Workbench

1. Install, and initialize the Google Cloud SDK by following [these instructions](https://cloud.google.com/sdk/docs/quickstart).

2. Install MySQL by following [these instructions](https://downloads.mysql.com/archives/community/).
3. Install MySQL Workbench - [MySQL Community Downloads](https://dev.mysql.com/downloads/workbench/).
4. Download the cloud SQL proxy if you haven't already done so.  Regardless of where you download it, you can connect to your cloud SQL database from there, but we recommend downloading it under the root of your project for convenience. Cloud SQ Proxy can be downloaded from below links along with instructions.
   - https://github.com/GoogleCloudPlatform/cloud-sql-proxy
   - https://cloud.google.com/sql/docs/mysql/sql-proxy 
5. Make TCP connection ```./cloud-sql-proxy --port 3306 "{instance_connection_name}"```. You can obtain "instance connection name" from the Google Cloud Console. Go to [View instance information](https://console.cloud.google.com/sql/instances) and click "Instance ID". Copy "Connection name" under "Connect to this instance" section and Rreplace "{instance_connection_name}".
6. Connect to the database instance with MySQL Workbench
   - Now you can connect to the database instance with the following connection details:
     - Host: 127.0.0.1
     - Username: (you should get the password from the maintainers of ShellCast if you're working on ShellCast)
     - Password: (you should get the password from the maintainers of ShellCast if you're working on ShellCast)
     - Port: 3306
7. You can close MySQL Workbench connection by closing DB connection tab.
8. `Ctrl+C` to close the Cloud SQL Proxy connection.

## 4. Downloading Database Tables

3.1 Using MySQL Workbench

1. Download MySQL Workbench from [here](https://dev.mysql.com/downloads/workbench/)
2. Use Cloud SQL Proxy to connect to the database 
3. See [Creating A New MySQL Connection](https://dev.mysql.com/doc/workbench/en/wb-getting-started-tutorial-create-connection.html)
4. You can download the current state of the database as CSV files using MySQL Workbench Sequel Pro or .</br>

### 3.2 Using MySQL Client

1. See [Connect using a MySQL client](https://cloud.google.com/sql/docs/mysql/connect-admin-ip#install-mysql-client)
2. In terminal, type in SQL query to download the table as a CSV file. For example, to download the `cmu_probabilities` table in the `shellcast_nc` database, you can use the following query:

```sql 
   SELECT * FROM shellcast_nc.cmu_probabilities INTO OUTFILE '/path/to/directory/nc_cmu_probabilities.csv' FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n';
```

## 5. Editing User Information and Leases

- User information such as phone number, email address, and email/text/probability preference can be found in the users table.  Simply double-click on the value you would like to change.
- User lease information such as growing area name, CMU name, rainfall threshold, and location can be found in the user_leases table.  Simply double-click on the value you would like to change.

## 5. Contact Information

If you have any questions, feedback, or suggestions please submit issues [through the NCSU Enterprise GitHub](https://github.ncsu.edu/biosystemsanalyticslab/shellcast/issues) or [through GitHub (public)](https://github.com/Biosystems-Analytics-Lab/shellcast/issues). You can also reach out to Sheila Saia (ssaia at ncsu dot edu) or Natalie Nelson (nnelson4 at ncsu dot edu).
