from flask import Blueprint, request, jsonify
from db import get_db

operations_bp = Blueprint('operations_bp', __name__)


# ══════════════════════════════════════════════════════════════════════
#  PERSONNEL — Full CRUD
# ══════════════════════════════════════════════════════════════════════

@operations_bp.route('/api/personnel')
def get_personnel():
    """Get all personnel, optionally filtered by base_id."""
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    base_id = request.args.get('base_id')
    if base_id:
        cur.execute("""
            SELECT p.*, b.base_name
            FROM Personnel p
            JOIN Bases b ON b.base_id = p.base_id
            WHERE p.base_id = %s
            ORDER BY p.role, p.name
        """, (base_id,))
    else:
        cur.execute("""
            SELECT p.*, b.base_name
            FROM Personnel p
            JOIN Bases b ON b.base_id = p.base_id
            ORDER BY b.base_name, p.role, p.name
        """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(rows)


@operations_bp.route('/api/personnel', methods=['POST'])
def add_personnel():
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Personnel (base_id, role, name, avail_status)
        VALUES (%s, %s, %s, %s)
    """, (d['base_id'], d['role'], d['name'], d.get('avail_status', 'On Duty')))
    conn.commit()
    pid = cur.lastrowid
    cur.close(); conn.close()
    return jsonify({"service_id": pid, "msg": "Personnel added"})


@operations_bp.route('/api/personnel/<int:sid>', methods=['PUT'])
def update_personnel(sid):
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE Personnel
        SET base_id=%s, role=%s, name=%s, avail_status=%s
        WHERE service_id=%s
    """, (d['base_id'], d['role'], d['name'], d['avail_status'], sid))
    conn.commit()
    cur.close(); conn.close()
    return jsonify({"msg": "Personnel updated"})


@operations_bp.route('/api/personnel/<int:sid>', methods=['DELETE'])
def delete_personnel(sid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM Personnel WHERE service_id=%s", (sid,))
    conn.commit()
    cur.close(); conn.close()
    return jsonify({"msg": "Personnel deleted"})


# ══════════════════════════════════════════════════════════════════════
#  RESOURCES — resource types + inventory CRUD
# ══════════════════════════════════════════════════════════════════════

@operations_bp.route('/api/resources')
def get_resources():
    """Get all resource types."""
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Resource ORDER BY resource_type")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(rows)


@operations_bp.route('/api/resource-inventory')
def get_resource_inventory():
    """Get resource inventory, optionally filtered by base_id."""
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    base_id = request.args.get('base_id')
    if base_id:
        cur.execute("""
            SELECT ri.inventory_id, ri.base_id, b.base_name,
                   ri.resource_id, r.resource_type, r.unit_of_measurement,
                   ri.quantity, ri.status
            FROM Resource_Inventory ri
            JOIN Bases b ON b.base_id = ri.base_id
            JOIN Resource r ON r.resource_id = ri.resource_id
            WHERE ri.base_id = %s
            ORDER BY r.resource_type
        """, (base_id,))
    else:
        cur.execute("""
            SELECT ri.inventory_id, ri.base_id, b.base_name,
                   ri.resource_id, r.resource_type, r.unit_of_measurement,
                   ri.quantity, ri.status
            FROM Resource_Inventory ri
            JOIN Bases b ON b.base_id = ri.base_id
            JOIN Resource r ON r.resource_id = ri.resource_id
            ORDER BY b.base_name, r.resource_type
        """)
    rows = cur.fetchall()
    # Convert Decimal to float for JSON
    for row in rows:
        if row.get('quantity') is not None:
            row['quantity'] = float(row['quantity'])
    cur.close(); conn.close()
    return jsonify(rows)


@operations_bp.route('/api/resource-inventory', methods=['POST'])
def add_resource_inventory():
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    # Use INSERT ... ON DUPLICATE KEY UPDATE for upsert
    cur.execute("""
        INSERT INTO Resource_Inventory (base_id, resource_id, quantity, status)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE quantity = %s, status = %s
    """, (d['base_id'], d['resource_id'], d['quantity'], d.get('status', 'Adequate'),
          d['quantity'], d.get('status', 'Adequate')))
    conn.commit()
    iid = cur.lastrowid
    cur.close(); conn.close()
    return jsonify({"inventory_id": iid, "msg": "Resource inventory updated"})


@operations_bp.route('/api/resource-inventory/<int:inv_id>', methods=['PUT'])
def update_resource_inventory(inv_id):
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE Resource_Inventory
        SET quantity=%s, status=%s
        WHERE inventory_id=%s
    """, (d['quantity'], d['status'], inv_id))
    conn.commit()
    cur.close(); conn.close()
    return jsonify({"msg": "Resource inventory updated"})


@operations_bp.route('/api/resource-inventory/<int:inv_id>', methods=['DELETE'])
def delete_resource_inventory(inv_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM Resource_Inventory WHERE inventory_id=%s", (inv_id,))
    conn.commit()
    cur.close(); conn.close()
    return jsonify({"msg": "Resource inventory deleted"})


# ══════════════════════════════════════════════════════════════════════
#  LOGISTICS TRANSFERS — Full CRUD
# ══════════════════════════════════════════════════════════════════════

@operations_bp.route('/api/transfers')
def get_transfers():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT lt.transfer_id,
               lt.source_base_id, bs.base_name AS source_base,
               lt.transfer_base_id, bd.base_name AS dest_base,
               lt.resource_id, r.resource_type, r.unit_of_measurement,
               lt.quantity_transferred, lt.start_date, lt.status
        FROM Logistics_Transfer lt
        JOIN Bases bs ON bs.base_id = lt.source_base_id
        JOIN Bases bd ON bd.base_id = lt.transfer_base_id
        JOIN Resource r ON r.resource_id = lt.resource_id
        ORDER BY lt.transfer_id DESC
    """)
    rows = cur.fetchall()
    for row in rows:
        if row.get('quantity_transferred') is not None:
            row['quantity_transferred'] = float(row['quantity_transferred'])
        if row.get('start_date') is not None:
            row['start_date'] = str(row['start_date'])
    cur.close(); conn.close()
    return jsonify(rows)


@operations_bp.route('/api/transfers', methods=['POST'])
def add_transfer():
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Logistics_Transfer
            (source_base_id, transfer_base_id, resource_id,
             quantity_transferred, start_date, status)
        VALUES (%s, %s, %s, %s, CURDATE(), %s)
    """, (d['source_base_id'], d['transfer_base_id'], d['resource_id'],
          d['quantity_transferred'], d.get('status', 'Pending')))
    conn.commit()
    tid = cur.lastrowid
    cur.close(); conn.close()
    return jsonify({"transfer_id": tid, "msg": "Transfer created"})


@operations_bp.route('/api/transfers/<int:tid>', methods=['PUT'])
def update_transfer(tid):
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE Logistics_Transfer
        SET status=%s
        WHERE transfer_id=%s
    """, (d['status'], tid))
    conn.commit()
    cur.close(); conn.close()
    return jsonify({"msg": "Transfer status updated"})


@operations_bp.route('/api/transfers/<int:tid>', methods=['DELETE'])
def delete_transfer(tid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM Logistics_Transfer WHERE transfer_id=%s", (tid,))
    conn.commit()
    cur.close(); conn.close()
    return jsonify({"msg": "Transfer deleted"})
