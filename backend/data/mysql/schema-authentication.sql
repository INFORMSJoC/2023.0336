DROP TABLE IF EXISTS `settings` ;
DROP TABLE IF EXISTS `login_attempts` ;
DROP TABLE IF EXISTS `user` ;

-- Table `user`
CREATE TABLE IF NOT EXISTS `user` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` varchar(32) NOT NULL,
  `password` varchar(255) NOT NULL,
  `email` varchar(64) NOT NULL,
  `role` enum('Member','Admin','Guest') NOT NULL DEFAULT 'Member',
  `activation_code` varchar(255) NOT NULL DEFAULT '',
  `rememberme` varchar(255) NOT NULL DEFAULT '',
  `reset` varchar(255) NOT NULL DEFAULT '',
  `registered` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_seen` timestamp,
  `tfa_code` varchar(255) NOT NULL DEFAULT '',
  `ip` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
);

-- Table `login_attempts`
CREATE TABLE IF NOT EXISTS `login_attempts` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `ip_address` varchar(255) NOT NULL,
  `attempts_left` tinyint(1) NOT NULL DEFAULT 5,
  `date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ip_address` (`ip_address`)
);

-- Table `settings`
CREATE TABLE IF NOT EXISTS `settings` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `setting_key` varchar(50) NOT NULL,
  `setting_value` varchar(50) NOT NULL,
  `category` varchar(50) NOT NULL,
  PRIMARY KEY (`id`)
);
