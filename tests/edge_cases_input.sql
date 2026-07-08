-- 测试文件：边界场景覆盖
-- 场景1: INSERT 数据含转义单引号（\' 不得翻转引号状态）
-- 场景2: 多个无名外键（不得生成重复约束名）
-- 场景3: 循环 FK 依赖（拓扑排序降级保持原顺序）
-- 场景4: CREATE TABLE IF NOT EXISTS 语法

-- ------------------------------------------------
-- 场景1: 含转义引号的 INSERT 数据
-- ------------------------------------------------
DROP TABLE IF EXISTS `escape_test`;
CREATE TABLE `escape_test` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `note` VARCHAR(256) NOT NULL COMMENT '备注',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `escape_test` VALUES (1, 'it\'s a test');
INSERT INTO `escape_test` VALUES (2, 'line1\r\nline2');
INSERT INTO `escape_test` VALUES (3, 'O\'Reilly\'s book');

-- ------------------------------------------------
-- 场景2: 多个无名外键
-- ------------------------------------------------
DROP TABLE IF EXISTS `ref_a`;
CREATE TABLE `ref_a` (
  `id` INT NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

DROP TABLE IF EXISTS `ref_b`;
CREATE TABLE `ref_b` (
  `id` INT NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

DROP TABLE IF EXISTS `multi_fk`;
CREATE TABLE `multi_fk` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `a_id` INT NOT NULL,
  `b_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`a_id`) REFERENCES `ref_a` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`b_id`) REFERENCES `ref_b` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ------------------------------------------------
-- 场景3: 循环 FK 依赖（A→B, B→A）
-- ------------------------------------------------
DROP TABLE IF EXISTS `cycle_a`;
CREATE TABLE `cycle_a` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `b_id` INT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_ca_cb` FOREIGN KEY (`b_id`) REFERENCES `cycle_b` (`id`)
) ENGINE=InnoDB;

DROP TABLE IF EXISTS `cycle_b`;
CREATE TABLE `cycle_b` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `a_id` INT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_cb_ca` FOREIGN KEY (`a_id`) REFERENCES `cycle_a` (`id`)
) ENGINE=InnoDB;

-- ------------------------------------------------
-- 场景4: CREATE TABLE IF NOT EXISTS（无 DROP TABLE）
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS `orphan_table` (
  `key` VARCHAR(128) NOT NULL,
  `value` TEXT NULL COMMENT '值',
  PRIMARY KEY (`key`)
);
