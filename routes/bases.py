from flask import Blueprint, jsonify, request
from db import get_db

bases_bp = Blueprint('bases_bp', __name__)

@bases_bp.route('/api/bases')
def get_bases():
    """Return all friendly bases with latest readiness."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.base_id, b.base_name, b.force_type, b.operational_capability,
               b.latitude, b.longitude, b.status, b.strength,
               r.overall_readiness, r.personnel_score, r.resource_score,
               r.missile_score, r.strategic_recomm,
               (SELECT COUNT(*) FROM Missile_Inventory mi WHERE mi.base_id = b.base_id AND mi.quantity < 5) as depleted_missiles
        FROM Bases b
        LEFT JOIN (
            SELECT rr.*
            FROM Readiness_Report rr
            INNER JOIN (
                SELECT base_id, MAX(assessment_date) AS latest
                FROM Readiness_Report
                GROUP BY base_id
            ) latest_rr ON rr.base_id = latest_rr.base_id
                        AND rr.assessment_date = latest_rr.latest
        ) r ON b.base_id = r.base_id
    """)
    bases = cursor.fetchall()
    for b in bases:
        b['latitude'] = float(b['latitude'])
        b['longitude'] = float(b['longitude'])
        if b['personnel_score']:
            b['personnel_score'] = float(b['personnel_score'])
        if b['resource_score']:
            b['resource_score'] = float(b['resource_score'])
        if b['missile_score']:
            b['missile_score'] = float(b['missile_score'])
    cursor.close()
    conn.close()
    return jsonify(bases)

@bases_bp.route('/api/bases/full')
def get_bases_full():
    """Bases with personnel/vehicle counts for the management table."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.*,
               (SELECT COUNT(*) FROM Personnel p WHERE p.base_id = b.base_id) as personnel_count,
               (SELECT COALESCE(SUM(vi.quantity),0) FROM Vehicle_Inventory vi WHERE vi.base_id = b.base_id) as vehicle_count,
               (SELECT rr.overall_readiness FROM Readiness_Report rr
                WHERE rr.base_id = b.base_id ORDER BY rr.assessment_date DESC LIMIT 1) as overall_readiness
        FROM Bases b ORDER BY b.base_name
    """)
    bases = cursor.fetchall()
    for b in bases:
        b['latitude'] = float(b['latitude'])
        b['longitude'] = float(b['longitude'])
        b['vehicle_count'] = int(b['vehicle_count'])
    cursor.close()
    conn.close()
    return jsonify(bases)

@bases_bp.route('/api/bases', methods=['POST'])
def create_base():
    data = request.json

    # Required field validation
    name = (data.get('base_name') or '').strip()
    if not name:
        return jsonify({'error': 'Base name is required'}), 400

    # Force type validation
    force_type = data.get('force_type')
    if force_type not in ('Air Force', 'Naval'):
        return jsonify({'error': 'Force type must be "Air Force" or "Naval"'}), 400

    # Status validation
    status = data.get('status', 'Active')
    if status not in ('Active', 'Under Maintenance', 'Inactive'):
        return jsonify({'error': 'Invalid status. Must be Active, Under Maintenance, or Inactive'}), 400

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

    # Strength validation
    try:
        strength = int(data.get('strength', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'Strength must be a valid number'}), 400
    if strength < 0:
        return jsonify({'error': 'Strength cannot be negative'}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Duplicate name check
        cursor.execute("SELECT base_id FROM Bases WHERE base_name = %s", (name,))
        if cursor.fetchone():
            return jsonify({'error': f'A base named "{name}" already exists'}), 400

        cursor.execute("""
            INSERT INTO Bases (base_name, force_type, operational_capability, latitude, longitude, status, strength)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, force_type, data.get('operational_capability'),
              lat, lng, status, strength))
        conn.commit()
        return jsonify({'success': True, 'base_id': cursor.lastrowid})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@bases_bp.route('/api/base/<int:base_id>/details')
def get_base_details(base_id):
    """Return detailed info about a friendly base."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Bases WHERE base_id = %s", (base_id,))
    base = cursor.fetchone()
    if not base:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Base not found'}), 404
    base['latitude'] = float(base['latitude'])
    base['longitude'] = float(base['longitude'])

    cursor.execute("""
        SELECT role, avail_status, COUNT(*) as count
        FROM Personnel WHERE base_id = %s
        GROUP BY role, avail_status
    """, (base_id,))
    personnel = cursor.fetchall()

    cursor.execute("""
        SELECT vt.vehicle_name, vt.category, vt.role as vehicle_role,
               vi.quantity, vi.operational_status
        FROM Vehicle_Inventory vi
        JOIN Vehicle_Type vt ON vi.vehicle_type_id = vt.vehicle_type_id
        WHERE vi.base_id = %s
    """, (base_id,))
    vehicles = cursor.fetchall()

    cursor.execute("""
        SELECT mt.missile_type_id, mt.missile_name, mt.category, mt.max_range,
               mi.quantity, mi.operational_status
        FROM Missile_Inventory mi
        JOIN Missile_Type mt ON mi.missile_type_id = mt.missile_type_id
        WHERE mi.base_id = %s
    """, (base_id,))
    missiles = cursor.fetchall()
    for m in missiles:
        m['max_range'] = float(m['max_range'])

    cursor.execute("""
        SELECT * FROM Readiness_Report
        WHERE base_id = %s ORDER BY assessment_date DESC LIMIT 1
    """, (base_id,))
    readiness = cursor.fetchone()
    if readiness:
        readiness['personnel_score'] = float(readiness['personnel_score']) if readiness['personnel_score'] else None
        readiness['resource_score'] = float(readiness['resource_score']) if readiness['resource_score'] else None
        readiness['missile_score'] = float(readiness['missile_score']) if readiness['missile_score'] else None
        readiness['assessment_date'] = str(readiness['assessment_date'])

    # Compute actual counts for the sidebar stats
    cursor.execute("""
        SELECT COUNT(*) as total FROM Personnel WHERE base_id = %s
    """, (base_id,))
    personnel_count = cursor.fetchone()['total'] or 0

    cursor.execute("""
        SELECT COALESCE(SUM(mi.quantity), 0) as total
        FROM Missile_Inventory mi WHERE mi.base_id = %s
    """, (base_id,))
    missile_count = cursor.fetchone()['total'] or 0

    cursor.execute("""
        SELECT COALESCE(SUM(vi.quantity), 0) as total
        FROM Vehicle_Inventory vi WHERE vi.base_id = %s
    """, (base_id,))
    vehicle_count = cursor.fetchone()['total'] or 0

    cursor.execute("""
        SELECT COUNT(*) as total
        FROM Resource_Inventory ri WHERE ri.base_id = %s
    """, (base_id,))
    resource_count = cursor.fetchone()['total'] or 0

    cursor.close()
    conn.close()

    return jsonify({
        'base': base,
        'personnel': personnel,
        'vehicles': vehicles,
        'missiles': missiles,
        'readiness': readiness,
        'counts': {
            'personnel': int(personnel_count),
            'missiles': int(missile_count),
            'vehicles': int(vehicle_count),
            'resources': int(resource_count)
        }
    })

@bases_bp.route('/api/base/<int:base_id>', methods=['PUT'])
def update_base(base_id):
    data = request.json

    # Required field validation
    name = (data.get('base_name') or '').strip()
    if not name:
        return jsonify({'error': 'Base name is required'}), 400

    force_type = data.get('force_type')
    if force_type not in ('Air Force', 'Naval'):
        return jsonify({'error': 'Force type must be "Air Force" or "Naval"'}), 400

    status = data.get('status', 'Active')
    if status not in ('Active', 'Under Maintenance', 'Inactive'):
        return jsonify({'error': 'Invalid status'}), 400

    try:
        lat = float(data['latitude'])
        lng = float(data['longitude'])
    except (KeyError, TypeError, ValueError):
        return jsonify({'error': 'Valid latitude and longitude are required'}), 400

    if not (-90 <= lat <= 90):
        return jsonify({'error': 'Latitude must be between -90 and 90'}), 400
    if not (-180 <= lng <= 180):
        return jsonify({'error': 'Longitude must be between -180 and 180'}), 400

    try:
        strength = int(data.get('strength', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'Strength must be a valid number'}), 400
    if strength < 0:
        return jsonify({'error': 'Strength cannot be negative'}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check base exists
        cursor.execute("SELECT base_id FROM Bases WHERE base_id = %s", (base_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Base not found'}), 404

        # Duplicate name check (exclude self)
        cursor.execute("SELECT base_id FROM Bases WHERE base_name = %s AND base_id != %s", (name, base_id))
        if cursor.fetchone():
            return jsonify({'error': f'A base named "{name}" already exists'}), 400

        cursor.execute("""
            UPDATE Bases SET base_name=%s, force_type=%s, operational_capability=%s,
            latitude=%s, longitude=%s, status=%s, strength=%s WHERE base_id=%s
        """, (name, force_type, data.get('operational_capability'),
              lat, lng, status, strength, base_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@bases_bp.route('/api/base/<int:base_id>', methods=['DELETE'])
def delete_base(base_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check base exists
        cursor.execute("SELECT base_id FROM Bases WHERE base_id = %s", (base_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Base not found'}), 404

        # Check for related data that would be lost
        cursor.execute("SELECT COUNT(*) as c FROM Personnel WHERE base_id = %s", (base_id,))
        personnel = cursor.fetchone()['c']
        cursor.execute("SELECT COUNT(*) as c FROM Vehicle_Inventory WHERE base_id = %s", (base_id,))
        vehicles = cursor.fetchone()['c']
        cursor.execute("SELECT COUNT(*) as c FROM Missile_Inventory WHERE base_id = %s", (base_id,))
        missiles = cursor.fetchone()['c']

        force = request.args.get('force', 'false').lower() == 'true'
        if not force and (personnel + vehicles + missiles) > 0:
            return jsonify({
                'error': 'Cannot delete base with existing inventory',
                'detail': f'{personnel} personnel, {vehicles} vehicle entries, {missiles} missile entries would be lost',
                'confirm_required': True
            }), 400

        # Delete related records first, then the base
        cursor.execute("DELETE FROM Readiness_Report WHERE base_id = %s", (base_id,))
        cursor.execute("DELETE FROM Resource_Inventory WHERE base_id = %s", (base_id,))
        cursor.execute("DELETE FROM Missile_Inventory WHERE base_id = %s", (base_id,))
        cursor.execute("DELETE FROM Vehicle_Inventory WHERE base_id = %s", (base_id,))
        cursor.execute("DELETE FROM Personnel WHERE base_id = %s", (base_id,))
        cursor.execute("DELETE FROM Logistics_Transfer WHERE source_base_id = %s OR transfer_base_id = %s", (base_id, base_id))
        cursor.execute("DELETE FROM Attack_Simulation WHERE base_id = %s", (base_id,))
        cursor.execute("DELETE FROM Bases WHERE base_id = %s", (base_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
