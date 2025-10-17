-- Create database

CREATE DATABASE IF NOT EXISTS shellcast_fl;

USE shellcast_fl;

-- Stores user information.
CREATE TABLE users (
	id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
	firebase_uid varchar(28) NULL,
	phone_number varchar(11) NULL,
	email varchar(50) NOT NULL,
	email_pref boolean NOT NULL DEFAULT false,
    email_consent boolean NOT NULL DEFAULT false,
	text_pref boolean NOT NULL DEFAULT false,
    text_consent boolean NOT NULL DEFAULT false,
	prob_pref tinyint NOT NULL DEFAULT 75,
    email_opt_in_date datetime NULL,
    text_opt_in_date datetime NULL,
    email_opt_out_date datetime NULL,
    text_opt_out_date datetime NULL,
    email_verification_sent boolean NOT NULL DEFAULT false,
    text_verification_sent boolean NOT NULL DEFAULT false,
	deleted boolean DEFAULT false,
	created datetime DEFAULT NOW(),
	updated datetime DEFAULT NOW() ON UPDATE NOW(),
);

-- Stores the growing units.
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
        u.email_consent,
        u.text_pref,
        u.text_consent,
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
