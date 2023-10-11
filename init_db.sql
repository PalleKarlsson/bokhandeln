CREATE DATABASE IF NOT EXISTS `bokhandeln`;
CREATE TABLE IF NOT EXISTS `inventory` (
  `ISBN` varchar(255) NOT NULL,
  `title` varchar(255) NOT NULL,
  `author` varchar(255) NOT NULL,
  `lang` varchar(255) DEFAULT NULL,
  `year` int(4) DEFAULT NULL,
  `amount` int(11) DEFAULT NULL,
  `sell_price` int(11) DEFAULT NULL,
  `buy_price` int(11) DEFAULT NULL,
  `cover` varchar(255) DEFAULT NULL,
  `row` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`ISBN`)
);
CREATE TABLE IF NOT EXISTS `sales` (
    `date` datetime,
    `ISBN` varchar(255),
    `price` int(11),
    `seller` varchar(255)
);
