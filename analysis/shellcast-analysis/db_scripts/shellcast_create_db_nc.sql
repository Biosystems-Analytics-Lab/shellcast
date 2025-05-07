-- Create database
CREATE DATABASE shellcast_nc;

USE shellcast_nc;

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
	service_provider_id int NULL,
	email varchar(50) NOT NULL,
	email_pref boolean NOT NULL DEFAULT false,
	text_pref boolean NOT NULL DEFAULT false,
	prob_pref tinyint NOT NULL DEFAULT 75,
	deleted boolean DEFAULT false,
	created datetime DEFAULT NOW(),
	updated datetime DEFAULT NOW() ON UPDATE NOW(),
    FOREIGN KEY (service_provider_id) REFERENCES phone_service_providers(id)
);

-- Stores information about all potential leases retrieved from the NCDMF API.
CREATE TABLE leases (
	lease_id varchar(20) NOT NULL PRIMARY KEY,
	grow_area_name varchar(3) NULL,
	grow_area_desc varchar(50) NULL,
	cmu_name varchar(10) NOT NULL,
	rainfall_thresh_in decimal(3, 2) NULL,
	latitude double NULL,
	longitude double NULL,
	created datetime DEFAULT NOW(),
	updated datetime DEFAULT NOW() ON UPDATE NOW()
);

-- Stores information about user leases.
CREATE TABLE user_leases (
	id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id int NOT NULL,
	lease_id varchar(20) NOT NULL,
	deleted tinyint DEFAULT 0,
	created datetime DEFAULT NOW(),
	updated datetime DEFAULT NOW() ON UPDATE NOW(),
    CONSTRAINT unique_leases_per_user UNIQUE (user_id, lease_id)
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

-- Stores the growing units.
CREATE TABLE cmus (
	id int AUTO_INCREMENT PRIMARY KEY,
	cmu_name varchar(10) NOT NULL,
	created datetime DEFAULT NOW()
);

-- Stores the closure probabilities for each growing unit.
CREATE TABLE cmu_probabilities (
  id int AUTO_INCREMENT PRIMARY KEY,
  cmu_name varchar(10) NOT NULL,
  prob_1d_perc tinyint NULL,
  prob_2d_perc tinyint NULL,
  prob_3d_perc tinyint NULL,
  created datetime DEFAULT NOW()
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

USE shellcast_nc;
DELIMITER //
CREATE PROCEDURE SelectCmuProbsToday()
BEGIN
    SELECT * FROM cmu_probabilities WHERE DATE(`created`) = CURDATE();
END //


DELIMITER //
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
        l.grow_area_name,
        l.cmu_name,
        cp.prob_1d_perc,
        cp.prob_2d_perc,
        cp.prob_3d_perc
    FROM users u
    JOIN user_leases ul ON u.id = ul.user_id
    JOIN leases l ON ul.lease_id = l.lease_id
    JOIN cmu_probabilities cp ON l.cmu_name = cp.cmu_name
    WHERE DATE(cp.created) = CURDATE()
    AND u.deleted = false
    AND ul.deleted = 0;
END //