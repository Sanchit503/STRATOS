from flask import Blueprint, jsonify, request
from db import get_db

missiles_bp = Blueprint('missiles_bp', __name__)

@missiles_bp.route('/api/base/<int:base_id>/missiles')
def get_base_missiles(base_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT mt.missile_type_id, mt.missile_name, mt.category,
               mt.max_range, mt.speed, mi.quantity
        FROM Missile_Inventory mi
        JOIN Missile_Type mt ON mi.missile_type_id = mt.missile_type_id
        WHERE mi.base_id = %s AND mi.quantity > 0
        ORDER BY mt.max_range DESC
    """, (base_id,))
    missiles = cursor.fetchall()
    for m in missiles:
        m['max_range'] = float(m['max_range'])
        m['speed'] = float(m['speed'])
    cursor.close()
    conn.close()
    return jsonify(missiles)

@missiles_bp.route('/api/missile-types')
def get_missile_types():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT missile_type_id, missile_name, category, max_range, speed FROM Missile_Type ORDER BY category, missile_name")
    types = cursor.fetchall()
    for t in types:
        t['max_range'] = float(t['max_range'])
        if t['speed'] is not None:
            t['speed'] = float(t['speed'])
    cursor.close()
    conn.close()
    return jsonify(types)

@missiles_bp.route('/api/base/<int:base_id>/inventory/missile', methods=['POST'])
def update_missile_inventory(base_id):
    data = request.json
    missile_type_id = data.get('missile_type_id')
    quantity = data.get('quantity')
    status = data.get('operational_status')

    if not all(v is not None for v in [missile_type_id, quantity, status]):
        return jsonify({'error': 'Missing required fields: missile_type_id, quantity, operational_status'}), 400

    # Quantity validation
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Quantity must be a valid number'}), 400
    if quantity <= 0:
        return jsonify({'error': 'Quantity must be a positive number'}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Validate base exists
        cursor.execute("SELECT base_id FROM Bases WHERE base_id = %s", (base_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Base not found'}), 404

        # Validate missile type exists
        cursor.execute("SELECT missile_type_id FROM Missile_Type WHERE missile_type_id = %s", (missile_type_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Missile type not found'}), 404

        cursor.execute("""
            INSERT INTO Missile_Inventory (base_id, missile_type_id, quantity, operational_status)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                quantity = VALUES(quantity),
                operational_status = VALUES(operational_status)
        """, (base_id, missile_type_id, quantity, status))
        conn.commit()
        return jsonify({'success': True, 'message': 'Inventory updated successfully.'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@missiles_bp.route('/api/inventory/missiles/all')
def all_missile_inventory():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.base_id, b.base_name, mt.missile_type_id, mt.missile_name, mt.category, mt.max_range, mi.quantity, mi.operational_status
        FROM Missile_Inventory mi
        JOIN Bases b ON mi.base_id = b.base_id
        JOIN Missile_Type mt ON mi.missile_type_id = mt.missile_type_id
        ORDER BY mi.quantity ASC
    """)
    data = cursor.fetchall()
    for row in data:
        row['max_range'] = float(row['max_range'])
    cursor.close()
    conn.close()
    return jsonify(data)
