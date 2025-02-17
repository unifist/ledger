CREATE TABLE IF NOT EXISTS `ledger`.`fact` (
  `id` BIGINT AUTO_INCREMENT,
  `origin_id` BIGINT,
  `who` VARCHAR(255) NOT NULL,
  `when` BIGINT,
  `what` JSON NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `when` (`when`),
  UNIQUE `origin_id_who` (`origin_id`,`who`)
);

CREATE TABLE IF NOT EXISTS `ledger`.`origin` (
  `id` BIGINT AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `description` VARCHAR(255),
  `meta` JSON NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE `name` (`name`)
);
