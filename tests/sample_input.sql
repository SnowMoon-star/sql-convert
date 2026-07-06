/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8mb4 */;
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS;
SET @@SESSION.SQL_MODE='';

LOCK TABLES `users` WRITE;
INSERT INTO `users` VALUES (1,'alice');
INSERT INTO `users` VALUES (2,'ENGINE=InnoDB is inside data, must NOT be stripped');
UNLOCK TABLES;

-- Navicat 风格导出: profiles 依赖 users
DROP TABLE IF EXISTS `profiles`;
CREATE TABLE `profiles` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `active` bit(1) NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  CONSTRAINT `fk_profiles_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `profiles` VALUES (1, 1, b'1');

-- DataGrip 风格导出: users（无外键，被 profiles 引用）
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=100 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin ROW_FORMAT=DYNAMIC;

INSERT INTO `users` VALUES (1,'alice');
INSERT INTO `users` VALUES (2,'ENGINE=InnoDB is inside data, must NOT be stripped');

-- 独立 ALTER TABLE 添加索引
ALTER TABLE `users` ADD UNIQUE KEY `idx_name` (`name`);

-- 手写 SQL 风格: settings 表（无 DROP TABLE，无 INSERT 数据，无外键）
CREATE TABLE IF NOT EXISTS `settings` (
  `key` VARCHAR(128) NOT NULL,
  `value` TEXT NULL COMMENT '配置值',
  PRIMARY KEY (`key`)
);

DELIMITER $$
CREATE PROCEDURE hello()
BEGIN
  SELECT 1;
END$$
DELIMITER ;

SET FOREIGN_KEY_CHECKS = 1;
