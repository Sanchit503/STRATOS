from flask import Blueprint, jsonify, request
from db import get_db

vehicles_bp = Blueprint('vehicles_bp', __name__)

@vehicles_bp.route('/api/vehicle-types')
def get_vehicle_types():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT vehicle_type_id, vehicle_name, category, role FROM Vehicle_Type ORDER BY category, vehicle_name")
    types = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(types)

@vehicles_bp.route('/api/base/<int:base_id>/vehicles')
def get_base_vehicles(base_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT vt.vehicle_type_id, vt.vehicle_name, vt.category, vt.role as vehicle_role,
               vi.quantity, vi.operational_status,
               vs.fuel_level
        FROM Vehicle_Inventory vi
        JOIN Vehicle_Type vt ON vi.vehicle_type_id = vt.vehicle_type_id
        LEFT JOIN Vehicle_Status vs ON vt.vehicle_type_id = vs.vehicle_type_id
        WHERE vi.base_id = %s
    """, (base_id,))
    vehicles = cursor.fetchall()
    for v in vehicles:
        v['fuel_level'] = float(v['fuel_level']) if v['fuel_level'] is not None else None
    cursor.close()
    conn.close()
    return jsonify(vehicles)

@vehicles_bp.route('/api/base/<int:base_id>/inventory/vehicle', methods=['POST'])
def update_vehicle_inventory(base_id):
    data = request.json
    qty = data.get('quantity', 0)

    # Edge case: quantity validation
    if not isinstance(qty, int) or qty <= 0:
        return jsonify({'error': 'Quantity must be a positive number'}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get base force type
        cursor.execute("SELECT force_type FROM Bases WHERE base_id = %s", (base_id,))
        base = cursor.fetchone()
        if not base:
            return jsonify({'error': 'Base not found'}), 404

        # Get vehicle category
        cursor.execute("SELECT category FROM Vehicle_Type WHERE vehicle_type_id = %s", (data['vehicle_type_id'],))
        vtype = cursor.fetchone()
        if not vtype:
            return jsonify({'error': 'Vehicle type not found'}), 404

        # Edge case: force type compatibility
        naval_categories = ['aircraft carrier', 'destroyer', 'frigate', 'corvette', 'patrol vessel', 'attack submarine', 'nuclear submarine']
        air_categories = ['fighter', 'bomber', 'transport', 'surveillance']
        cat_lower = vtype['category'].lower()

        if base['force_type'] == 'Air Force' and cat_lower in naval_categories:
            return jsonify({'error': f'Cannot assign naval vessel ({vtype["category"]}) to an Air Force base'}), 400
        if base['force_type'] == 'Naval' and cat_lower in air_categories:
            return jsonify({'error': f'Cannot assign aircraft ({vtype["category"]}) to a Naval base'}), 400

        cursor.execute("""
            INSERT INTO Vehicle_Inventory (base_id, vehicle_type_id, quantity, operational_status)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                quantity = VALUES(quantity),
                operational_status = VALUES(operational_status)
        """, (base_id, data['vehicle_type_id'], qty, data['operational_status']))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@vehicles_bp.route('/api/inventory/vehicles/all')
def all_vehicle_inventory():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.base_id, b.base_name, vt.vehicle_name, vt.category, vi.quantity, vi.operational_status, vs.fuel_level
        FROM Vehicle_Inventory vi
        JOIN Bases b ON vi.base_id = b.base_id
        JOIN Vehicle_Type vt ON vi.vehicle_type_id = vt.vehicle_type_id
        LEFT JOIN Vehicle_Status vs ON vt.vehicle_type_id = vs.vehicle_type_id
        ORDER BY vi.quantity ASC
    """)
    data = cursor.fetchall()
    for row in data:
        if row['fuel_level'] is not None:
            row['fuel_level'] = float(row['fuel_level'])
    cursor.close()
    conn.close()
    return jsonify(data)

@vehicles_bp.route('/api/vehicles/diagnostics')
def vehicle_diagnostics():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Aggregate vehicle data: Total count, Active count, Maintenance count, Fuel Level, and stationed bases
        cursor.execute("""
            SELECT 
                vt.vehicle_type_id,
                vt.vehicle_name,
                vt.category,
                vt.role,
                IFNULL(SUM(vi.quantity), 0) as total_units,
                IFNULL(SUM(CASE WHEN vi.operational_status IN ('Fully Operational', 'Partially Operational', 'Active') THEN vi.quantity ELSE 0 END), 0) as active_units,
                IFNULL(SUM(CASE WHEN vi.operational_status IN ('Under Maintenance', 'Maintenance', 'Damaged', 'Critical') THEN vi.quantity ELSE 0 END), 0) as maintenance_units,
                vs.fuel_level,
                CONCAT('[', GROUP_CONCAT(DISTINCT CONCAT('{"id":', b.base_id, ',"name":"', b.base_name, '","quantity":', vi.quantity, ',"status":"', vi.operational_status, '","lat":', b.latitude, ',"lng":', b.longitude, '}') SEPARATOR ','), ']') as stationed_bases_json
            FROM Vehicle_Type vt
            LEFT JOIN Vehicle_Inventory vi ON vt.vehicle_type_id = vi.vehicle_type_id
            LEFT JOIN Bases b ON vi.base_id = b.base_id
            LEFT JOIN Vehicle_Status vs ON vt.vehicle_type_id = vs.vehicle_type_id
            GROUP BY vt.vehicle_type_id, vt.vehicle_name, vt.category, vt.role, vs.fuel_level
            ORDER BY vt.category, vt.vehicle_name
        """)
        data = cursor.fetchall()
        
        import json

        # Format decimals and arrays
        for row in data:
            if row['fuel_level'] is not None:
                row['fuel_level'] = float(row['fuel_level'])
            
            # Parse stationed bases JSON
            if row['stationed_bases_json'] and row['stationed_bases_json'] != '[None]':
                try:
                    row['stationed_bases'] = json.loads(row['stationed_bases_json'])
                except:
                    row['stationed_bases'] = []
            else:
                row['stationed_bases'] = []
            
            del row['stationed_bases_json']

            # Determine compatible payload based on category and role (Simulation, since DB might lack direct mapping)
            if row['category'] == 'Aircraft':
                if 'Fighter' in row['role']:
                    row['payload'] = ['AIM-9 Sidewinder', 'AIM-120 AMRAAM']
                elif 'Bomber' in row['role']:
                    row['payload'] = ['AGM-158 JASSM', 'B61 Nuclear Bomb']
                elif 'AWACS' in row['role'] or 'Transport' in row['role']:
                    row['payload'] = ['Defensive Chaff/Flares']
                else:
                    row['payload'] = ['Standard Munitions']
            elif row['category'] == 'Naval Vessel':
                if 'Submarine' in row['role']:
                    row['payload'] = ['UGM-109 Tomahawk', 'Mark 48 Torpedo']
                elif 'Destroyer' in row['role'] or 'Cruiser' in row['role']:
                    row['payload'] = ['BGM-109 Tomahawk', 'RIM-162 ESSM', 'RUM-139 VL-ASROC']
                elif 'Carrier' in row['role']:
                    row['payload'] = ['F-35C Lightning II', 'F/A-18 Super Hornet']
                else:
                    row['payload'] = ['Standard Naval Armament']
            else:
                row['payload'] = []

        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@vehicles_bp.route('/api/vehicles/toggle-status', methods=['POST'])
def toggle_vehicle_status():
    data = request.json

    # ── Strict input validation ────────────────────────────────────────────────
    base_id   = data.get('base_id')
    v_type_id = data.get('vehicle_type_id')
    to_status = data.get('to_status')   # must be 'Under Maintenance' or 'Fully Operational'

    VALID_STATUSES = {'Under Maintenance', 'Fully Operational'}

    if not all([base_id, v_type_id, to_status]):
        return jsonify({'error': 'Missing required parameters: base_id, vehicle_type_id, to_status'}), 400

    if to_status not in VALID_STATUSES:
        return jsonify({'error': f'Invalid target status "{to_status}". Must be one of: {", ".join(VALID_STATUSES)}'}), 400

    # ── Status groups ──────────────────────────────────────────────────────────
    ACTIVE_GROUP = {'Fully Operational', 'Partially Operational', 'Active'}
    MAINT_GROUP  = {'Under Maintenance', 'Maintenance', 'Damaged', 'Critical'}
    target_group = ACTIVE_GROUP if to_status == 'Fully Operational' else MAINT_GROUP

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # ── Verify the inventory row exists with quantity > 0 ──────────────────
        cursor.execute("""
            SELECT vi.quantity, vi.operational_status, b.base_name
            FROM Vehicle_Inventory vi
            JOIN Bases b ON vi.base_id = b.base_id
            WHERE vi.base_id = %s AND vi.vehicle_type_id = %s AND vi.quantity > 0
        """, (base_id, v_type_id))
        row = cursor.fetchone()

        if not row:
            return jsonify({'error': 'No inventory record found for this vehicle at the specified base'}), 404

        current_status   = row['operational_status']
        current_quantity = row['quantity']
        base_name        = row['base_name']

        # ── No-op guard: already in target status group ────────────────────────
        if current_status in target_group:
            label = 'Active' if to_status == 'Fully Operational' else 'Maintenance'
            return jsonify({
                'error': f'Vehicle is already in {label} status at {base_name} (current: {current_status})'
            }), 400

        # ── Quantity validation ────────────────────────────────────────────────
        # If not supplied, default to the full fleet count at this base
        new_qty = data.get('quantity', current_quantity)
        if not isinstance(new_qty, int) or new_qty <= 0:
            return jsonify({'error': 'Quantity must be a positive integer'}), 400
        if new_qty > current_quantity:
            return jsonify({
                'error': f'Quantity {new_qty} exceeds available units ({current_quantity}) at {base_name}'
            }), 400

        # ── Update operational_status AND quantity together ────────────────────
        cursor.execute("""
            UPDATE Vehicle_Inventory
            SET operational_status = %s, quantity = %s
            WHERE base_id = %s AND vehicle_type_id = %s
        """, (to_status, new_qty, base_id, v_type_id))

        conn.commit()
        return jsonify({
            'success': True,
            'msg': f'Status changed from "{current_status}" to "{to_status}" ({new_qty} units) at {base_name}',
            'base_name': base_name,
            'previous_status': current_status,
            'new_status': to_status,
            'quantity': new_qty
        })

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
