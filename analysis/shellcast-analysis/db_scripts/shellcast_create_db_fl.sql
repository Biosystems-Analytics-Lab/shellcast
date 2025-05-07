-- Create database

CREATE DATABASE IF NOT EXISTS shellcast_fl;

USE shellcast_fl;

-- Stores the mobile phone service providers that we can send MMS messages to.
CREATE TABLE phone_service_providers (
	id int AUTO_INCREMENT PRIMARY KEY,
	name varchar(30) NOT NULL DEFAULT '',
	mms_gateway varchar(30) NOT NULL DEFAULT '',
	sms_gateway varchar(30) NOT NULL DEFAULT ''
);

-- Stores user information.
CREATE TABLE users (
	id int AUTO_INCREMENT PRIMARY KEY,
	firebase_uid varchar(28) NULL,
	phone_number varchar(11) NULL,
	service_provider_id int,
	email varchar(50) NOT NULL,
	email_pref boolean NOT NULL DEFAULT false,
	text_pref boolean NOT NULL DEFAULT false,
	prob_pref tinyint NOT NULL DEFAULT 75,
	deleted boolean DEFAULT false,
	created datetime DEFAULT NOW(),
	updated datetime DEFAULT NOW() ON UPDATE NOW(),
    FOREIGN KEY (service_provider_id) REFERENCES phone_service_providers(id)
);

-- Stores the growing units.
-- DROP TABLE IF EXISTS cmus;
-- CREATE TABLE cmus (
--	id varchar(10) NOT NULL PRIMARY KEY,
--	sh_name varchar(50) NULL,
--	rainfall_desc varchar(100),
--	rainfall_thresh_days int NOT NULL,
--	rainfall_thresh_in decimal(4, 2) NOT NULL,
--	emerg_cond varchar(3) NULL,
--	created datetime DEFAULT NOW()
-- );

-- DROP TABLE IF EXISTS cmus;
CREATE TABLE cmus (
    id varchar(10) NOT NULL PRIMARY KEY,
	sh_id varchar(10) NOT NULL,
	sh_name varchar(50) NULL,
	rainfall_desc varchar(100),
	rainfall_thresh_days int NOT NULL,
	rainfall_thresh_in decimal(4, 2) NOT NULL,
	season varchar(100) NOT NULL,
	created datetime DEFAULT NOW()
);

-- Stores information about all potential leases retrieved from the API.
-- DROP TABLE IF EXISTS leases;
CREATE TABLE leases (
    id int AUTO_INCREMENT PRIMARY KEY,
	lease_id varchar(20) NOT NULL,
	cmu_id varchar(10) NOT NULL,
    parcel_name varchar(50) NULL,
	waterbody varchar(50) NULL,
	grow_area_type varchar(20) NULL,
	latitude double NOT NULL,
	longitude double NOT NULL,
	created datetime DEFAULT NOW(),
	updated datetime DEFAULT NOW() ON UPDATE NOW(),
	FOREIGN KEY (cmu_id) REFERENCES cmus(id)
);

-- Stores information about user leases.
CREATE TABLE user_leases (
	id int AUTO_INCREMENT PRIMARY KEY,
    user_id int NOT NULL,
	lease_id varchar(20) NOT NULL,
	deleted tinyint DEFAULT 0,
	created datetime DEFAULT NOW(),
	updated datetime DEFAULT NOW() ON UPDATE NOW(),
    CONSTRAINT unique_leases_per_user UNIQUE (user_id, lease_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
);

-- Stores a log of all notifications that are sent to users.
CREATE TABLE notification_log (
	id int AUTO_INCREMENT PRIMARY KEY ,
	user_id int NOT NULL,
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
  id int AUTO_INCREMENT PRIMARY KEY,
  cmu_id varchar(10) NOT NULL,
  prob_1d_perc tinyint NULL,
  created datetime DEFAULT NOW(),
  FOREIGN KEY (cmu_id) REFERENCES cmus(id)
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

DELIMITER //
CREATE PROCEDURE SelectUserLeaseProbsToday()
BEGIN
    SELECT
        u.id AS user_id,
        u.email,
        u.phone_number,
        u.service_provider_id,
        u.email_pref,
        u.text_pref,
        u.prob_pref,
        l.lease_id,
        l.parcel_name,
        l.waterbody,
        l.grow_area_type,
        l.cmu_id,
        cp.prob_1d_perc
    FROM users u
    JOIN user_leases ul ON u.id = ul.user_id
    JOIN leases l ON ul.lease_id = l.lease_id
    JOIN cmu_probabilities cp ON l.cmu_id = cp.cmu_id
    WHERE DATE(cp.created) = CURDATE()
    AND u.deleted = false
    AND ul.deleted = 0;
END //