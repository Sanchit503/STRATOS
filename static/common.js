/* ═══════════════════════════════════════════════════════
   STRATOS — Shared Utilities
   ═══════════════════════════════════════════════════════ */

// ── Toast Notifications ───────────────────────────────
function showToast(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    const t = document.createElement('div');
    t.className = `toast toast-${type}`;
    t.textContent = message;
    container.appendChild(t);
    setTimeout(() => t.remove(), 3000);
}

// ── Modal Helpers ─────────────────────────────────────
function openModal(id) {
    document.getElementById(id).classList.add('show');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('show');
}

// ── API Fetch Wrapper ─────────────────────────────────
async function api(url, options = {}) {
    try {
        if (options.body && typeof options.body === 'object') {
            options.headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
            options.body = JSON.stringify(options.body);
        }
        const res = await fetch(url, options);
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Request failed');
        return data;
    } catch (e) {
        showToast(e.message, 'error');
        throw e;
    }
}

// ── Sidebar Toggle ────────────────────────────────────
function toggleNav() {
    document.getElementById('sidenav').classList.toggle('open');
}

// ── Badge Helpers ─────────────────────────────────────
function statusBadge(status) {
    const map = {
        'Active': 'badge-green',
        'Under Maintenance': 'badge-orange',
        'Inactive': 'badge-dim',
        'Fully Operational': 'badge-green',
        'Partially Operational': 'badge-yellow',
        'Damaged': 'badge-red',
        'Critical': 'badge-red',
        'Operational': 'badge-green',
        'Decommissioned': 'badge-dim'
    };
    return `<span class="badge ${map[status] || 'badge-dim'}">${status}</span>`;
}

function threatBadge(level) {
    const map = {
        'Critical': 'badge-red',
        'High': 'badge-orange',
        'Medium': 'badge-yellow',
        'Low': 'badge-dim'
    };
    return `<span class="badge ${map[level] || 'badge-dim'}">${level}</span>`;
}

function readinessBadge(readiness) {
    const map = {
        'Fully Ready': 'badge-green',
        'Ready with Support': 'badge-yellow',
        'Vulnerable': 'badge-orange',
        'Critical': 'badge-red'
    };
    return `<span class="badge ${map[readiness] || 'badge-dim'}">${readiness || '—'}</span>`;
}

function fuelBar(level) {
    const cls = level >= 60 ? 'fuel-ok' : level >= 30 ? 'fuel-mid' : 'fuel-low';
    return `<div class="fuel-bar"><div class="fuel-fill ${cls}" style="width:${level}%"></div></div>
            <span style="font-size:11px;color:${level < 30 ? 'var(--red)' : 'var(--dim)'};font-family:'JetBrains Mono',monospace;font-weight:600;">${level}%</span>`;
}

// ── Number Formatting ─────────────────────────────────
function fmt(n) {
    return n != null ? Number(n).toLocaleString() : '—';
}

// ═══════════════════════════════════════════════════════
//  Feature-Page Transaction Runner
//  Reusable: call runFeatureTx('t1') from any page
// ═══════════════════════════════════════════════════════

const _TX_SQL_CHAINS = {
    t1: [
        '-- T1: Atomic Fuel Transfer (Ambala → Halwara)',
        'START TRANSACTION;',
        'UPDATE Resource_Inventory SET quantity = quantity - 400000',
        '  WHERE base_id = 2 AND resource_id = 1;',
        'UPDATE Resource_Inventory SET quantity = quantity + 400000,',
        "  status = 'Adequate' WHERE base_id = 3 AND resource_id = 1;",
        'INSERT INTO Logistics_Transfer (source_base_id, transfer_base_id,',
        "  resource_id, quantity_transferred, start_date, status)",
        "  VALUES (2, 3, 1, 400000, CURDATE(), 'Completed');",
        'COMMIT;',
    ],
    t2: [
        '-- T2: Mission Deployment (Tezpur — Agni-V)',
        'START TRANSACTION;',
        'UPDATE Missile_Inventory SET quantity = quantity - 1',
        '  WHERE base_id = 12 AND missile_type_id = 10;',
        "UPDATE Personnel SET avail_status = 'In Mission'",
        "  WHERE base_id = 12 AND role = 'Pilot' LIMIT 1;",
        'INSERT INTO Attack_Simulation (target_base_id, base_id,',
        "  simulation_type, simulation_date, readiness_level, recommendation)",
        "  VALUES (3, 12, 'Ballistic Strike', CURDATE(), 'High', ...);",
        'COMMIT;',
    ],
    t3: [
        '-- T3: Emergency Restock with SAVEPOINT',
        'START TRANSACTION;',
        'UPDATE Resource_Inventory SET quantity = quantity - 200000',
        '  WHERE base_id = 1 AND resource_id = 1;',
        'UPDATE Resource_Inventory SET quantity = quantity + 200000',
        '  WHERE base_id = 4 AND resource_id = 1;',
        'SAVEPOINT before_ammo;',
        'UPDATE Resource_Inventory SET quantity = quantity - 100',
        '  WHERE base_id = 2 AND resource_id = 4;',
        'UPDATE Resource_Inventory SET quantity = quantity + 100',
        '  WHERE base_id = 4 AND resource_id = 4;',
        '-- ⚠ Security alert!',
        'ROLLBACK TO SAVEPOINT before_ammo;',
        'COMMIT;  -- Only fuel transfer kept',
    ],
    t8: [
        '-- T8: Explicit ROLLBACK — insufficient stock',
        'START TRANSACTION;',
        'UPDATE Missile_Inventory SET quantity = quantity + 99999',
        '  WHERE base_id = 2 AND missile_type_id = 1;',
        'UPDATE Missile_Inventory SET quantity = quantity - 99999',
        '  WHERE base_id = 1 AND missile_type_id = 1;',
        'SELECT quantity FROM Missile_Inventory',
        '  WHERE base_id = 1 AND missile_type_id = 1;',
        '-- Result: NEGATIVE! → ROLLBACK;',
    ],
};

function _sqlHighlight(line) {
    return line
        .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
        .replace(/\b(START TRANSACTION|COMMIT|ROLLBACK|ROLLBACK TO SAVEPOINT|SAVEPOINT|SELECT|UPDATE|INSERT INTO|DELETE|FROM|WHERE|SET|AND|OR|VALUES|LIMIT|JOIN|ON|FOR UPDATE)\b/g,'<span style="color:#c792ea;font-weight:700;">$1</span>')
        .replace(/\b(Resource_Inventory|Missile_Inventory|Logistics_Transfer|Personnel|Attack_Simulation|Readiness_Report)\b/g,'<span style="color:#ffcb6b;">$1</span>')
        .replace(/'([^']+)'/g,"<span style='color:#c3e88d;'>'$1'</span>")
        .replace(/(\b\d+\.?\d*\b)/g,'<span style="color:#f78c6c;">$1</span>')
        .replace(/(--.*$)/g,'<span style="color:rgba(255,255,255,0.25);font-style:italic;">$1</span>');
}

function _renderTxResult(txId, data) {
    // SQL chain
    const sqlLines = (_TX_SQL_CHAINS[txId] || []).map(l =>
        `<div style="font-family:'JetBrains Mono',monospace;font-size:11px;line-height:1.8;color:var(--dim);">${l ? _sqlHighlight(l) : '&nbsp;'}</div>`
    ).join('');
    const sqlBlock = sqlLines ? `
        <div style="margin-bottom:16px;">
            <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:var(--cyan);margin-bottom:8px;">SQL Chain</div>
            <div style="background:rgba(0,0,0,0.4);border:1px solid rgba(0,240,255,0.1);border-radius:8px;padding:12px 16px;">${sqlLines}</div>
        </div>` : '';

    // Before/After tables
    function miniTbl(tableData, beforeRows) {
        if (!tableData || !tableData.rows || !tableData.rows.length) return '';
        const keys = Object.keys(tableData.rows[0]);
        const hdr = keys.map(k => `<th style="padding:6px 10px;font-size:10px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);background:rgba(0,0,0,0.2);border-bottom:1px solid var(--glass-border);white-space:nowrap;">${k}</th>`).join('');
        const rows = tableData.rows.map((row, ri) => {
            const cells = keys.map(k => {
                let v = row[k]; if (v == null) v = '—';
                let style = 'padding:7px 10px;border-bottom:1px solid rgba(255,255,255,0.03);white-space:nowrap;';
                if (beforeRows && beforeRows[ri]) {
                    const bv = beforeRows[ri][k];
                    if (typeof v === 'number' && typeof bv === 'number') {
                        if (v > bv) style += 'color:var(--green);font-weight:700;';
                        else if (v < bv) style += 'color:var(--red);font-weight:700;';
                        else style += 'color:var(--muted);';
                    } else if (v !== bv) style += 'color:var(--cyan);font-weight:700;';
                }
                return `<td style="${style}">${v}</td>`;
            }).join('');
            return `<tr>${cells}</tr>`;
        }).join('');
        return `<div style="background:rgba(0,0,0,0.2);border:1px solid var(--glass-border);border-radius:8px;overflow:hidden;margin-bottom:8px;">
            <div style="padding:8px 12px;font-size:11px;font-weight:600;color:var(--dim);background:rgba(0,0,0,0.25);border-bottom:1px solid var(--glass-border);">${tableData.title}</div>
            <div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:12px;font-family:'JetBrains Mono',monospace;"><thead><tr>${hdr}</tr></thead><tbody>${rows}</tbody></table></div>
        </div>`;
    }

    const beforeHtml = data.before.map(t => miniTbl(t)).join('');
    const afterHtml = data.after.map((t, i) => miniTbl(t, data.before[i]?.rows)).join('');

    // Steps
    const stepsHtml = data.steps.map(s => {
        const sl = s.toLowerCase();
        let dotColor = 'var(--cyan)';
        if (sl.includes('commit')) dotColor = 'var(--green)';
        else if (sl.includes('rollback')) dotColor = 'var(--red)';
        else if (sl.includes('savepoint')) dotColor = 'var(--yellow)';
        else if (sl.includes('⚠') || sl.includes('deadlock') || sl.includes('error')) dotColor = 'var(--orange)';
        return `<div style="display:flex;align-items:flex-start;gap:10px;font-family:'JetBrains Mono',monospace;font-size:11px;line-height:1.6;">
            <div style="width:6px;height:6px;border-radius:50%;background:${dotColor};margin-top:5px;flex-shrink:0;box-shadow:0 0 6px ${dotColor};"></div>
            <div style="color:var(--text);">${s}</div>
        </div>`;
    }).join('');

    // Effects
    const isAnomaly = ['anomaly','deadlock','dirty_read','rolled_back'].includes(data.status);
    const effectColor = isAnomaly ? 'rgba(255,51,102,0.1)' : 'rgba(0,240,255,0.04)';
    const effectBorder = isAnomaly ? 'rgba(255,51,102,0.15)' : 'rgba(0,240,255,0.12)';
    const effectArrow = isAnomaly ? 'var(--red)' : 'var(--cyan)';
    const effectsHtml = data.effect.map(e =>
        `<div style="font-size:12px;color:var(--dim);display:flex;gap:10px;align-items:flex-start;line-height:1.6;"><span style="color:${effectArrow};font-family:monospace;">→</span>${e}</div>`
    ).join('');

    // Status
    const statusMap = { committed:'COMMITTED', partial_commit:'PARTIAL COMMIT', anomaly:'ANOMALY', deadlock:'DEADLOCK', resolved:'RESOLVED', dirty_read:'DIRTY READ', rolled_back:'ROLLED BACK' };
    const statusLabel = statusMap[data.status] || data.status.toUpperCase();
    const statusColor = isAnomaly ? 'var(--red)' : 'var(--green)';

    return `
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
            <span style="font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;padding:4px 12px;border-radius:100px;border:1px solid ${statusColor};color:${statusColor};background:rgba(0,0,0,0.2);">${statusLabel}</span>
        </div>
        ${sqlBlock}
        <div style="margin-bottom:16px;">
            <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:var(--muted);margin-bottom:8px;">Before State</div>
            ${beforeHtml}
        </div>
        <div style="margin-bottom:16px;">
            <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:var(--muted);margin-bottom:8px;">Execution Steps</div>
            <div style="background:rgba(0,0,0,0.35);border:1px solid var(--glass-border);border-radius:8px;padding:12px 16px;display:flex;flex-direction:column;gap:6px;">${stepsHtml}</div>
        </div>
        <div style="margin-bottom:16px;">
            <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:var(--muted);margin-bottom:8px;">After State</div>
            ${afterHtml}
        </div>
        <div>
            <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:var(--muted);margin-bottom:8px;">Effect on DB</div>
            <div style="background:${effectColor};border:1px solid ${effectBorder};border-radius:8px;padding:14px 16px;display:flex;flex-direction:column;gap:6px;">${effectsHtml}</div>
        </div>
    `;
}

async function runFeatureTx(txId, resultContainerId) {
    const container = document.getElementById(resultContainerId);
    container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--muted);">Running transaction…</div>';
    container.style.display = 'block';
    try {
        const data = await api(`/api/transactions/${txId}`, { method: 'POST' });
        container.innerHTML = _renderTxResult(txId, data);
    } catch(e) {
        container.innerHTML = `<div style="color:var(--red);padding:14px;">Error: ${e.message}</div>`;
    }
}
