-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Aug 03, 2025 at 08:01 PM
-- Server version: 10.4.24-MariaDB
-- PHP Version: 8.1.6

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `william`
--

-- --------------------------------------------------------

--
-- Table structure for table `patient`
--

CREATE TABLE `patient` (
  `id` int(11) NOT NULL,
  `name` text DEFAULT NULL,
  `details` text DEFAULT NULL,
  `casetype` text DEFAULT NULL,
  `description` text DEFAULT NULL,
  `lastsession` text DEFAULT NULL,
  `nextsession` text DEFAULT NULL,
  `totalfees` float DEFAULT NULL,
  `paidfees` float DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `patient`
--

INSERT INTO `patient` (`id`, `name`, `details`, `casetype`, `description`, `lastsession`, `nextsession`, `totalfees`, `paidfees`) VALUES
(20, 'Samir', 'address: honik\r\nPhone: 123', 'shoulder dislocation', '-assesment: bla bla\r\n-medical history: ma ba3ref\r\n-whatever: whatever', '2025-08-03T11:30', '2025-09-04T15:40, 2025-09-06T11:20, 2025-09-10T15:00', 60, 40),
(21, 'boumale', 'fefegrg', 'ewgfsnof', 'klsnflknwesf', '2025-07-03T11:30', '2025-08-13', 20, 20),
(22, 'karam', 'sddsgvgws', 'lknsdgvnkl', 'lknsdlvknsnlv', '2025-08-03T11:30', '2025-09-04T15:40', 90, 60),
(23, 'toni', 'vdmvvm', ' .,sdv.s dd', 'wfwefwf', '2025-07-03T11:30', '2025-09-04T15:40, 2025-09-06T11:20, 2025-09-10T15:00', 70, 67),
(24, 'abdo', 'kn,mn,knkl.', 'khl', 'hhbkjbjk,bkjb\r\n-assesment:njkjkj\r\n-medical history: kjiu', '2025-08-03T11:30', '2025-09-03T15:00,2025-09-05T12:00', 50, 40);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `patient`
--
ALTER TABLE `patient`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `patient`
--
ALTER TABLE `patient`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=26;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
