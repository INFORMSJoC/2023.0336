-- Dumping data for table `permission`
LOCK TABLES `permission` WRITE;
INSERT INTO `permission`
(`id`, `name`) 
VALUES
(1,'read'),
(2,'write');
UNLOCK TABLES;


-- Dumping data for table `user`
LOCK TABLES `user` WRITE;
INSERT INTO `user`
(`id`, `username`, `password`, `email`, `role`, `activation_code`, `rememberme`, `reset`, `registered`, `last_seen`, `tfa_code`, `ip`)
VALUES
(1, 'admin', 'admin', 'microgrid@nps.edu', 'Admin', 'activated', '', '', '2023-02-22 19:30:00', '2023-02-22 19:30:00', '', ''),
(2, 'guest', 'guest', 'microgrid@nps.edu', 'Guest', 'activated', '', '', '2023-02-22 19:30:00', '2023-02-22 19:30:00', '', '');
UNLOCK TABLES;


-- Dumping data for table `user_settings`
LOCK TABLES `user_settings` WRITE;
INSERT INTO `user_settings` 
(`id`, `setting_key`, `setting_value`, `category`)
VALUES
(1, 'account_activation', 'not_required', 'General'),
(2, 'csrf_protection', 'true', 'Add-ons'),
(3, 'brute_force_protection', 'true', 'Add-ons'),
(4, 'twofactor_protection', 'false', 'Add-ons'),
(5, 'auto_login_after_register', 'false', 'Registration'),
(6, 'recaptcha', 'false', 'reCAPTCHA'),
(7, 'recaptcha_site_key', '', 'reCAPTCHA'),
(8, 'recaptcha_secret_key', '', 'reCAPTCHA');
UNLOCK TABLES;


-- Dumping data for table `component_type`
LOCK TABLES `component_type` WRITE;
INSERT INTO `component_type`
(`id`, `name`, `parameterName`, `description`, `displayOrder`, `graphLineColor`) 
VALUES
(1,'Photovoltaic','SolarPhotovoltaicPanel','Solar Photovoltaic Panel',3,'green'),
(2,'Wind Turbine','WindTurbine','Wind Turbine',4,'magenta'),
(3,'Diesel Generator','DieselGenerator','Diesel Generator',2,'blue'),
(4,'BESS','Battery','Battery Energy Storage System',1,'purple');
UNLOCK TABLES;


-- Dumping data for table `component_spec_meta`
LOCK TABLES `component_spec_meta` WRITE;
INSERT INTO `component_spec_meta`
(`id`, `componentTypeId`, `name`, `parameterName`, `value`, `minVal`, `maxVal`, `visibility`, `displayOrder`) 
VALUES 
(1,1,'Photovoltaic Power (kW)','pv_power',NULL,0.01,NULL,1,1),
(2,1,'Photovoltaic Economic Lifespan (years)','pv_economic_lifespan',NULL,0.01,NULL,1,2),
(3,1,'Photovoltaic Investment Cost ($)','pv_investment_cost',NULL,0.01,NULL,1,3),
(4,1,'Photovoltaic OM Annual Cost ($)','pv_om_cost',NULL,0.01,NULL,1,4),
(5,2,'Wind Turbine Availability (percentage)','wt_availability',0.98,0.01,1,0,3),
(6,2,'Wind Turbine Capacity (percentage)','wt_capacity',0.22,0.01,1,1,2),
(7,2,'Wind Turbine Power (kW)','wt_power',NULL,0.01,NULL,1,1),
(8,2,'Wind Turbine Economic Lifespan (years)','wt_economic_lifespan',NULL,0.01,NULL,1,4),
(9,2,'Wind Turbine Investment Cost ($)','wt_investment_cost',NULL,0.01,NULL,1,5),
(10,2,'Wind Turbine OM Annual Cost ($)','wt_om_cost',NULL,0,NULL,1,6),
(11,3,'Diesel Generator Load (percentage)','dg_load',1,0.01,1,1,2),
(12,3,'Diesel Generator Min Load (percentage)','dg_min_load',0.6,0,1,0,3),
(13,3,'Diesel Generator Peak Consumption Rate (gallons / hour)','dg_peak_cons_rate',NULL,0.01,NULL,1,4),
(14,3,'Diesel Generator Power (kW)','dg_power',NULL,0.01,NULL,1,1),
(15,3,'Diesel Generator Startup Delay (hours)','dg_startup_delay',0,0,NULL,0,5),
(16,3,'Diesel Generator Economic Lifespan (years)','dg_economic_lifespan',NULL,0.01,NULL,1,6),
(17,3,'Diesel Generator Investment Cost ($)','dg_investment_cost',NULL,0.01,NULL,1,7),
(18,3,'Diesel Generator OM Annual Cost ($)','dg_om_cost',NULL,0.01,NULL,1,8),
(19,4,'BESS Charge Efficiency (percentage)','b_charge_eff',0.95,0.01,1,1,5),
(20,4,'BESS Charge Power (kW)','b_charge_power',NULL,0.01,NULL,1,4),
(21,4,'BESS Discharge Efficiency (percentage)','b_discharge_eff',0.95,0.01,1,1,3),
(22,4,'BESS Discharge Power (kW)','b_discharge_power',NULL,0.01,NULL,1,2),
(23,4,'BESS Energy (kWh)','b_energy',NULL,0.01,NULL,1,1),
(24,4,'BESS Max SOC (percentage)','b_max_soc',1,0.5,1,1,7),
(25,4,'BESS Min SOC (percentage)','b_min_soc',0.2,0,0.5,1,6),
(26,4,'BESS Economic Lifespan (years)','b_economic_lifespan',NULL,0.01,NULL,1,8),
(27,4,'BESS Investment Cost ($)','b_investment_cost',NULL,0.01,NULL,1,9),
(28,4,'BESS OM Annual Cost ($)','b_om_cost',NULL,0.01,NULL,1,10);
UNLOCK TABLES;
