from flask import Blueprint, jsonify, request
from db import get_db
from utils import haversine

missions_bp = Blueprint('missions_bp', __name__)


def _run_analysis(friendly_base_id: int, enemy_base_id: int) -> dict:
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    # ── Coordinates ──────────────────────────────────────────────────────
    cur.execute("SELECT base_name, latitude, longitude FROM Bases WHERE base_id = %s", (friendly_base_id,))
    fb = cur.fetchone()
    cur.execute("SELECT enemy_base_name, latitude, longitude, threat_level FROM Enemy_Base WHERE enemy_base_id = %s", (enemy_base_id,))
    eb = cur.fetchone()

    if not fb or not eb:
        cur.close(); conn.close()
        return {'error': 'Invalid base IDs'}

    distance_km = haversine(float(fb['latitude']), float(fb['longitude']),
                            float(eb['latitude']), float(eb['longitude']))

    checks = []

    # ── CHECK 1: Range Capability ────────────────────────────────────────
    cur.execute("""
        SELECT mt.missile_name, mt.max_range, mi.quantity, mi.operational_status,
               CASE WHEN mt.max_range >= %s THEN 'SUFFICIENT' ELSE 'INSUFFICIENT' END AS range_status
        FROM Missile_Inventory mi
        JOIN Missile_Type mt ON mi.missile_type_id = mt.missile_type_id
        WHERE mi.base_id = %s AND mi.quantity > 0
        ORDER BY mt.max_range DESC
    """, (distance_km, friendly_base_id))
    all_missiles = cur.fetchall()
    capable = [m for m in all_missiles if m['range_status'] == 'SUFFICIENT']
    for m in all_missiles:
        m['max_range'] = float(m['max_range'])
    checks.append({
        'id': 1, 'name': 'Range Capability',
        'status': 'PASS' if capable else 'FAIL',
        'result': f"{len(capable)} missile type(s) can reach target ({int(distance_km)} km)",
        'items': [{'label': m['missile_name'], 'sub': f"Range: {int(m['max_range'])} km", 'ok': m['range_status'] == 'SUFFICIENT'} for m in all_missiles[:6]]
    })

    # ── CHECK 2: Missile Availability ────────────────────────────────────
    cur.execute("""
        SELECT mt.missile_name, mi.quantity
        FROM Missile_Inventory mi
        JOIN Missile_Type mt ON mi.missile_type_id = mt.missile_type_id
        WHERE mi.base_id = %s AND mt.max_range >= %s
          AND LOWER(mi.operational_status) LIKE '%%operational%%' AND mi.quantity > 0
    """, (friendly_base_id, distance_km))
    avail = cur.fetchall()
    total_avail = sum(int(m['quantity']) for m in avail)
    checks.append({
        'id': 2, 'name': 'Missile Availability',
        'status': 'PASS' if total_avail >= 4 else ('WARNING' if total_avail > 0 else 'FAIL'),
        'result': f"{total_avail} operational in-range missiles available",
        'items': [{'label': m['missile_name'], 'sub': f"{m['quantity']} units", 'ok': int(m['quantity']) >= 4} for m in avail[:6]]
    })

    # ── CHECK 3: Base Readiness ──────────────────────────────────────────
    cur.execute("""
        SELECT overall_readiness, personnel_score, resource_score, missile_score, assessment_date
        FROM Readiness_Report WHERE base_id = %s
        ORDER BY assessment_date DESC LIMIT 1
    """, (friendly_base_id,))
    rr = cur.fetchone()
    ready_order = {'Fully Ready': 0, 'Ready with Support': 1, 'Vulnerable': 2, 'Critical': 3}
    r_status = 'PASS' if rr and ready_order.get(rr['overall_readiness'], 3) <= 1 else ('WARNING' if rr else 'FAIL')
    checks.append({
        'id': 3, 'name': 'Base Readiness',
        'status': r_status,
        'result': rr['overall_readiness'] if rr else 'No readiness data',
        'items': [] if not rr else [
            {'label': 'Overall Readiness', 'sub': rr['overall_readiness'], 'ok': ready_order.get(rr['overall_readiness'], 3) <= 1},
            {'label': 'Personnel Score', 'sub': f"{float(rr['personnel_score'] or 0):.1f}", 'ok': float(rr['personnel_score'] or 0) >= 70},
            {'label': 'Resource Score', 'sub': f"{float(rr['resource_score'] or 0):.1f}", 'ok': float(rr['resource_score'] or 0) >= 70},
            {'label': 'Missile Score', 'sub': f"{float(rr['missile_score'] or 0):.1f}", 'ok': float(rr['missile_score'] or 0) >= 70},
        ]
    })

    # ── CHECK 4: Personnel Availability ─────────────────────────────────
    cur.execute("""
        SELECT role, COUNT(*) as count
        FROM Personnel WHERE base_id = %s AND avail_status IN ('On Duty', 'In Mission')
        GROUP BY role
    """, (friendly_base_id,))
    personnel = {r['role']: r['count'] for r in cur.fetchall()}
    pilots = personnel.get('Pilot', 0)
    support = sum(v for k, v in personnel.items() if k != 'Pilot')
    checks.append({
        'id': 4, 'name': 'Personnel Availability',
        'status': 'PASS' if pilots >= 2 and support >= 5 else ('WARNING' if pilots >= 1 else 'FAIL'),
        'result': f"{pilots} pilots · {support} support staff on duty",
        'items': [{'label': role, 'sub': f"{cnt} active", 'ok': cnt >= (2 if role == 'Pilot' else 3)} for role, cnt in personnel.items()]
    })

    # ── CHECK 5: Vehicle Readiness ───────────────────────────────────────
    cur.execute("""
        SELECT vt.vehicle_name, vt.category, vi.quantity, vi.operational_status
        FROM Vehicle_Inventory vi
        JOIN Vehicle_Type vt ON vi.vehicle_type_id = vt.vehicle_type_id
        WHERE vi.base_id = %s AND vi.quantity > 0
        ORDER BY vi.quantity DESC
    """, (friendly_base_id,))
    vehicles = cur.fetchall()
    op_vehicles = [v for v in vehicles if 'operational' in (v['operational_status'] or '').lower()]
    checks.append({
        'id': 5, 'name': 'Vehicle Readiness',
        'status': 'PASS' if op_vehicles else ('WARNING' if vehicles else 'FAIL'),
        'result': f"{len(op_vehicles)} operational vehicle type(s)",
        'items': [{'label': v['vehicle_name'], 'sub': f"{v['quantity']} units · {v['operational_status']}", 'ok': 'operational' in (v['operational_status'] or '').lower()} for v in vehicles[:6]]
    })

    # ── CHECK 6: Fuel Availability ───────────────────────────────────────
    cur.execute("""
        SELECT ri.quantity, ri.status, r.unit_of_measurement
        FROM Resource_Inventory ri
        JOIN Resource r ON ri.resource_id = r.resource_id
        WHERE ri.base_id = %s AND LOWER(r.resource_type) LIKE '%%fuel%%'
        LIMIT 1
    """, (friendly_base_id,))
    fuel = cur.fetchone()
    fuel_qty = float(fuel['quantity']) if fuel else 0
    fuel_required = 56400  # ~6 aircraft round trip
    checks.append({
        'id': 6, 'name': 'Fuel Availability',
        'status': 'PASS' if fuel_qty >= fuel_required else ('WARNING' if fuel_qty > 0 else 'FAIL'),
        'result': f"{fuel_qty:,.0f} {fuel['unit_of_measurement'] if fuel else 'units'} available (need ~{fuel_required:,})",
        'items': [{'label': 'Jet Fuel Stock', 'sub': f"{fuel_qty:,.0f} available", 'ok': fuel_qty >= fuel_required}] if fuel else [{'label': 'No fuel data', 'sub': '', 'ok': False}]
    })

    # ── CHECK 7: Risk Assessment ─────────────────────────────────────────
    cur.execute("SELECT enemy_base_id, enemy_base_name, latitude, longitude, threat_level FROM Enemy_Base WHERE enemy_base_id != %s", (enemy_base_id,))
    other_enemies = cur.fetchall()
    nearby = []
    for e in other_enemies:
        d = haversine(float(eb['latitude']), float(eb['longitude']), float(e['latitude']), float(e['longitude']))
        if d <= 200 and e['threat_level'] in ('Critical', 'High'):
            nearby.append({**e, 'distance_km': int(d)})
    nearby.sort(key=lambda x: x['distance_km'])

    checks.append({
        'id': 7, 'name': 'Risk Assessment',
        'status': 'WARNING' if nearby else 'PASS',
        'result': f"{len(nearby)} high-threat enemy base(s) within 200km of target" if nearby else "No nearby high-threat enemy bases detected",
        'items': [{'label': n['enemy_base_name'], 'sub': f"{n['distance_km']} km · {n['threat_level']}", 'ok': False} for n in nearby[:4]]
    })

    cur.close(); conn.close()

    # ── Final Decision ───────────────────────────────────────────────────
    failed = [c for c in checks if c['status'] == 'FAIL']
    warnings = [c for c in checks if c['status'] == 'WARNING']
    if not failed:
        decision = 'MISSION GO'
        decision_color = 'green'
    elif len(failed) <= 2:
        decision = 'MISSION POSSIBLE WITH SUPPORT'
        decision_color = 'yellow'
    else:
        decision = 'MISSION NO-GO'
        decision_color = 'red'

    # Recommended strike package from available assets
    pkg_missiles = avail[:2] if avail else []
    pkg_vehicles = op_vehicles[:3] if op_vehicles else []
    package = []
    for m in pkg_missiles:
        package.append(f"4x {m['missile_name']}")
    for v in pkg_vehicles:
        package.append(f"2x {v['vehicle_name']} ({v['category'] or 'support'})")
    if fuel_qty >= fuel_required:
        package.append(f"~{fuel_required:,} L jet fuel")

    return {
        'friendly_base': fb['base_name'],
        'enemy_base': eb['enemy_base_name'],
        'threat_level': eb['threat_level'],
        'distance_km': int(distance_km),
        'checks': checks,
        'decision': decision,
        'decision_color': decision_color,
        'failed_count': len(failed),
        'warning_count': len(warnings),
        'strike_package': package
    }


@missions_bp.route('/api/mission/analyze', methods=['POST'])
def analyze_mission():
    data = request.get_json()
    result = _run_analysis(int(data['friendly_base_id']), int(data['enemy_base_id']))
    return jsonify(result)


@missions_bp.route('/api/mission/best-base')
def best_base():
    enemy_base_id = request.args.get('enemy_base_id', type=int)
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT latitude, longitude FROM Enemy_Base WHERE enemy_base_id = %s", (enemy_base_id,))
    eb = cur.fetchone()
    if not eb:
        cur.close(); conn.close()
        return jsonify([])

    cur.execute("""
        SELECT b.base_id, b.base_name, b.latitude, b.longitude,
               rr.overall_readiness, rr.missile_score,
               COUNT(DISTINCT mi.missile_type_id) as missile_variety,
               COALESCE(SUM(mi.quantity), 0) as total_missiles
        FROM Bases b
        LEFT JOIN Readiness_Report rr ON rr.base_id = b.base_id
        LEFT JOIN (SELECT base_id, MAX(assessment_date) AS latest FROM Readiness_Report GROUP BY base_id) lr
            ON rr.base_id = lr.base_id AND rr.assessment_date = lr.latest
        JOIN Missile_Inventory mi ON b.base_id = mi.base_id
        JOIN Missile_Type mt ON mi.missile_type_id = mt.missile_type_id
        WHERE b.status = 'Active' AND mi.quantity > 0
          AND (lr.base_id IS NOT NULL OR rr.base_id IS NULL)
        GROUP BY b.base_id, rr.overall_readiness, rr.missile_score
        ORDER BY rr.missile_score DESC, total_missiles DESC
    """)
    bases = cur.fetchall()
    cur.close(); conn.close()

    results = []
    for b in bases:
        d = haversine(float(b['latitude']), float(b['longitude']),
                      float(eb['latitude']), float(eb['longitude']))
        results.append({**b, 'distance_km': int(d), 'total_missiles': int(b['total_missiles']),
                        'missile_score': float(b['missile_score'] or 0)})

    results.sort(key=lambda x: (-x['missile_score'], -x['total_missiles']))
    return jsonify(results[:3])


@missions_bp.route('/api/mission/save', methods=['POST'])
def save_mission():
    data = request.get_json()

    # Required field validation
    friendly_id = data.get('friendly_base_id')
    enemy_id = data.get('enemy_base_id')

    if not friendly_id or not enemy_id:
        return jsonify({'error': 'Both friendly and enemy base IDs are required'}), 400

    try:
        friendly_id = int(friendly_id)
        enemy_id = int(enemy_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Base IDs must be valid numbers'}), 400

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    try:
        # Validate friendly base exists
        cur.execute("SELECT base_id FROM Bases WHERE base_id = %s", (friendly_id,))
        if not cur.fetchone():
            return jsonify({'error': 'Friendly base not found'}), 404

        # Validate enemy base exists
        cur.execute("SELECT enemy_base_id FROM Enemy_Base WHERE enemy_base_id = %s", (enemy_id,))
        if not cur.fetchone():
            return jsonify({'error': 'Enemy base not found'}), 404

        cur.execute("""
            INSERT INTO Attack_Simulation
                (target_base_id, base_id, simulation_type, simulation_date, readiness_level, recommendation)
            VALUES (%s, %s, 'Precision Strike', CURDATE(), %s, %s)
        """, (enemy_id, friendly_id,
              data.get('decision', 'Unknown'),
              data.get('recommendation', '')))
        conn.commit()
        sim_id = cur.lastrowid
        return jsonify({'ok': True, 'simulation_id': sim_id})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()
