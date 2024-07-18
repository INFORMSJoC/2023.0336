-- Dumping data for table `user`
LOCK TABLES `user` WRITE;
INSERT INTO `user`
(`id`, `username`, `password`, `email`, `role`, `activation_code`, `rememberme`, `reset`, `registered`, `last_seen`, `tfa_code`, `ip`)
VALUES
(3, 'user1', 'usera', 'microgrid@nps.edu', 'Member', 'activated', '', '', '2023-02-22 19:30:00', '2023-02-22 19:30:00', '', ''),
(4, 'user2', 'userb', 'microgrid@nps.edu', 'Member', 'activated', '', '', '2023-02-22 19:30:00', '2023-02-22 19:30:00', '', ''),
(5, 'user3', 'userc', 'microgrid@nps.edu', 'Guest', 'activated', '', '', '2023-02-22 19:30:00', '2023-02-22 19:30:00', '', '');
UNLOCK TABLES;
