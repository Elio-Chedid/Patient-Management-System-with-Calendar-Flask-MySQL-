-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: May 16, 2026 at 04:51 PM
-- Server version: 10.4.27-MariaDB
-- PHP Version: 8.1.12

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
(2, 'william', 'scrypt:32768:8:1$lrullKyr8pmLGRWR$f93f598d20b3777921b57ef447d6c0d1b5446c33334806330444e5563573bb8ab5645ce2187a477255e7522030bd52a4201df85f7d22de8c0c33e72fc633b674', 'william hanna', 'doctor'),
(3, 'elio', 'scrypt:32768:8:1$BidXcslbqMpIcb8f$66d2aee2edb2974624e3e65285939896c1c3ad9835ad661bc7eda9f979b3f78b53290cb4850de92ec82c42424b08cb38209e881804f0686f6c80e55b5ae6524a', 'elio chedid', 'doctor');

-- --------------------------------------------------------

--
-- Table structure for table `documents`
--

CREATE TABLE `documents` (
  `id` int(11) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `filename` varchar(255) NOT NULL,
  `stored_filename` varchar(255) NOT NULL,
  `mime_type` varchar(100) NOT NULL,
  `uploaded_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `documents`
--

INSERT INTO `documents` (`id`, `patient_id`, `filename`, `stored_filename`, `mime_type`, `uploaded_at`) VALUES
(1, 20, 'bg1.png', '7b5e415ac5d04f4c868a4588229b49f9.png', 'image/png', '2026-05-16 17:48:07');

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
  `totalfees` float DEFAULT NULL,
  `paidfees` float DEFAULT NULL,
  `doctor_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `patient`
--

INSERT INTO `patient` (`id`, `name`, `details`, `casetype`, `totalfees`, `paidfees`, `doctor_id`) VALUES
(20, 'Samir', 'address: honik\r\nPhone: 123', 'shoulder dislocation', 60, 40, 2),
(21, 'boumale', 'fefegrg\r\n-phone:+96176336806', 'ewgfsnof', 20, 20, 3),
(22, 'karam', 'sddsgvgws', 'lknsdgvnkl', 90, 60, NULL),
(23, 'toni', 'vdmvvm', ' .,sdv.s dd', 70, 67, 3),
(24, 'abdo1', 'kn,mn,knkl.', 'khl', 50, 40, 2),
(27, 'gdfgh', 'fd', 'fdd', 20, 10, 3),
(28, 'ali', 'phone: +96176412744', 'injured', 400, 50, 2),
(29, 'test send', '- phone: +96176412744\r\n', 'mentek', 150, 150, 3),
(30, 'sanfour', 'phone: +96176412744', 'mentek', 120, 120, 2),
(31, 'wiloz', 'phone: +9613931372', 'ccc', 111, 110, 2),
(32, 'elio1', '-phone:+96176412744', 'ssss', 123, 123, 2);

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
(7, 27, 10, '2026-02-17'),
(8, 28, 50, '2026-02-17'),
(9, 29, 150, '2026-05-12'),
(10, 30, 120, '2026-05-16'),
(11, 31, 110, '2026-05-16'),
(12, 32, 123, '2026-05-16');

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
(1, 28, '2026-02-18T11:32', '2026-02-17 11:33:22'),
(2, 29, '2026-05-21T18:17', '2026-05-12 18:17:58'),
(3, 29, '2026-05-12T20:33', '2026-05-12 18:35:08'),
(5, 29, '2026-05-29T18:40', '2026-05-12 18:40:41'),
(6, 21, '2025-07-03T11:30', '2026-05-12 18:49:59'),
(7, 21, '2026-05-12T20:52', '2026-05-12 18:54:16'),
(9, 30, '2026-05-16T12:32', '2026-05-16 12:34:07'),
(10, 31, '2026-05-16T13:39', '2026-05-16 12:38:40'),
(11, 31, '2026-05-16T13:40', '2026-05-16 12:43:32'),
(12, 31, '2026-05-16T12:36', '2026-05-16 12:44:14'),
(13, 32, '2026-05-16T12:46', '2026-05-16 12:46:52'),
(14, 31, '2026-05-18T12:47', '2026-05-16 12:47:40'),
(15, 31, '2026-05-18T12:58', '2026-05-16 12:54:22'),
(16, 31, '2026-06-02T12:54', '2026-05-16 12:55:11'),
(17, 28, '2026-02-17T11:32', '2026-05-16 12:55:43');

-- --------------------------------------------------------

--
-- Table structure for table `sessions`
--

CREATE TABLE `sessions` (
  `id` int(11) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `session_datetime` varchar(50) NOT NULL DEFAULT '',
  `description` text DEFAULT NULL,
  `is_first` tinyint(1) NOT NULL DEFAULT 0,
  `sort_order` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `sessions`
--

INSERT INTO `sessions` (`id`, `patient_id`, `session_datetime`, `description`, `is_first`, `sort_order`) VALUES
(5, 21, '2025-07-03T11:30', 'klsnflknwesf', 1, 0),
(6, 21, '2026-05-12T20:52', '', 0, 1),
(7, 22, '2025-08-03T11:30', 'lknsdlvknsnlv', 1, 0),
(8, 22, '2025-09-04T15:40', '', 0, 1),
(9, 23, '2025-07-03T11:30', 'wfwefwf', 1, 0),
(10, 23, '2025-09-04T15:40', '', 0, 1),
(11, 23, '2025-09-06T11:20', '', 0, 2),
(12, 23, '2025-09-10T15:00', '', 0, 3),
(19, 27, '2026-01-16T09:03', 'fdgd', 1, 0),
(20, 27, '2026-01-19T00:00', '', 0, 1),
(21, 28, '2026-02-17T11:32', 'qwscfg', 1, 0),
(22, 28, '2026-02-18T11:32', '', 0, 1),
(23, 29, '2026-05-12T18:17', 'abcds', 1, 0),
(24, 29, '2026-05-21T18:17', '', 0, 1),
(25, 29, '2026-05-12T20:33', '', 0, 2),
(26, 29, '2026-05-29T18:40', '', 0, 3),
(27, 24, '2025-08-03T11:30', 'hhbkjbjk,bkjb\r\n-assesment:njkjkj\r\n-medical history: kjiu', 1, 0),
(28, 24, '2025-09-03T15:00', '', 0, 1),
(29, 24, '2025-09-05T12:00', '', 0, 2),
(30, 30, '2026-05-16T12:32', 'whatever', 1, 0),
(31, 30, '2026-05-18T12:32', '', 0, 1),
(37, 32, '2026-05-16T12:46', 'qwee', 1, 0),
(53, 31, '2026-05-16T12:36', 'wwww', 1, 0),
(54, 31, '2026-05-16T13:39', 'sdwretet', 0, 1),
(55, 31, '2026-05-16T13:40', 'eeeee', 0, 2),
(56, 31, '2026-05-18T12:47', '8876hgfd', 0, 3),
(57, 31, '2026-05-18T12:58', 'ffhgjr', 0, 4),
(58, 31, '2026-06-02T12:54', 'sfsfw', 0, 5),
(63, 20, '2025-08-03T11:30', '-assesment: bla bla\r\n-medical history: ma ba3ref\r\n-whatever: whatever', 1, 0),
(64, 20, '2025-09-04T15:40', '', 0, 1),
(65, 20, '2025-09-06T11:20', '', 0, 2),
(66, 20, '2025-09-10T15:00', '', 0, 3);

-- --------------------------------------------------------

--
-- Table structure for table `settings`
--

CREATE TABLE `settings` (
  `key` varchar(64) NOT NULL,
  `value` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `settings`
--

INSERT INTO `settings` (`key`, `value`) VALUES
('reminder_delta_minutes', '120'),
('reminder_template', 'Hello {name},\r\nthis is a test for customized message automated message');

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
-- Indexes for table `documents`
--
ALTER TABLE `documents`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_doc_patient` (`patient_id`);

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
-- Indexes for table `sessions`
--
ALTER TABLE `sessions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_patient` (`patient_id`);

--
-- Indexes for table `settings`
--
ALTER TABLE `settings`
  ADD PRIMARY KEY (`key`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `doctors`
--
ALTER TABLE `doctors`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `documents`
--
ALTER TABLE `documents`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `expenses`
--
ALTER TABLE `expenses`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `patient`
--
ALTER TABLE `patient`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=33;

--
-- AUTO_INCREMENT for table `payments`
--
ALTER TABLE `payments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT for table `reminders_sent`
--
ALTER TABLE `reminders_sent`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=18;

--
-- AUTO_INCREMENT for table `sessions`
--
ALTER TABLE `sessions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=67;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `documents`
--
ALTER TABLE `documents`
  ADD CONSTRAINT `fk_doc_patient` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`id`) ON DELETE CASCADE;

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

--
-- Constraints for table `sessions`
--
ALTER TABLE `sessions`
  ADD CONSTRAINT `fk_sessions_patient` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
