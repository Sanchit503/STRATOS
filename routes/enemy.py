from flask import Blueprint, jsonify, request
from db import get_db
from utils import haversine

enemy_bp = Blueprint('enemy_bp', __name__)

@enemy_bp.route('/api/enemy-bases', methods=['GET'])
def get_enemy_bases():
    """Return all enemy bases."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT enemy_base_id, enemy_base_name, latitude, longitude, threat_level
        FROM Enemy_Base
    """)
    bases = cursor.fetchall()
    for b in bases:
        b['latitude'] = float(b['latitude'])
        b['longitude'] = float(b['longitude'])
    cursor.close()
    conn.close()
    return jsonify(bases)

@enemy_bp.route('/api/enemy-bases', methods=['POST'])
def create_enemy_base():
    data = request.json

    # Required field validation
    name = (data.get('enemy_base_name') or '').strip()
    if not name:
        return jsonify({'error': 'Enemy base name is required'}), 400

    # Threat level validation
    threat_level = data.get('threat_level', 'Low')
    if threat_level not in ('Low', 'Medium', 'High', 'Critical'):
        return jsonify({'error': 'Threat level must be Low, Medium, High, or Critical'}), 400

    # Coordinate validation
    try:
        lat = float(data['latitude'])
        lng = float(data['longitude'])
    except (KeyError, TypeError, ValueError):
        return jsonify({'error': 'Valid latitude and longitude are required'}), 400

    if not (-90 <= lat <= 90):
        return jsonify({'error': 'Latitude must be between -90 and 90'}), 400
    if not (-180 <= lng <= 180):
        return jsonify({'error': 'Longitude must be between -180 and 180'}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Duplicate name check
        cursor.execute("SELECT enemy_base_id FROM Enemy_Base WHERE enemy_base_name = %s", (name,))
        if cursor.fetchone():
            return jsonify({'error': f'An enemy base named "{name}" already exists'}), 400

        cursor.execute("""
            INSERT INTO Enemy_Base (enemy_base_name, latitude, longitude, threat_level)
            VALUES (%s, %s, %s, %s)
        """, (name, lat, lng, threat_level))
        conn.commit()
        return jsonify({'success': True, 'enemy_base_id': cursor.lastrowid})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@enemy_bp.route('/api/enemy-base/<int:enemy_id>', methods=['PUT'])
def update_enemy_base(enemy_id):
    data = request.json

    # Required field validation
    name = (data.get('enemy_base_name') or '').strip()
    if not name:
        return jsonify({'error': 'Enemy base name is required'}), 400

    threat_level = data.get('threat_level', 'Low')
    if threat_level not in ('Low', 'Medium', 'High', 'Critical'):
        return jsonify({'error': 'Threat level must be Low, Medium, High, or Critical'}), 400

    try:
        lat = float(data['latitude'])
        lng = float(data['longitude'])
    except (KeyError, TypeError, ValueError):
        return jsonify({'error': 'Valid latitude and longitude are required'}), 400

    if not (-90 <= lat <= 90):
        return jsonify({'error': 'Latitude must be between -90 and 90'}), 400
    if not (-180 <= lng <= 180):
        return jsonify({'error': 'Longitude must be between -180 and 180'}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check enemy base exists
        cursor.execute("SELECT enemy_base_id FROM Enemy_Base WHERE enemy_base_id = %s", (enemy_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Enemy base not found'}), 404

        # Duplicate name check (exclude self)
        cursor.execute("SELECT enemy_base_id FROM Enemy_Base WHERE enemy_base_name = %s AND enemy_base_id != %s", (name, enemy_id))
        if cursor.fetchone():
            return jsonify({'error': f'An enemy base named "{name}" already exists'}), 400

        cursor.execute("""
            UPDATE Enemy_Base SET enemy_base_name=%s, latitude=%s, longitude=%s, threat_level=%s
            WHERE enemy_base_id=%s
        """, (name, lat, lng, threat_level, enemy_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@enemy_bp.route('/api/enemy-base/<int:enemy_id>', methods=['DELETE'])
def delete_enemy_base(enemy_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT enemy_base_id FROM Enemy_Base WHERE enemy_base_id = %s", (enemy_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Enemy base not found'}), 404

        # Check for related simulations
        cursor.execute("SELECT COUNT(*) as c FROM Attack_Simulation WHERE target_base_id = %s", (enemy_id,))
        sims = cursor.fetchone()['c']

        force = request.args.get('force', 'false').lower() == 'true'
        if not force and sims > 0:
            return jsonify({
                'error': 'Cannot delete enemy base with existing simulations',
                'detail': f'{sims} attack simulation(s) reference this target',
                'confirm_required': True
            }), 400

        cursor.execute("DELETE FROM Attack_Simulation WHERE target_base_id = %s", (enemy_id,))
        cursor.execute("DELETE FROM Enemy_Base WHERE enemy_base_id = %s", (enemy_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@enemy_bp.route('/api/enemy-base/<int:enemy_id>/reachable')
def get_reachable_bases(enemy_id):
    """Which friendly bases can strike this enemy base, with recommended strike force."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Get enemy location
    cursor.execute("SELECT * FROM Enemy_Base WHERE enemy_base_id = %s", (enemy_id,))
    enemy = cursor.fetchone()
    if not enemy:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Enemy base not found'}), 404
    enemy['latitude'] = float(enemy['latitude'])
    enemy['longitude'] = float(enemy['longitude'])

    # Get all friendly bases with their missile inventories
    cursor.execute("""
        SELECT b.base_id, b.base_name, b.force_type, b.latitude, b.longitude,
               b.status, b.strength,
               mt.missile_name, mt.max_range, mt.category as missile_category,
               mt.speed as missile_speed, mi.quantity
        FROM Bases b
        JOIN Missile_Inventory mi ON b.base_id = mi.base_id
        JOIN Missile_Type mt ON mi.missile_type_id = mt.missile_type_id
        WHERE b.status = 'Active' AND mi.quantity > 0
    """)
    all_entries = cursor.fetchall()

    # Group by base and filter by distance
    reachable = {}
    for entry in all_entries:
        entry['latitude'] = float(entry['latitude'])
        entry['longitude'] = float(entry['longitude'])
        entry['max_range'] = float(entry['max_range'])
        entry['missile_speed'] = float(entry['missile_speed'])

        dist = haversine(entry['latitude'], entry['longitude'],
                         enemy['latitude'], enemy['longitude'])

        if dist <= entry['max_range']:
            bid = entry['base_id']
            if bid not in reachable:
                reachable[bid] = {
                    'base_id': bid,
                    'base_name': entry['base_name'],
                    'force_type': entry['force_type'],
                    'latitude': entry['latitude'],
                    'longitude': entry['longitude'],
                    'distance_km': dist,
                    'available_missiles': [],
                    'strength': entry['strength']
                }
            reachable[bid]['available_missiles'].append({
                'missile_name': entry['missile_name'],
                'category': entry['missile_category'],
                'max_range': entry['max_range'],
                'speed': entry['missile_speed'],
                'quantity': entry['quantity']
            })

    # Get vehicle info for each reachable base
    for bid in reachable:
        cursor.execute("""
            SELECT vt.vehicle_name, vt.category, vt.role, vi.quantity, vi.operational_status
            FROM Vehicle_Inventory vi
            JOIN Vehicle_Type vt ON vi.vehicle_type_id = vt.vehicle_type_id
            WHERE vi.base_id = %s AND vi.operational_status IN ('Fully Operational', 'Partially Operational')
        """, (bid,))
        reachable[bid]['vehicles'] = cursor.fetchall()

        # Personnel count
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN avail_status = 'On Duty' THEN 1 ELSE 0 END) as on_duty
            FROM Personnel WHERE base_id = %s
        """, (bid,))
        p = cursor.fetchone()
        reachable[bid]['personnel_total'] = p['total'] or 0
        reachable[bid]['personnel_on_duty'] = p['on_duty'] or 0

    # Sort by distance
    result = sorted(reachable.values(), key=lambda x: x['distance_km'])

    # Build recommendation
    recommendation = ""
    if result:
        best = result[0]
        total_missiles = sum(m['quantity'] for m in best['available_missiles'])
        recommendation = (
            f"Primary strike from {best['base_name']} ({int(best['distance_km'])} km). "
            f"{total_missiles} missiles available. "
            f"{'Multi-base coordinated strike recommended.' if len(result) > 1 else 'Single-base strike feasible.'}"
        )

    cursor.close()
    conn.close()

    return jsonify({
        'enemy_base': {
            'enemy_base_id': enemy['enemy_base_id'],
            'enemy_base_name': enemy['enemy_base_name'],
            'latitude': enemy['latitude'],
            'longitude': enemy['longitude'],
            'threat_level': enemy['threat_level']
        },
        'reachable_bases': result,
        'recommendation': recommendation
    })
