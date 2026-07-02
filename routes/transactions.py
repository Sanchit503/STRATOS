"""
STRATOS  |  Task 6 — Database Transactions
All 7 transactions exposed as JSON API endpoints.
Each endpoint returns { before, steps, after, effect } so the UI
can render the live before/after DB state with explanations.
"""
from flask import Blueprint, jsonify
from db import get_db
import threading, time

transactions_bp = Blueprint('transactions_bp', __name__)


# ─── helpers ──────────────────────────────────────────────────────────────
def _rows(cur):
    """Fetch all rows as list-of-dicts, converting Decimal/Date to str."""
    import decimal, datetime
    rows = cur.fetchall()
    clean = []
    for row in rows:
        r = {}
        for k, v in row.items():
            if isinstance(v, decimal.Decimal):
                v = float(v)
            elif isinstance(v, (datetime.date, datetime.datetime)):
                v = str(v)
            r[k] = v
        clean.append(r)
    return clean

def _q(conn, sql, params=None):
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params or ())
    rows = _rows(cur)
    cur.close()
    return rows

def _run(conn, sql, params=None):
    cur = conn.cursor()
    cur.execute(sql, params or ())
    cur.close()

def _read_conn():
    """Connection for read-only queries (autocommit on)."""
    import mysql.connector, os
    cfg = {
        'host':     os.environ.get('DB_HOST', 'localhost'),
        'user':     os.environ.get('DB_USER', 'root'),
        'password': os.environ.get('DB_PASSWORD', '1983'),
        'database': os.environ.get('DB_NAME', 'STRATOS_DB'),
        'autocommit': True,
        'use_pure': True,
    }
    return mysql.connector.connect(**cfg)

def _write_conn():
    """Connection for write transactions (autocommit off)."""
    import mysql.connector, os
    cfg = {
        'host':     os.environ.get('DB_HOST', 'localhost'),
        'user':     os.environ.get('DB_USER', 'root'),
        'password': os.environ.get('DB_PASSWORD', '1983'),
        'database': os.environ.get('DB_NAME', 'STRATOS_DB'),
        'autocommit': False,
        'use_pure': True,
    }
    return mysql.connector.connect(**cfg)


# ══════════════════════════════════════════════════════════════════════
#  T1 — Logistics Fuel Transfer
# ══════════════════════════════════════════════════════════════════════
@transactions_bp.route('/api/transactions/t1', methods=['POST'])
def t1_fuel_transfer():
    FUEL_Q = """
        SELECT b.base_name, ri.quantity AS fuel_litres, ri.status
        FROM   Resource_Inventory ri
        JOIN   Bases b ON b.base_id = ri.base_id
        WHERE  ri.base_id IN (2,3) AND ri.resource_id = 1"""
    LT_Q = """
        SELECT lt.transfer_id, bs.base_name AS source, bd.base_name AS destination,
               lt.quantity_transferred, lt.status
        FROM   Logistics_Transfer lt
        JOIN   Bases bs ON bs.base_id = lt.source_base_id
        JOIN   Bases bd ON bd.base_id = lt.transfer_base_id
        WHERE  lt.source_base_id = 2 AND lt.transfer_base_id = 3
          AND  lt.resource_id = 1
        ORDER  BY lt.transfer_id DESC LIMIT 1"""

    rconn = _read_conn()
    before_fuel = _q(rconn, FUEL_Q)
    before_lt   = _q(rconn, """SELECT COUNT(*) AS total_transfers FROM Logistics_Transfer""")
    rconn.close()

    conn = _write_conn()
    steps = []
    conn.start_transaction()
    try:
        _run(conn, "UPDATE Resource_Inventory SET quantity=quantity-400000 WHERE base_id=2 AND resource_id=1")
        steps.append("UPDATE Resource_Inventory — Ambala fuel − 400,000 L  ✓")
        _run(conn, "UPDATE Resource_Inventory SET quantity=quantity+400000, status='Adequate' WHERE base_id=3 AND resource_id=1")
        steps.append("UPDATE Resource_Inventory — Halwara fuel + 400,000 L, status → 'Adequate'  ✓")
        _run(conn, "INSERT INTO Logistics_Transfer (source_base_id,transfer_base_id,resource_id,quantity_transferred,start_date,status) VALUES (2,3,1,400000,CURDATE(),'Completed')")
        steps.append("INSERT Logistics_Transfer — transfer record created  ✓")
        conn.commit()
        steps.append("COMMIT — all 3 operations committed atomically  ✓")
        status = "committed"
    except Exception as e:
        conn.rollback()
        steps.append(f"ROLLBACK — error: {e}")
        status = "rolled_back"

    aconn = _read_conn()
    after_fuel = _q(aconn, FUEL_Q)
    after_lt   = _q(aconn, LT_Q)
    aconn.close(); conn.close()

    return jsonify({
        "status": status,
        "before": [
            {"title": "Resource_Inventory — Jet Fuel (Ambala & Halwara)", "rows": before_fuel},
            {"title": "Logistics_Transfer total rows", "rows": before_lt}
        ],
        "steps": steps,
        "after": [
            {"title": "Resource_Inventory — Jet Fuel (updated)", "rows": after_fuel},
            {"title": "Logistics_Transfer — new record", "rows": after_lt}
        ],
        "effect": [
            "Ambala fuel:  3,200,000 → 2,800,000 L  (−400,000)",
            "Halwara fuel: 2,800,000 → 3,200,000 L  (+400,000), status: Low → Adequate",
            "New Logistics_Transfer row inserted (status = 'Completed')",
            "ACID — Atomicity: all 3 DML ops succeed or none apply"
        ]
    })


# ══════════════════════════════════════════════════════════════════════
#  T2 — Mission Deployment
# ══════════════════════════════════════════════════════════════════════
@transactions_bp.route('/api/transactions/t2', methods=['POST'])
def t2_mission():
    MISSILE_Q = """
        SELECT b.base_name, mt.missile_name, mi.quantity, mi.operational_status
        FROM   Missile_Inventory mi
        JOIN   Bases b        ON b.base_id        = mi.base_id
        JOIN   Missile_Type mt ON mt.missile_type_id = mi.missile_type_id
        WHERE  mi.base_id = 12 AND mi.missile_type_id = 10"""
    PERSONNEL_Q = "SELECT service_id, name, role, avail_status FROM Personnel WHERE base_id=12"
    SIM_Q = """
        SELECT sim.simulation_id, b.base_name AS launched_from,
               eb.enemy_base_name AS target, sim.simulation_type,
               sim.readiness_level, sim.simulation_date
        FROM   Attack_Simulation sim
        JOIN   Bases b      ON b.base_id         = sim.base_id
        JOIN   Enemy_Base eb ON eb.enemy_base_id  = sim.target_base_id
        WHERE  sim.base_id = 12
        ORDER  BY sim.simulation_id DESC LIMIT 1"""

    rconn = _read_conn()
    before_missiles   = _q(rconn, MISSILE_Q)
    before_personnel  = _q(rconn, PERSONNEL_Q)
    rconn.close()

    conn = _write_conn()
    steps = []
    conn.start_transaction()
    try:
        _run(conn, "UPDATE Personnel SET avail_status='In Mission' WHERE base_id=12 AND role='Pilot' LIMIT 1")
        steps.append("UPDATE Personnel — pilot status → 'In Mission'  ✓")
        _run(conn, "UPDATE Missile_Inventory SET quantity=quantity-1 WHERE base_id=12 AND missile_type_id=10")
        steps.append("UPDATE Missile_Inventory — Agni-V quantity − 1  ✓")
        _run(conn, """INSERT INTO Attack_Simulation
            (target_base_id,base_id,simulation_type,simulation_date,readiness_level,recommendation)
            VALUES (3,12,'Ballistic Strike',CURDATE(),'High',
                    'Agni-V launch authorised. Target neutralised.')""")
        steps.append("INSERT Attack_Simulation — mission logged  ✓")
        conn.commit()
        steps.append("COMMIT — all 3 operations committed atomically  ✓")
        status = "committed"
    except Exception as e:
        conn.rollback()
        steps.append(f"ROLLBACK — error: {e}")
        status = "rolled_back"

    aconn = _read_conn()
    after_missiles   = _q(aconn, MISSILE_Q)
    after_personnel  = _q(aconn, PERSONNEL_Q)
    after_sim        = _q(aconn, SIM_Q)
    aconn.close(); conn.close()

    return jsonify({
        "status": status,
        "before": [
            {"title": "Missile_Inventory — Agni-V at Tezpur", "rows": before_missiles},
            {"title": "Personnel — Tezpur", "rows": before_personnel}
        ],
        "steps": steps,
        "after": [
            {"title": "Missile_Inventory — Agni-V at Tezpur (updated)", "rows": after_missiles},
            {"title": "Personnel — Tezpur (updated)", "rows": after_personnel},
            {"title": "Attack_Simulation — new record", "rows": after_sim}
        ],
        "effect": [
            "Agni-V quantity at Tezpur:  3 → 2",
            "Pilot avail_status confirmed as 'In Mission'",
            "New Attack_Simulation record: Tezpur → PAF Base Rafiqui",
            "ACID — Consistency: missile count only decrements when simulation is also logged"
        ]
    })


# ══════════════════════════════════════════════════════════════════════
#  T3 — Savepoint / Partial Rollback
# ══════════════════════════════════════════════════════════════════════
@transactions_bp.route('/api/transactions/t3', methods=['POST'])
def t3_savepoint():
    FUEL_Q = """SELECT b.base_name, ri.quantity AS fuel_litres
                FROM Resource_Inventory ri JOIN Bases b ON b.base_id=ri.base_id
                WHERE ri.base_id IN (1,4) AND ri.resource_id=1"""
    AMMO_Q = """SELECT b.base_name, ri.quantity AS ammo_tons
                FROM Resource_Inventory ri JOIN Bases b ON b.base_id=ri.base_id
                WHERE ri.base_id=2 AND ri.resource_id=4"""
    LT_COUNT = "SELECT COUNT(*) AS total_transfers FROM Logistics_Transfer"

    rconn = _read_conn()
    before_fuel  = _q(rconn, FUEL_Q)
    before_ammo  = _q(rconn, AMMO_Q)
    before_count = _q(rconn, LT_COUNT)
    rconn.close()

    conn = _write_conn()
    steps = []
    conn.start_transaction()
    try:
        # Part A – Fuel
        _run(conn, "UPDATE Resource_Inventory SET quantity=quantity-200000 WHERE base_id=1 AND resource_id=1")
        _run(conn, "UPDATE Resource_Inventory SET quantity=quantity+200000 WHERE base_id=4 AND resource_id=1")
        _run(conn, "INSERT INTO Logistics_Transfer (source_base_id,transfer_base_id,resource_id,quantity_transferred,start_date,status) VALUES (1,4,1,200000,CURDATE(),'Completed')")
        steps.append("Part A — Fuel transfer Hindon → Pathankot  ✓")

        cur = conn.cursor()
        cur.execute("SAVEPOINT after_fuel_transfer")
        cur.close()
        steps.append("SAVEPOINT after_fuel_transfer  ← checkpoint created")

        # Part B – Ammunition (tentative)
        _run(conn, "UPDATE Resource_Inventory SET quantity=quantity-100 WHERE base_id=2 AND resource_id=4")
        _run(conn, "UPDATE Resource_Inventory SET quantity=quantity+100 WHERE base_id=4 AND resource_id=4")
        _run(conn, "INSERT INTO Logistics_Transfer (source_base_id,transfer_base_id,resource_id,quantity_transferred,start_date,status) VALUES (2,4,4,100,CURDATE(),'Pending')")
        steps.append("Part B — Ammo transfer Ambala → Pathankot (tentative)  ✓")

        # Security alert — cancel Part B
        steps.append("⚠ SECURITY ALERT — ammunition convoy cancelled!")
        cur = conn.cursor()
        cur.execute("ROLLBACK TO SAVEPOINT after_fuel_transfer")
        cur.execute("RELEASE SAVEPOINT after_fuel_transfer")
        cur.close()
        steps.append("ROLLBACK TO SAVEPOINT — ammo changes undone, fuel preserved  ✓")

        conn.commit()
        steps.append("COMMIT — only Part A (fuel transfer) is committed  ✓")
        status = "partial_commit"
    except Exception as e:
        conn.rollback()
        steps.append(f"ROLLBACK — error: {e}")
        status = "rolled_back"

    aconn = _read_conn()
    after_fuel  = _q(aconn, FUEL_Q)
    after_ammo  = _q(aconn, AMMO_Q)
    after_count = _q(aconn, LT_COUNT)
    aconn.close(); conn.close()

    return jsonify({
        "status": status,
        "before": [
            {"title": "Fuel — Hindon & Pathankot", "rows": before_fuel},
            {"title": "Ammunition — Ambala", "rows": before_ammo},
            {"title": "Logistics_Transfer row count", "rows": before_count}
        ],
        "steps": steps,
        "after": [
            {"title": "Fuel — Hindon & Pathankot (updated)", "rows": after_fuel},
            {"title": "Ammunition — Ambala (UNCHANGED = rollback worked)", "rows": after_ammo},
            {"title": "Logistics_Transfer row count (after)", "rows": after_count}
        ],
        "effect": [
            "Hindon fuel  − 200,000 L  ✓ committed",
            "Pathankot fuel  + 200,000 L  ✓ committed",
            f"Logistics_Transfer: {before_count[0]['total_transfers']} → {after_count[0]['total_transfers']}  (+1 fuel record only)  ✓",
            "Ambala ammo — UNCHANGED  ✓  (rolled back to savepoint)",
            "No ammo Logistics_Transfer row  ✓  (rolled back to savepoint)",
            "ACID — SAVEPOINT enables surgical partial undo within one transaction"
        ]
    })


# ══════════════════════════════════════════════════════════════════════
#  T4 — Lost Update (WITHOUT locking) — anomaly demo
# ══════════════════════════════════════════════════════════════════════
@transactions_bp.route('/api/transactions/t4', methods=['POST'])
def t4_lost_update():
    MISSILE_Q = """SELECT b.base_name, mt.missile_name, mi.quantity
                   FROM Missile_Inventory mi
                   JOIN Bases b ON b.base_id=mi.base_id
                   JOIN Missile_Type mt ON mt.missile_type_id=mi.missile_type_id
                   WHERE mi.base_id=4 AND mi.missile_type_id=1"""

    # Reset to 50 for a clean demo
    reset = _write_conn(); reset.autocommit=True
    _run(reset, "UPDATE Missile_Inventory SET quantity=50 WHERE base_id=4 AND missile_type_id=1")
    reset.close()

    before = _q(_read_conn(), MISSILE_Q)
    steps  = []
    result = {}
    barrier = threading.Barrier(2)

    def session_a():
        c = _write_conn(); cur = c.cursor()
        c.start_transaction()
        cur.execute("SELECT quantity FROM Missile_Inventory WHERE base_id=4 AND missile_type_id=1")
        qty = cur.fetchone()[0]; result["a_read"] = qty
        barrier.wait()
        time.sleep(0.05)
        new = qty - 30; result["a_write"] = new
        cur.execute("UPDATE Missile_Inventory SET quantity=%s WHERE base_id=4 AND missile_type_id=1", (new,))
        c.commit(); cur.close(); c.close()

    def session_b():
        c = _write_conn(); cur = c.cursor()
        c.start_transaction()
        cur.execute("SELECT quantity FROM Missile_Inventory WHERE base_id=4 AND missile_type_id=1")
        qty = cur.fetchone()[0]; result["b_read"] = qty
        barrier.wait()
        time.sleep(0.25)
        new = qty - 25; result["b_write"] = new
        try:
            cur.execute("UPDATE Missile_Inventory SET quantity=%s WHERE base_id=4 AND missile_type_id=1", (new,))
            c.commit()
            result["b_error"] = None
        except Exception as e:
            c.rollback()
            result["b_error"] = str(e)
        cur.close(); c.close()

    ta = threading.Thread(target=session_a)
    tb = threading.Thread(target=session_b)
    ta.start(); tb.start(); ta.join(); tb.join()

    b_err = result.get("b_error")
    if b_err:
        # MySQL 9.x detected the conflict at the server level
        steps = [
            f"Session A  READ qty = {result['a_read']}  (needs 30 — sees sufficient stock)",
            f"Session B  READ qty = {result['b_read']}  ← STALE READ! (also sees {result['b_read']} — no lock)",
            f"Session A  WRITE qty = {result['a_read']} − 30 = {result['a_write']}  → COMMIT  ✓",
            f"Session B  WRITE qty = {result['b_read']} − 25 = {result['b_write']}  → ERROR 1020!",
            f"⚠ MySQL detected: 'Record has changed since last read' — B's stale write REJECTED",
        ]
    else:
        steps = [
            f"Session A  READ qty = {result['a_read']}  (needs 30 — sees sufficient stock)",
            f"Session B  READ qty = {result['b_read']}  ← STALE READ! (also sees {result['b_read']} — no lock)",
            f"Session A  WRITE qty = {result['a_read']} − 30 = {result['a_write']}  → COMMIT",
            f"Session B  WRITE qty = {result['b_read']} − 25 = {result['b_write']}  → COMMIT  ← OVERWRITES A's committed value!",
        ]

    after_conn = _read_conn()
    after = _q(after_conn, MISSILE_Q)
    after_conn.close()
    final = after[0]["quantity"]

    if b_err:
        effect = [
            f"Session A committed qty = {result['a_write']}  (50 − 30 = correct)",
            f"Session B attempted qty = {result['b_write']}  (50 − 25 = based on STALE read)",
            f"MySQL 9.x DETECTED the stale write (Error 1020) and REJECTED Session B",
            f"Final DB value = {final} — Session A's deduction preserved correctly",
            "NOTE: Older MySQL versions would allow this — creating a LOST UPDATE anomaly",
            "⚠ Without explicit locking (T5), you rely on server-version-specific behaviour — not portable"
        ]
    else:
        effect = [
            f"Session A committed qty = {result['a_write']}  (50 − 30 = correct)",
            f"Session B committed qty = {result['b_write']}  (50 − 25 = based on STALE read)",
            f"Final DB value = {final}  — Session A's deduction of 30 is SILENTLY LOST",
            "In real terms: 55 missiles allocated from a stock of only 50",
            "ANOMALY: LOST UPDATE — last writer wins on stale data"
        ]

    return jsonify({
        "status": "anomaly",
        "before": [{"title": "Missile_Inventory — BrahMos at Pathankot (reset to 50)", "rows": before}],
        "steps": steps,
        "after": [{"title": "Missile_Inventory — BrahMos at Pathankot" + (" (A preserved)" if b_err else " (CORRUPTED)"), "rows": after}],
        "effect": effect
    })


# ══════════════════════════════════════════════════════════════════════
#  T5 — Lost Update FIXED (SELECT … FOR UPDATE)
# ══════════════════════════════════════════════════════════════════════
@transactions_bp.route('/api/transactions/t5', methods=['POST'])
def t5_fixed():
    MISSILE_Q = """SELECT b.base_name, mt.missile_name, mi.quantity
                   FROM Missile_Inventory mi
                   JOIN Bases b ON b.base_id=mi.base_id
                   JOIN Missile_Type mt ON mt.missile_type_id=mi.missile_type_id
                   WHERE mi.base_id=4 AND mi.missile_type_id=1"""

    reset = _write_conn(); reset.autocommit=True
    _run(reset, "UPDATE Missile_Inventory SET quantity=50 WHERE base_id=4 AND missile_type_id=1")
    reset.close()

    before = _q(_read_conn(), MISSILE_Q)
    result = {}
    a_locked = threading.Event()

    def session_a():
        c = _write_conn(); cur = c.cursor()
        c.start_transaction()
        cur.execute("SELECT quantity FROM Missile_Inventory WHERE base_id=4 AND missile_type_id=1 FOR UPDATE")
        qty = cur.fetchone()[0]; result["a_read"] = qty
        a_locked.set()
        time.sleep(0.5)
        new = qty - 30; result["a_write"] = new
        cur.execute("UPDATE Missile_Inventory SET quantity=%s WHERE base_id=4 AND missile_type_id=1", (new,))
        c.commit(); cur.close(); c.close()

    def session_b():
        a_locked.wait(); time.sleep(0.02)
        c = _write_conn(); cur = c.cursor()
        c.start_transaction()
        result["b_blocked"] = True
        cur.execute("SELECT quantity FROM Missile_Inventory WHERE base_id=4 AND missile_type_id=1 FOR UPDATE")
        qty = cur.fetchone()[0]; result["b_read"] = qty
        if qty >= 25:
            new = qty - 25
            cur.execute("UPDATE Missile_Inventory SET quantity=%s WHERE base_id=4 AND missile_type_id=1", (new,))
            c.commit(); result["b_outcome"] = f"COMMITTED — qty → {new}"
        else:
            c.rollback()
            result["b_outcome"] = f"ROLLED BACK — qty = {qty}, insufficient stock (needed 25)"
        cur.close(); c.close()

    ta = threading.Thread(target=session_a)
    tb = threading.Thread(target=session_b)
    ta.start(); tb.start(); ta.join(); tb.join()

    steps = [
        f"Session A  SELECT FOR UPDATE → qty = {result['a_read']}  🔒 exclusive row lock acquired",
        "Session B  SELECT FOR UPDATE → ⏸ BLOCKED — waiting for Session A's lock",
        f"Session A  WRITE qty = {result['a_read']} − 30 = {result['a_write']}  → COMMIT  🔓 lock released",
        f"Session B  UNBLOCKED → re-reads qty = {result['b_read']}  (true post-commit value)",
        f"Session B  {result['b_outcome']}",
    ]

    after = _q(_read_conn(), MISSILE_Q)

    return jsonify({
        "status": "resolved",
        "before": [{"title": "Missile_Inventory — BrahMos at Pathankot (reset to 50)", "rows": before}],
        "steps": steps,
        "after": [{"title": "Missile_Inventory — BrahMos at Pathankot (CORRECT)", "rows": after}],
        "effect": [
            f"Session A committed qty = {result['a_write']}  (50 − 30 — correct)",
            f"Session B: {result['b_outcome']}",
            "No overwrite. No lost update. No phantom allocation.",
            "FIX: SELECT … FOR UPDATE serialises access — B always sees A's committed value"
        ]
    })


# ══════════════════════════════════════════════════════════════════════
#  T6 — Deadlock
# ══════════════════════════════════════════════════════════════════════
@transactions_bp.route('/api/transactions/t6', methods=['POST'])
def t6_deadlock():
    import mysql.connector
    RESOURCE_Q = """
        SELECT b.base_name, r.resource_type, ri.quantity
        FROM   Resource_Inventory ri
        JOIN   Bases b    ON b.base_id    = ri.base_id
        JOIN   Resource r ON r.resource_id = ri.resource_id
        WHERE  (ri.base_id=2 AND ri.resource_id=1)
            OR (ri.base_id=4 AND ri.resource_id=1)
            OR (ri.base_id=2 AND ri.resource_id=4)
            OR (ri.base_id=4 AND ri.resource_id=4)"""

    before = _q(_read_conn(), RESOURCE_Q)
    result = {"victim": "none", "error": "", "a_out": "?", "b_out": "?"}
    a_locked = threading.Event()
    b_locked = threading.Event()

    def session_a():
        c = _write_conn(); cur = c.cursor()
        try:
            c.start_transaction()
            cur.execute("SELECT quantity FROM Resource_Inventory WHERE base_id=2 AND resource_id=1 FOR UPDATE")
            cur.fetchall()
            a_locked.set()
            b_locked.wait(); time.sleep(0.1)
            cur.execute("SELECT quantity FROM Resource_Inventory WHERE base_id=4 AND resource_id=1 FOR UPDATE")
            cur.fetchall()
            cur.execute("UPDATE Resource_Inventory SET quantity=quantity-300000 WHERE base_id=2 AND resource_id=1")
            cur.execute("UPDATE Resource_Inventory SET quantity=quantity+300000 WHERE base_id=4 AND resource_id=1")
            c.commit(); result["a_out"] = "COMMITTED"
        except mysql.connector.errors.DatabaseError as e:
            if e.errno == 1213:
                result["victim"] = "A"
                result["error"]  = f"ERROR 1213: {e.msg}"
                result["a_out"]  = "AUTO-ROLLED BACK (deadlock victim)"
                try: c.rollback()
                except: pass
        finally:
            try: cur.close(); c.close()
            except: pass

    def session_b():
        a_locked.wait(); time.sleep(0.02)
        c = _write_conn(); cur = c.cursor()
        try:
            c.start_transaction()
            cur.execute("SELECT quantity FROM Resource_Inventory WHERE base_id=4 AND resource_id=4 FOR UPDATE")
            cur.fetchall()
            b_locked.set(); time.sleep(0.1)
            cur.execute("SELECT quantity FROM Resource_Inventory WHERE base_id=2 AND resource_id=4 FOR UPDATE")
            cur.fetchall()
            cur.execute("UPDATE Resource_Inventory SET quantity=quantity-50 WHERE base_id=4 AND resource_id=4")
            cur.execute("UPDATE Resource_Inventory SET quantity=quantity+50 WHERE base_id=2 AND resource_id=4")
            c.commit(); result["b_out"] = "COMMITTED"
        except mysql.connector.errors.DatabaseError as e:
            if e.errno == 1213:
                result["victim"] = "B"
                result["error"]  = f"ERROR 1213: {e.msg}"
                result["b_out"]  = "AUTO-ROLLED BACK (deadlock victim)"
                try: c.rollback()
                except: pass
        finally:
            try: cur.close(); c.close()
            except: pass

    ta = threading.Thread(target=session_a)
    tb = threading.Thread(target=session_b)
    ta.start(); tb.start(); ta.join(); tb.join()

    after = _q(_read_conn(), RESOURCE_Q)

    steps = [
        "Session A  SELECT FOR UPDATE — Ambala-Fuel row  🔒 locked",
        "Session B  SELECT FOR UPDATE — Pathankot-Ammo row  🔒 locked",
        "Session A  Tries to lock Pathankot-Fuel  → ⏸ BLOCKED (Session B holds it)",
        "Session B  Tries to lock Ambala-Ammo      → ⏸ BLOCKED (Session A holds it)",
        "⚡ DEADLOCK DETECTED — circular wait: A waits for B, B waits for A",
        f"MySQL auto-selects victim: Session {result['victim']}",
        result["error"] if result["error"] else "Deadlock resolved",
        f"Session A outcome: {result['a_out']}",
        f"Session B outcome: {result['b_out']}"
    ]

    return jsonify({
        "status": "deadlock",
        "victim": result["victim"],
        "before": [{"title": "Resource_Inventory — Fuel & Ammo at Ambala & Pathankot", "rows": before}],
        "steps": steps,
        "after": [{"title": "Resource_Inventory — after deadlock resolution", "rows": after}],
        "effect": [
            f"Deadlock victim: Session {result['victim']} — auto-rolled back by MySQL",
            f"Survivor committed. DB is consistent — no partial writes from victim.",
            result["error"] if result["error"] else "Lock cycle resolved",
            "FIX: Always acquire locks in ascending order (e.g. by base_id) to break circular waits"
        ]
    })


# ══════════════════════════════════════════════════════════════════════
#  T7 — Dirty Read (READ UNCOMMITTED)
# ══════════════════════════════════════════════════════════════════════
@transactions_bp.route('/api/transactions/t7', methods=['POST'])
def t7_dirty_read():
    MISSILE_Q = """SELECT b.base_name, mt.missile_name, mi.quantity
                   FROM Missile_Inventory mi
                   JOIN Bases b ON b.base_id=mi.base_id
                   JOIN Missile_Type mt ON mt.missile_type_id=mi.missile_type_id
                   WHERE mi.base_id=12 AND mi.missile_type_id=10"""
    REPORT_Q  = """SELECT overall_readiness, missile_score, strategic_recomm
                   FROM Readiness_Report WHERE base_id=12
                   ORDER BY assessment_id DESC LIMIT 1"""

    # Ensure known start state
    reset = _write_conn(); reset.autocommit=True
    _run(reset, "UPDATE Missile_Inventory SET quantity=2 WHERE base_id=12 AND missile_type_id=10")
    reset.close()

    before_missile = _q(_read_conn(), MISSILE_Q)
    result = {}
    a_wrote = threading.Event()
    b_done  = threading.Event()

    def session_a():
        c = _write_conn(); cur = c.cursor()
        c.start_transaction()
        cur.execute("UPDATE Missile_Inventory SET quantity=0 WHERE base_id=12 AND missile_type_id=10")
        result["a_wrote"] = 0
        a_wrote.set()
        b_done.wait(); time.sleep(0.05)
        c.rollback(); result["a_out"] = "ROLLED BACK — launch aborted, qty restored to 2"
        cur.close(); c.close()

    def session_b():
        a_wrote.wait(); time.sleep(0.02)
        c = _write_conn(); cur = c.cursor()
        cur.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
        c.start_transaction()
        cur.execute("SELECT quantity FROM Missile_Inventory WHERE base_id=12 AND missile_type_id=10")
        qty = cur.fetchone()[0]; result["b_read"] = qty
        cur.execute("""INSERT INTO Readiness_Report
            (base_id,assessment_date,overall_readiness,personnel_score,resource_score,missile_score,strategic_recomm)
            VALUES (12,CURDATE(),'Vulnerable',75.00,70.00,20.00,
                    'DIRTY READ DEMO: Agni-V arsenal depleted — emergency resupply required')""")
        c.commit(); result["b_out"] = "COMMITTED (wrong report)"
        cur.close(); c.close()
        b_done.set()

    ta = threading.Thread(target=session_a)
    tb = threading.Thread(target=session_b)
    ta.start(); tb.start(); ta.join(); tb.join()

    after_missile = _q(_read_conn(), MISSILE_Q)
    after_report  = _q(_read_conn(), REPORT_Q)

    steps = [
        "Session A  UPDATE Agni-V qty → 0  (NOT committed yet — still inside transaction)",
        "Session B  SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED",
        f"Session B  SELECT qty → {result.get('b_read','?')}  ⚠ DIRTY READ — reading A's uncommitted value!",
        "Session B  INSERT Readiness_Report — 'Vulnerable', missile_score=20  → COMMIT",
        f"Session A  {result.get('a_out','?')}",
        "Session B's committed report is now WRONG — based on data that never existed"
    ]

    return jsonify({
        "status": "dirty_read",
        "before": [{"title": "Missile_Inventory — Agni-V at Tezpur (true value)", "rows": before_missile}],
        "steps": steps,
        "after": [
            {"title": "Missile_Inventory — Agni-V at Tezpur (after A's rollback — true value)", "rows": after_missile},
            {"title": "Readiness_Report — committed by B (WRONG, based on dirty data)", "rows": after_report}
        ],
        "effect": [
            f"Agni-V qty = {after_missile[0]['quantity']}  (A rolled back — true value unchanged)",
            "Readiness_Report: 'Vulnerable' committed — WRONG. Based on qty=0 (never existed).",
            "Session B read dirty (uncommitted) data from Session A's transaction",
            "FIX: Use READ COMMITTED or higher. B would read qty=2 and produce a correct report"
        ]
    })


# ══════════════════════════════════════════════════════════════════════
#  T8 — Explicit ROLLBACK (invalid transfer)
# ══════════════════════════════════════════════════════════════════════
@transactions_bp.route('/api/transactions/t8', methods=['POST'])
def t8_rollback():
    MISSILE_Q = """SELECT b.base_name, mt.missile_name, mi.quantity
                   FROM Missile_Inventory mi
                   JOIN Bases b ON b.base_id=mi.base_id
                   JOIN Missile_Type mt ON mt.missile_type_id=mi.missile_type_id
                   WHERE mi.base_id IN (1,2) AND mi.missile_type_id=1"""

    rconn = _read_conn()
    before = _q(rconn, MISSILE_Q)
    rconn.close()

    conn = _write_conn()
    steps = []
    conn.start_transaction()
    try:
        # First operation succeeds
        _run(conn, "UPDATE Missile_Inventory SET quantity=quantity+99999 WHERE base_id=2 AND missile_type_id=1")
        steps.append("UPDATE Missile_Inventory — Ambala BrahMos + 99,999  ✓ (not yet committed)")

        # Second operation — subtract 99999 from Hindon
        _run(conn, "UPDATE Missile_Inventory SET quantity=quantity-99999 WHERE base_id=1 AND missile_type_id=1")
        steps.append("UPDATE Missile_Inventory — Hindon BrahMos − 99,999  ✓ (not yet committed)")

        # Manual validation: check if quantity went negative
        check = _q(conn, "SELECT quantity FROM Missile_Inventory WHERE base_id=1 AND missile_type_id=1")
        qty = check[0]['quantity'] if check else 0
        steps.append(f"VALIDATION CHECK — Hindon qty = {qty}")

        if qty < 0:
            steps.append(f"⚠ CONSTRAINT VIOLATION — quantity = {qty} (NEGATIVE!) — insufficient stock")
            raise ValueError(f"Insufficient missiles: quantity would be {qty}")

        conn.commit()
        steps.append("COMMIT — transfer completed (shouldn't reach here)")
        status = "committed"
    except Exception as e:
        conn.rollback()
        steps.append(f"ROLLBACK — error: {e}")
        steps.append("ROLLBACK executed — ALL changes undone, DB unchanged  ✓")
        status = "rolled_back"

    aconn = _read_conn()
    after = _q(aconn, MISSILE_Q)
    aconn.close(); conn.close()

    return jsonify({
        "status": status,
        "before": [{"title": "Missile_Inventory — BrahMos at Hindon & Ambala", "rows": before}],
        "steps": steps,
        "after": [{"title": "Missile_Inventory — BrahMos (UNCHANGED after ROLLBACK)", "rows": after}],
        "effect": [
            "Attempted transfer: 99,999 BrahMos Hindon → Ambala",
            f"Hindon only has {before[0]['quantity'] if before else '?'} — transfer is IMPOSSIBLE",
            "Both Ambala +99999 AND Hindon −99999 were UNDONE by ROLLBACK",
            "DB is exactly as it was before the transaction started",
            "ACID — Atomicity: partial application is NEVER visible. All or nothing."
        ]
    })


# ══════════════════════════════════════════════════════════════════════
#  Reset — restore DB to seed values for all transaction-affected tables
# ══════════════════════════════════════════════════════════════════════
@transactions_bp.route('/api/transactions/reset', methods=['POST'])
def reset_db():
    conn = _write_conn()
    conn.start_transaction()
    try:
        cur = conn.cursor()
        # Resource_Inventory — fuel & ammo for bases 1,2,3,4
        cur.execute("UPDATE Resource_Inventory SET quantity=2500000, status='Adequate' WHERE base_id=1 AND resource_id=1")
        cur.execute("UPDATE Resource_Inventory SET quantity=3200000, status='Adequate' WHERE base_id=2 AND resource_id=1")
        cur.execute("UPDATE Resource_Inventory SET quantity=2800000, status='Low'      WHERE base_id=3 AND resource_id=1")
        cur.execute("UPDATE Resource_Inventory SET quantity=2900000, status='Adequate' WHERE base_id=4 AND resource_id=1")
        cur.execute("UPDATE Resource_Inventory SET quantity=450,     status='Adequate' WHERE base_id=1 AND resource_id=4")
        cur.execute("UPDATE Resource_Inventory SET quantity=580,     status='Adequate' WHERE base_id=2 AND resource_id=4")
        # Missile_Inventory — BrahMos at Hindon/Ambala/Pathankot, Agni-V at Tezpur
        cur.execute("UPDATE Missile_Inventory SET quantity=48  WHERE base_id=1  AND missile_type_id=1")
        cur.execute("UPDATE Missile_Inventory SET quantity=60  WHERE base_id=2  AND missile_type_id=1")
        cur.execute("UPDATE Missile_Inventory SET quantity=50  WHERE base_id=4  AND missile_type_id=1")
        cur.execute("UPDATE Missile_Inventory SET quantity=3   WHERE base_id=12 AND missile_type_id=10")
        # Personnel — reset pilot status at Tezpur
        cur.execute("UPDATE Personnel SET avail_status='In Mission' WHERE base_id=12 AND role='Pilot'")
        # Clean up transaction-inserted rows
        cur.execute("DELETE FROM Logistics_Transfer WHERE transfer_id > 33")
        cur.execute("DELETE FROM Attack_Simulation WHERE simulation_id > 30")
        cur.execute("DELETE FROM Readiness_Report WHERE assessment_id > 30")
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "ok", "message": "Database reset to seed values"})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════
#  Snapshot — current DB state for all relevant tables
# ══════════════════════════════════════════════════════════════════════
@transactions_bp.route('/api/transactions/snapshot')
def snapshot():
    conn = _read_conn()
    data = {
        "fuel": _q(conn, """
            SELECT b.base_name, ri.quantity AS fuel_litres, ri.status
            FROM   Resource_Inventory ri JOIN Bases b ON b.base_id=ri.base_id
            JOIN   Resource r ON r.resource_id=ri.resource_id
            WHERE  ri.base_id IN (1,2,3,4) AND ri.resource_id=1
            ORDER  BY ri.base_id"""),
        "ammo": _q(conn, """
            SELECT b.base_name, ri.quantity AS ammo_tons
            FROM   Resource_Inventory ri JOIN Bases b ON b.base_id=ri.base_id
            WHERE  ri.base_id IN (1,2,3,4) AND ri.resource_id=4
            ORDER  BY ri.base_id"""),
        "missiles": _q(conn, """
            SELECT b.base_name, mt.missile_name, mi.quantity
            FROM   Missile_Inventory mi
            JOIN   Bases b ON b.base_id=mi.base_id
            JOIN   Missile_Type mt ON mt.missile_type_id=mi.missile_type_id
            WHERE  (mi.base_id=4 AND mi.missile_type_id=1)
                OR (mi.base_id=12 AND mi.missile_type_id=10)
                OR (mi.base_id=1 AND mi.missile_type_id=1)
                OR (mi.base_id=2 AND mi.missile_type_id=1)"""),
        "transfers": _q(conn, """
            SELECT lt.transfer_id, bs.base_name AS source, bd.base_name AS dest,
                   r.resource_type, lt.quantity_transferred, lt.status
            FROM   Logistics_Transfer lt
            JOIN   Bases bs ON bs.base_id=lt.source_base_id
            JOIN   Bases bd ON bd.base_id=lt.transfer_base_id
            JOIN   Resource r ON r.resource_id=lt.resource_id
            ORDER  BY lt.transfer_id DESC LIMIT 8"""),
        "simulations": _q(conn, """
            SELECT sim.simulation_id, b.base_name AS launched_from,
                   eb.enemy_base_name AS target, sim.simulation_type, sim.simulation_date
            FROM   Attack_Simulation sim
            JOIN   Bases b ON b.base_id=sim.base_id
            JOIN   Enemy_Base eb ON eb.enemy_base_id=sim.target_base_id
            ORDER  BY sim.simulation_id DESC LIMIT 5"""),
    }
    conn.close()
    return jsonify(data)
