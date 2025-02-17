CREATE TABLE IF NOT EXISTS `ledger`.`fact` (
  `id` BIGINT AUTO_INCREMENT,
  `origin_id` BIGINT,
  `when` BIGINT,
  `meta` JSON NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE `origin_id_when` (`origin_id`,`when`)
);

CREATE TABLE IF NOT EXISTS `ledger`.`origin` (
  `id` BIGINT AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `description` VARCHAR(255),
  `meta` JSON NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE `name` (`name`)
);
