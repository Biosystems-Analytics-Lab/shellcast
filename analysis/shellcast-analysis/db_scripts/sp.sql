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
CREATE PROCEDURE DeleteUserAccount()
BEGIN
	SET SQL_SAFE_UPDATES = 0;
	DELETE FROM user_leases WHERE user_id IN (SELECT id FROM users WHERE deleted=1);
	DELETE FROM notification_log WHERE user_id IN (SELECT id FROM users WHERE deleted=1);
	DELETE FROM users WHERE deleted=1;
	SET SQL_SAFE_UPDATES = 1;
END //

DELIMITER //
CREATE PROCEDURE DeleteUserLeases()
BEGIN
	SET SQL_SAFE_UPDATES = 0;
	DELETE FROM user_leases WHERE deleted=1;
	SET SQL_SAFE_UPDATES = 1;
END //
