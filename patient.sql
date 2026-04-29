-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Feb 17, 2026 at 10:59 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `patient`
--

-- --------------------------------------------------------

--
-- Table structure for table `doctors`
--

CREATE TABLE `doctors` (
  `id` int(11) NOT NULL,
  `username` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `full_name` varchar(200) NOT NULL,
  `role` enum('admin','doctor') NOT NULL DEFAULT 'doctor'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `doctors`
--

INSERT INTO `doctors` (`id`, `username`, `password_hash`, `full_name`, `role`) VALUES
(1, 'admin', 'scrypt:32768:8:1$CKzeUBegZ4evt1Lf$d4750ea64112caaf218105cf68d7d41b19efcec32ec8d7feb496ca5f6235b0a970c948e0b28a16978dacad43bdfa7526bd2056928e61f1e0301084b29a00f36b', 'Administrator', 'admin'),
(2, 'william', 'scrypt:32768:8:1$yJlFooO6fg52ymxW$f4c228f68acce2ade13d6b435ae3af54acf3cd5dc0a7008c4ff10a68b5d93dfee13f69aa2a01f8376aac0f186964d8faa81ad81e43f3cdf7d4d607a96a55865e', 'william hanna', 'doctor'),
(3, 'elio', 'scrypt:32768:8:1$BidXcslbqMpIcb8f$66d2aee2edb2974624e3e65285939896c1c3ad9835ad661bc7eda9f979b3f78b53290cb4850de92ec82c42424b08cb38209e881804f0686f6c80e55b5ae6524a', 'elio chedid', 'doctor');

-- --------------------------------------------------------

--
-- Table structure for table `expenses`
--

CREATE TABLE `expenses` (
  `id` int(11) NOT NULL,
  `description` text NOT NULL,
  `amount` float NOT NULL,
  `expense_date` date NOT NULL,
  `doctor_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `expenses`
--

INSERT INTO `expenses` (`id`, `description`, `amount`, `expense_date`, `doctor_id`) VALUES
(1, 'gloves', 40, '2026-02-17', 1),
(2, 'batata', 13, '2026-02-17', 2);

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
  `paidfees` float DEFAULT NULL,
  `doctor_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `patient`
--

INSERT INTO `patient` (`id`, `name`, `details`, `casetype`, `description`, `lastsession`, `nextsession`, `totalfees`, `paidfees`, `doctor_id`) VALUES
(20, 'Samir', 'address: honik\r\nPhone: 123', 'shoulder dislocation', '-assesment: bla bla\r\n-medical history: ma ba3ref\r\n-whatever: whatever', '2025-08-03T11:30', '2025-09-04T15:40,2025-09-06T11:20,2025-09-10T15:00', 60, 40, 2),
(21, 'boumale', 'fefegrg', 'ewgfsnof', 'klsnflknwesf', '2025-07-03T11:30', '', 20, 20, 3),
(22, 'karam', 'sddsgvgws', 'lknsdgvnkl', 'lknsdlvknsnlv', '2025-08-03T11:30', '2025-09-04T15:40', 90, 60, NULL),
(23, 'toni', 'vdmvvm', ' .,sdv.s dd', 'wfwefwf', '2025-07-03T11:30', '2025-09-04T15:40,2025-09-06T11:20,2025-09-10T15:00', 70, 67, 3),
(24, 'abdo', 'kn,mn,knkl.', 'khl', 'hhbkjbjk,bkjb\r\n-assesment:njkjkj\r\n-medical history: kjiu', '2025-08-03T11:30', '2025-09-03T15:00,2025-09-05T12:00', 50, 40, 2),
(26, 'elio', 'sdfgh', 'hgfds', 'sssdd', '2026-01-16T08:09', '2026-02-16T08:09,2026-01-17T08:09', 300, 300, 2),
(27, 'gdfgh', 'fd', 'fdd', 'fdgd', '2026-01-16T09:03', '2026-01-19T00:00', 20, 10, 3),
(28, 'ali', 'phone: +96176412744', 'injured', 'qwscfg', '2026-02-17T11:32', '2026-02-18T11:32', 400, 50, 2);

-- --------------------------------------------------------

--
-- Table structure for table `payments`
--

CREATE TABLE `payments` (
  `id` int(11) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `amount` float NOT NULL,
  `payment_date` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `payments`
--

INSERT INTO `payments` (`id`, `patient_id`, `amount`, `payment_date`) VALUES
(1, 20, 40, '2026-02-17'),
(2, 21, 20, '2026-02-17'),
(3, 22, 60, '2026-02-17'),
(4, 23, 67, '2026-02-17'),
(5, 24, 40, '2026-02-17'),
(6, 26, 300, '2026-02-17'),
(7, 27, 10, '2026-02-17'),
(8, 28, 50, '2026-02-17');

-- --------------------------------------------------------

--
-- Table structure for table `reminders_sent`
--

CREATE TABLE `reminders_sent` (
  `id` int(11) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `session_datetime` varchar(50) NOT NULL,
  `sent_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `reminders_sent`
--

INSERT INTO `reminders_sent` (`id`, `patient_id`, `session_datetime`, `sent_at`) VALUES
(1, 28, '2026-02-18T11:32', '2026-02-17 11:33:22');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `doctors`
--
ALTER TABLE `doctors`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Indexes for table `expenses`
--
ALTER TABLE `expenses`
  ADD PRIMARY KEY (`id`),
  ADD KEY `doctor_id` (`doctor_id`);

--
-- Indexes for table `patient`
--
ALTER TABLE `patient`
  ADD PRIMARY KEY (`id`),
  ADD KEY `doctor_id` (`doctor_id`);

--
-- Indexes for table `payments`
--
ALTER TABLE `payments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `patient_id` (`patient_id`);

--
-- Indexes for table `reminders_sent`
--
ALTER TABLE `reminders_sent`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_reminder` (`patient_id`,`session_datetime`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `doctors`
--
ALTER TABLE `doctors`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `expenses`
--
ALTER TABLE `expenses`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `patient`
--
ALTER TABLE `patient`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=29;

--
-- AUTO_INCREMENT for table `payments`
--
ALTER TABLE `payments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `reminders_sent`
--
ALTER TABLE `reminders_sent`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `expenses`
--
ALTER TABLE `expenses`
  ADD CONSTRAINT `expenses_ibfk_1` FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `patient`
--
ALTER TABLE `patient`
  ADD CONSTRAINT `patient_ibfk_1` FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `payments`
--
ALTER TABLE `payments`
  ADD CONSTRAINT `payments_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `reminders_sent`
--
ALTER TABLE `reminders_sent`
  ADD CONSTRAINT `reminders_sent_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
