-- Dumping data for table `permission`
LOCK TABLES `permission` WRITE;
INSERT INTO `permission`
(`id`, `name`) 
VALUES
(1,'read'),
(2,'write');
UNLOCK TABLES;


-- Dumping data for table `energy_management_system`
LOCK TABLES `energy_management_system` WRITE;
INSERT INTO `energy_management_system`
(`id`, `name`, `parameterName`, `description`, `displayOrder`) 
VALUES
(1,'Favor battery energy storage system usage','_energy_management_system_2','Use battery energy storage system when renewables cannot meet power load demands. Continue to use diesel if battery is in the process of charging and diesel is on. Avoid diesel generator on/off switches. Avoid wet stacking when battery energy storage system is fully charged.',1),
(2,'Favor diesel','_energy_management_system_3','Use diesel when renewables cannot meet power load demands or when battery energy storage system is not fully charged. Avoid diesel generator on/off switches. Avoid wet stacking when battery energy storage system is fully charged.',2),
(3,'Maintain max state of charge','_energy_management_system_4','Use diesel when renewables cannot meet power load demands or when battery energy storage system is not fully charged. Discharge the battery energy storage system only when renewables and diesel combined cannot meet power load demand. Allow wet stacking.',3);
UNLOCK TABLES;


-- Dumping data for table `component_type`
LOCK TABLES `component_type` WRITE;
INSERT INTO `component_type`
(`id`, `name`, `parameterName`, `description`, `displayOrder`, `graphLineColor`) 
VALUES
(1,'Photovoltaic','SolarPhotovoltaicPanel','Solar Photovoltaic Panel',3,'#008000'),
(2,'Wind Turbine','WindTurbine','Wind Turbine',4,'#F893FA'),
(3,'Diesel Generator','DieselGenerator','Diesel Generator',2,'#0000FF'),
(4,'BESS','Battery','Battery Energy Storage System',1,'#A94176');
UNLOCK TABLES;


-- Dumping data for table `component_spec_meta`
LOCK TABLES `component_spec_meta` WRITE;
INSERT INTO `component_spec_meta`
(`id`, `componentTypeId`, `name`, `parameterName`, `parameterType`, `value`, `minVal`, `maxVal`, `visibility`, `displayOrder`) 
VALUES 
(1,1,'Photovoltaic Power (kW)','pv_power','float',NULL,0.01,NULL,1,1),
(29,1,'Photovoltaic Temperature Coefficient (proportion/&degC)','pv_temperature_coefficient','proportion',-0.0033,-0.01,0.0,1,3),
(30,1,'Photovoltaic Is Sun Tracking?','is_sun_tracking','boolean',NULL,NULL,NULL,1,2),
(2,1,'Photovoltaic Economic Lifespan (years)','pv_economic_lifespan','integer',NULL,1,NULL,1,4),
(3,1,'Photovoltaic Investment Cost ($)','pv_investment_cost','float',NULL,0.01,NULL,1,5),
(4,1,'Photovoltaic OM Annual Cost ($)','pv_om_cost','float',NULL,0.01,NULL,1,6),
(5,2,'Wind Turbine Cut-in Speed (m/s)','wt_cutin_speed','float',3.0,0.0,NULL,1,3),
(6,2,'Wind Turbine Cut-out Speed (m/s)','wt_cutout_speed','float',25.0,0.0,NULL,1,4),
(31,2,'Wind Turbine Rated Speed (m/s)','wt_rated_speed','float',10.0,0.0,NULL,1,5),
(32,2,'Wind Turbine Peak Power (kW)','wt_peak_power','float',NULL,0.01,NULL,1,2),
(33,2,'Wind Turbine Height (m)','wt_height','float',NULL,1.0,500.0,1,6),
(7,2,'Wind Turbine Rated Power (kW)','wt_power','float',NULL,0.01,NULL,1,1),
(8,2,'Wind Turbine Economic Lifespan (years)','wt_economic_lifespan','integer',NULL,1,NULL,1,7),
(9,2,'Wind Turbine Investment Cost ($)','wt_investment_cost','float',NULL,0.01,NULL,1,8),
(10,2,'Wind Turbine OM Annual Cost ($)','wt_om_cost','float',NULL,0,NULL,1,9),
(11,3,'Diesel Generator Load (proportion)','dg_load','proportion',1,0.01,1,1,2),
(12,3,'Diesel Generator Min Load (proportion)','dg_min_load','proportion',0.6,0,1,0,3),
(13,3,'Diesel Generator EPG efficiency (proportion)','dg_epg_efficiency','proportion',0.40,0.01,1.0,1,4),
(14,3,'Diesel Generator Power (kW)','dg_power','float',NULL,0.01,NULL,1,1),
(15,3,'Diesel Generator Startup Delay (hours)','dg_startup_delay','float',0,0,NULL,0,5),
(16,3,'Diesel Generator Economic Lifespan (years)','dg_economic_lifespan','integer',NULL,1,NULL,1,6),
(17,3,'Diesel Generator Investment Cost ($)','dg_investment_cost','float',NULL,0.01,NULL,1,7),
(18,3,'Diesel Generator OM Annual Cost ($)','dg_om_cost','float',NULL,0.01,NULL,1,8),
(19,4,'BESS Charge Efficiency (proportion)','b_charge_eff','proportion',0.95,0.01,1,1,5),
(20,4,'BESS Charge Power (kW)','b_charge_power','float',NULL,0.01,NULL,1,4),
(21,4,'BESS Discharge Efficiency (proportion)','b_discharge_eff','proportion',0.95,0.01,1,1,3),
(22,4,'BESS Discharge Power (kW)','b_discharge_power','float',NULL,0.01,NULL,1,2),
(23,4,'BESS Energy (kWh)','b_energy','float',NULL,0.01,NULL,1,1),
(24,4,'BESS Max SOC (proportion)','b_max_soc','proportion',1,0.5,1,1,7),
(25,4,'BESS Min SOC (proportion)','b_min_soc','proportion',0.2,0,0.5,1,6),
(26,4,'BESS Economic Lifespan (years)','b_economic_lifespan','integer',NULL,1,NULL,1,8),
(27,4,'BESS Investment Cost ($)','b_investment_cost','float',NULL,0.01,NULL,1,9),
(28,4,'BESS OM Annual Cost ($)','b_om_cost','float',NULL,0.01,NULL,1,10);
UNLOCK TABLES;
