-- Dumping data for table `user`
LOCK TABLES `user` WRITE;
INSERT INTO `user`
(`id`, `username`, `password`, `email`, `role`, `activation_code`, `rememberme`, `reset`, `registered`, `last_seen`, `tfa_code`, `ip`)
VALUES
(1, 'admin', 'admin', 'microgrid@nps.edu', 'Admin', 'activated', '', '', '2023-02-22 19:30:00', '2023-02-22 19:30:00', '', ''),
(2, 'guest', 'guest', 'microgrid@nps.edu', 'Guest', 'activated', '', '', '2023-02-22 19:30:00', '2023-02-22 19:30:00', '', '');
UNLOCK TABLES;


-- Dumping data for table `settings`
LOCK TABLES `settings` WRITE;
INSERT INTO `settings` 
(`id`, `setting_key`, `setting_value`, `category`)
VALUES
(1, 'account_activation', 'manual_approval', 'General'),
(2, 'csrf_protection', 'false', 'Add-ons'),
(3, 'brute_force_protection', 'false', 'Add-ons'),
(4, 'twofactor_protection', 'true', 'Add-ons'),
(5, 'auto_login_after_register', 'false', 'Registration'),
(6, 'recaptcha', 'false', 'reCAPTCHA'),
(7, 'recaptcha_site_key', '', 'reCAPTCHA'),
(8, 'recaptcha_secret_key', '', 'reCAPTCHA');
UNLOCK TABLES;
