
SELECT mt.missile_name, mt.max_range, mi.quantity, mi.operational_status,
       CASE WHEN mt.max_range >= 500 THEN 'SUFFICIENT' ELSE 'INSUFFICIENT' END AS range_status
FROM Missile_Inventory mi
JOIN Missile_Type mt ON mi.missile_type_id = mt.missile_type_id
WHERE mi.base_id = 1 AND mi.quantity > 0
ORDER BY mt.max_range DESC;


SELECT overall_readiness, personnel_score, resource_score, missile_score, assessment_date
FROM Readiness_Report 
WHERE base_id = 1
ORDER BY assessment_date DESC LIMIT 1;


SELECT role, COUNT(*) as count
FROM Personnel 
WHERE base_id = 2 AND avail_status IN ('On Duty', 'In Mission')
GROUP BY role;


SELECT vt.vehicle_name, vt.category, vi.quantity, vi.operational_status
FROM Vehicle_Inventory vi
JOIN Vehicle_Type vt ON vi.vehicle_type_id = vt.vehicle_type_id
WHERE vi.base_id = 1 AND vi.quantity > 0
ORDER BY vi.quantity DESC;


SELECT ri.quantity, ri.status, r.unit_of_measurement
FROM Resource_Inventory ri
JOIN Resource r ON ri.resource_id = r.resource_id
WHERE ri.base_id = 1 AND LOWER(r.resource_type) LIKE '%fuel%'
LIMIT 1;



INSERT INTO Missile_Inventory (base_id, missile_type_id, quantity, operational_status)
VALUES (1, 14, 50, 'Fully Operational')
ON DUPLICATE KEY UPDATE 
    quantity = VALUES(quantity),
    operational_status = VALUES(operational_status);



SELECT b.base_id, b.base_name, b.latitude, b.longitude,
       rr.overall_readiness, rr.missile_score,
       COUNT(DISTINCT mi.missile_type_id) as missile_variety,
       COALESCE(SUM(mi.quantity), 0) as total_missiles
FROM Bases b
LEFT JOIN Readiness_Report rr ON rr.base_id = b.base_id
INNER JOIN (SELECT base_id, MAX(assessment_date) AS latest FROM Readiness_Report GROUP BY base_id) lr
    ON rr.base_id = lr.base_id AND rr.assessment_date = lr.latest
JOIN Missile_Inventory mi ON b.base_id = mi.base_id
JOIN Missile_Type mt ON mi.missile_type_id = mt.missile_type_id
WHERE b.status = 'Active' AND mi.quantity > 0
GROUP BY b.base_id, rr.overall_readiness, rr.missile_score
ORDER BY rr.missile_score DESC, total_missiles DESC;


SELECT b.base_name, b.base_id
FROM Bases b
WHERE NOT EXISTS (
    SELECT 1 FROM Vehicle_Inventory vi
    WHERE vi.base_id = b.base_id
      AND LOWER(vi.operational_status) LIKE '%operational%'
      AND vi.quantity > 0
);



SELECT DISTINCT B.base_name
FROM Bases B
LEFT JOIN Vehicle_Inventory VI ON B.base_id = VI.base_id
LEFT JOIN Vehicle_Type VT ON VI.vehicle_type_id = VT.vehicle_type_id
LEFT JOIN Missile_Inventory MI ON B.base_id = MI.base_id
LEFT JOIN Missile_Type MT ON MI.missile_type_id = MT.missile_type_id
GROUP BY B.base_id, B.base_name
HAVING 
(
    SUM(CASE WHEN VT.category = 'Fighter' THEN 1 ELSE 0 END) > 0
    AND
    SUM(CASE WHEN MT.category = 'Ballistic' THEN 1 ELSE 0 END) > 0
)
OR
(
    SUM(CASE WHEN VT.category = 'Destroyer' THEN 1 ELSE 0 END) > 0
    AND
    SUM(CASE WHEN MT.category = 'Cruise' THEN 1 ELSE 0 END) > 0
);


SELECT 
    B.base_name,
    E.enemy_base_name,
    E.threat_level,
    (
        6371 * ACOS(
            COS(RADIANS(B.latitude)) *
            COS(RADIANS(E.latitude)) *
            COS(RADIANS(E.longitude) - RADIANS(B.longitude)) +
            SIN(RADIANS(B.latitude)) *
            SIN(RADIANS(E.latitude))
        )
    ) AS distance_km
FROM Bases B
CROSS JOIN Enemy_Base E
WHERE E.threat_level = 'Critical'
ORDER BY distance_km ASC
LIMIT 5;




SELECT rr.overall_readiness, COUNT(*) as c
FROM Readiness_Report rr
INNER JOIN (SELECT base_id, MAX(assessment_date) AS latest FROM Readiness_Report GROUP BY base_id) lr
ON rr.base_id = lr.base_id AND rr.assessment_date = lr.latest
GROUP BY rr.overall_readiness;
SELECT COALESCE(SUM(quantity), 0) as total 
FROM Missile_Inventory;

SELECT
    b.base_name,
    COALESCE(SUM(CASE WHEN LOWER(mi.operational_status) LIKE '%operational%' THEN mi.quantity ELSE 0 END), 0) AS op_qty,
    COALESCE(SUM(mi.quantity), 0) AS total_qty
FROM Missile_Inventory mi
JOIN Bases b ON mi.base_id = b.base_id
GROUP BY b.base_id, b.base_name;


SELECT b.base_id, b.base_name, b.force_type, b.operational_capability,
       (SELECT COUNT(*) FROM Personnel p WHERE p.base_id = b.base_id) as personnel_count,
       (SELECT COUNT(*) FROM Missile_Inventory mi WHERE mi.base_id = b.base_id AND mi.quantity < 5) as depleted_missiles
FROM Bases b 
ORDER BY b.base_name;


SELECT sim.simulation_id, sim.simulation_type, b.base_name AS striking_from, eb.enemy_base_name AS target, sim.readiness_level AS result, sim.recommendation
FROM Attack_Simulation sim
JOIN Bases b ON sim.base_id = b.base_id
JOIN Enemy_Base eb ON sim.target_base_id = eb.enemy_base_id
WHERE eb.enemy_base_id = 2;


    SELECT mt.missile_type_id, mt.missile_name, mt.category, mt.max_range, mt.speed, mi.quantity, mi.operational_status
    FROM Missile_Inventory mi
    JOIN Missile_Type mt ON mi.missile_type_id = mt.missile_type_id
    WHERE mi.base_id = 1
    ORDER BY mt.category, mt.missile_name;
