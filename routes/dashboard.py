from flask import Blueprint, jsonify
from db import get_db
from utils import haversine

dashboard_bp = Blueprint('dashboard_bp', __name__)


@dashboard_bp.route('/api/dashboard/summary')
def dashboard_summary():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Base counts
    cursor.execute("SELECT COUNT(*) as total FROM Bases")
    total = cursor.fetchone()['total']
    cursor.execute("SELECT status, COUNT(*) as c FROM Bases GROUP BY status")
    status_counts = {r['status']: r['c'] for r in cursor.fetchall()}

    cursor.execute("SELECT force_type, COUNT(*) as c FROM Bases GROUP BY force_type")
    force_counts = {r['force_type']: r['c'] for r in cursor.fetchall()}

    # Enemy counts
    cursor.execute("SELECT COUNT(*) as total FROM Enemy_Base")
    enemy_total = cursor.fetchone()['total']
    cursor.execute("SELECT threat_level, COUNT(*) as c FROM Enemy_Base GROUP BY threat_level")
    threat_counts = {r['threat_level']: r['c'] for r in cursor.fetchall()}

    # Missiles and vehicles totals
    cursor.execute("SELECT COALESCE(SUM(quantity), 0) as total FROM Missile_Inventory")
    total_missiles = int(cursor.fetchone()['total'])
    cursor.execute("SELECT COALESCE(SUM(quantity), 0) as total FROM Vehicle_Inventory")
    total_vehicles = int(cursor.fetchone()['total'])

    # Readiness breakdown (latest per base)
    cursor.execute("""
        SELECT overall_readiness, COUNT(*) as c
        FROM (
            SELECT rr.overall_readiness
            FROM Readiness_Report rr
            INNER JOIN (SELECT base_id, MAX(assessment_date) AS latest FROM Readiness_Report GROUP BY base_id) lr
            ON rr.base_id = lr.base_id AND rr.assessment_date = lr.latest
        ) sub
        GROUP BY overall_readiness
    """)
    readiness = {r['overall_readiness']: r['c'] for r in cursor.fetchall()}

    # Active missions: In Transit transfers + recent simulations (last 30 days)
    cursor.execute("SELECT COUNT(*) as c FROM Logistics_Transfer WHERE status = 'In Transit'")
    in_transit = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) as c FROM Attack_Simulation WHERE simulation_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)")
    recent_sims = cursor.fetchone()['c']
    active_missions = in_transit + recent_sims

    # Mission readiness % = active bases / total
    active_bases = status_counts.get('Active', 0)
    readiness_pct = round((active_bases / total * 100) if total > 0 else 0, 1)

    # Base pins for mini mapm
    cursor.execute("SELECT base_name, latitude, longitude, force_type FROM Bases")
    pins = [{'name': r['base_name'], 'lat': float(r['latitude']), 'lng': float(r['longitude']),
             'force_type': r['force_type']} for r in cursor.fetchall()]

    cursor.close()
    conn.close()

    return jsonify({
        'total_bases': total,
        'active': status_counts.get('Active', 0),
        'maintenance': status_counts.get('Under Maintenance', 0),
        'inactive': status_counts.get('Inactive', 0),
        'air_force': force_counts.get('Air Force', 0),
        'naval': force_counts.get('Naval', 0),
        'enemy_bases': enemy_total,
        'critical_threats': threat_counts.get('Critical', 0),
        'high_threats': threat_counts.get('High', 0),
        'total_missiles': total_missiles,
        'total_vehicles': total_vehicles,
        'readiness_fr': readiness.get('Fully Ready', 0),
        'readiness_rs': readiness.get('Ready with Support', 0),
        'readiness_vul': readiness.get('Vulnerable', 0),
        'readiness_crit': readiness.get('Critical', 0),
        'active_missions': active_missions,
        'in_transit_transfers': in_transit,
        'recent_simulations': recent_sims,
        'readiness_pct': readiness_pct,
        'base_pins': pins
    })


@dashboard_bp.route('/api/dashboard/alerts')
def dashboard_alerts():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    alerts = []

    # Depleted missiles (<5)
    cursor.execute("""
        SELECT b.base_name, mt.missile_name, mi.quantity
        FROM Missile_Inventory mi
        JOIN Bases b ON mi.base_id = b.base_id
        JOIN Missile_Type mt ON mi.missile_type_id = mt.missile_type_id
        WHERE mi.quantity < 5
        ORDER BY mi.quantity ASC
    """)
    for r in cursor.fetchall():
        alerts.append({
            'severity': 'critical',
            'title': f"{r['base_name']}: {r['missile_name']} depleted",
            'detail': f"Only {r['quantity']} remaining"
        })

    # Low fuel vehicles (<30%)
    cursor.execute("""
        SELECT vt.vehicle_name, vs.fuel_level
        FROM Vehicle_Status vs
        JOIN Vehicle_Type vt ON vs.vehicle_type_id = vt.vehicle_type_id
        WHERE vs.fuel_level < 30
        ORDER BY vs.fuel_level ASC
    """)
    for r in cursor.fetchall():
        alerts.append({
            'severity': 'warning',
            'title': f"{r['vehicle_name']}: Low fuel",
            'detail': f"Fuel at {float(r['fuel_level'])}%"
        })

    # Critical / Low resources
    cursor.execute("""
        SELECT b.base_name, r.resource_type, ri.status, ri.quantity
        FROM Resource_Inventory ri
        JOIN Bases b ON ri.base_id = b.base_id
        JOIN Resource r ON ri.resource_id = r.resource_id
        WHERE ri.status IN ('Critical', 'Low')
        ORDER BY FIELD(ri.status, 'Critical', 'Low')
    """)
    for r in cursor.fetchall():
        sev = 'critical' if r['status'] == 'Critical' else 'warning'
        alerts.append({
            'severity': sev,
            'title': f"{r['base_name']}: {r['resource_type']} {r['status'].lower()}",
            'detail': f"Quantity: {float(r['quantity']):.0f} — Immediate resupply {'required' if sev == 'critical' else 'recommended'}"
        })

    # Vulnerable/Critical readiness
    cursor.execute("""
        SELECT b.base_name, rr.overall_readiness
        FROM Readiness_Report rr
        JOIN Bases b ON rr.base_id = b.base_id
        INNER JOIN (SELECT base_id, MAX(assessment_date) AS latest FROM Readiness_Report GROUP BY base_id) lr
        ON rr.base_id = lr.base_id AND rr.assessment_date = lr.latest
        WHERE rr.overall_readiness IN ('Vulnerable', 'Critical')
    """)
    for r in cursor.fetchall():
        alerts.append({
            'severity': 'critical' if r['overall_readiness'] == 'Critical' else 'warning',
            'title': f"{r['base_name']}: {r['overall_readiness']}",
            'detail': 'Base readiness below acceptable levels'
        })

    cursor.close()
    conn.close()
    return jsonify(alerts)


@dashboard_bp.route('/api/dashboard/transfers')
def dashboard_transfers():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.base_name as source, d.base_name as dest, r.resource_type as resource,
               lt.quantity_transferred as quantity, lt.status, lt.start_date
        FROM Logistics_Transfer lt
        JOIN Bases s ON lt.source_base_id = s.base_id
        JOIN Bases d ON lt.transfer_base_id = d.base_id
        JOIN Resource r ON lt.resource_id = r.resource_id
        ORDER BY lt.start_date DESC LIMIT 12
    """)
    transfers = cursor.fetchall()
    for t in transfers:
        t['quantity'] = float(t['quantity'])
        t['date'] = str(t['start_date'])
    cursor.close()
    conn.close()
    return jsonify(transfers)


@dashboard_bp.route('/api/dashboard/personnel')
def dashboard_personnel():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(avail_status = 'On Duty')    AS on_duty,
            SUM(avail_status = 'In Mission') AS in_mission,
            SUM(avail_status = 'Off Duty')   AS off_duty,
            SUM(avail_status = 'On Leave')   AS on_leave
        FROM Personnel
    """)
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    total = int(row['total'] or 0)
    on_duty = int(row['on_duty'] or 0)
    in_mission = int(row['in_mission'] or 0)
    off_duty = int(row['off_duty'] or 0)
    on_leave = int(row['on_leave'] or 0)
    readiness_pct = round(((on_duty + in_mission) / total * 100) if total > 0 else 0, 1)

    return jsonify({
        'total': total,
        'on_duty': on_duty,
        'in_mission': in_mission,
        'off_duty': off_duty,
        'on_leave': on_leave,
        'readiness_pct': readiness_pct
    })


@dashboard_bp.route('/api/dashboard/capability')
def dashboard_capability():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Missile readiness: operational qty / total qty
    cursor.execute("""
        SELECT
            COALESCE(SUM(CASE WHEN LOWER(operational_status) LIKE '%operational%' THEN quantity ELSE 0 END), 0) AS op_qty,
            COALESCE(SUM(quantity), 0) AS total_qty
        FROM Missile_Inventory
    """)
    r = cursor.fetchone()
    missile_r = round(float(r['op_qty']) / max(float(r['total_qty']), 1) * 100, 1)

    # Vehicle readiness
    cursor.execute("""
        SELECT
            COALESCE(SUM(CASE WHEN LOWER(operational_status) LIKE '%operational%' THEN quantity ELSE 0 END), 0) AS op_qty,
            COALESCE(SUM(quantity), 0) AS total_qty
        FROM Vehicle_Inventory
    """)
    r = cursor.fetchone()
    vehicle_r = round(float(r['op_qty']) / max(float(r['total_qty']), 1) * 100, 1)

    # Personnel readiness: (on_duty + in_mission) / total
    cursor.execute("""
        SELECT COUNT(*) AS total,
               SUM(avail_status IN ('On Duty', 'In Mission')) AS active
        FROM Personnel
    """)
    r = cursor.fetchone()
    total_p = float(r['total'] or 1)
    personnel_r = round(float(r['active'] or 0) / total_p * 100, 1)

    # Resource score: map status to a score
    cursor.execute("""
        SELECT
            AVG(CASE status
                WHEN 'Optimal'   THEN 100
                WHEN 'Adequate'  THEN 75
                WHEN 'Low'       THEN 40
                WHEN 'Critical'  THEN 10
                ELSE 60
            END) AS avg_score
        FROM Resource_Inventory
    """)
    r = cursor.fetchone()
    resource_r = round(float(r['avg_score'] or 60), 1)

    overall = round((missile_r + vehicle_r + personnel_r + resource_r) / 4, 1)

    cursor.close()
    conn.close()
    return jsonify({
        'missile_readiness': missile_r,
        'vehicle_readiness': vehicle_r,
        'personnel_readiness': personnel_r,
        'resource_readiness': resource_r,
        'overall': overall
    })


@dashboard_bp.route('/api/dashboard/top-threats')
def dashboard_top_threats():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Enemy_Base WHERE threat_level IN ('Critical', 'High') ORDER BY FIELD(threat_level, 'Critical', 'High')")
    enemies = cursor.fetchall()
    cursor.execute("SELECT base_id, base_name, latitude, longitude FROM Bases")
    bases = cursor.fetchall()

    threats = []
    for eb in enemies:
        # Find nearest friendly base
        nearest = None
        min_dist = float('inf')
        for b in bases:
            d = haversine(float(eb['latitude']), float(eb['longitude']),
                          float(b['latitude']), float(b['longitude']))
            if d < min_dist:
                min_dist = d
                nearest = b

        threats.append({
            'enemy_base_id': eb['enemy_base_id'],
            'name': eb['enemy_base_name'],
            'threat_level': eb['threat_level'],
            'nearest_base': nearest['base_name'] if nearest else 'N/A',
            'nearest_base_id': nearest['base_id'] if nearest else None,
            'distance_km': int(min_dist)
        })

    # Sort: Critical first, then by distance ascending (closest = most dangerous)
    order = {'Critical': 0, 'High': 1}
    threats.sort(key=lambda x: (order.get(x['threat_level'], 2), x['distance_km']))
    threats = threats[:3]

    cursor.close()
    conn.close()
    return jsonify(threats)


@dashboard_bp.route('/api/dashboard/vulnerability')
def dashboard_vulnerability():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    issues = []

    # Bases with very few on-duty personnel (<5)
    cursor.execute("""
        SELECT b.base_name, b.base_id,
               COUNT(p.service_id) AS on_duty_count
        FROM Bases b
        LEFT JOIN Personnel p ON b.base_id = p.base_id AND p.avail_status IN ('On Duty', 'In Mission')
        GROUP BY b.base_id, b.base_name
        HAVING on_duty_count < 5
    """)
    for r in cursor.fetchall():
        issues.append({
            'base_name': r['base_name'],
            'base_id': r['base_id'],
            'issue': f"Only {r['on_duty_count']} active personnel"
        })

    # Inactive bases
    cursor.execute("SELECT base_id, base_name FROM Bases WHERE status = 'Inactive'")
    for r in cursor.fetchall():
        issues.append({
            'base_name': r['base_name'],
            'base_id': r['base_id'],
            'issue': 'Base is Inactive'
        })

    # Bases with 0 operational vehicles
    cursor.execute("""
        SELECT b.base_name, b.base_id
        FROM Bases b
        WHERE NOT EXISTS (
            SELECT 1 FROM Vehicle_Inventory vi
            WHERE vi.base_id = b.base_id
              AND LOWER(vi.operational_status) LIKE '%operational%'
              AND vi.quantity > 0
        )
    """)
    for r in cursor.fetchall():
        # Avoid duplicate entries
        if not any(i['base_id'] == r['base_id'] and 'vehicle' in i['issue'].lower() for i in issues):
            issues.append({
                'base_name': r['base_name'],
                'base_id': r['base_id'],
                'issue': 'No operational vehicles'
            })

    # Readiness summary counts
    cursor.execute("""
        SELECT overall_readiness, COUNT(*) as c
        FROM (
            SELECT rr.overall_readiness
            FROM Readiness_Report rr
            INNER JOIN (SELECT base_id, MAX(assessment_date) AS latest FROM Readiness_Report GROUP BY base_id) lr
            ON rr.base_id = lr.base_id AND rr.assessment_date = lr.latest
        ) sub
        GROUP BY overall_readiness
    """)
    readiness = {r['overall_readiness']: r['c'] for r in cursor.fetchall()}

    cursor.close()
    conn.close()
    return jsonify({
        'issues': issues[:6],  # cap at 6 most critical
        'mission_ready': readiness.get('Fully Ready', 0),
        'need_support': readiness.get('Ready with Support', 0),
        'vulnerable': readiness.get('Vulnerable', 0),
        'critical': readiness.get('Critical', 0)
    })


@dashboard_bp.route('/api/dashboard/most-exposed')
def dashboard_most_exposed():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Get all bases with their latest readiness
    cursor.execute("""
        SELECT b.base_id, b.base_name, b.status, b.latitude, b.longitude,
               rr.overall_readiness, rr.personnel_score
        FROM Bases b
        LEFT JOIN (
            SELECT r1.*
            FROM Readiness_Report r1
            INNER JOIN (
                SELECT base_id, MAX(assessment_date) AS latest
                FROM Readiness_Report GROUP BY base_id
            ) lr ON r1.base_id = lr.base_id AND r1.assessment_date = lr.latest
        ) rr ON b.base_id = rr.base_id
    """)
    bases = cursor.fetchall()

    cursor.execute("SELECT * FROM Enemy_Base WHERE threat_level IN ('Critical', 'High')")
    enemies = cursor.fetchall()

    cursor.close()
    conn.close()

    if not bases:
        return jsonify(None)

    # Score each base: nearby high-threat enemies within 400km + low readiness
    readiness_order = {'Critical': 0, 'Vulnerable': 1, 'Ready with Support': 2, 'Fully Ready': 3, None: 1}
    best = None
    best_score = -1

    for b in bases:
        nearby = sum(
            1 for e in enemies
            if haversine(float(b['latitude']), float(b['longitude']),
                         float(e['latitude']), float(e['longitude'])) < 400
        )
        # Higher nearby count + worse readiness = higher risk score
        readiness_penalty = 3 - readiness_order.get(b['overall_readiness'], 1)
        score = nearby * 2 + readiness_penalty
        if score > best_score:
            best_score = score
            best = {**b, 'nearby_threat_count': nearby}

    if not best:
        return jsonify(None)

    return jsonify({
        'base_id': best['base_id'],
        'base_name': best['base_name'],
        'status': best['status'],
        'overall_readiness': best['overall_readiness'],
        'personnel_score': float(best['personnel_score']) if best['personnel_score'] else None,
        'nearby_threats': best['nearby_threat_count']
    })
