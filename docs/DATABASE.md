_The following instructions assume that you are using [Sequel Pro](https://sequelpro.com/) as your database client.  Unfortunately, Sequel Pro is only available on Mac, however, you should be able to use any database client to access the database by following the instructions under [Connecting to Cloud SQL](#connecting-to-cloud-sql).  A powerful alternative to Sequel Pro is [DBeaver](https://dbeaver.io/) which is free, open source, and multiplatform._

## Database Design
ShellCast uses a MySQL 5.7 instance hosted on Google Cloud SQL.

There are 6 tables.
- users
  - Stores information about users.
  - User accounts and authentication are mainly handled by Firebase.  In our database, we simply create a user record when a new user registers through Firebase and store the Firebase UID in the record along with other information.
- user_leases
  - Stores the leases that users have added to their accounts.
  - Leases are associated with a particular user.  If two users create two of the exact same leases, then they will still be stored as two different records in the database.
- ncmdf_leases
  - Stores all of the leases registered with the North Carolina Division of Marine Fisheries (NCDMF).  These are the leases that users can search for in the application and then add to their accounts.
  - The records in this table are "manually" added and should be updated periodically.  There were intentions to automate the retrieval of leases directly from NCDMF's database on a regular basis, but this has not been set up.
- cmus
  - Stores the NCDMF conditional management units (CMU).
- cmu_probabilities
  - Stores calculated closure probabilities for each CMU.
  - These probabilities are calculated and added to the database on a daily basis.  The probability for the CMU that a given lease belongs to is also the probability for that lease.
- notification_log
  - Stores a log of all notifications that are sent to users.
  - Each notification is associated with a user that the notification is sent to as well as the closure probability that triggered the notification.

_ADD DB DIAGRAM_

## Connecting to Google Cloud SQL


## Downloading database tables
You can download the current state of the database as CSV files using Sequel Pro.
1. Select all of the tables you'd like to download records for.
2. Click the gear icon at the bottom left of the window.
3. Choose "Export > As CSV file...".
4. A new window should open where you can change some settings related to the export.  The default settings are probably what you want, so just choose where you want to the files to be saved to and click "Export".

## Editing user records
