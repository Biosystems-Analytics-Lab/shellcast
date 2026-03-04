-- Create database
CREATE DATABASE shellcast_nc;

USE shellcast_nc;

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
	updated datetime DEFAULT NOW() ON UPDATE NOW()
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
	notification_text text NOT NULL,
	notification_type varchar(10) NOT NULL,
	send_success boolean DEFAULT true,
	response_text text NULL,
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


-- Stores text notification and email notification events.
CREATE TABLE notification_events (
    id int AUTO_INCREMENT PRIMARY KEY,
    state varchar(2) NOT NULL,
    user_id int NOT NULL,
    notification_type VARCHAR(10) NOT NULL,       -- 'email' or 'text'

    -- Recipient info (one will be NULL depending on type)
    email_address VARCHAR(100) NULL,              -- For email notifications
    phone_number VARCHAR(15) NULL,                -- For SMS notifications

     -- Message content
    text_content_template TEXT (200) NULL, -- for "sms_clousre_aleart"
    email_content TEXT(1000) NULL,

    -- Status tracking
    send_success BOOLEAN DEFAULT TRUE,

    -- SMS and Email
    message_id VARCHAR(100) NULL,
    message_direction VARCHAR(10) NULL, -- "inbound" or "outbound"
    delivery_status VARCHAR(20) NULL, -- "RECEIVED", "QUEUED", "SENDING", "SENT", "FAILED", "DELIVERED", "ACCEPTED", "UNDELIVERABLE", "FAILED", "UNKNOWN"
    delivery_time DATETIME NULL, -- "messages.receiveTime - 2020-04-07T14:03:07.000Z"
    error_code VARCHAR(20) NULL, -- "messages.errorCode"


    created DATETIME DEFAULT NOW(),
    -- Indexes
    INDEX idx_state_user (state, user_id),
    INDEX idx_phone (phone_number),
    INDEX idx_email (email_address),
    INDEX idx_bandwidth_msg (message_id)
);


DELIMITER //
CREATE PROCEDURE SelectCmuProbsToday()
BEGIN
    SELECT * FROM cmu_probabilities WHERE DATE(`created`) = CURDATE();
END //

DELIMITER //
CREATE PROCEDURE DeleteUserByEmail(IN p_email VARCHAR(50))
BEGIN
    START TRANSACTION;
    SET SQL_SAFE_UPDATES = 0;

    -- Remove any user_leases rows referencing users with the given email
    DELETE ul FROM user_leases ul
    JOIN users u ON u.id = ul.user_id
    WHERE u.email = p_email;

    -- Remove any notification_log rows referencing users with the given email
    DELETE nl FROM notification_log nl
    JOIN users u2 ON u2.id = nl.user_id
    WHERE u2.email = p_email;

    -- Finally remove the user rows
    DELETE FROM users WHERE email = p_email;

    SET SQL_SAFE_UPDATES = 1;
    COMMIT;
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
        u.email_pref,
        u.email_consent,
        u.text_pref,
        u.text_consent,
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
