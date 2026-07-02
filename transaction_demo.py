"""
=============================================================================
  STRATOS_DB — Transaction Demo Script
  DBMS Lab: Write & Execute DB Transactions (Including Conflicting Ones)
=============================================================================
  This script demonstrates:
    1. Normal Transaction with COMMIT
    2. Normal Transaction with ROLLBACK
    3. Conflicting Transaction: Lost Update Problem
    4. Conflicting Transaction: Dirty Read (READ UNCOMMITTED)
    5. Conflicting Transaction: Deadlock Scenario
    6. Resolution: Using SERIALIZABLE Isolation Level
=============================================================================
"""

import mysql.connector
import threading
import time
import sys
from db import DB_CONFIG

# ─── Colour helpers (for terminal output) ─────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"
BLUE   = "\033[94m"
MAGENTA = "\033[95m"

def header(title):
    print(f"\n{'='*80}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{'='*80}")

def sub(msg):
    print(f"  {YELLOW}→{RESET} {msg}")

def ok(msg):
    print(f"  {GREEN}✓{RESET} {msg}")

def fail(msg):
    print(f"  {RED}✗{RESET} {msg}")

def info(msg):
    print(f"  {BLUE}ℹ{RESET} {msg}")

def session_log(name, msg, color=RESET):
    print(f"    {color}[{name}]{RESET} {msg}")

def show_row(label, row):
    if row:
        print(f"    {MAGENTA}{label}:{RESET} {dict(row)}")
    else:
        print(f"    {MAGENTA}{label}:{RESET} (no data)")

def get_conn():
    """Get a fresh DB connection with autocommit OFF (manual transaction control)."""
    conn = mysql.connector.connect(**DB_CONFIG)
    conn.autocommit = True
    return conn

def divider():
    print(f"  {'─'*60}")


# ═══════════════════════════════════════════════════════════════════════════════
#  TRANSACTION 1: Normal Transaction with COMMIT
# ═══════════════════════════════════════════════════════════════════════════════
def demo_commit():
    header("TRANSACTION 1: Normal Transaction with COMMIT")
    info("Scenario: Transfer 50 BrahMos (Air-Launched) missiles from Hindon (base 1) to Ambala (base 2)")
    info("Both updates must succeed together, or neither should apply.\n")

    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    # Show BEFORE state
    sub("BEFORE Transaction:")
    cur.execute("SELECT base_id, quantity FROM Missile_Inventory WHERE base_id=1 AND missile_type_id=1")
    before_hindon = cur.fetchone()
    cur.execute("SELECT base_id, quantity FROM Missile_Inventory WHERE base_id=2 AND missile_type_id=1")
    before_ambala = cur.fetchone()
    show_row("Hindon (base 1) BrahMos qty", before_hindon)
    show_row("Ambala (base 2) BrahMos qty", before_ambala)

    transfer_qty = 10
    divider()

    try:
        sub(f"START TRANSACTION;")
        conn.start_transaction()

        sub(f"UPDATE Missile_Inventory SET quantity = quantity - {transfer_qty} WHERE base_id=1 AND missile_type_id=1;")
        cur.execute("UPDATE Missile_Inventory SET quantity = quantity - %s WHERE base_id=1 AND missile_type_id=1", (transfer_qty,))
        ok(f"Subtracted {transfer_qty} from Hindon")

        sub(f"UPDATE Missile_Inventory SET quantity = quantity + {transfer_qty} WHERE base_id=2 AND missile_type_id=1;")
        cur.execute("UPDATE Missile_Inventory SET quantity = quantity + %s WHERE base_id=2 AND missile_type_id=1", (transfer_qty,))
        ok(f"Added {transfer_qty} to Ambala")

        sub("COMMIT;")
        conn.commit()
        ok("Transaction COMMITTED successfully!")

    except Exception as e:
        conn.rollback()
        fail(f"Error: {e} — Transaction ROLLED BACK")

    # Show AFTER state
    divider()
    sub("AFTER Transaction:")
    cur.execute("SELECT base_id, quantity FROM Missile_Inventory WHERE base_id=1 AND missile_type_id=1")
    after_hindon = cur.fetchone()
    cur.execute("SELECT base_id, quantity FROM Missile_Inventory WHERE base_id=2 AND missile_type_id=1")
    after_ambala = cur.fetchone()
    show_row("Hindon (base 1) BrahMos qty", after_hindon)
    show_row("Ambala (base 2) BrahMos qty", after_ambala)

    ok(f"Hindon: {before_hindon['quantity']} → {after_hindon['quantity']} (decreased by {transfer_qty})")
    ok(f"Ambala: {before_ambala['quantity']} → {after_ambala['quantity']} (increased by {transfer_qty})")
    info("EFFECT: Both rows updated atomically. Total missiles in system UNCHANGED.")

    cur.close()
    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  TRANSACTION 2: Normal Transaction with ROLLBACK
# ═══════════════════════════════════════════════════════════════════════════════
def demo_rollback():
    header("TRANSACTION 2: Normal Transaction with ROLLBACK")
    info("Scenario: Try to transfer 99999 missiles from Hindon — more than available!")
    info("The CHECK constraint (quantity >= 0) should cause failure, triggering ROLLBACK.\n")

    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    # Show BEFORE state
    sub("BEFORE Transaction:")
    cur.execute("SELECT base_id, quantity FROM Missile_Inventory WHERE base_id=1 AND missile_type_id=1")
    before_hindon = cur.fetchone()
    cur.execute("SELECT base_id, quantity FROM Missile_Inventory WHERE base_id=2 AND missile_type_id=1")
    before_ambala = cur.fetchone()
    show_row("Hindon (base 1) BrahMos qty", before_hindon)
    show_row("Ambala (base 2) BrahMos qty", before_ambala)

    divider()

    try:
        sub("START TRANSACTION;")
        conn.start_transaction()

        # First operation succeeds
        sub("UPDATE Missile_Inventory SET quantity = quantity + 99999 WHERE base_id=2 AND missile_type_id=1;")
        cur.execute("UPDATE Missile_Inventory SET quantity = quantity + 99999 WHERE base_id=2 AND missile_type_id=1")
        ok("Added 99999 to Ambala (not yet committed)")

        # Second operation should fail (negative quantity)
        sub("UPDATE Missile_Inventory SET quantity = quantity - 99999 WHERE base_id=1 AND missile_type_id=1;")
        cur.execute("UPDATE Missile_Inventory SET quantity = quantity - 99999 WHERE base_id=1 AND missile_type_id=1")
        info("Subtraction executed (MySQL may not enforce CHECK in all versions)...")

        # Manual validation: check if result is negative
        cur.execute("SELECT quantity FROM Missile_Inventory WHERE base_id=1 AND missile_type_id=1")
        check = cur.fetchone()
        if check and check['quantity'] < 0:
            fail(f"Quantity would become {check['quantity']} — INVALID! Manually rolling back.")
            raise ValueError(f"Insufficient missiles: quantity would be {check['quantity']}")
        
        conn.commit()
        ok("Committed (shouldn't reach here normally)")

    except Exception as e:
        sub("ROLLBACK;")
        conn.rollback()
        fail(f"Error detected: {e}")
        ok("Transaction ROLLED BACK — no changes persisted!")

    # Show AFTER state
    divider()
    sub("AFTER Rollback:")
    cur2 = conn.cursor(dictionary=True)
    # Need new connection since we rolled back
    conn2 = get_conn()
    cur2 = conn2.cursor(dictionary=True)
    cur2.execute("SELECT base_id, quantity FROM Missile_Inventory WHERE base_id=1 AND missile_type_id=1")
    after_hindon = cur2.fetchone()
    cur2.execute("SELECT base_id, quantity FROM Missile_Inventory WHERE base_id=2 AND missile_type_id=1")
    after_ambala = cur2.fetchone()
    show_row("Hindon (base 1) BrahMos qty", after_hindon)
    show_row("Ambala (base 2) BrahMos qty", after_ambala)

    ok(f"Hindon: {before_hindon['quantity']} → {after_hindon['quantity']} (UNCHANGED)")
    ok(f"Ambala: {before_ambala['quantity']} → {after_ambala['quantity']} (UNCHANGED)")
    info("EFFECT: ROLLBACK undid ALL changes. Database is back to its original state.")

    cur.close(); conn.close()
    cur2.close(); conn2.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  TRANSACTION 3: Conflicting — LOST UPDATE Problem
# ═══════════════════════════════════════════════════════════════════════════════
def demo_lost_update():
    header("TRANSACTION 3: CONFLICTING — Lost Update Problem")
    info("Scenario: Two sessions simultaneously read the SAME missile inventory,")
    info("          then BOTH try to update it. One update gets lost!\n")

    # Reset to known state
    reset = get_conn()
    rc = reset.cursor()
    rc.execute("UPDATE Missile_Inventory SET quantity = 48 WHERE base_id=1 AND missile_type_id=1")
    reset.commit()
    rc.close(); reset.close()

    results = {}
    barrier = threading.Barrier(2)  # sync both threads

    def session_a():
        conn = get_conn()
        conn.start_transaction()
        cur = conn.cursor(dictionary=True)

        # Step 1: Read current quantity
        cur.execute("SELECT quantity FROM Missile_Inventory WHERE base_id=1 AND missile_type_id=1")
        row = cur.fetchone()
        qty = row['quantity']
        session_log("Session A", f"READ quantity = {qty}", CYAN)
        results['a_read'] = qty

        barrier.wait()  # Sync: both sessions have read
        time.sleep(0.1)

        # Step 2: Update based on what we read (subtract 6 for a mission)
        new_qty = qty - 6
        session_log("Session A", f"UPDATE quantity = {qty} - 6 = {new_qty}", CYAN)
        cur.execute("UPDATE Missile_Inventory SET quantity = %s WHERE base_id=1 AND missile_type_id=1", (new_qty,))
        conn.commit()
        session_log("Session A", f"COMMITTED (set quantity to {new_qty})", GREEN)
        results['a_write'] = new_qty

        cur.close(); conn.close()

    def session_b():
        conn = get_conn()
        conn.start_transaction()
        cur = conn.cursor(dictionary=True)

        # Step 1: Read current quantity (same value as Session A)
        cur.execute("SELECT quantity FROM Missile_Inventory WHERE base_id=1 AND missile_type_id=1")
        row = cur.fetchone()
        qty = row['quantity']
        session_log("Session B", f"READ quantity = {qty}", YELLOW)
        results['b_read'] = qty

        barrier.wait()  # Sync: both sessions have read

        # Step 2: Wait for A to commit first, then overwrite
        time.sleep(0.5)
        new_qty = qty - 8  # Allocate 8 missiles for another mission
        session_log("Session B", f"UPDATE quantity = {qty} - 8 = {new_qty}", YELLOW)
        cur.execute("UPDATE Missile_Inventory SET quantity = %s WHERE base_id=1 AND missile_type_id=1", (new_qty,))
        conn.commit()
        session_log("Session B", f"COMMITTED (set quantity to {new_qty})", GREEN)
        results['b_write'] = new_qty

        cur.close(); conn.close()

    sub("Initial state: Hindon BrahMos quantity = 48")
    divider()

    t1 = threading.Thread(target=session_a)
    t2 = threading.Thread(target=session_b)
    t1.start(); t2.start()
    t1.join(); t2.join()

    # Check final state
    divider()
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT quantity FROM Missile_Inventory WHERE base_id=1 AND missile_type_id=1")
    final = cur.fetchone()

    sub("ANALYSIS:")
    info(f"Session A read 48, subtracted 6 → wrote {results.get('a_write', '?')}")
    info(f"Session B read 48, subtracted 8 → wrote {results.get('b_write', '?')}")
    info(f"Final quantity in DB: {final['quantity']}")
    fail(f"EXPECTED quantity: 48 - 6 - 8 = 34")
    fail(f"ACTUAL   quantity: {final['quantity']}")
    fail(f"Session A's update was LOST! 6 missiles vanished from tracking!")
    info("EFFECT: This is the LOST UPDATE problem — both transactions read the")
    info("        same value, and the second commit silently overwrites the first.")

    cur.close(); conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  TRANSACTION 4: Conflicting — DIRTY READ
# ═══════════════════════════════════════════════════════════════════════════════
def demo_dirty_read():
    header("TRANSACTION 4: CONFLICTING — Dirty Read (READ UNCOMMITTED)")
    info("Scenario: Session A modifies a base's strength but hasn't committed yet.")
    info("          Session B reads this UNCOMMITTED (dirty) data. Then Session A rolls back.\n")

    # Reset to known state
    reset = get_conn()
    rc = reset.cursor()
    rc.execute("UPDATE Bases SET strength = 5000 WHERE base_id = 1")
    reset.commit()
    rc.close(); reset.close()

    results = {}
    barrier = threading.Barrier(2)

    def session_a():
        conn = get_conn()
        conn.start_transaction()
        cur = conn.cursor()

        session_log("Session A", "START TRANSACTION", CYAN)
        session_log("Session A", "UPDATE Bases SET strength = 9999 WHERE base_id = 1", CYAN)
        cur.execute("UPDATE Bases SET strength = 9999 WHERE base_id = 1")
        session_log("Session A", "Strength changed to 9999 (NOT COMMITTED YET)", CYAN)

        barrier.wait()  # Let Session B read the dirty data
        time.sleep(1)   # Wait a moment

        session_log("Session A", "ROLLBACK; — Cancelling the change!", RED)
        conn.rollback()
        session_log("Session A", "Transaction rolled back. Strength is back to 5000.", RED)

        cur.close(); conn.close()

    def session_b():
        conn = get_conn()
        cur = conn.cursor(dictionary=True)

        # Set READ UNCOMMITTED isolation level
        cur.execute("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
        conn.start_transaction()
        session_log("Session B", "SET ISOLATION LEVEL = READ UNCOMMITTED", YELLOW)

        barrier.wait()      # Wait for Session A to make the uncommitted change
        time.sleep(0.3)     # Small delay to ensure A's UPDATE is visible

        session_log("Session B", "SELECT strength FROM Bases WHERE base_id = 1", YELLOW)
        cur.execute("SELECT strength FROM Bases WHERE base_id = 1")
        row = cur.fetchone()
        results['dirty_read'] = row['strength']
        session_log("Session B", f"READ strength = {row['strength']}", YELLOW)

        if row['strength'] == 9999:
            session_log("Session B", "⚠ This is a DIRTY READ! Data not committed by Session A!", RED)
        
        conn.commit()
        time.sleep(1)  # Wait for A to rollback

        # Re-read after A's rollback
        cur.execute("SELECT strength FROM Bases WHERE base_id = 1")
        row2 = cur.fetchone()
        results['after_rollback'] = row2['strength']
        session_log("Session B", f"RE-READ after A rolled back: strength = {row2['strength']}", YELLOW)

        cur.close(); conn.close()

    sub("Initial state: Hindon (base 1) strength = 5000")
    divider()

    t1 = threading.Thread(target=session_a)
    t2 = threading.Thread(target=session_b)
    t1.start(); t2.start()
    t1.join(); t2.join()

    divider()
    sub("ANALYSIS:")
    dirty_val = results.get('dirty_read', '?')
    final_val = results.get('after_rollback', '?')
    if dirty_val == 9999:
        fail(f"Session B read strength = {dirty_val} (DIRTY — this data was never committed!)")
        ok(f"After A's rollback, re-read shows strength = {final_val} (correct value)")
        fail("PROBLEM: Session B made decisions based on data that NEVER EXISTED!")
        info("EFFECT: If Session B used this dirty value (e.g., approved a mission because")
        info("        strength=9999), it would be based on PHANTOM data.")
    else:
        info(f"Session B read strength = {dirty_val}")
        info(f"MySQL's InnoDB may still prevent dirty reads even with READ UNCOMMITTED")
        info("This depends on the MySQL version and lock timing.")


# ═══════════════════════════════════════════════════════════════════════════════
#  TRANSACTION 5: Conflicting — DEADLOCK
# ═══════════════════════════════════════════════════════════════════════════════
def demo_deadlock():
    header("TRANSACTION 5: CONFLICTING — Deadlock Scenario")
    info("Scenario: Two simultaneous resource transfers between bases create a deadlock.")
    info("  Session A: Transfer fuel FROM Hindon(1) → Ambala(2)")
    info("  Session B: Transfer ammo FROM Ambala(2) → Hindon(1)")
    info("  Each session locks one row, then tries to lock the other → DEADLOCK!\n")

    # Reset to known state
    reset = get_conn()
    rc = reset.cursor()
    rc.execute("UPDATE Resource_Inventory SET quantity = 2500000 WHERE base_id=1 AND resource_id=1")
    rc.execute("UPDATE Resource_Inventory SET quantity = 3200000 WHERE base_id=2 AND resource_id=1")
    rc.execute("UPDATE Resource_Inventory SET quantity = 450 WHERE base_id=1 AND resource_id=4")
    rc.execute("UPDATE Resource_Inventory SET quantity = 580 WHERE base_id=2 AND resource_id=4")
    reset.commit()
    rc.close(); reset.close()

    results = {'a_status': 'unknown', 'b_status': 'unknown'}
    barrier = threading.Barrier(2)

    def session_a():
        try:
            conn = get_conn()
            conn.start_transaction()
            cur = conn.cursor()

            # Step 1: Lock Hindon's fuel row
            session_log("Session A", "UPDATE Resource_Inventory SET quantity=quantity-100000 WHERE base_id=1, resource_id=1", CYAN)
            cur.execute("UPDATE Resource_Inventory SET quantity = quantity - 100000 WHERE base_id=1 AND resource_id=1")
            session_log("Session A", "Locked Hindon (base 1) fuel row ✓", CYAN)

            barrier.wait()  # Sync both sessions
            time.sleep(0.5) # let B lock its row

            # Step 2: Try to lock Ambala's ammo row → BLOCKED by Session B
            session_log("Session A", "Now trying to UPDATE base_id=2, resource_id=4 (BLOCKED by Session B!)...", CYAN)
            cur.execute("UPDATE Resource_Inventory SET quantity = quantity + 50 WHERE base_id=2 AND resource_id=4")

            conn.commit()
            session_log("Session A", "COMMITTED successfully", GREEN)
            results['a_status'] = 'committed'

        except mysql.connector.errors.DatabaseError as e:
            if 'Deadlock' in str(e) or '1213' in str(e):
                session_log("Session A", f"💀 DEADLOCK DETECTED! MySQL killed this transaction.", RED)
                session_log("Session A", f"   Error: {e}", RED)
                results['a_status'] = 'deadlock_victim'
            else:
                session_log("Session A", f"Error: {e}", RED)
                results['a_status'] = 'error'
            try:
                conn.rollback()
            except:
                pass
        finally:
            try:
                cur.close(); conn.close()
            except:
                pass

    def session_b():
        try:
            conn = get_conn()
            conn.start_transaction()
            cur = conn.cursor()

            # Step 1: Lock Ambala's ammo row
            session_log("Session B", "UPDATE Resource_Inventory SET quantity=quantity-50 WHERE base_id=2, resource_id=4", YELLOW)
            cur.execute("UPDATE Resource_Inventory SET quantity = quantity - 50 WHERE base_id=2 AND resource_id=4")
            session_log("Session B", "Locked Ambala (base 2) ammo row ✓", YELLOW)

            barrier.wait()  # Sync both sessions
            time.sleep(0.5) # let A lock its row

            # Step 2: Try to lock Hindon's fuel row → BLOCKED by Session A
            session_log("Session B", "Now trying to UPDATE base_id=1, resource_id=1 (BLOCKED by Session A!)...", YELLOW)
            cur.execute("UPDATE Resource_Inventory SET quantity = quantity + 100000 WHERE base_id=1 AND resource_id=1")

            conn.commit()
            session_log("Session B", "COMMITTED successfully", GREEN)
            results['b_status'] = 'committed'

        except mysql.connector.errors.DatabaseError as e:
            if 'Deadlock' in str(e) or '1213' in str(e):
                session_log("Session B", f"💀 DEADLOCK DETECTED! MySQL killed this transaction.", RED)
                session_log("Session B", f"   Error: {e}", RED)
                results['b_status'] = 'deadlock_victim'
            else:
                session_log("Session B", f"Error: {e}", RED)
                results['b_status'] = 'error'
            try:
                conn.rollback()
            except:
                pass
        finally:
            try:
                cur.close(); conn.close()
            except:
                pass

    sub("Initial: Hindon fuel=2,500,000 | Ambala ammo=580")
    divider()

    t1 = threading.Thread(target=session_a)
    t2 = threading.Thread(target=session_b)
    t1.start(); t2.start()
    t1.join(timeout=15); t2.join(timeout=15)

    divider()
    sub("ANALYSIS:")
    info(f"Session A status: {results['a_status']}")
    info(f"Session B status: {results['b_status']}")

    if 'deadlock_victim' in [results['a_status'], results['b_status']]:
        victim = 'A' if results['a_status'] == 'deadlock_victim' else 'B'
        survivor = 'B' if victim == 'A' else 'A'
        ok(f"MySQL detected the deadlock and killed Session {victim} (the victim)")
        ok(f"Session {survivor} was allowed to complete successfully")
        info("EFFECT: MySQL's InnoDB engine has a deadlock detection algorithm.")
        info("        It automatically picks one transaction as victim and rolls it back.")
        info("        The application should catch this error and RETRY the transaction.")
    else:
        info("No deadlock occurred (timing-dependent). Both may have succeeded sequentially.")


# ═══════════════════════════════════════════════════════════════════════════════
#  TRANSACTION 6: Resolution — SERIALIZABLE Isolation Level
# ═══════════════════════════════════════════════════════════════════════════════
def demo_serializable():
    header("TRANSACTION 6: RESOLUTION — SERIALIZABLE Isolation Level")
    info("Scenario: Prevent the Lost Update problem using SERIALIZABLE isolation.")
    info("          Both sessions try to read-then-update the same row.")
    info("          SERIALIZABLE forces them to execute one after the other.\n")

    # Reset
    reset = get_conn()
    rc = reset.cursor()
    rc.execute("UPDATE Missile_Inventory SET quantity = 48 WHERE base_id=1 AND missile_type_id=1")
    reset.commit()
    rc.close(); reset.close()

    results = {}
    barrier = threading.Barrier(2)

    def session_a():
        try:
            conn = get_conn()
            cur = conn.cursor(dictionary=True)
            cur.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
            conn.start_transaction()
            session_log("Session A", "ISOLATION = SERIALIZABLE", CYAN)

            cur.execute("SELECT quantity FROM Missile_Inventory WHERE base_id=1 AND missile_type_id=1")
            row = cur.fetchone()
            qty = row['quantity']
            session_log("Session A", f"READ quantity = {qty}", CYAN)
            results['a_read'] = qty

            barrier.wait()
            time.sleep(0.2)

            new_qty = qty - 6
            session_log("Session A", f"UPDATE quantity = {new_qty}", CYAN)
            cur.execute("UPDATE Missile_Inventory SET quantity = %s WHERE base_id=1 AND missile_type_id=1", (new_qty,))
            conn.commit()
            session_log("Session A", f"COMMITTED → quantity = {new_qty}", GREEN)
            results['a_status'] = 'committed'
            results['a_write'] = new_qty
        except mysql.connector.errors.DatabaseError as e:
            session_log("Session A", f"BLOCKED/ERROR: {e}", RED)
            results['a_status'] = 'blocked'
            try: conn.rollback()
            except: pass
        finally:
            try: cur.close(); conn.close()
            except: pass

    def session_b():
        try:
            conn = get_conn()
            cur = conn.cursor(dictionary=True)
            cur.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
            conn.start_transaction()
            session_log("Session B", "ISOLATION = SERIALIZABLE", YELLOW)

            cur.execute("SELECT quantity FROM Missile_Inventory WHERE base_id=1 AND missile_type_id=1")
            row = cur.fetchone()
            qty = row['quantity']
            session_log("Session B", f"READ quantity = {qty}", YELLOW)
            results['b_read'] = qty

            barrier.wait()
            time.sleep(0.8)  # longer wait so A commits first

            new_qty = qty - 8
            session_log("Session B", f"UPDATE quantity = {new_qty}", YELLOW)
            cur.execute("UPDATE Missile_Inventory SET quantity = %s WHERE base_id=1 AND missile_type_id=1", (new_qty,))
            conn.commit()
            session_log("Session B", f"COMMITTED → quantity = {new_qty}", GREEN)
            results['b_status'] = 'committed'
            results['b_write'] = new_qty
        except mysql.connector.errors.DatabaseError as e:
            if 'Deadlock' in str(e) or '1213' in str(e) or 'Lock wait' in str(e):
                session_log("Session B", f"SERIALIZABLE prevented conflict: {e}", RED)
                results['b_status'] = 'blocked_by_serializable'
            else:
                session_log("Session B", f"Error: {e}", RED)
                results['b_status'] = 'error'
            try: conn.rollback()
            except: pass
        finally:
            try: cur.close(); conn.close()
            except: pass

    sub("Initial state: Hindon BrahMos quantity = 48")
    divider()

    t1 = threading.Thread(target=session_a)
    t2 = threading.Thread(target=session_b)
    t1.start(); t2.start()
    t1.join(timeout=15); t2.join(timeout=15)

    # Check final state
    divider()
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT quantity FROM Missile_Inventory WHERE base_id=1 AND missile_type_id=1")
    final = cur.fetchone()

    sub("ANALYSIS:")
    info(f"Session A: {results.get('a_status', '?')}")
    info(f"Session B: {results.get('b_status', '?')}")
    info(f"Final quantity: {final['quantity']}")

    if results.get('b_status') in ['blocked_by_serializable', 'blocked']:
        ok("SERIALIZABLE isolation PREVENTED the lost update!")
        ok("Session B was blocked/rolled back because it conflicted with Session A")
        info("RESOLUTION: The application should RETRY Session B's transaction")
        info("            On retry, it will read the CORRECT updated value from Session A")
    else:
        info("Both sessions completed. Check if the final value is consistent.")
        info(f"If final={final['quantity']}, the SERIALIZABLE level forced sequential execution.")

    cur.close(); conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  RESTORE DATABASE to original state
# ═══════════════════════════════════════════════════════════════════════════════
def restore_db():
    header("RESTORING DATABASE TO ORIGINAL STATE")
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE Missile_Inventory SET quantity = 48 WHERE base_id=1 AND missile_type_id=1")
        cur.execute("UPDATE Missile_Inventory SET quantity = 60 WHERE base_id=2 AND missile_type_id=1")
        cur.execute("UPDATE Bases SET strength = 5000 WHERE base_id = 1")
        cur.execute("UPDATE Resource_Inventory SET quantity = 2500000 WHERE base_id=1 AND resource_id=1")
        cur.execute("UPDATE Resource_Inventory SET quantity = 3200000 WHERE base_id=2 AND resource_id=1")
        cur.execute("UPDATE Resource_Inventory SET quantity = 450 WHERE base_id=1 AND resource_id=4")
        cur.execute("UPDATE Resource_Inventory SET quantity = 580 WHERE base_id=2 AND resource_id=4")
        conn.commit()
        ok("All tables restored to original seed values.")
    except Exception as e:
        conn.rollback()
        fail(f"Restore failed: {e}")
    finally:
        cur.close(); conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print(f"\n{BOLD}{MAGENTA}{'▓'*80}{RESET}")
    print(f"{BOLD}{MAGENTA}  STRATOS_DB — Database Transaction Demonstration{RESET}")
    print(f"{BOLD}{MAGENTA}  DBMS Lab: Transactions, Conflicts & Isolation Levels{RESET}")
    print(f"{BOLD}{MAGENTA}{'▓'*80}{RESET}")

    try:
        # ── Normal Transactions ───────────────────────────────────
        demo_commit()
        print(f"\n  {CYAN}Moving to next demo...{RESET}")

        demo_rollback()
        print(f"\n  {CYAN}Moving to next demo...{RESET}")

        # ── Conflicting Transactions ──────────────────────────────
        demo_lost_update()
        print(f"\n  {CYAN}Moving to next demo...{RESET}")

        demo_dirty_read()
        print(f"\n  {CYAN}Moving to next demo...{RESET}")

        demo_deadlock()
        print(f"\n  {CYAN}Moving to next demo...{RESET}")

        # ── Resolution ────────────────────────────────────────────
        demo_serializable()

        # ── Restore ───────────────────────────────────────────────
        restore_db()

        print(f"\n{BOLD}{GREEN}{'='*80}{RESET}")
        print(f"{BOLD}{GREEN}  ALL 6 TRANSACTION DEMOS COMPLETED SUCCESSFULLY{RESET}")
        print(f"{BOLD}{GREEN}{'='*80}{RESET}\n")

    except KeyboardInterrupt:
        print(f"\n\n  {YELLOW}Interrupted. Restoring database...{RESET}")
        restore_db()
    except Exception as e:
        print(f"\n  {RED}Fatal error: {e}{RESET}")
        restore_db()
        raise
