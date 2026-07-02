# 15 Application SQL Queries & Relational Algebra Explanations
**Project:** STRATOS Command & Control System

The following 15 SQL queries are extracted **directly from the operational source code** located in the `routes/*.py` directory. These queries power the live backend features and demonstrate standard Relational Algebraic logic mathematically.

---

### Query 1 (`routes/missions.py` : analyze_mission)
```sql
SELECT mt.missile_name, mt.max_range, mi.quantity, mi.operational_status,
       CASE WHEN mt.max_range >= 500 THEN 'SUFFICIENT' ELSE 'INSUFFICIENT' END AS range_status
FROM Missile_Inventory mi
JOIN Missile_Type mt ON mi.missile_type_id = mt.missile_type_id
WHERE mi.base_id = 1 AND mi.quantity > 0
ORDER BY mt.max_range DESC;
```
* **Relational Algebraic Operations:** Inner Join ($\bowtie$), Selection ($\sigma$), Projection ($\pi$), Sorting ($\tau$).
* **Explanation:** Evaluates Range Capability during Mission Analysis. It joins a base's specific physical missile inventory with the blueprint types to evaluate if they have the theoretical geographic range to strike a given target over 500km away.

### Query 2 (`routes/missions.py` : analyze_mission)
```sql
SELECT overall_readiness, personnel_score, resource_score, missile_score, assessment_date
FROM Readiness_Report 
WHERE base_id = 1
ORDER BY assessment_date DESC LIMIT 1;
```
* **Relational Algebraic Operations:** Projection ($\pi$), Selection ($\sigma$), Sorting ($\tau$).
* **Explanation:** Retrieves the single absolute most recent historical diagnostic footprint (readiness scores) for a given friendly facility before launching a strike package.

### Query 3 (`routes/missions.py` : analyze_mission)
```sql
SELECT role, COUNT(*) as count
FROM Personnel 
WHERE base_id = 1 AND avail_status IN ('On Duty', 'In Mission')
GROUP BY role;
```
* **Relational Algebraic Operations:** Selection ($\sigma$), Grouping/Aggregation ($\gamma$).
* **Explanation:** Generates the "Personnel Availability" matrix for mission planning. It identifies active personnel grouped specifically by category (e.g. how many active Pilots vs Support Staff exist right now).

### Query 4 (`routes/missions.py` : analyze_mission)
```sql
SELECT vt.vehicle_name, vt.category, vi.quantity, vi.operational_status
FROM Vehicle_Inventory vi
JOIN Vehicle_Type vt ON vi.vehicle_type_id = vt.vehicle_type_id
WHERE vi.base_id = 1 AND vi.quantity > 0
ORDER BY vi.quantity DESC;
```
* **Relational Algebraic Operations:** Inner Join ($\bowtie$), Selection ($\sigma$), Projection ($\pi$).
* **Explanation:** Assesses "Vehicle Readiness". Joins raw inventory records back to the static physics templates (`Vehicle_Type`) so the commanding officer can evaluate deployable operational aircraft.

### Query 5 (`routes/missions.py` : analyze_mission)
```sql
SELECT ri.quantity, ri.status, r.unit_of_measurement
FROM Resource_Inventory ri
JOIN Resource r ON ri.resource_id = r.resource_id
WHERE ri.base_id = 1 AND LOWER(r.resource_type) LIKE '%fuel%'
LIMIT 1;
```
* **Relational Algebraic Operations:** Inner Join ($\bowtie$), Selection ($\sigma$ mapping to `LIKE`), Projection ($\pi$).
* **Explanation:** Dynamically locates internal Jet Fuel capacities at a specific staging base to verify there are >56,000 liters available for a proposed combat flight path.

### Query 6 (`routes/missiles.py` : update_missile_inventory)
```sql
INSERT INTO Missile_Inventory (base_id, missile_type_id, quantity, operational_status)
VALUES (1, 14, 50, 'Fully Operational')
ON DUPLICATE KEY UPDATE 
    quantity = VALUES(quantity),
    operational_status = VALUES(operational_status);
```
* **Relational Algebraic Operations:** Conditional Union/Update (Modification of Set Union $\cup$).
* **Explanation:** When a logistics truck arrives and unloads new payloads, this algorithm checks if the base already officially stocks that missile type. If yes, it updates the ledger count. If it's a completely new weapon type for that base, it inserts a brand new inventory row seamlessly.

### Query 7 (`routes/missions.py` : best_base)
```sql
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
```
* **Relational Algebraic Operations:** Left Outer Join ($\leftouterjoin$), Inner Join ($\bowtie$), Correlated Derived Table Joins, Grouping ($\gamma$).
* **Explanation:** A mathematically dense intelligence query that evaluates the most optimal facility globally to attack from. It crosses Readiness reports with live physical payloads seamlessly, outputting bases sorted algorithmically for tactical supremacy.

### Query 8 (`routes/dashboard.py` : dashboard_issues)
```sql
SELECT b.base_name, b.base_id
FROM Bases b
WHERE NOT EXISTS (
    SELECT 1 FROM Vehicle_Inventory vi
    WHERE vi.base_id = b.base_id
      AND LOWER(vi.operational_status) LIKE '%operational%'
      AND vi.quantity > 0
);
```
* **Relational Algebraic Operations:** Relational Division / Anti-Join equivalent (implemented via Nested `NOT EXISTS`), Projection ($\pi$).
* **Explanation:** This query actively scans the network to identify vulnerable "Empty Garrisons" or bases that possess zero operational deployed vehicles. It acts as an Anti-Join filtering out any base that successfully satisfies the existence of combat-ready payloads.

### Query 9 (`routes/dashboard.py` : dashboard_data)
```sql
SELECT status, COUNT(*) as c 
FROM Bases 
GROUP BY status;
```
* **Relational Algebraic Operations:** Grouping/Aggregation ($\gamma$).
* **Explanation:** Drives the overarching Executive Dashboard widgets, breaking down entire global military networks by their Active vs Maintained statuses.

### Query 10 (`routes/dashboard.py` : dashboard_data)
```sql
SELECT COALESCE(SUM(quantity), 0) as total 
FROM Missile_Inventory;
```
* **Relational Algebraic Operations:** Aggregation ($\mathcal{F}_{SUM}$).
* **Explanation:** Powers the high-level dashboard "Global Payload Array" integer widget, collapsing across the whole planetary system to yield a single total sum scalar.

### Query 11 (`routes/dashboard.py` : dashboard_data)
```sql
SELECT rr.overall_readiness, COUNT(*) as c
FROM Readiness_Report rr
INNER JOIN (SELECT base_id, MAX(assessment_date) AS latest FROM Readiness_Report GROUP BY base_id) lr
ON rr.base_id = lr.base_id AND rr.assessment_date = lr.latest
GROUP BY rr.overall_readiness;
```
* **Relational Algebraic Operations:** Inner Join ($\bowtie$) Correlated Subquery Joins.
* **Explanation:** Builds the "Global Threat Ledger" chart on the dashboard. Generates a histogram counting overall readiness status groups using only the most modern assessment metric mathematically valid per location.

### Query 12 (`routes/dashboard.py` : dashboard_capability)
```sql
SELECT
    b.base_name,
    COALESCE(SUM(CASE WHEN LOWER(mi.operational_status) LIKE '%operational%' THEN mi.quantity ELSE 0 END), 0) AS op_qty,
    COALESCE(SUM(mi.quantity), 1) AS total_qty
FROM Missile_Inventory mi
JOIN Bases b ON mi.base_id = b.base_id
GROUP BY b.base_id, b.base_name;
```
* **Relational Algebraic Operations:** Inner Join ($\bowtie$), Conditional Aggregation ($\gamma$ with embedded Selection $\sigma$).
* **Explanation:** Calculates the true Missile Readiness fraction on a *per-base level*. Instead of just counting raw rows, it conditionally sums only the missiles matching the 'operational' status and aggregates it against the total payload per facility directly within a single database pass.

### Query 13 (`routes/bases.py` : get_base)
```sql
SELECT b.base_id, b.base_name, b.force_type, b.operational_capability,
       (SELECT COUNT(*) FROM Personnel p WHERE p.base_id = b.base_id) as personnel_count,
       (SELECT COUNT(*) FROM Missile_Inventory mi WHERE mi.base_id = b.base_id AND mi.quantity < 5) as depleted_missiles
FROM Bases b 
ORDER BY b.base_name;
```
* **Relational Algebraic Operations:** Multiple Subqueries within SELECT equivalent to projection ($\pi$) extensions of dependent aggregations ($\gamma$).
* **Explanation:** Fetches the comprehensive operational dossier table of friendly facilities. Correlated subqueries dynamically generate adjacent metrics like local personnel counts and depleted payload inventories.

### Query 14 (`routes/missions.py` : analyze_mission alternative)
```sql
SELECT sim.simulation_id, sim.simulation_type, b.base_name AS striking_from, eb.enemy_base_name AS target, sim.readiness_level AS result, sim.recommendation
FROM Attack_Simulation sim
JOIN Bases b ON sim.base_id = b.base_id
JOIN Enemy_Base eb ON sim.target_base_id = eb.enemy_base_id
WHERE eb.enemy_base_id = 2;
```
* **Relational Algebraic Operations:** Consecutive Inner Joins over a Many-to-Many entity ($\bowtie$), Selection ($\sigma$).
* **Explanation:** Discovers all conceptual intelligence initiatives mapping explicitly over a targeted physical target space through the `Target_Enemy` junction table.

### Query 15 (`routes/missiles.py` : base_missile_inventory)
```sql
SELECT mt.missile_type_id, mt.missile_name, mt.category, mt.max_range, mt.speed, mi.quantity, mi.operational_status
FROM Missile_Inventory mi
JOIN Missile_Type mt ON mi.missile_type_id = mt.missile_type_id
WHERE mi.base_id = 1
ORDER BY mt.category, mt.missile_name;
```
* **Relational Algebraic Operations:** Inner Join ($\bowtie$), Projection ($\pi$), Routing ($\tau$), Selection ($\sigma$).
* **Explanation:** Operates the local armory ledger interface for a designated base, filtering the master planetary payload stockpile strictly to local deployment lines.
