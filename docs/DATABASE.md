# DATABASE.md

This document is intended to help a developer understand the ShellCast database structure and make changes to the database.

_The following instructions assume that you are using [Sequel Pro](https://sequelpro.com/) as your database client.  Unfortunately, Sequel Pro is only available on Mac, however, you should be able to use any database client to access the database by following the instructions under [Connecting to Cloud SQL](#2-connecting-to-google-cloud-sql).  A powerful alternative to Sequel Pro is [DBeaver](https://dbeaver.io/) which is free, open source, and multiplatform._

## Table of Contents

1. [Database Design](#1-database-design)

2. [Connecting to Google Cloud SQL](#2-connecting-to-google-cloud-sql)

3. [Downloading Database Tables](#3-downloading-database-tables)

4. [Editing User Information and Leases](#4-editing-user-information-and-leases)

5. [Contact Information](#5-contact-information)

## 1. Database Design

ShellCast uses a MySQL 5.7 instance hosted on Google Cloud SQL.
⚒️_TODO: Upgrade to MySQL 8.0_

There are 7 tables for North Carolina and Florida. There is no 'cmu' table for South Carolina. Each state has a slightly different set of table columns. The database table schema can be found in the `analysis/shellcast-analysis/db_scripts` directory in the sql files.
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

There are 3 "databases" in the MySQL instance: `shellcast_fl`, `shellcast_nc`, and `shellcast_sc` production database that the live, public site uses.  `shellcast_dev` is the development database that is used when running the application on a local machine.  `shellcast_testing` is a database that is used for running the unit tests for the application.  `shellcast_testing` is wiped clean after every test. </br></br>
Alternatively, you can use locally installed MySQL or a Docker MySQL image for ShellCast analysis development. Modify the `config.ini` database connection variable and the database name in `[state]_main.py` to use the new database connection.

![`shellcast_fl`](images/shellcast_fl_db.png)



![shellcast_nc](/Users/makiko/CGAProjects/NCSUGitHubProjects/shellcast/docs/images/shellcast_nc_db.png)

![shellcast_sc](/Users/makiko/CGAProjects/NCSUGitHubProjects/shellcast/docs/images/shellcast_sc_db.png)

## 2. Connecting to Google Cloud SQL

1. Complete the [Install and initialize Google Cloud SDK](DEVELOPER.md#41-install-and-initialize-google-cloud-sdk)
2. Complete the [Download Cloud SQL proxy](DEVELOPER.md#42-download-cloud-sql-proxy).
3. Start a TCP connection by running the first command in the [Use the Cloud SQL proxy](DEVELOPER.md#51-use-the-cloud-sql-proxy-tcp-and-unix-socket)
4. Now you can connect to the database instance with Sequel Pro (or any other SQL client) with the following connection details:
  - Host: 127.0.0.1
  - Username: (you should get the password from the maintainers of ShellCast if you're working on ShellCast)
  - Password: (you should get the password from the maintainers of ShellCast if you're working on ShellCast)
  - Port: 3306

## 3. Downloading Database Tables

3.1 Using MySQL Client
1. See [Connect using a MySQL client](https://cloud.google.com/sql/docs/mysql/connect-admin-ip#install-mysql-client)
2. ```sql 
   SELECT * FROM shellcast_nc.cmu_probabilities INTO OUTFILE '/path/to/directory/nc_cmu_probabilities.csv' FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n';
   ```
3.2 Using MySQL Workbench
1. Download MySQL Workbench from [here](https://dev.mysql.com/downloads/workbench/)
2. Use Cloud SQL Proxy to connect to the database 
3. See [Creating A New MySQL Connection](https://dev.mysql.com/doc/workbench/en/wb-getting-started-tutorial-create-connection.html)
3. You can download the current state of the database as CSV files using MySQL Workbench Sequel Pro or .</br></br>
__Instructions for Sequel Pro__: </br>
1. Select all of the tables you'd like to download records for.
2. Click the gear icon at the bottom left of the window.
3. Choose "Export > As CSV file...".
4. A new window should open where you can change some settings related to the export.  The default settings are probably what you want, so just choose where you want to the files to be saved to and click "Export".

## 4. Editing User Information and Leases

- User information such as phone number, email address, and email/text/probability preference can be found in the users table.  Simply double-click on the value you would like to change.
- User lease information such as growing area name, CMU name, rainfall threshold, and location can be found in the user_leases table.  Simply double-click on the value you would like to change.

## 5. Contact Information

If you have any questions, feedback, or suggestions please submit issues [through the NCSU Enterprise GitHub](https://github.ncsu.edu/biosystemsanalyticslab/shellcast/issues) or [through GitHub (public)](https://github.com/Biosystems-Analytics-Lab/shellcast/issues). You can also reach out to Sheila Saia (ssaia at ncsu dot edu) or Natalie Nelson (nnelson4 at ncsu dot edu).
