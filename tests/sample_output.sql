


INSERT INTO `users` VALUES (1,'alice');
INSERT INTO `users` VALUES (2,'ENGINE=InnoDB is inside data, must NOT be stripped');

CREATE TABLE `users` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(64) NOT NULL,
  PRIMARY KEY (`id`)
);
CREATE PROCEDURE hello()
BEGIN
  SELECT 1;
END;
