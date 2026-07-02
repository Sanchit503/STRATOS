-- Create the Database
CREATE DATABASE IF NOT EXISTS STRATOS_DB;
USE STRATOS_DB;

-- 1. BASES Table (Strong Entity - The Hub)
CREATE TABLE Bases (
    base_id INT PRIMARY KEY AUTO_INCREMENT,
    base_name VARCHAR(100) NOT NULL,
    force_type ENUM('Naval', 'Air Force') NOT NULL,
    operational_capability VARCHAR(100), -- e.g., Offensive, Defensive, Logistics
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    status ENUM('Active', 'Under Maintenance', 'Inactive') DEFAULT 'Active',
    strength INT CHECK (strength >= 0)
);

-- 2. PERSONNEL Table
CREATE TABLE Personnel (
    service_id INT PRIMARY KEY AUTO_INCREMENT,
    base_id INT NOT NULL,
    role VARCHAR(50), -- e.g., Pilot, Support, Engineer
    name VARCHAR(100) NOT NULL,
    avail_status ENUM('On Duty', 'Off Duty', 'On Leave', 'In Mission') DEFAULT 'On Duty',
    FOREIGN KEY (base_id) REFERENCES Bases(base_id) ON DELETE CASCADE
);

-- 3. VEHICLE_TYPE Table
CREATE TABLE Vehicle_Type (
    vehicle_type_id INT PRIMARY KEY AUTO_INCREMENT,
    speed DECIMAL(10, 2),
    vehicle_name VARCHAR(100) NOT NULL,
    role VARCHAR(50),
    crew_capacity INT,
    fuel_capacity INT,
    category VARCHAR(50), 
    max_range DECIMAL(10, 2)
);

-- 4. VEHICLE_STATUS Table 
CREATE TABLE Vehicle_Status (
    vehicle_type_id INT PRIMARY KEY,
    fuel_level DECIMAL(5, 2) CHECK (fuel_level BETWEEN 0 AND 100),
    mission_id INT,
    last_updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_type_id) REFERENCES Vehicle_Type(vehicle_type_id) ON DELETE CASCADE
);

-- 5. VEHICLE_INVENTORY (Weak Entity)
CREATE TABLE Vehicle_Inventory (
    base_vehicle_id INT PRIMARY KEY AUTO_INCREMENT,
    base_id INT NOT NULL,
    vehicle_type_id INT NOT NULL,
    quantity INT DEFAULT 0 CHECK (quantity >= 0),
    operational_status VARCHAR(50),
    UNIQUE(base_id, vehicle_type_id), -- Enforcing the identification relationship
    FOREIGN KEY (base_id) REFERENCES Bases(base_id) ON DELETE CASCADE,
    FOREIGN KEY (vehicle_type_id) REFERENCES Vehicle_Type(vehicle_type_id) ON DELETE CASCADE
);

-- 6. MISSILE_TYPE Table
CREATE TABLE Missile_Type (
    missile_type_id INT PRIMARY KEY AUTO_INCREMENT,
    speed DECIMAL(10, 2),
    missile_name VARCHAR(100) NOT NULL,
    category ENUM('Surface-to-Air', 'Air-to-Air', 'Ballistic', 'Cruise'),
    max_range DECIMAL(10, 2)
);

-- 7. MISSILE_INVENTORY (Weak Entity)
CREATE TABLE Missile_Inventory (
    base_missile_id INT PRIMARY KEY AUTO_INCREMENT,
    base_id INT NOT NULL,
    missile_type_id INT NOT NULL,
    quantity INT DEFAULT 0 CHECK (quantity >= 0),
    operational_status VARCHAR(50),
    UNIQUE(base_id, missile_type_id),
    FOREIGN KEY (base_id) REFERENCES Bases(base_id) ON DELETE CASCADE,
    FOREIGN KEY (missile_type_id) REFERENCES Missile_Type(missile_type_id) ON DELETE CASCADE
);

-- 8. RESOURCE Table
CREATE TABLE Resource (
    resource_id INT PRIMARY KEY AUTO_INCREMENT,
    unit_of_measurement VARCHAR(20), -- e.g., Liters, Tons, Units
    resource_type VARCHAR(50) NOT NULL -- e.g., Fuel, Ammunition, Medical
);

-- 9. RESOURCE_INVENTORY (Weak Entity)
CREATE TABLE Resource_Inventory (
    inventory_id INT PRIMARY KEY AUTO_INCREMENT,
    base_id INT NOT NULL,
    resource_id INT NOT NULL,
    quantity DECIMAL(15, 2) DEFAULT 0 CHECK (quantity >= 0),
    status VARCHAR(50),
    UNIQUE(base_id, resource_id),
    FOREIGN KEY (base_id) REFERENCES Bases(base_id) ON DELETE CASCADE,
    FOREIGN KEY (resource_id) REFERENCES Resource(resource_id) ON DELETE CASCADE
);

-- 10. ENEMY_BASE Table
CREATE TABLE Enemy_Base (
    enemy_base_id INT PRIMARY KEY AUTO_INCREMENT,
    enemy_base_name VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    threat_level ENUM('Low', 'Medium', 'High', 'Critical') DEFAULT 'Low'
);

-- 11. ATTACK_SIMULATION Table
CREATE TABLE Attack_Simulation (
    simulation_id INT PRIMARY KEY AUTO_INCREMENT,
    target_base_id INT NOT NULL, -- Target (Enemy Base)
    base_id INT NOT NULL,        -- Conducting Base (Friendly)
    simulation_type VARCHAR(50),
    simulation_date DATE,
    readiness_level VARCHAR(50),
    recommendation TEXT,
    FOREIGN KEY (target_base_id) REFERENCES Enemy_Base(enemy_base_id) ON DELETE CASCADE,
    FOREIGN KEY (base_id) REFERENCES Bases(base_id) ON DELETE CASCADE
);

-- 12. READINESS_REPORT Table
CREATE TABLE Readiness_Report (
    assessment_id INT PRIMARY KEY AUTO_INCREMENT,
    base_id INT NOT NULL,
    assessment_date DATE NOT NULL,
    overall_readiness ENUM('Fully Ready', 'Ready with Support', 'Vulnerable', 'Critical'),
    personnel_score DECIMAL(4, 2),
    resource_score DECIMAL(4, 2),
    missile_score DECIMAL(4, 2),
    strategic_recomm TEXT,
    FOREIGN KEY (base_id) REFERENCES Bases(base_id) ON DELETE CASCADE
);

-- 13. LOGISTICS_TRANSFER Table
CREATE TABLE Logistics_Transfer (
    transfer_id INT PRIMARY KEY AUTO_INCREMENT,
    source_base_id INT NOT NULL,
    transfer_base_id INT NOT NULL, -- Destination Base
    resource_id INT NOT NULL,
    quantity_transferred DECIMAL(15, 2) NOT NULL,
    start_date DATE,
    status ENUM('Pending', 'In Transit', 'Completed', 'Cancelled') DEFAULT 'Pending',
    FOREIGN KEY (source_base_id) REFERENCES Bases(base_id),
    FOREIGN KEY (transfer_base_id) REFERENCES Bases(base_id),
    FOREIGN KEY (resource_id) REFERENCES Resource(resource_id)
);

-- Index on Coordinates for distance-based calculations
CREATE INDEX idx_base_coords ON Bases(latitude, longitude);
CREATE INDEX idx_enemy_coords ON Enemy_Base(latitude, longitude);

-- Index on Foreign Keys to speed up joins for readiness reports and simulations
CREATE INDEX idx_personnel_base ON Personnel(base_id);
CREATE INDEX idx_simulation_base ON Attack_Simulation(base_id);
CREATE INDEX idx_transfer_source ON Logistics_Transfer(source_base_id);

-- Index on Threat level for quick filtering of high-risk targets
CREATE INDEX idx_enemy_threat ON Enemy_Base(threat_level);