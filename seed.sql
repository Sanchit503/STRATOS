-- STRATOS Database Seed Data
-- Geographic Focus: India (Friendly Force)
-- Enemy Focus: Pakistan, China, and neighboring threats
-- 20+ entries per table with realistic military data

USE STRATOS_DB;

-- =====================================================
-- 1. BASES - Indian Air Force and Naval Bases (30 entries with EDGE CASES)
-- =====================================================
INSERT INTO Bases (base_name, force_type, operational_capability, latitude, longitude, status, strength) VALUES
-- Air Force Bases
('Hindon Air Force Station', 'Air Force', 'Offensive', 28.6692, 77.3538, 'Active', 5000),
('Ambala Air Force Station', 'Air Force', 'Offensive', 30.3752, 76.8166, 'Active', 4500),
('Halwara Air Force Station', 'Air Force', 'Offensive', 30.7476, 75.6333, 'Active', 3800),
('Pathankot Air Force Station', 'Air Force', 'Offensive', 32.2333, 75.6344, 'Active', 4200),
('Adampur Air Force Station', 'Air Force', 'Offensive', 31.4326, 75.7585, 'Active', 3500),
('Jodhpur Air Force Station', 'Air Force', 'Offensive', 26.2510, 73.0489, 'Active', 4000),
('Jaisalmer Air Force Station', 'Air Force', 'Offensive', 26.8886, 70.8652, 'Active', 3200),
('Pune Air Force Station', 'Air Force', 'Defensive', 18.5822, 73.9197, 'Active', 3600),
('Sulur Air Force Station', 'Air Force', 'Offensive', 11.0094, 77.0683, 'Active', 3900),
('Thanjavur Air Force Station', 'Air Force', 'Defensive', 10.7222, 79.1014, 'Active', 2800),
('Kalaikunda Air Force Station', 'Air Force', 'Offensive', 22.3450, 87.2290, 'Active', 4100),
('Tezpur Air Force Station', 'Air Force', 'Offensive', 26.7091, 92.7847, 'Active', 3700),
('Chabua Air Force Station', 'Air Force', 'Logistics', 27.4714, 95.1768, 'Active', 2500),
('Bagdogra Air Force Station', 'Air Force', 'Offensive', 26.6815, 88.3285, 'Active', 3300),
('Gorakhpur Air Force Station', 'Air Force', 'Defensive', 26.7397, 83.4498, 'Under Maintenance', 2200),
-- EDGE CASE: Critical Status Bases
('Leh Air Force Station', 'Air Force', 'Offensive', 34.1526, 77.5464, 'Active', 2800),  -- High-altitude base
('Awantipur Air Force Station', 'Air Force', 'Offensive', 33.8333, 75.0167, 'Under Maintenance', 1900), -- Critical zone

-- Naval Bases
('INS Vikramaditya (Mumbai)', 'Naval', 'Offensive', 18.9388, 72.8354, 'Active', 6500),
('INS Kadamba (Karwar)', 'Naval', 'Offensive', 14.8076, 74.1240, 'Active', 7000),
('INS Circars (Visakhapatnam)', 'Naval', 'Offensive', 17.6833, 83.2167, 'Active', 6800),
('INS Shivaji (Lonavla)', 'Naval', 'Logistics', 18.7537, 73.4087, 'Active', 3000),
('INS Jarawa (Port Blair)', 'Naval', 'Defensive', 11.6234, 92.7265, 'Active', 4500),
('INS Rajali (Arakkonam)', 'Naval', 'Offensive', 13.0833, 79.6667, 'Active', 5200),
('INS Hansa (Goa)', 'Naval', 'Defensive', 15.3808, 73.8314, 'Active', 4800),
('INS Kochi Naval Base', 'Naval', 'Offensive', 9.9674, 76.2427, 'Active', 5500),
('INS Chilka (Odisha)', 'Naval', 'Logistics', 19.7150, 85.3220, 'Active', 3500),
('INS Kattabomman (Tamil Nadu)', 'Naval', 'Defensive', 8.7642, 78.1348, 'Under Maintenance', 2600),
-- EDGE CASE: Remote/Critical Naval Bases
('INS Baaz (Campbell Bay)', 'Naval', 'Defensive', 7.0167, 93.9000, 'Active', 1800), -- Southernmost base
('INS Dweeprakshak (Lakshadweep)', 'Naval', 'Defensive', 10.5667, 72.6333, 'Active', 1500),
('INS Parundu (Tamil Nadu)', 'Naval', 'Logistics', 10.7905, 79.8378, 'Inactive', 800); -- EDGE: Inactive base

-- =====================================================
-- 2. PERSONNEL - Military Personnel across bases (35 entries WITH EDGE CASES)
-- =====================================================
INSERT INTO Personnel (base_id, role, name, avail_status) VALUES
-- Air Force Personnel
(1, 'Pilot', 'Wing Commander Arjun Mehta', 'On Duty'),
(1, 'Engineer', 'Flight Lieutenant Priya Sharma', 'On Duty'),
(1, 'Support', 'Sergeant Vikram Singh', 'Off Duty'),
(2, 'Pilot', 'Squadron Leader Rajesh Kumar', 'In Mission'),
(2, 'Pilot', 'Flying Officer Sneha Reddy', 'On Duty'),
(2, 'Engineer', 'Corporal Amit Patel', 'On Duty'),
(3, 'Pilot', 'Group Captain Karan Kapoor', 'On Leave'),
(3, 'Support', 'Airman Rahul Verma', 'On Duty'),
(4, 'Pilot', 'Wing Commander Deepak Chauhan', 'On Duty'),
(4, 'Engineer', 'Squadron Leader Neha Gupta', 'On Duty'),
(5, 'Pilot', 'Flight Lieutenant Aditya Rao', 'In Mission'),
(5, 'Support', 'Sergeant Manoj Tiwari', 'On Duty'),
(6, 'Pilot', 'Wing Commander Sanjay Malhotra', 'On Duty'),
(7, 'Engineer', 'Flight Lieutenant Kavita Nair', 'Off Duty'),
(8, 'Pilot', 'Squadron Leader Ravi Shankar', 'On Duty'),
(12, 'Pilot', 'Wing Commander Aryan Singh', 'In Mission'),
(16, 'Pilot', 'Squadron Leader Rohan Das', 'On Leave'),

-- Naval Personnel
(18, 'Captain', 'Captain Vikrant Bose', 'On Duty'),
(18, 'Engineer', 'Lieutenant Commander Anjali Desai', 'On Duty'),
(18, 'Support', 'Petty Officer Suresh Kumar', 'On Duty'),
(19, 'Captain', 'Commander Anil Khanna', 'In Mission'),
(19, 'Engineer', 'Lieutenant Pooja Joshi', 'On Duty'),
(19, 'Support', 'Seaman Ramesh Yadav', 'Off Duty'),
(20, 'Captain', 'Captain Naveen Pillai', 'On Duty'),
(20, 'Engineer', 'Lieutenant Shruti Iyer', 'On Duty'),
(22, 'Support', 'Petty Officer Ganesh Babu', 'On Leave'),
(22, 'Captain', 'Commander Rohit Menon', 'On Duty'),
(24, 'Pilot', 'Lieutenant Commander Ashwin Kumar', 'In Mission'),
(24, 'Engineer', 'Lieutenant Meera Shah', 'On Duty'),
(25, 'Support', 'Chief Petty Officer Prakash Mishra', 'On Duty'),
(25, 'Captain', 'Commander Satish Nambiar', 'On Duty'),
(26, 'Engineer', 'Lieutenant Divya Krishnan', 'Off Duty'),
(28, 'Captain', 'Commander Vivek Reddy', 'On Duty'),
(29, 'Engineer', 'Lieutenant Shweta Kulkarni', 'On Duty'),
(30, 'Support', 'Seaman Karthik Iyer', 'On Duty');

-- =====================================================
-- 3. VEHICLE_TYPE - Aircraft, Ships, Submarines (35 entries)
-- =====================================================
INSERT INTO Vehicle_Type (speed, vehicle_name, role, crew_capacity, fuel_capacity, category, max_range) VALUES
-- Fighter Jets
(2130.00, 'Dassault Rafale', 'Multirole Fighter', 1, 4700, 'Fighter', 3700.00),
(2500.00, 'Sukhoi Su-30MKI', 'Air Superiority Fighter', 2, 9400, 'Fighter', 3000.00),
(2200.00, 'HAL Tejas Mk1', 'Light Combat Aircraft', 1, 2458, 'Fighter', 3000.00),
(2400.00, 'Mirage 2000', 'Multirole Fighter', 1, 3978, 'Fighter', 1550.00),
(1900.00, 'MiG-29', 'Air Superiority Fighter', 1, 4500, 'Fighter', 1430.00),
(2495.00, 'MiG-21 Bison', 'Interceptor', 1, 2650, 'Fighter', 1210.00),
(2336.00, 'Jaguar SEPECAT', 'Ground Attack', 1, 4200, 'Fighter', 1610.00),

-- Transport Aircraft
(870.00, 'C-17 Globemaster III', 'Strategic Transport', 3, 134556, 'Transport', 4482.00),
(671.00, 'C-130J Super Hercules', 'Tactical Transport', 4, 25300, 'Transport', 3334.00),
(550.00, 'Il-76 Gajraj', 'Heavy Transport', 7, 109500, 'Transport', 4200.00),
(500.00, 'An-32 Sutlej', 'Medium Transport', 4, 10500, 'Transport', 2500.00),
(450.00, 'Dornier 228', 'Light Transport', 2, 1140, 'Transport', 1200.00),
-- ADDED: Tanker Aircraft for Aerial Refueling
(850.00, 'Il-78 Midas', 'Aerial Refueling Tanker', 6, 92500, 'Transport', 5500.00),

-- Surveillance Aircraft
(850.00, 'DRDO AEW&CS (AWACS)', 'Airborne Early Warning', 10, 20000, 'Surveillance', 3500.00),
(900.00, 'Embraer ERJ 145I (NETRA)', 'Airborne Early Warning', 8, 5950, 'Surveillance', 2800.00),
(650.00, 'Boeing P-8I Neptune', 'Maritime Patrol', 9, 34000, 'Surveillance', 7500.00),

-- Bombers
(900.00, 'Su-30MKI (Striker Config)', 'Strike Aircraft', 2, 9400, 'Bomber', 3000.00),
(850.00, 'Jaguar IM (Maritime)', 'Maritime Strike', 1, 4200, 'Bomber', 1400.00),

-- Naval Surface Vessels
(32.00, 'INS Vikramaditya', 'Aircraft Carrier', 1600, 8500000, 'Aircraft Carrier', 7000.00),
(30.00, 'INS Vikrant', 'Aircraft Carrier', 1700, 7800000, 'Aircraft Carrier', 7500.00),
(30.00, 'Kolkata-class Destroyer', 'Guided Missile Destroyer', 350, 2380000, 'Destroyer', 8000.00),
(32.00, 'Delhi-class Destroyer', 'Guided Missile Destroyer', 350, 2200000, 'Destroyer', 7500.00),
(30.00, 'Shivalik-class Frigate', 'Stealth Frigate', 257, 1800000, 'Frigate', 9000.00),
(28.00, 'Talwar-class Frigate', 'Guided Missile Frigate', 220, 1600000, 'Frigate', 4500.00),
(25.00, 'Kamorta-class Corvette', 'Anti-Submarine Corvette', 180, 850000, 'Corvette', 3450.00),
(32.00, 'Rajput-class Destroyer', 'Guided Missile Destroyer', 300, 2100000, 'Destroyer', 7200.00),

-- Naval Surveillance
(28.00, 'Saryu-class Patrol Vessel', 'Offshore Patrol', 118, 650000, 'Patrol Vessel', 6000.00),
(20.00, 'Sukanya-class Patrol Vessel', 'Offshore Patrol', 109, 450000, 'Patrol Vessel', 4500.00),

-- Submarines
(25.00, 'Scorpene-class (Kalvari)', 'Attack Submarine', 31, 500000, 'Attack Submarine', 11000.00),
(30.00, 'Kilo-class (Sindhughosh)', 'Attack Submarine', 53, 450000, 'Attack Submarine', 7400.00),
(24.00, 'INS Arihant', 'Nuclear Ballistic Missile Sub', 95, 800000, 'Nuclear Submarine', 15000.00),
(25.00, 'INS Arighat', 'Nuclear Ballistic Missile Sub', 95, 800000, 'Nuclear Submarine', 15000.00),
(22.00, 'Type 209 (Shishumar-class)', 'Attack Submarine', 40, 420000, 'Attack Submarine', 8200.00),

-- Special Operations
(580.00, 'HAL Dhruv', 'Utility Helicopter', 4, 1000, 'Transport', 800.00),
(295.00, 'HAL Rudra', 'Attack Helicopter', 2, 1000, 'Fighter', 600.00),
(315.00, 'Apache AH-64E', 'Attack Helicopter', 2, 1420, 'Fighter', 476.00),
(278.00, 'Mi-17 V5', 'Medium Lift Helicopter', 3, 3700, 'Transport', 950.00);

-- =====================================================
-- 4. VEHICLE_STATUS - Status for each vehicle type (WITH EDGE CASES)
-- =====================================================
INSERT INTO Vehicle_Status (vehicle_type_id, fuel_level, mission_id, last_updated_time) VALUES
(1, 95.50, NULL, NOW()),
(2, 87.30, 101, NOW()),
(3, 92.00, NULL, NOW()),
(4, 78.50, NULL, NOW()),
(5, 65.20, 102, NOW()),
(6, 88.90, NULL, NOW()),
(7, 91.40, NULL, NOW()),
(8, 94.00, NULL, NOW()),
(9, 82.10, NULL, NOW()),
(10, 76.50, 103, NOW()),
(11, 89.00, NULL, NOW()),
-- EDGE CASE: IL-78 Tanker with low fuel
(12, 35.20, NULL, NOW()),  -- IL-78: Critically low fuel after refueling mission
(13, 85.70, NULL, NOW()),
(14, 79.30, NULL, NOW()),
(15, 90.50, 104, NOW()),
(16, 88.00, NULL, NOW()),
(17, 72.40, NULL, NOW()),
(18, 95.00, NULL, NOW()),
(19, 91.80, NULL, NOW()),
-- EDGE CASE: Very low fuel levels
(20, 22.50, NULL, NOW()),  -- Kolkata Destroyer: Critical fuel
(21, 18.20, NULL, NOW()),  -- Delhi Destroyer: Emergency fuel level
(22, 77.90, NULL, NOW()),
(23, 92.60, NULL, NOW()),
(24, 28.30, NULL, NOW()),  -- Kamorta Corvette: Low fuel
(25, 89.70, NULL, NOW()),
(26, 81.50, NULL, NOW()),
(27, 94.80, NULL, NOW()),
(28, 87.60, NULL, NOW()),
(29, 31.20, 105, NOW()),  -- Kilo Sub: Critical fuel, in mission
(30, 91.30, NULL, NOW()),
(31, 86.90, NULL, NOW()),
(32, 25.50, NULL, NOW()),  -- Type 209: Very low fuel
(33, 80.10, NULL, NOW()),
(34, 88.40, NULL, NOW()),
(35, 92.70, NULL, NOW()),
(36, 45.80, NULL, NOW()); -- Mi-17: Low fuel after transport mission

-- =====================================================
-- 5. VEHICLE_INVENTORY - Vehicles at bases (40 entries)
-- =====================================================
INSERT INTO Vehicle_Inventory (base_id, vehicle_type_id, quantity, operational_status) VALUES
-- Air Force Bases with Jets
(1, 1, 18, 'Fully Operational'), -- Hindon: Rafale
(1, 3, 12, 'Fully Operational'), -- Hindon: Tejas
(2, 2, 24, 'Fully Operational'), -- Ambala: Su-30MKI
(2, 1, 20, 'Fully Operational'), -- Ambala: Rafale
(3, 2, 18, 'Fully Operational'), -- Halwara: Su-30MKI
(3, 4, 10, 'Partially Operational'), -- Halwara: Mirage 2000
(4, 2, 22, 'Fully Operational'), -- Pathankot: Su-30MKI
(4, 5, 16, 'Fully Operational'), -- Pathankot: MiG-29
(5, 7, 14, 'Fully Operational'), -- Adampur: Jaguar
(6, 2, 20, 'Fully Operational'), -- Jodhpur: Su-30MKI
(6, 5, 12, 'Fully Operational'), -- Jodhpur: MiG-29
(7, 2, 16, 'Fully Operational'), -- Jaisalmer: Su-30MKI
(8, 4, 18, 'Fully Operational'), -- Pune: Mirage 2000
(9, 2, 24, 'Fully Operational'), -- Sulur: Su-30MKI
(10, 7, 12, 'Partially Operational'), -- Thanjavur: Jaguar
(11, 2, 18, 'Fully Operational'), -- Kalaikunda: Su-30MKI
(12, 2, 22, 'Fully Operational'), -- Tezpur: Su-30MKI
(13, 9, 8, 'Fully Operational'), -- Chabua: C-130J
(14, 2, 20, 'Fully Operational'), -- Bagdogra: Su-30MKI
(15, 5, 10, 'Under Maintenance'), -- Gorakhpur: MiG-29

-- Transport & Surveillance at Air Bases
(1, 8, 4, 'Fully Operational'), -- C-17
(2, 9, 6, 'Fully Operational'), -- C-130J
(3, 10, 5, 'Fully Operational'), -- Il-76
(12, 13, 3, 'Fully Operational'), -- AWACS
(8, 14, 2, 'Fully Operational'), -- NETRA
-- ADDED: IL-78 Tanker Aircraft at Strategic Bases
(2, 12, 3, 'Fully Operational'), -- Ambala: IL-78 Tanker
(6, 12, 2, 'Fully Operational'), -- Jodhpur: IL-78 Tanker
(1, 12, 2, 'Partially Operational'), -- Hindon: IL-78 (1 under maintenance)

-- Naval Bases with Ships
(18, 19, 1, 'Fully Operational'), -- Mumbai: INS Vikramaditya
(19, 20, 1, 'Fully Operational'), -- Karwar: INS Vikrant
(19, 21, 3, 'Fully Operational'), -- Karwar: Kolkata Destroyer
(20, 22, 2, 'Fully Operational'), -- Visakhapatnam: Delhi Destroyer
(20, 23, 4, 'Fully Operational'), -- Visakhapatnam: Shivalik Frigate
(18, 24, 3, 'Fully Operational'), -- Mumbai: Talwar Frigate
(24, 25, 2, 'Fully Operational'), -- Goa: Kamorta Corvette
(25, 26, 1, 'Fully Operational'), -- Kochi: Rajput Destroyer

-- Naval Surveillance
(22, 27, 2, 'Fully Operational'), -- Port Blair: Saryu Patrol
(26, 28, 3, 'Fully Operational'), -- Chilka: Sukanya Patrol

-- Submarines at Naval Bases
(19, 29, 4, 'Fully Operational'), -- Karwar: Scorpene
(20, 30, 6, 'Fully Operational'), -- Visakhapatnam: Kilo
(19, 31, 1, 'Fully Operational'), -- Karwar: INS Arihant
(19, 32, 1, 'Fully Operational'), -- Karwar: INS Arighat
-- EDGE CASE: Damaged/Critical Equipment
(18, 33, 3, 'Damaged'), -- Mumbai: Type 209 - 2 damaged, 1 operational
(20, 29, 2, 'Under Maintenance'), -- Visakhapatnam: Scorpene
(18, 30, 2, 'Critical'); -- Mumbai: Kilo - Critical operational status

-- =====================================================
-- 6. MISSILE_TYPE - Indian Missile Arsenal (25 entries)
-- =====================================================
INSERT INTO Missile_Type (speed, missile_name, category, max_range) VALUES
-- Cruise Missiles
(2900.00, 'BrahMos (Air-Launched)', 'Cruise', 400.00),
(2900.00, 'BrahMos (Ship-Launched)', 'Cruise', 450.00),
(2900.00, 'BrahMos (Land-Attack)', 'Cruise', 500.00),
(2900.00, 'BrahMos-NG', 'Cruise', 290.00),
(1000.00, 'Nirbhay', 'Cruise', 1000.00),

-- Ballistic Missiles
(7000.00, 'Agni-I', 'Ballistic', 700.00),
(7500.00, 'Agni-II', 'Ballistic', 2000.00),
(8000.00, 'Agni-III', 'Ballistic', 3000.00),
(9000.00, 'Agni-IV', 'Ballistic', 4000.00),
(10000.00, 'Agni-V', 'Ballistic', 5500.00),
(6500.00, 'Prithvi-II', 'Ballistic', 350.00),
(7000.00, 'Prithvi-III', 'Ballistic', 600.00),
(3500.00, 'Shaurya', 'Ballistic', 750.00),

-- Surface-to-Air Missiles
(2000.00, 'Akash', 'Surface-to-Air', 30.00),
(2500.00, 'Akash-NG', 'Surface-to-Air', 35.00),
(1800.00, 'Barak-8', 'Surface-to-Air', 100.00),
(1500.00, 'Trishul', 'Surface-to-Air', 9.00),
(2200.00, 'S-400 Triumf', 'Surface-to-Air', 400.00),
(1700.00, 'QRSAM', 'Surface-to-Air', 30.00),

-- Air-to-Air Missiles
(3500.00, 'Astra Mk1', 'Air-to-Air', 110.00),
(4000.00, 'Astra Mk2', 'Air-to-Air', 160.00),
(3800.00, 'R-77 (AA-12)', 'Air-to-Air', 110.00),
(4500.00, 'R-27 (AA-10)', 'Air-to-Air', 130.00),
(4200.00, 'Python-5', 'Air-to-Air', 20.00),
(3200.00, 'Derby', 'Air-to-Air', 50.00);

-- =====================================================
-- 7. MISSILE_INVENTORY - Missiles at bases (35 entries)
-- =====================================================
INSERT INTO Missile_Inventory (base_id, missile_type_id, quantity, operational_status) VALUES
-- Air Force Bases with Air-Launched & Air-to-Air Missiles
(1, 1, 48, 'Fully Operational'), -- Hindon: BrahMos Air
(1, 20, 120, 'Under Maintenance'), -- Hindon: Astra Mk1
(2, 1, 60, 'Fully Operational'), -- Ambala: BrahMos Air
(2, 21, 80, 'Under Maintenance'), -- Ambala: Astra Mk2
(2, 22, 100, 'Fully Operational'), -- Ambala: R-77
(3, 20, 90, 'Fully Operational'), -- Halwara: Astra Mk1
(3, 23, 70, 'Fully Operational'), -- Halwara: R-27
(4, 1, 50, 'Fully Operational'), -- Pathankot: BrahMos Air
(4, 24, 40, 'Fully Operational'), -- Pathankot: Python-5
(6, 21, 85, 'Fully Operational'), -- Jodhpur: Astra Mk2
(9, 1, 55, 'Fully Operational'), -- Sulur: BrahMos Air
(11, 20, 95, 'Fully Operational'), -- Kalaikunda: Astra Mk1
(12, 21, 110, 'Fully Operational'), -- Tezpur: Astra Mk2

-- Strategic Ballistic Missiles at Select Air Bases
(2, 6, 12, 'Fully Operational'), -- Ambala: Agni-I
(2, 7, 8, 'Fully Operational'), -- Ambala: Agni-II
(6, 8, 6, 'Fully Operational'), -- Jodhpur: Agni-III
(7, 9, 4, 'Fully Operational'), -- Jaisalmer: Agni-IV
(12, 10, 3, 'Fully Operational'), -- Tezpur: Agni-V
(11, 11, 15, 'Fully Operational'), -- Kalaikunda: Prithvi-II

-- Surface-to-Air at Air and Naval Bases
(1, 14, 24, 'Fully Operational'), -- Hindon: Akash
(2, 15, 18, 'Fully Operational'), -- Ambala: Akash-NG
(4, 18, 12, 'Fully Operational'), -- Pathankot: S-400
(12, 18, 10, 'Fully Operational'), -- Tezpur: S-400
(18, 16, 32, 'Fully Operational'), -- Mumbai Naval: Barak-8
(19, 16, 40, 'Fully Operational'), -- Karwar Naval: Barak-8
(20, 16, 36, 'Fully Operational'), -- Visakhapatnam: Barak-8

-- Naval Ship-Launched BrahMos
(18, 2, 48, 'Fully Operational'), -- Mumbai: BrahMos Ship
(19, 2, 64, 'Fully Operational'), -- Karwar: BrahMos Shipl
(20, 2, 56, 'Fully Operational'), -- Visakhapatnam: BrahMos Ship
(24, 2, 32, 'Fully Operational'), -- Goa: BrahMos Ship
(25, 2, 40, 'Fully Operational'), -- Kochi: BrahMos Ship

-- Land-Attack Cruise Missiles
(6, 3, 30, 'Fully Operational'), -- Jodhpur: BrahMos Land
(7, 3, 25, 'Fully Operational'), -- Jaisalmer: BrahMos Land
(12, 5, 18, 'Fully Operational'), -- Tezpur: Nirbhay
(11, 5, 20, 'Fully Operational'); -- Kalaikunda: Nirbhay

-- =====================================================
-- 8. RESOURCE - Resource Types (22 entries)
-- =====================================================
INSERT INTO Resource (unit_of_measurement, resource_type) VALUES
('Liters', 'Aviation Fuel (Jet A-1)'),
('Liters', 'Marine Diesel'),
('Liters', 'Nuclear Fuel (Enriched Uranium)'),
('Tons', 'General Ammunition'),
('Units', 'Air-to-Air Missiles'),
('Units', 'Surface-to-Air Missiles'),
('Units', 'Anti-Ship Missiles'),
('Units', 'Torpedoes'),
('Units', 'Depth Charges'),
('Tons', 'Spare Parts (Aircraft)'),
('Tons', 'Spare Parts (Naval)'),
('Units', 'Medical Supplies'),
('Tons', 'Food Rations'),
('Liters', 'Drinking Water'),
('Units', 'Communication Equipment'),
('Units', 'Radar Systems'),
('Units', 'Electronic Warfare Systems'),
('Tons', 'Explosives'),
('Units', 'Night Vision Equipment'),
('Units', 'Protective Gear'),
('Tons', 'Maintenance Tools'),
('Tons', 'Construction Materials');

-- =====================================================
-- 9. RESOURCE_INVENTORY - Resources at bases (45 entries)
-- =====================================================
INSERT INTO Resource_Inventory (base_id, resource_id, quantity, status) VALUES
-- Air Force Bases - Aviation Resources
(1, 1, 2500000.00, 'Adequate'), -- Hindon: Jet Fuel
(1, 4, 450.00, 'Adequate'), -- Hindon: Ammunition
(1, 5, 280, 'Adequate'), -- Hindon: Air-to-Air Missiles
(1, 10, 120.00, 'Adequate'), -- Hindon: Aircraft Spare Parts
(2, 1, 3200000.00, 'Adequate'), -- Ambala: Jet Fuel
(2, 4, 580.00, 'Adequate'), -- Ambala: Ammunition
(2, 5, 350, 'Adequate'), -- Ambala: Air-to-Air Missiles
(2, 6, 80, 'Adequate'), -- Ambala: SAMs
(2, 10, 180.00, 'Adequate'), -- Ambala: Aircraft Spare Parts
(3, 1, 2800000.00, 'Low'), -- Halwara: Jet Fuel
(3, 4, 420.00, 'Adequate'), -- Halwara: Ammunition
(4, 1, 2900000.00, 'Adequate'), -- Pathankot: Jet Fuel
(4, 5, 320, 'Adequate'), -- Pathankot: Air-to-Air Missiles
(6, 1, 2700000.00, 'Adequate'), -- Jodhpur: Jet Fuel
(6, 4, 550.00, 'Adequate'), -- Jodhpur: Ammunition
(7, 1, 2400000.00, 'Adequate'), -- Jaisalmer: Jet Fuel
(9, 1, 3100000.00, 'Adequate'), -- Sulur: Jet Fuel
(11, 1, 2850000.00, 'Adequate'), -- Kalaikunda: Jet Fuel
(12, 1, 2950000.00, 'Adequate'), -- Tezpur: Jet Fuel
(12, 16, 45, 'Adequate'), -- Tezpur: Radar Systems

-- Naval Bases - Naval Resources
(16, 2, 8500000.00, 'Adequate'), -- Mumbai: Marine Diesel
(16, 7, 120, 'Adequate'), -- Mumbai: Anti-Ship Missiles
(16, 8, 180, 'Adequate'), -- Mumbai: Torpedoes
(16, 11, 320.00, 'Adequate'), -- Mumbai: Naval Spare Parts
(17, 2, 9200000.00, 'Adequate'), -- Karwar: Marine Diesel
(17, 3, 1500000.00, 'Adequate'), -- Karwar: Nuclear Fuel
(17, 7, 150, 'Adequate'), -- Karwar: Anti-Ship Missiles
(17, 8, 220, 'Adequate'), -- Karwar: Torpedoes
(17, 9, 140, 'Adequate'), -- Karwar: Depth Charges
(17, 11, 450.00, 'Adequate'), -- Karwar: Naval Spare Parts
(18, 2, 8800000.00, 'Adequate'), -- Visakhapatnam: Marine Diesel
(18, 7, 135, 'Adequate'), -- Visakhapatnam: Anti-Ship Missiles
(18, 8, 200, 'Adequate'), -- Visakhapatnam: Torpedoes
(18, 11, 380.00, 'Adequate'), -- Visakhapatnam: Naval Spare Parts
(22, 2, 5500000.00, 'Low'), -- Goa: Marine Diesel
(22, 11, 220.00, 'Adequate'), -- Goa: Naval Spare Parts
(23, 2, 6200000.00, 'Adequate'), -- Kochi: Marine Diesel

-- Common Resources across bases
(1, 12, 850, 'Adequate'), -- Hindon: Medical
(2, 12, 1100, 'Adequate'), -- Ambala: Medical
(16, 12, 1500, 'Adequate'), -- Mumbai: Medical
(17, 12, 1650, 'Adequate'), -- Karwar: Medical
(1, 13, 180.00, 'Adequate'), -- Hindon: Food
(16, 13, 420.00, 'Adequate'), -- Mumbai: Food
(17, 13, 480.00, 'Adequate'), -- Karwar: Food
(20, 13, 320.00, 'Low'), -- Port Blair: Food
-- EDGE CASE: Critical Resource Shortages
(15, 1, 180000.00, 'Critical'), -- Gorakhpur: Critically low jet fuel
(30, 4, 25.00, 'Critical'), -- INS Parundu: Very low ammunition
(17, 16, 15, 'Low'), -- Awantipur: Limited radar systems
(28, 2, 950000.00, 'Low'), -- INS Baaz: Low marine diesel
(29, 12, 45, 'Critical'); -- INS Dweeprakshak: Critical medical shortage

-- =====================================================
-- 10. ENEMY_BASE - Pakistan, China, Myanmar bases (40 entries - EXPANDED)
-- =====================================================
INSERT INTO Enemy_Base (enemy_base_name, latitude, longitude, threat_level) VALUES
-- Pakistan Air Force and Strategic Bases
('PAF Base Sargodha', 32.0486, 72.6656, 'Critical'),
('PAF Base Mushaf (Sargodha)', 32.0400, 72.6700, 'High'),
('PAF Base Rafiqui (Shorkot)', 30.7544, 72.2656, 'High'),
('PAF Base Masroor (Karachi)', 24.8934, 66.9385, 'High'),
('PAF Base Minhas (Kamra)', 33.8694, 72.4003, 'Critical'),
('PAF Base Jacobabad', 28.2842, 68.4496, 'Medium'),
('PAF Base Samungli (Quetta)', 30.2517, 67.1522, 'Medium'),
('Rawalpindi Strategic Command', 33.6007, 73.0679, 'Critical'),
('Gwadar Naval Base', 25.1264, 62.3295, 'High'),
('Karachi Naval Dockyard', 24.8414, 67.0011, 'High'),
('Ormara Naval Base', 25.2089, 64.6357, 'Medium'),
('Pasni Naval Base', 25.2630, 63.4681, 'Low'),
('Khuzdar Strategic Site', 27.8118, 66.6410, 'Medium'),
('Multan Strategic Storage', 30.1978, 71.4697, 'Medium'),
-- MORE Pakistan Bases
('PAF Base Faisal (Karachi)', 24.9056, 67.1608, 'High'),
('PAF Base Mianwali', 32.5631, 71.5701, 'High'),
('PAF Base Peshawar', 33.9939, 71.5143, 'Critical'),
('Chaklala Air Base (Islamabad)', 33.6167, 73.0997, 'High'),
('PAF Base Risalpur', 34.0811, 71.9728, 'Medium'),
('Jinnah Naval Base (Ormara)', 25.2700, 64.5800, 'Medium'),
('Pakistan Naval Station Mehran', 24.9051, 67.1622, 'High'),

-- China PLA Bases near India
('PLA Hotan Air Base', 37.0385, 79.8649, 'Critical'),
('PLA Kashgar Air Base', 39.4677, 76.0199, 'High'),
('PLA Ngari Gunsa Air Base', 32.1000, 80.0500, 'Critical'),
('PLA Shigatse Air Base', 29.3517, 89.3114, 'High'),
('PLA Lhasa Gonggar Air Base', 29.2978, 90.9117, 'High'),
('PLA Chamdo Bangda Air Base', 30.5536, 97.1083, 'Medium'),
('PLA Linzhi Air Base', 29.3033, 94.3353, 'Medium'),
('Chengdu Military Region HQ', 30.5728, 104.0668, 'High'),
('PLA Kunming Air Base', 24.9927, 102.7439, 'Medium'),
('PLA Xining Air Base', 36.5275, 101.7000, 'Medium'),
('PLA Strategic Missile Base (Tibet)', 31.2000, 91.5000, 'Critical'),
-- MORE China PLA Bases
('PLA Dingxin Air Base', 40.2000, 99.5200, 'High'),
('PLA Korla Air Base', 41.7273, 86.0779, 'Medium'),
('PLA Gar Gunsa Air Base', 32.0833, 80.0500, 'Critical'),
('PLA Shigatse Main Base', 29.2500, 88.8900, 'High'),
('PLA Lanzhou Military Region', 36.0564, 103.7922, 'Medium'),
('PLA Chongqing Strategic Base', 29.5630, 106.5516, 'Medium'),
('PLA Navy Yulin Base (Hainan)', 18.2300, 109.5800, 'High'),

-- Myanmar/Bangladesh Bases (Regional Threats)
('Myanmar Meiktila Air Base', 20.8667, 95.8667, 'Low'),
('Myanmar Magway Air Base', 20.1500, 94.9300, 'Low'),
('Myanmar Sittwe Naval Base', 20.1500, 92.9000, 'Medium');

-- =====================================================
-- 11. ATTACK_SIMULATION - Simulations (30 entries)
-- =====================================================
INSERT INTO Attack_Simulation (target_base_id, base_id, simulation_type, simulation_date, readiness_level, recommendation) VALUES
(1, 2, 'Air Superiority Strike', '2026-01-15', 'High', 'Deploy 12x Su-30MKI with BrahMos support. Expected success rate: 85%'),
(1, 4, 'Missile Barrage', '2026-01-18', 'High', 'Launch Agni-II from safe distance. Target: Command & Control'),
(2, 2, 'Suppression of Enemy Air Defense', '2026-01-20', 'Medium', 'SEAD mission using Rafale with anti-radiation missiles'),
(5, 12, 'Preemptive Strike', '2026-01-22', 'High', 'Long-range BrahMos strike from Tezpur. High success probability'),
(3, 6, 'Strategic Bombing', '2026-01-10', 'High', 'Deploy Su-30MKI from Jodhpur with precision-guided munitions'),
(4, 1, 'Maritime Interdiction Prep', '2026-01-12', 'Medium', 'Coordinate with naval assets for port strike'),
(9, 17, 'Naval Blockade Simulation', '2026-01-14', 'High', 'Deploy Kolkata-class destroyers with submarine support'),
(10, 16, 'Anti-Ship Mission', '2026-01-16', 'High', 'BrahMos ship-launched from INS Vikramaditya'),
(6, 7, 'Deep Strike Operation', '2026-01-25', 'Medium', 'Long-range cruise missile strike. Refueling required'),
(7, 6, 'Close Air Support', '2026-01-27', 'High', 'Jaguar ground attack with fighter escort'),
(8, 2, 'Decapitation Strike', '2026-01-05', 'Critical', 'Target command structure with precision strikes'),
(15, 12, 'Border Air Defense', '2026-01-08', 'High', 'CAP missions with Su-30MKI, S-400 backup'),
(16, 11, 'High-Altitude Strike', '2026-01-11', 'Medium', 'Deploy specialized munitions for high-altitude targets'),
(17, 18, 'Air Base Neutralization', '2026-01-13', 'High', 'Runway denial using cruise missiles and cluster munitions'),
(18, 9, 'Intelligence Gathering', '2026-01-17', 'Low', 'Deploy AWACS and surveillance before main strike'),
(19, 2, 'Electronic Warfare', '2026-01-19', 'Medium', 'Disrupt enemy communications and radar'),
(20, 12, 'Multi-Domain Operation', '2026-01-21', 'High', 'Coordinated air-land-cyber strike'),
(21, 11, 'Counter-Air Mission', '2026-01-23', 'High', 'Destroy enemy aircraft on ground'),
(22, 6, 'Strategic Infrastructure', '2026-01-24', 'Medium', 'Target fuel depots and ammunition storage'),
(14, 7, 'Logistics Disruption', '2026-01-26', 'Medium', 'Interdict supply lines and transport nodes'),
(25, 2, 'Ballistic Missile Defense Test', '2026-01-28', 'Low', 'Simulate incoming missile defense with S-400'),
(1, 11, 'Saturation Attack', '2026-01-09', 'High', 'Overwhelm air defenses with multiple vectors'),
(3, 9, 'Surgical Strike', '2026-01-07', 'High', 'Precision strike on identified high-value targets'),
(5, 1, 'Stand-off Strike', '2026-01-06', 'Medium', 'Long-range missile attack beyond enemy air defense'),
(10, 18, 'Anti-Access/Area Denial', '2026-01-04', 'High', 'Establish naval blockade with missile coverage'),
(12, 16, 'Force Projection', '2026-01-03', 'Medium', 'Demonstrate capability with carrier battle group'),
(15, 4, 'Air Interdiction', '2026-01-02', 'High', 'Prevent enemy reinforcements via air'),
(17, 12, 'Cross-Border Strike', '2026-01-01', 'Critical', 'Rapid response to provocation'),
(19, 17, 'Amphibious Support', '2025-12-30', 'Medium', 'Naval gunfire and air support for landing operations'),
(22, 23, 'Maritime Strike', '2025-12-28', 'High', 'Coordinate surface and subsurface assets for port attack');

-- =====================================================
-- 12. READINESS_REPORT - Base assessments (25 entries)
-- =====================================================
INSERT INTO Readiness_Report (base_id, assessment_date, overall_readiness, personnel_score, resource_score, missile_score, strategic_recomm) VALUES
(1, '2026-01-28', 'Fully Ready', 92.50, 88.30, 95.00, 'Maintain current readiness. Excellent operational status.'),
(2, '2026-01-27', 'Fully Ready', 95.00, 91.50, 97.50, 'Strategic asset. Continue high-alert posture.'),
(3, '2026-01-26', 'Ready with Support', 85.00, 72.00, 88.00, 'Low fuel reserves. Recommend immediate resupply.'),
(4, '2026-01-25', 'Fully Ready', 90.00, 87.50, 93.00, 'Forward base ready for rapid deployment.'),
(5, '2026-01-24', 'Vulnerable', 82.00, 78.00, 0.00, 'No missile inventory assigned. Ground attack capability only via Jaguar aircraft. Urgent resupply needed.'),
(6, '2026-01-23', 'Fully Ready', 93.50, 89.00, 94.50, 'Strategic importance. Maintain ballistic missile readiness.'),
(7, '2026-01-22', 'Fully Ready', 91.00, 86.50, 92.00, 'Desert operations optimized. Ready for long-range missions.'),
(8, '2026-01-21', 'Ready with Support', 87.00, 83.00, 86.00, 'Adequate for defensive operations.'),
(9, '2026-01-20', 'Fully Ready', 94.00, 90.50, 95.50, 'Southern command hub. Excellent multi-role capability.'),
(10, '2026-01-19', 'Ready with Support', 80.00, 75.00, 82.00, 'Limited offensive capability. Focus on air defense.'),
(11, '2026-01-18', 'Fully Ready', 92.00, 88.00, 93.50, 'Eastern front ready. Strategic cruise missile stockpile.'),
(12, '2026-01-17', 'Fully Ready', 96.00, 92.00, 98.00, 'Critical border defense. S-400 systems active.'),
(13, '2026-01-16', 'Ready with Support', 78.00, 80.00, 70.00, 'Logistics hub. Limited combat capability.'),
(14, '2026-01-15', 'Fully Ready', 89.00, 85.50, 90.00, 'Northern defense ready. Good operational status.'),
(15, '2026-01-14', 'Vulnerable', 65.00, 60.00, 68.00, 'Under maintenance. Not recommended for operations.'),
(16, '2026-01-27', 'Fully Ready', 94.50, 93.00, 96.00, 'Carrier battle group ready. Premier naval asset.'),
(17, '2026-01-26', 'Fully Ready', 97.00, 95.50, 98.50, 'Naval headquarters. Nuclear submarine capability operational.'),
(18, '2026-01-25', 'Fully Ready', 95.50, 92.50, 97.00, 'Eastern naval command. Full strike capability.'),
(19, '2026-01-24', 'Ready with Support', 84.00, 81.00, 83.00, 'Training base. Limited combat operations.'),
(20, '2026-01-23', 'Ready with Support', 81.00, 76.00, 79.00, 'Remote location. Adequate for surveillance and patrol.'),
(21, '2026-01-22', 'Fully Ready', 91.50, 88.50, 93.00, 'Naval aviation ready. Carrier operations capable.'),
(22, '2026-01-21', 'Ready with Support', 83.00, 79.00, 85.00, 'Coastal defense optimized. Limited blue-water capability.'),
(23, '2026-01-20', 'Fully Ready', 90.50, 87.00, 91.50, 'Southern naval hub. Ready for deployment.'),
(24, '2026-01-19', 'Ready with Support', 77.00, 72.00, 75.00, 'Under scheduled maintenance. Reduced patrol capacity.'),
(25, '2026-01-18', 'Vulnerable', 68.00, 65.00, 70.00, 'Maintenance period. Limited defensive capability only.'),
-- EDGE CASE: Additional bases with critical readiness
(16, '2026-01-29', 'Fully Ready', 88.00, 84.00, 80.00, 'High-altitude operations. Equipment stress monitoring required.'),
(17, '2026-01-28', 'Vulnerable', 55.00, 48.00, 52.00, 'Under major maintenance. Multiple systems offline. Do not engage.'),
(28, '2026-01-27', 'Ready with Support', 72.00, 68.00, 65.00, 'Remote island base. Limited resupply. Defensive posture only.'),
(29, '2026-01-26', 'Ready with Support', 75.00, 70.00, 68.00, 'Island defense adequate. Surveillance capabilities functional.'),
(30, '2026-01-25', 'Critical', 42.00, 35.00, 40.00, 'INACTIVE BASE. Major systems failure. Emergency resupply required urgently.');

-- =====================================================
-- 13. LOGISTICS_TRANSFER - Resource transfers (28 entries)
-- =====================================================
INSERT INTO Logistics_Transfer (source_base_id, transfer_base_id, resource_id, quantity_transferred, start_date, status) VALUES
-- Fuel Transfers
(2, 3, 1, 500000.00, '2026-01-20', 'Completed'), -- Ambala to Halwara: Jet Fuel
(1, 15, 1, 300000.00, '2026-01-22', 'In Transit'), -- Hindon to Gorakhpur: Jet Fuel
(17, 22, 2, 800000.00, '2026-01-18', 'Completed'), -- Karwar to Goa: Marine Diesel
(16, 23, 2, 600000.00, '2026-01-25', 'In Transit'), -- Mumbai to Kochi: Marine Diesel
(17, 16, 3, 200000.00, '2026-01-15', 'Completed'), -- Karwar to Mumbai: Nuclear Fuel

-- Ammunition and Missile Transfers
(2, 4, 4, 120.00, '2026-01-19', 'Completed'), -- Ambala to Pathankot: Ammunition
(1, 3, 5, 50, '2026-01-21', 'In Transit'), -- Hindon to Halwara: Air-to-Air Missiles
(6, 7, 6, 20, '2026-01-17', 'Completed'), -- Jodhpur to Jaisalmer: SAMs
(16, 18, 7, 30, '2026-01-24', 'In Transit'), -- Mumbai to Visakhapatnam: Anti-Ship Missiles
(17, 16, 8, 40, '2026-01-16', 'Completed'), -- Karwar to Mumbai: Torpedoes

-- Spare Parts Transfers
(2, 12, 10, 25.00, '2026-01-23', 'In Transit'), -- Ambala to Tezpur: Aircraft Parts
(1, 8, 10, 18.00, '2026-01-20', 'Completed'), -- Hindon to Pune: Aircraft Parts
(17, 18, 11, 45.00, '2026-01-19', 'Completed'), -- Karwar to Visakhapatnam: Naval Parts
(16, 22, 11, 30.00, '2026-01-26', 'Pending'), -- Mumbai to Goa: Naval Parts

-- Medical and Food Supplies
(2, 12, 12, 200, '2026-01-18', 'Completed'), -- Ambala to Tezpur: Medical
(16, 20, 12, 180, '2026-01-21', 'In Transit'), -- Mumbai to Port Blair: Medical
(17, 24, 12, 150, '2026-01-24', 'In Transit'), -- Karwar to Chilka: Medical
(1, 14, 13, 50.00, '2026-01-22', 'Completed'), -- Hindon to Bagdogra: Food
(16, 20, 13, 120.00, '2026-01-17', 'Completed'), -- Mumbai to Port Blair: Food
(17, 20, 13, 80.00, '2026-01-25', 'In Transit'), -- Karwar to Port Blair: Food

-- Equipment Transfers
(2, 12, 15, 15, '2026-01-16', 'Completed'), -- Ambala to Tezpur: Comm Equipment
(1, 4, 16, 8, '2026-01-23', 'In Transit'), -- Hindon to Pathankot: Radar Systems
(12, 11, 17, 5, '2026-01-19', 'Completed'), -- Tezpur to Kalaikunda: EW Systems
(16, 18, 17, 6, '2026-01-26', 'Pending'), -- Mumbai to Visakhapatnam: EW Systems

-- Maintenance and Construction
(1, 15, 21, 35.00, '2026-01-20', 'In Transit'), -- Hindon to Gorakhpur: Tools
(17, 24, 21, 28.00, '2026-01-18', 'Completed'), -- Karwar to Chilka: Tools
(16, 22, 22, 40.00, '2026-01-27', 'Pending'), -- Mumbai to Goa: Construction Materials
(17, 25, 22, 32.00, '2026-01-24', 'In Transit'), -- Karwar to Kattabomman: Construction Materials

-- EDGE CASE: Cancelled/Failed Transfers
(2, 15, 1, 400000.00, '2026-01-12', 'Cancelled'), -- Ambala to Gorakhpur: Cancelled due to weather
(16, 30, 2, 500000.00, '2026-01-10', 'Cancelled'), -- Mumbai to Parundu: Base inactive, transfer aborted
(12, 17, 6, 15, '2026-01-08', 'Cancelled'), -- Tezpur to Awantipur: Security threat, mission aborted
(1, 28, 12, 100, '2026-01-05', 'Cancelled'), -- Hindon to Baaz: Logistics failure
(17, 29, 7, 25, '2026-01-29', 'Pending'); -- Karwar to Dweeprakshak: Emergency anti-ship missiles

-- =====================================================
-- SEED DATA 
-- =====================================================
-- Summary:
-- - 30 Bases (17 Air Force, 13 Naval) 
-- - 35 Personnel - WITH DIVERSE STATUS
-- - 36 Vehicle Types (Jets, Ships, Subs, Helicopters, IL-78 Tanker)
-- - 36 Vehicle Status entries - WITH CRITICAL LOW FUEL CASES (18-45%)
-- - 43 Vehicle Inventory entries - WITH DAMAGED/CRITICAL STATUS
-- - 25 Missile Types (BrahMos, Agni, Astra, etc.)
-- - 35 Missile Inventory entries
-- - 22 Resource Types
-- - 50 Resource Inventory entries - WITH CRITICAL SHORTAGES
-- - 40 Enemy Bases (Pakistan, China, Myanmar) - EXPANDED
-- - 30 Attack Simulations
-- - 30 Readiness Reports - INCLUDING CRITICAL/VULNERABLE STATES
-- - 33 Logistics Transfers - WITH CANCELLATIONS
-- =====================================================

