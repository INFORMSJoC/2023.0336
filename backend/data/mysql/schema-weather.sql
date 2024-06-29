DROP TABLE IF EXISTS `weather` ;
DROP TABLE IF EXISTS `location` ;


-- Table `location`
CREATE TABLE IF NOT EXISTS `location` (
  `id` INT NOT NULL,
  `name` VARCHAR(64) NOT NULL,
  `region` VARCHAR(64) NOT NULL,
  `country` VARCHAR(64) NOT NULL,
  `latitude` FLOAT NOT NULL,
  `longitude` FLOAT NOT NULL,
  `elevation` FLOAT NOT NULL,
  `timezone` FLOAT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY (`name`,`region`,`country`),
  UNIQUE KEY (`latitude`,`longitude`)
);

-- Table `weather`
CREATE TABLE IF NOT EXISTS `weather` (
  `locationId` INT NOT NULL,
  `yearOrStat` VARCHAR(8) NOT NULL,
  `month` TINYINT NOT NULL,
  `day` TINYINT NOT NULL,
  `hour` TINYINT NOT NULL,
  `minute` TINYINT NOT NULL,
  `temperature` FLOAT NOT NULL,
  `ghi` FLOAT NOT NULL,
  `dhi` FLOAT NOT NULL,
  `dni` FLOAT NOT NULL,
  `solarZenithAngle` FLOAT NOT NULL,
  `surfaceAlbedo` FLOAT NOT NULL,  
  `pressure` FLOAT NOT NULL,
  `windSpeed` FLOAT NOT NULL,
  PRIMARY KEY (`locationId`,`yearOrStat`,`month`,`day`,`hour`,`minute`),
  CONSTRAINT `fk_weather_location`
    FOREIGN KEY (`locationId`)
    REFERENCES `location` (`id`)
);
