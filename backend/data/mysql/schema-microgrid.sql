DROP TABLE IF EXISTS `sizing_user` ;
DROP TABLE IF EXISTS `sizing_grid_component_spec_data` ;
DROP TABLE IF EXISTS `sizing_grid_component` ;
DROP TABLE IF EXISTS `sizing_grid` ;
DROP TABLE IF EXISTS `sizing` ;
DROP TABLE IF EXISTS `powerload_data` ;
DROP TABLE IF EXISTS `powerload_user` ;
DROP TABLE IF EXISTS `powerload` ;
DROP TABLE IF EXISTS `grid_user` ;
DROP TABLE IF EXISTS `grid_component` ;
DROP TABLE IF EXISTS `grid` ;
DROP TABLE IF EXISTS `component_user` ;
DROP TABLE IF EXISTS `component_spec_data` ;
DROP TABLE IF EXISTS `component_spec_meta` ;
DROP TABLE IF EXISTS `component` ;
DROP TABLE IF EXISTS `component_type` ;
DROP TABLE IF EXISTS `energy_management_system` ;
DROP TABLE IF EXISTS `permission` ;

-- Table `permission`
CREATE TABLE IF NOT EXISTS `permission` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` enum('read','write') NOT NULL DEFAULT 'read',
  PRIMARY KEY (`id`)
);

-- Table `energy_management_system`
CREATE TABLE IF NOT EXISTS `energy_management_system` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(64) NOT NULL,
  `parameterName` VARCHAR(64) NOT NULL,
  `description` VARCHAR(512) NULL DEFAULT NULL,
  `displayOrder` TINYINT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE (`parameterName`)
);

-- Table `component_type`
CREATE TABLE IF NOT EXISTS `component_type` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(32) NOT NULL,
  `parameterName` VARCHAR(64) NOT NULL,
  `description` VARCHAR(128) NULL DEFAULT NULL,
  `displayOrder` TINYINT NOT NULL,
  `graphLineColor` VARCHAR(16) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE (`parameterName`)
);

-- Table `component_spec_meta`
CREATE TABLE IF NOT EXISTS `component_spec_meta` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `componentTypeId` INT NOT NULL,
  `name` VARCHAR(64) NOT NULL,
  `parameterName` VARCHAR(64) NOT NULL,
  `parameterType` VARCHAR(16) NOT NULL,  
  `value` FLOAT NULL DEFAULT '0',
  `minVal` FLOAT NULL DEFAULT NULL,
  `maxVal` FLOAT NULL DEFAULT NULL,
  `visibility` TINYINT NOT NULL DEFAULT '1',
  `displayOrder` TINYINT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE (`parameterName`),
  INDEX `fk_component_componenttype_idx` (`componentTypeId` ASC),
  CONSTRAINT `check_type` CHECK (`parameterType` IN ('boolean', 'proportion', 'float', 'integer')),
  CONSTRAINT `fk_component_componenttype_2`
    FOREIGN KEY (`componentTypeId`)
    REFERENCES `component_type` (`id`)
);

-- Table `component`
CREATE TABLE IF NOT EXISTS `component` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(64) NOT NULL,
  `componentTypeId` INT NOT NULL,
  `description` VARCHAR(128) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_component_componenttype_idx` (`componentTypeId` ASC),
  CONSTRAINT `fk_component_componenttype_1`
    FOREIGN KEY (`componentTypeId`)
    REFERENCES `component_type` (`id`)
);


-- Table `component_spec_data`
CREATE TABLE IF NOT EXISTS `component_spec_data` (
  `componentId` INT NOT NULL,
  `componentSpecMetaId` INT NOT NULL,
  `value` FLOAT NOT NULL,
  PRIMARY KEY (`componentId`,`componentSpecMetaId`),  
  INDEX `fk_specification_component_idx` (`componentId` ASC),  
  INDEX `fk_specification_data_specification_idx` (`componentSpecMetaId` ASC),
  CONSTRAINT `fk_specification_component`
    FOREIGN KEY (`componentId`)
    REFERENCES `component` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_specification_data_specification`
    FOREIGN KEY (`componentSpecMetaId`)
    REFERENCES `component_spec_meta` (`id`)
);


-- Table `component_user`
CREATE TABLE IF NOT EXISTS `component_user` (
  `userId` INT NOT NULL,
  `componentId` INT NOT NULL,
  `permissionId` INT NOT NULL,
  PRIMARY KEY (`userId`, `componentId`),
  INDEX `fk_usercomponent_component_idx` (`componentId` ASC),
  INDEX `fk_component_user_permission_idx` (`permissionId` ASC),
  CONSTRAINT `fk_component_user_permission`
    FOREIGN KEY (`permissionId`)
    REFERENCES `permission` (`id`),
  CONSTRAINT `fk_usercomponent_component`
    FOREIGN KEY (`componentId`)
    REFERENCES `component` (`id`)
    ON DELETE CASCADE
);


-- Table `grid`
CREATE TABLE IF NOT EXISTS `grid` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(64) NOT NULL,
  `description` VARCHAR(128) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  `isSizingTemplate` BOOLEAN NOT NULL DEFAULT 0
);


-- Table `grid_component`
CREATE TABLE IF NOT EXISTS `grid_component` (
  `gridId` INT NOT NULL,
  `componentId` INT NOT NULL,
  `quantity` INT NOT NULL DEFAULT 1,
  PRIMARY KEY (`gridId`, `componentId`),
  INDEX `fk_gridcomponenet_component_idx` (`componentId` ASC),
  CONSTRAINT `fk_gridcomponent_component`
    FOREIGN KEY (`componentId`)
    REFERENCES `component` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_gridcomponent_grid`
    FOREIGN KEY (`gridId`)
    REFERENCES `grid` (`id`)
    ON DELETE CASCADE
);


-- Table `grid_user`
CREATE TABLE IF NOT EXISTS `grid_user` (
  `gridId` INT NOT NULL,
  `userId` INT NOT NULL,
  `permissionId` INT NOT NULL,
  PRIMARY KEY (`gridId`, `userId`),
  INDEX `fk_griduser_user_idx` (`userId` ASC),
  INDEX `fk_grid_user_permission_idx` (`permissionId` ASC),
  CONSTRAINT `fk_grid_user_permission`
    FOREIGN KEY (`permissionId`)
    REFERENCES `permission` (`id`),
  CONSTRAINT `fk_griduser_grid`
    FOREIGN KEY (`gridId`)
    REFERENCES `grid` (`id`)
    ON DELETE CASCADE
);


-- Table `powerload`
CREATE TABLE `powerload` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(32) NOT NULL,
  `description` varchar(128) DEFAULT NULL,
  `startdatetime` DATETIME NOT NULL,
  `enddatetime` DATETIME NOT NULL,
  `image` MEDIUMBLOB DEFAULT NULL,
  PRIMARY KEY (`id`)
);


-- Table `powerload_user`
CREATE TABLE `powerload_user` (
  `powerloadId` int NOT NULL,
  `userId` int NOT NULL,
  `permissionId` INT NOT NULL,
  PRIMARY KEY (`powerloadId`,`userId`),
  INDEX `fk_powerload_user_user_idx` (`userId` ASC),
  INDEX `fk_powerload_user_permission_idx` (`permissionId` ASC),
  CONSTRAINT `fk_powerload_user_powerload`
    FOREIGN KEY (`powerloadId`)
    REFERENCES `powerload` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_powerload_user_permission` 
    FOREIGN KEY (`permissionId`) 
    REFERENCES `permission` (`id`)
);


-- Table `powerload_data`
CREATE TABLE `powerload_data` (
  `powerloadId` int NOT NULL,
  `time` double NOT NULL,
  `value` float NOT NULL,
  INDEX `fk_powerload_data_powerloadId_idx` (`powerloadId` ASC),
  UNIQUE KEY `uc_powerloadId_time` (`powerloadId`,`time`),
  CONSTRAINT `fk_powerload_powerload_data` 
    FOREIGN KEY (`powerloadId`)
    REFERENCES `powerload` (`id`)
    ON DELETE CASCADE
);

-- Table `simulate`
CREATE TABLE IF NOT EXISTS `simulate` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `gridId` INT NOT NULL,
  `energyManagementSystemId` INT NOT NULL,
  `powerloadId` INT NOT NULL,
  `locationId` INT NOT NULL,
  `startdatetime` DATETIME NOT NULL,
  `enddatetime` DATETIME NOT NULL,
  `metrics` MEDIUMBLOB DEFAULT NULL,
  `computeJobId` VARCHAR(16) DEFAULT NULL,
  `runsubmitdatetime` DATETIME DEFAULT NULL,
  `runstartdatetime` DATETIME DEFAULT NULL,
  `runenddatetime` DATETIME DEFAULT NULL,
  `success` BOOLEAN DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `simulate_unique` (`gridId`,`energyManagementSystemId`,`powerloadId`,`locationId`,`startdatetime`,`enddatetime`),
  CONSTRAINT `fk_simulate` 
    FOREIGN KEY (`gridId`)
    REFERENCES `grid` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_simulate_energy_management_system` 
    FOREIGN KEY (`energyManagementSystemId`)
    REFERENCES `energy_management_system` (`id`),
  CONSTRAINT `fk_simulate_powerload`
    FOREIGN KEY (`powerloadId`)
    REFERENCES `powerload` (`id`)
    ON DELETE CASCADE
);

-- Table `simulate_user`
CREATE TABLE IF NOT EXISTS `simulate_user` (
  `simulateId` INT NOT NULL,
  `userId` INT NOT NULL,
  `permissionId` INT NOT NULL,
  PRIMARY KEY (`simulateId`, `userId`),
  INDEX `fk_simulate_user_idx` (`userId` ASC),
  INDEX `fk_simulate_user_permission_idx` (`permissionId` ASC),
  CONSTRAINT `fk_simulate_user_permission`
    FOREIGN KEY (`permissionId`)
    REFERENCES `permission` (`id`),
  CONSTRAINT `fk_simulate_user_id`
    FOREIGN KEY (`simulateId`)
    REFERENCES `simulate` (`id`)
    ON DELETE CASCADE
);

-- Table `sizing`
CREATE TABLE IF NOT EXISTS `sizing` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `gridId` INT NOT NULL,
  `energyManagementSystemId` INT NOT NULL,
  `powerloadId` INT NOT NULL,
  `locationId` INT NOT NULL,
  `startdatetime` DATETIME NOT NULL,
  `enddatetime` DATETIME NOT NULL,
  `computeJobId` VARCHAR(16) DEFAULT NULL,
  `runsubmitdatetime` DATETIME DEFAULT NULL,
  `runstartdatetime` DATETIME DEFAULT NULL,
  `runenddatetime` DATETIME DEFAULT NULL,
  `success` BOOLEAN DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `sizing_unique` (`gridId`,`energyManagementSystemId`,`powerloadId`,`locationId`,`startdatetime`,`enddatetime`),
  CONSTRAINT `fk_sizing_grid` 
    FOREIGN KEY (`gridId`)
    REFERENCES `grid` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_sizing_energy_management_system` 
    FOREIGN KEY (`energyManagementSystemId`)
    REFERENCES `energy_management_system` (`id`),
  CONSTRAINT `fk_sizing_powerload`
    FOREIGN KEY (`powerloadId`)
    REFERENCES `powerload` (`id`)
    ON DELETE CASCADE
);

-- Table `sizing_grid`
CREATE TABLE IF NOT EXISTS `sizing_grid` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(256) NOT NULL,
  `sizingId` INT NOT NULL,
  `deficitPercentage` FLOAT NOT NULL,
  `excessPercentage` FLOAT NOT NULL, 
  `dominatedBy` VARCHAR(256) NULL,
  `parent` VARCHAR(256) NOT NULL,
  `metricsSummaryStats` VARCHAR(512) NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_sizing_id`
    FOREIGN KEY (`sizingId`)
    REFERENCES `sizing` (`id`)
    ON DELETE CASCADE
);

-- Table `sizing_grid_component`
CREATE TABLE IF NOT EXISTS `sizing_grid_component` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `sizingGridId` INT NOT NULL,
  `componentTypeId` INT NOT NULL,
  `unusedPercentage` FLOAT NOT NULL,
  `timeStepsPercentage` FLOAT NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_sizing_grid_id`
    FOREIGN KEY (`sizingGridId`)
    REFERENCES `sizing_grid` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_sizing_grid_componentType` 
    FOREIGN KEY (`componentTypeId`)
    REFERENCES `component_type` (`id`)
);

-- Table `sizing_grid_component_spec_data`
CREATE TABLE IF NOT EXISTS `sizing_grid_component_spec_data` (
  `sizingGridComponentId` INT NOT NULL,
  `componentSpecMetaId` INT NOT NULL,
  `value` FLOAT NOT NULL, 
  PRIMARY KEY (`sizingGridComponentId`,`componentSpecMetaId`),
  CONSTRAINT `fk_sizing_grid_component_id` 
    FOREIGN KEY (`sizingGridComponentId`)
    REFERENCES `sizing_grid_component` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_sizing_grid_component_spec_meta_id`
    FOREIGN KEY (`componentSpecMetaId`)
    REFERENCES `component_spec_meta` (`id`)
);

-- Table `sizing_user`
CREATE TABLE IF NOT EXISTS `sizing_user` (
  `sizingId` INT NOT NULL,
  `userId` INT NOT NULL,
  `permissionId` INT NOT NULL,
  PRIMARY KEY (`sizingId`, `userId`),
  INDEX `fk_sizing_user_idx` (`userId` ASC),
  INDEX `fk_sizing_user_permission_idx` (`permissionId` ASC),
  CONSTRAINT `fk_sizing_user_permission`
    FOREIGN KEY (`permissionId`)
    REFERENCES `permission` (`id`),
  CONSTRAINT `fk_sizing_user_id`
    FOREIGN KEY (`sizingId`)
    REFERENCES `sizing` (`id`)
    ON DELETE CASCADE
);
