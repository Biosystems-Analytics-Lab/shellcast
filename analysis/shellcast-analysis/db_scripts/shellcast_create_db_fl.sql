-- Create database

CREATE DATABASE IF NOT EXISTS shellcast_fl;

USE shellcast_fl;

-- Stores the mobile phone service providers that we can send MMS messages to.
CREATE TABLE phone_service_providers (
	id int(3) UNSIGNED ZEROFILL NOT NULL AUTO_INCREMENT PRIMARY KEY,
	name varchar(30) NOT NULL DEFAULT '',
	mms_gateway varchar(30) NOT NULL DEFAULT '',
	sms_gateway varchar(30) NOT NULL DEFAULT ''
);

-- Stores user information.
CREATE TABLE users (
	id int(5) UNSIGNED ZEROFILL NOT NULL AUTO_INCREMENT PRIMARY KEY,
	firebase_uid varchar(28) NULL,
	phone_number varchar(11) NULL,
	service_provider_id int(5) UNSIGNED ZEROFILL NULL,
	email varchar(50) NOT NULL,
	email_pref boolean NOT NULL DEFAULT false,
	text_pref boolean NOT NULL DEFAULT false,
	prob_pref tinyint(3) NOT NULL DEFAULT 75,
	deleted boolean DEFAULT false,
	created datetime DEFAULT NOW(),
	updated datetime DEFAULT NOW() ON UPDATE NOW(),
    FOREIGN KEY (service_provider_id) REFERENCES phone_service_providers(id)
);

-- Stores the growing units.
-- DROP TABLE IF EXISTS cmus;
CREATE TABLE cmus (
	id varchar(10) NOT NULL PRIMARY KEY,
	sh_name varchar(50) NULL,
	rainfall_desc varchar(100),
	rainfall_thresh_days int NOT NULL,
	rainfall_thresh_in decimal(4, 2) NOT NULL,
	emerg_cond varchar(3) NULL,
	created datetime DEFAULT NOW()
);

-- Stores information about all potential leases retrieved from the API.
-- DROP TABLE IF EXISTS leases;
CREATE TABLE leases (
	lease_id varchar(20) NOT NULL PRIMARY KEY,
	cmu_id varchar(10) NOT NULL,
    parcel_number varchar(20) NULL,
    parcel_name varchar(50) NULL,
	grow_area_type varchar(20) NULL,
	waterbody varchar(50) NULL,
	latitude double NOT NULL,
	longitude double NOT NULL,
	created datetime DEFAULT NOW(),
	updated datetime DEFAULT NOW() ON UPDATE NOW(),
	FOREIGN KEY (cmu_id) REFERENCES cmus(id)
);

-- Stores information about user leases.
CREATE TABLE user_leases (
	id int(5) UNSIGNED ZEROFILL NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id int(5) UNSIGNED ZEROFILL NOT NULL,
	lease_id varchar(20) NOT NULL,
	deleted TINYINT(1) DEFAULT 0,
	created datetime DEFAULT NOW(),
	updated datetime DEFAULT NOW() ON UPDATE NOW(),
    CONSTRAINT unique_leases_per_user UNIQUE (user_id, lease_id)
);

-- Stores a log of all notifications that are sent to users.
CREATE TABLE notification_log (
	id int(5) UNSIGNED ZEROFILL NOT NULL AUTO_INCREMENT PRIMARY KEY ,
	user_id int(5) UNSIGNED ZEROFILL NOT NULL,
	address varchar(50) NOT NULL,
	notification_text text(10000) NOT NULL,
	notification_type varchar(10) NOT NULL,
	send_success boolean DEFAULT true,
	response_text text(10000) NULL,
	created datetime DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Stores the closure probabilities for each growing unit.
CREATE TABLE cmu_probabilities (
  id int(5) UNSIGNED ZEROFILL NOT NULL AUTO_INCREMENT PRIMARY KEY,
  cmu_id varchar(10) NOT NULL,
  prob_1d_perc tinyint(3) NULL,
  created datetime DEFAULT NOW(),
  FOREIGN KEY (cmu_name) REFERENCES cmus(id)
);

-- Mobile phone service providers
INSERT INTO phone_service_providers (`name`, `mms_gateway`, `sms_gateway`)
VALUES
    ('AT&T', 'mms.att.net', 'txt.att.net'),
    ('T-Mobile', 'tmomail.net', 'tmomail.net'),
    ('Verizon', 'vzwpix.com', 'vtext.com'),
    ('Sprint (Pre-merger)', 'pm.sprint.com', 'messaging.sprintpcs.com'),
    ('US Cellular', 'mms.uscc.net', 'email.uscc.net'),
    ('Straight Talk', 'mypixmessages.com', 'vtext.com'),
    ('Xfinity Mobile', 'mypixmessages.com', 'vtext.com'),
    ('Virgin Mobile', 'vmpix.com', 'vmobl.com'),
    ('Metro PCS', 'mymetropcs.com', 'mymetropcs.com'),
    ('Boost Mobile', 'myboostmobile.com', 'sms.myboostmobile.com'),
    ('Cricket Wireless', 'mms.cricketwireless.net', 'mms.cricketwireless.net'),
    ('Google Fi', 'msg.fi.google.com', 'msg.fi.google.com')
;


INSERT INTO cmus (`id`, `sh_name`, `rainfall_desc`, `rainfall_thresh_in`, `rainfall_thresh_days`, `emerg_cond`)
VALUES
     ('02_1', 'Pensacola Bay System', '5 days > 3.35\"', 3.35, 5, 'NO'),
    ('02_3', 'Pensacola Bay System', '5 days > 3.80\" NOAA', 3.80, 5, 'NO'),
    ('08_9', 'West Bay', '5 days > 2.63\" NOAA', 2.63, 5, 'NO'),
    ('12_10', 'East Bay', '5 days > 3.87\"', 3.87, 5, 'NO'),
    ('18_3', 'Alligator Harbor', '4 days > 9.13\"', 9.13, 4, 'YES'),
    ('22_6', 'Wakulla', '7 days > 3.58\" Ochlock SP', 3.58, 7, 'NO'),
    ('22_8', 'Wakulla', '7 days > 1.08\" Ochlock SP', 1.08, 7, 'NO'),
    ('25_6', 'Horseshoe Beach', '1 day > 3.56\" Manatee Springs SP', 3.56, 1, 'NO'),
    ('30_1', 'Cedar Key', '3 days > 10.5\" Cedar Key Forestry', 10.5, 3, 'YES'),
    ('30_10', 'Cedar Key', '3 days > 6.67\" Cedar Key Forestry', 6.67, 3, 'NO'),
    ('48_1', 'Lower Tampa Bay', '3 days > 4.22\" Palmetto WWTP', 4.22, 3, 'NO'),
    ('58_5', 'Gasparilla Sound', '3 days > 6.97\" Gasparilla WWTP', 6.97, 3, 'NO'),
    ('62_5', 'Pine Island Sound', '2 days > 6.23\" NOAA', 6.23, 2, 'NO'),
    ('62_6', 'Pine Island Sound', '3 days > 3.69\" NOAA', 3.69, 3, 'NO'),
    ('66_1', 'Ten Thousand Islands', '2 days > 3.50\" NOAA', 3.50, 2, 'NO'),
    ('72_2', 'North Indian River', '2 days > 2.54\" NOAA', 2.54, 2, 'NO'),
    ('74_1', 'Body F', '2 days > 3.05\" NOAA', 3.05, 2, 'NO'),
    ('82_27', 'South Volusia', '2 days > 2.40\" Vol Cty SE Water Reclamation', 2.40, 2, 'NO'),
    ('82_32', 'South Volusia', '2 days > 2.40\" Vol Cty SE Water Reclamation', 2.40, 2, 'NO'),
    ('82_9', 'South Volusia', '2 days > 5.37\" Vol Cty SE Water Reclamation', 5.37, 2, 'NO'),
    ('88_10', 'South St. Johns', '6 days > 4.84\" NOAA', 4.84, 6, 'NO')
;


-- Stored procedures
DELIMITER //
DROP PROCEDURE IF EXISTS SelectCmuProbsToday;
CREATE PROCEDURE SelectCmuProbsToday()
BEGIN
    SELECT * FROM cmu_probabilities WHERE DATE(`created`) = CURDATE();
END //


DELIMITER //
DROP PROCEDURE IF EXISTS DeleteCmuProbsToday;
CREATE PROCEDURE DeleteCmuProbsToday()
BEGIN
    SET SQL_SAFE_UPDATES = 0;
    DELETE FROM cmu_probabilities WHERE DATE(created) = CURDATE();
    SET SQL_SAFE_UPDATES = 1;
END //