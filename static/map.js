// ══════════════════════════════════════════════════════════
// STRATOS Strategic Map — map.js
// ══════════════════════════════════════════════════════════

// ── Map init ──────────────────────────────────────────────
const map = L.map('map', {
  center: [22.5, 78.9],
  zoom: 5,
  minZoom: 3,
  maxZoom: 16,
  worldCopyJump: false,
  maxBounds: [[-85, -180], [85, 180]],   // prevent panning beyond one world
  maxBoundsViscosity: 1.0
});

// noWrap: true prevents the repeated world copies on zoom out
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  subdomains: 'abcd',
  maxZoom: 19,
  noWrap: true
}).addTo(map);

// ── Layer groups (one per toggle category) ────────────────
const L$ = {
  af: L.layerGroup().addTo(map),
  naval: L.layerGroup().addTo(map),
  ecrit: L.layerGroup().addTo(map),
  ehigh: L.layerGroup().addTo(map),
  emed: L.layerGroup().addTo(map),
  elow: L.layerGroup().addTo(map),
  ranges: L.layerGroup().addTo(map),
  lines: L.layerGroup().addTo(map),
  dist: L.layerGroup().addTo(map),
};

// ── State ─────────────────────────────────────────────────
let allFriendly = [];
let allEnemy = [];
let allMissileTypes = []; // For the Add New Missile dropdown
let distMode = false;
let distPts = [];
let lpOpen = true;

// ══════════════════════════════════════════════════════════
// DATA LOADING
// ══════════════════════════════════════════════════════════
async function init() {
  try {
    const [fr, er, geo, mtypes] = await Promise.all([
      fetch('/api/bases'),
      fetch('/api/enemy-bases'),
      fetch('/static/india.geojson').catch(() => null),
      fetch('/api/missile-types')
    ]);

    if (!fr.ok || !er.ok || !mtypes.ok) {
      console.error('API request failed:', { bases: fr.status, enemy: er.status, missiles: mtypes.status });
      mapToast('Failed to load base data. Check server connection.', 'error');
      return;
    }

    allFriendly = await fr.json();
    allEnemy = await er.json();
    allMissileTypes = await mtypes.json();

    if (geo && geo.ok) {
      try {
        const geoData = await geo.json();
        // 1. A thick, faded path under the main border acting as a faux, pre-rendered blur "glow"
        L.geoJSON(geoData, {
          style: {
            color: '#06b6d4',
            weight: 12,        // thick stroke 
            opacity: 0.25,     // faded to look like a halo
            fillColor: '#06b6d4',
            fillOpacity: 0.08, // Keep the solid interior tint
            className: 'glowing-halo'
          },
          renderer: L.svg({ padding: 1.0, clip: false }),
          interactive: false
        }).addTo(map);

        // 2. The sharp, dashed main tactical line riding on top
        L.geoJSON(geoData, {
          style: {
            color: '#22d3ee',  // slightly brighter cyan
            weight: 2.5,
            opacity: 1.0,
            fill: false,       // don't double up the fill
            className: 'tactical-border-dash'
          },
          // Use a custom SVGRenderer that explicitly disabled clipping
          renderer: L.svg({ padding: 1.0, clip: false }),
          interactive: false // So it doesn't block mouse events for targets below
        }).addTo(map);
      } catch (e) {
        console.warn("Could not load border geojson", e);
      }
    }

    renderFriendly();
    renderEnemy();
    updateCounts();
  } catch (e) {
    console.error('Failed to initialize map data:', e);
    mapToast('Error loading map data. Please refresh the page.', 'error');
  }
}

// ══════════════════════════════════════════════════════════
// ICON FACTORIES
// ══════════════════════════════════════════════════════════
function afIcon(base) {
  const sz = clamp(Math.round((base.strength || 1000) / 140), 38, 60);
  const rc = readinessColor(base.overall_readiness);

  // Clean vector jet icon
  const svg = `<svg viewBox="0 0 24 24" fill="currentColor" width="${sz * 0.5}" height="${sz * 0.5}"><path d="M12,2A2,2 0 0,1 14,4C14,4.74 13.6,5.39 13,5.73V7.5L19.5,11.5V13.5L13,11.5V17.5L15,19V20.5L12,19.5L9,20.5V19L11,17.5V11.5L4.5,13.5V11.5L11,7.5V5.73C10.4,5.39 10,4.74 10,4A2,2 0 0,1 12,2Z"/></svg>`;

  const alert = base.depleted_missiles > 0 ? `<div class="alert-dot"></div>` : '';

  return L.divIcon({
    className: '',
    html: `<div class="mm mm-af" style="width:${sz}px;height:${sz}px;border-color:${rc};">
             <span class="mm-sym">${svg}</span>
             ${alert}
           </div>`,
    iconSize: [sz, sz],
    iconAnchor: [sz / 2, sz / 2]
  });
}

function navalIcon(base) {
  const sz = clamp(Math.round((base.strength || 1000) / 140), 38, 60);
  const rc = readinessColor(base.overall_readiness);
  const alert = base.depleted_missiles > 0 ? `<div class="alert-dot"></div>` : '';

  // Clean vector anchor icon
  const svg = `<svg viewBox="0 0 24 24" fill="currentColor" width="${sz * 0.5}" height="${sz * 0.5}"><path d="M12,2A3,3 0 0,1 15,5A3,3 0 0,1 12,8A3,3 0 0,1 9,5A3,3 0 0,1 12,2M12,4A1,1 0 0,0 11,5A1,1 0 0,0 12,6A1,1 0 0,0 13,5A1,1 0 0,0 12,4M15,10V11H13V15.5L15.9,16.5L16.2,16.4C16.8,16 17,15.3 16.7,14.6L16.4,14L18.2,13.4L18.5,14C19,15.2 18.6,16.5 17.5,17.2L17.2,17.4L13,18.8V20H15V22H9V20H11V18.8L6.8,17.4L6.5,17.2C5.4,16.5 5,15.2 5.5,14L5.8,13.4L7.6,14L7.3,14.6C7,15.3 7.2,16 7.8,16.4L8.1,16.5L11,15.5V11H9V10H15M4,10C4,14.4 7.6,18 12,18C16.4,18 20,14.4 20,10H18C18,13.3 15.3,16 12,16C8.7,16 6,13.3 6,10H4Z"/></svg>`;

  return L.divIcon({
    className: '',
    html: `<div class="mm mm-naval" style="width:${sz}px;height:${sz}px;border-color:${rc};">
             <span class="mm-sym">${svg}</span>
             ${alert}
           </div>`,
    iconSize: [sz, sz],
    iconAnchor: [sz / 2, sz / 2]
  });
}

function enemyIcon(base) {
  const configs = {
    'Critical': { size: 40, icon: '☠️', glow: 'drop-shadow(0 0 12px #ff2020)' },
    'High': { size: 34, icon: '☠️', glow: 'drop-shadow(0 0 8px #fb923c)' },
    'Medium': { size: 28, icon: '☠️', glow: 'drop-shadow(0 0 4px #fbbf24)' },
    'Low': { size: 24, icon: '☠️', glow: 'none' }
  };

  const threat = configs[base.threat_level] || configs['Low'];

  return L.divIcon({
    className: '',
    html: `<div class="em-wrap em-wrap-${base.threat_level.toLowerCase()}" style="width:${threat.size}px; height:${threat.size}px; filter:${threat.glow}; display:flex; align-items:center; justify-content:center;">
             <div class="em em-${base.threat_level.toLowerCase()}" style="width:100%; height:100%; color:#fff; display:flex; align-items:center; justify-content:center;">
               <span class="em-sym" style="font-size:${threat.size * 0.55}px; line-height:1; display:flex; align-items:center; justify-content:center; text-shadow:0 0 4px rgba(0,0,0,0.8);">${threat.icon}</span>
             </div>
           </div>`,
    iconSize: [threat.size, threat.size],
    iconAnchor: [threat.size / 2, threat.size / 2]
  });
}

// ══════════════════════════════════════════════════════════
// RENDERING
// ══════════════════════════════════════════════════════════
function renderFriendly() {
  L$.af.clearLayers();
  L$.naval.clearLayers();

  allFriendly.forEach(base => {
    const isNaval = base.force_type === 'Naval';
    const icon = isNaval ? navalIcon(base) : afIcon(base);
    const key = isNaval ? 'naval' : 'af';
    const rc = readinessColor(base.overall_readiness);
    const sym = isNaval ? '⚓' : '✈️';

    const m = L.marker([base.latitude, base.longitude], { icon });
    m.bindTooltip(
      `<div style="text-align:center">
         <strong>${sym} ${base.base_name}</strong><br>
         <span style="color:${rc};font-size:11px">${readinessIcon(base.overall_readiness)} ${base.overall_readiness || 'N/A'}</span>
         <span style="color:#64748b;font-size:10px"> · ${base.force_type} · Str: ${(base.strength || 0).toLocaleString()}</span>
       </div>`,
      { className: 'mtt', direction: 'top', offset: [0, -18] }
    );
    m.on('click', () => onFriendly(base));
    L$[key].addLayer(m);
  });
}

// Lookup table: exact DB value → L$ key
const THREAT_LAYER = {
  'Critical': 'ecrit',
  'High': 'ehigh',
  'Medium': 'emed',
  'Low': 'elow',
};

function renderEnemy() {
  ['ecrit', 'ehigh', 'emed', 'elow'].forEach(k => L$[k].clearLayers());

  allEnemy.forEach(base => {
    const cfg = threatCfg(base.threat_level);
    // Robust lookup — any unrecognised level falls back to 'elow'
    const key = THREAT_LAYER[base.threat_level] || 'elow';

    if (!base.latitude || !base.longitude) return; // skip malformed rows

    const m = L.marker([base.latitude, base.longitude], { icon: enemyIcon(base) });
    m.bindTooltip(
      `<div style="text-align:center">
         <strong style="color:${cfg.color}">⚠ ${base.enemy_base_name}</strong><br>
         <span class="tbadge ${base.threat_level.toLowerCase()}">${base.threat_level} Threat</span>
       </div>`,
      { className: 'mtt', direction: 'top', offset: [0, -14] }
    );
    m.on('click', () => onEnemy(base));
    L$[key].addLayer(m);
  });
}

// ══════════════════════════════════════════════════════════
// LAYER PANEL
// ══════════════════════════════════════════════════════════
function toggleLayer(key) {
  if (map.hasLayer(L$[key])) {
    map.removeLayer(L$[key]);
  } else {
    map.addLayer(L$[key]);
  }
}

function toggleLP() {
  lpOpen = !lpOpen;
  document.getElementById('lp-body').style.display = lpOpen ? 'block' : 'none';
  document.getElementById('lp-chev').textContent = lpOpen ? '▾' : '▸';
}

function updateCounts() {
  const af = allFriendly.filter(b => b.force_type === 'Air Force').length;
  const nv = allFriendly.filter(b => b.force_type === 'Naval').length;
  document.getElementById('cnt-af').textContent = af;
  document.getElementById('cnt-naval').textContent = nv;
  document.getElementById('cnt-ecrit').textContent = allEnemy.filter(b => b.threat_level === 'Critical').length;
  document.getElementById('cnt-ehigh').textContent = allEnemy.filter(b => b.threat_level === 'High').length;
  document.getElementById('cnt-emed').textContent = allEnemy.filter(b => b.threat_level === 'Medium').length;
  document.getElementById('cnt-elow').textContent = allEnemy.filter(b => b.threat_level === 'Low').length;
  document.getElementById('tot-f').textContent = allFriendly.length;
  document.getElementById('tot-e').textContent = allEnemy.length;
}

// ══════════════════════════════════════════════════════════
// FRIENDLY BASE CLICK
// ══════════════════════════════════════════════════════════
async function onFriendly(base) {
  clearOverlays();
  const sym = base.force_type === 'Naval' ? '⚓' : '✈️';
  openSB('FRIENDLY BASE', `${sym} ${base.base_name}`,
    `${base.force_type} · ${base.operational_capability || ''} · ${base.status}`,
    '<div class="loader"><div class="spinner"></div></div>');

  const [dr, mr] = await Promise.all([
    fetch(`/api/base/${base.base_id}/details`),
    fetch(`/api/base/${base.base_id}/missiles`)
  ]);
  const det = await dr.json();
  const missiles = await mr.json();

  drawRanges(base, missiles);

  let h = '';

  // Container for Default View
  h += `<div id="sb-default-view">`;

  // Readiness badge
  if (det.readiness) {
    const rc = readinessClass(det.readiness.overall_readiness);
    h += `<div class="rbadge ${rc}">${readinessIcon(det.readiness.overall_readiness)} ${det.readiness.overall_readiness}</div>`;
    if (det.readiness.strategic_recomm)
      h += `<div class="recbox"><strong>Assessment:</strong> ${det.readiness.strategic_recomm}</div>`;
  }

  // Actual counts grid (Personnel, Missiles, Vehicles, Resources)
  const counts = det.counts || {};
  h += `<div class="mgrid mgrid-4">
    <div class="mcard"><div class="mcard-lbl">Personnel</div><div class="mcard-val">${(counts.personnel || 0).toLocaleString()}</div></div>
    <div class="mcard"><div class="mcard-lbl">Missiles</div><div class="mcard-val" style="${counts.missiles === 0 ? 'color:#fca5a5;' : ''}">${(counts.missiles || 0).toLocaleString()}</div></div>
    <div class="mcard"><div class="mcard-lbl">Vehicles</div><div class="mcard-val">${(counts.vehicles || 0).toLocaleString()}</div></div>
    <div class="mcard"><div class="mcard-lbl">Resources</div><div class="mcard-val">${(counts.resources || 0).toLocaleString()}</div></div>
  </div>`;

  // Strength


  // Missiles
  if (det.missiles?.length) {
    h += makeSection('🚀 Missile Arsenal', det.missiles.length,
      det.missiles.map(m => {
        const warning = m.quantity < 5 ? `<div class="depleted-badge">⚠ Low Stock</div>` : '';
        return `<div class="irow">
                  <div>
                    <div class="iname" style="display:flex;align-items:center;gap:6px;">${m.missile_name} ${warning}</div>
                    <div class="imeta">${m.category} · ${m.max_range} km</div>
                  </div>
                  <div class="iqty" style="${m.quantity < 5 ? 'color:#fca5a5;' : ''}">×${m.quantity}</div>
                </div>`;
      }).join('')
    );
  }

  // Manage Inventory Button
  h += `<button class="btn-manage" onclick="toggleInventoryView()">⚙️ Manage Missile Inventory</button>`;

  // Vehicles
  if (det.vehicles?.length)
    h += makeSection('🚗 Vehicle Inventory', det.vehicles.length,
      det.vehicles.map(v =>
        `<div class="irow"><div><div class="iname">${v.vehicle_name}</div><div class="imeta">${v.category} · ${v.operational_status}</div></div><div class="iqty">×${v.quantity}</div></div>`
      ).join(''));

  // Personnel
  if (det.personnel?.length)
    h += makeSection('👤 Personnel', det.personnel.length,
      det.personnel.map(p =>
        `<div class="irow"><div><div class="iname">${p.role}</div><div class="imeta">${p.avail_status}</div></div><div class="iqty">${p.count}</div></div>`
      ).join(''));

  h += `</div>`; // End Default View

  // Container for Manage Inventory View
  h += `<div id="sb-manage-view" class="inv-view">`;
  h += `<button class="btn-manage" style="margin-top:0; margin-bottom:10px;" onclick="toggleInventoryView()">← Back to Overview</button>`;
  h += `<div class="sec-hd" style="padding:0; border:none; margin-bottom:5px;"><span class="sec-title">Manage Missiles</span></div>`;

  // Existing missile forms
  if (det.missiles?.length) {
    det.missiles.forEach((m, idx) => {
      h += `
        <div class="inv-row">
          <div class="inv-row-header">
            <span class="inv-m-name">${m.missile_name}</span>
            <span style="font-size:10px; color:var(--dim)">${m.category}</span>
          </div>
          <div class="inv-controls">
            <div class="inv-input-group" style="flex:0.4">
              <label>Qty</label>
              <div class="qty-control">
                <button class="qty-btn" onclick="document.getElementById('qty-${base.base_id}-${idx}').value = Math.max(0, parseInt(document.getElementById('qty-${base.base_id}-${idx}').value) - 1)">-</button>
                <input class="qty-input" type="number" id="qty-${base.base_id}-${idx}" value="${m.quantity}" min="0">
                <button class="qty-btn" onclick="document.getElementById('qty-${base.base_id}-${idx}').value = parseInt(document.getElementById('qty-${base.base_id}-${idx}').value) + 1">+</button>
              </div>
            </div>
            <div class="inv-input-group">
              <label>Status</label>
              <select class="inv-input" id="status-${base.base_id}-${idx}">
                <option value="Operational" ${m.operational_status === 'Operational' ? 'selected' : ''}>Operational</option>
                <option value="Under Maintenance" ${m.operational_status === 'Under Maintenance' ? 'selected' : ''}>Maintenance</option>
                <option value="Decommissioned" ${m.operational_status === 'Decommissioned' ? 'selected' : ''}>Decommissioned</option>
              </select>
            </div>
          </div>
          <div style="display:flex; justify-content:flex-end;">
            <button class="btn-save" onclick="saveMissile(${base.base_id}, ${m.missile_type_id}, 'qty-${base.base_id}-${idx}', 'status-${base.base_id}-${idx}')">Save</button>
          </div>
        </div>
      `;
    });
  }

  // Add New Missile form
  let opts = allMissileTypes.map(mt => `<option value="${mt.missile_type_id}">${mt.missile_name} (${mt.category})</option>`).join('');
  h += `
    <div class="inv-row inv-add-new">
      <div class="inv-row-header">
        <span class="inv-m-name" style="color:var(--green)">+ Add New Missile</span>
      </div>
      <div class="inv-controls">
        <div class="inv-input-group">
          <label>Type</label>
          <select class="inv-input" id="new-m-type-${base.base_id}">${opts}</select>
        </div>
      </div>
      <div class="inv-controls" style="margin-top:10px;">
        <div class="inv-input-group" style="flex:0.4">
          <label>Qty</label>
          <input class="inv-input" type="number" id="new-m-qty-${base.base_id}" value="0" min="0">
        </div>
        <div class="inv-input-group">
          <label>Status</label>
          <select class="inv-input" id="new-m-status-${base.base_id}">
             <option value="Operational">Operational</option>
             <option value="Under Maintenance">Maintenance</option>
          </select>
        </div>
      </div>
      <div style="display:flex; justify-content:flex-end;">
        <button class="btn-add" onclick="saveMissile(${base.base_id}, 'new-m-type-${base.base_id}', 'new-m-qty-${base.base_id}', 'new-m-status-${base.base_id}', true)">Add to Inventory</button>
      </div>
    </div>
  </div>`; // End Manage View

  document.getElementById('sb-body').innerHTML = h;
}

// ══════════════════════════════════════════════════════════
// INVENTORY ACTIONS
// ══════════════════════════════════════════════════════════
window.toggleInventoryView = function () {
  const def = document.getElementById('sb-default-view');
  const man = document.getElementById('sb-manage-view');
  if (def.style.display === 'none') {
    def.style.display = 'block';
    man.style.display = 'none';
  } else {
    def.style.display = 'none';
    man.style.display = 'flex';
  }
};

window.saveMissile = async function (baseId, typeIdOrElemId, qtyElemId, statusElemId, isNew = false) {
  let typeId = isNew ? document.getElementById(typeIdOrElemId).value : typeIdOrElemId;
  let qty = document.getElementById(qtyElemId).value;
  let status = document.getElementById(statusElemId).value;

  try {
    const res = await fetch(`/api/base/${baseId}/inventory/missile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        missile_type_id: parseInt(typeId),
        quantity: parseInt(qty),
        operational_status: status
      })
    });

    if (res.ok) {
      // Re-fetch everything gracefully to update marks and sidebar
      await init();
      const b = allFriendly.find(f => f.base_id === baseId);
      if (b) await onFriendly(b);
      // Force back to inventory view
      document.getElementById('sb-default-view').style.display = 'none';
      document.getElementById('sb-manage-view').style.display = 'flex';
      mapToast('Inventory saved successfully.', 'success');
    } else {
      mapToast('Failed to save missile inventory.', 'error');
    }
  } catch (e) {
    console.error(e);
    mapToast('Error communicating with server.', 'error');
  }
};

// ══════════════════════════════════════════════════════════
// DRAW MISSILE RANGE CIRCLES
// ══════════════════════════════════════════════════════════
function drawRanges(base, missiles) {
  L$.ranges.clearLayers();
  L$.lines.clearLayers();

  const colors = ['#06b6d4', '#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ec4899'];
  let maxR = 0;

  // Deduplicate similar ranges (group within 50 km)
  const seen = new Set();
  const uniq = [];
  missiles.forEach(m => {
    const k = Math.round(m.max_range / 50) * 50;
    if (!seen.has(k)) { seen.add(k); uniq.push(m); }
    if (m.max_range > maxR) maxR = m.max_range;
  });

  uniq.forEach((m, i) => {
    const color = colors[i % colors.length];
    L.circle([base.latitude, base.longitude], {
      radius: m.max_range * 1000,
      fillColor: color, fillOpacity: 0.04,
      color: color, weight: 1, opacity: 0.4, dashArray: '6 4'
    })
      .bindTooltip(`${m.missile_name}: ${m.max_range} km`, { className: 'mtt', sticky: true })
      .addTo(L$.ranges);
  });

  // Highlight enemies within max range
  if (maxR > 0) {
    allEnemy.forEach(e => {
      const d = haversine(base.latitude, base.longitude, e.latitude, e.longitude);
      if (d <= maxR) {
        L.circleMarker([e.latitude, e.longitude], {
          radius: 13, fillColor: '#fbbf24', fillOpacity: 0.2,
          color: '#fbbf24', weight: 2.5, dashArray: '4 3'
        })
          .bindTooltip(`🎯 ${e.enemy_base_name} — ${d.toFixed(0)} km`, { className: 'mtt' })
          .addTo(L$.lines);
      }
    });
  }
}

// ══════════════════════════════════════════════════════════
// ENEMY BASE CLICK
// ══════════════════════════════════════════════════════════
async function onEnemy(base) {
  clearOverlays();
  openSB('ENEMY TARGET', `⚠ ${base.enemy_base_name}`,
    `<span class="tbadge ${base.threat_level.toLowerCase()}">${base.threat_level} Threat</span>`,
    '<div class="loader"><div class="spinner"></div></div>');

  const res = await fetch(`/api/enemy-base/${base.enemy_base_id}/reachable`);
  const data = await res.json();

  let h = `<div class="tbadge ${base.threat_level.toLowerCase()}" style="font-size:12px;padding:7px 14px;">⚠ Threat Level: ${base.threat_level}</div>`;
  h += `<div class="mgrid">
    <div class="mcard"><div class="mcard-lbl">Latitude</div><div class="mcard-val" style="font-size:12px">${base.latitude.toFixed(4)}°</div></div>
    <div class="mcard"><div class="mcard-lbl">Longitude</div><div class="mcard-val" style="font-size:12px">${base.longitude.toFixed(4)}°</div></div>
  </div>`;

  if (data.recommendation)
    h += `<div class="recbox"><strong>Strike Recommendation:</strong> ${data.recommendation}</div>`;

  if (data.reachable_bases?.length) {
    const rows = data.reachable_bases.map((rb, idx) => {
      const isNearest = idx === 0;
      const ico = rb.force_type === 'Air Force' ? '✈️' : '⚓';
      const cls = rb.force_type === 'Air Force' ? 'af' : 'naval';
      const msl = rb.available_missiles.map(m => m.missile_name).join(', ');
      const nearestBadge = isNearest
        ? `<span style="font-size:9px;font-weight:700;color:#00ffaa;background:rgba(0,255,170,0.12);border:1px solid rgba(0,255,170,0.4);border-radius:4px;padding:1px 5px;margin-left:6px;letter-spacing:.5px;">⭐ NEAREST</span>`
        : '';
      const rowStyle = isNearest
        ? `style="border-left:2px solid #00ffaa;padding-left:6px;background:rgba(0,255,170,0.05);"`
        : '';
      return `<div class="rrow" ${rowStyle}>
        <div class="ricon ${cls}">${ico}</div>
        <div class="rinfo"><div class="rname">${rb.base_name}${nearestBadge}</div><div class="rmeta">${msl}</div></div>
        <div class="rdist" style="${isNearest ? 'color:#00ffaa;font-weight:700;' : ''}">${rb.distance_km.toFixed(0)} km</div>
      </div>`;
    }).join('');
    h += makeSection('🎯 Bases That Can Strike', data.reachable_bases.length, rows);

    // Draw strike lines — nearest base gets a distinct highlight
    data.reachable_bases.forEach((rb, idx) => {
      const isNearest = idx === 0;

      // Line to enemy base
      L.polyline([[rb.latitude, rb.longitude], [base.latitude, base.longitude]], {
        color:     isNearest ? '#00ffaa' : '#f59e0b',
        weight:    isNearest ? 2.5       : 1.5,
        opacity:   isNearest ? 0.85      : 0.45,
        dashArray: isNearest ? '10 4'    : '8 6'
      }).addTo(L$.lines);

      // Circle around the friendly base
      L.circleMarker([rb.latitude, rb.longitude], {
        radius:      isNearest ? 17        : 12,
        fillColor:   isNearest ? '#00ffaa' : '#3b82f6',
        fillOpacity: isNearest ? 0.30      : 0.20,
        color:       isNearest ? '#00ffaa' : '#3b82f6',
        weight:      isNearest ? 3         : 2.5,
        dashArray:   isNearest ? null      : '4 3'
      })
        .bindTooltip(
          isNearest
            ? `⭐ NEAREST — ${rb.base_name}<br>${rb.distance_km.toFixed(0)} km`
            : `${rb.base_name} — ${rb.distance_km.toFixed(0)} km`,
          { className: 'mtt', direction: 'top' }
        )
        .addTo(L$.lines);
    });
    L.circleMarker([base.latitude, base.longitude],
      { radius: 16, fillColor: 'transparent', fillOpacity: 0, color: '#ef4444', weight: 3, dashArray: '4 3' }).addTo(L$.lines);
  } else {
    h += `<div class="recbox"><strong>No friendly bases</strong> currently have missiles in range.</div>`;
  }

  document.getElementById('sb-body').innerHTML = h;
}

// ══════════════════════════════════════════════════════════
// DISTANCE CALCULATOR
// ══════════════════════════════════════════════════════════
function toggleDist() {
  distMode = !distMode;
  document.getElementById('dbtn').classList.toggle('active', distMode);
  document.getElementById('dtool').classList.toggle('active', distMode);
  map.getContainer().style.cursor = distMode ? 'crosshair' : '';
}

function clearDist() {
  distPts = [];
  L$.dist.clearLayers();
  document.getElementById('dres').textContent = '— km';
  if (distMode) toggleDist();
}

map.on('click', e => {
  if (!distMode) return;
  distPts.push(e.latlng);
  L.circleMarker(e.latlng, { radius: 5, fillColor: '#06b6d4', fillOpacity: 1, color: '#fff', weight: 1.5 }).addTo(L$.dist);

  if (distPts.length === 2) {
    const [p1, p2] = distPts;
    const d = haversine(p1.lat, p1.lng, p2.lat, p2.lng);
    document.getElementById('dres').textContent = `${d.toFixed(1)} km`;

    L.polyline([p1, p2], { color: '#06b6d4', weight: 2, opacity: 0.8, dashArray: '6 4' }).addTo(L$.dist);

    const mid = [(p1.lat + p2.lat) / 2, (p1.lng + p2.lng) / 2];
    L.marker(mid, {
      icon: L.divIcon({
        className: '',
        html: `<div style="background:rgba(10,16,30,.9);border:1px solid rgba(6,182,212,.3);border-radius:6px;
                   padding:3px 9px;font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;
                   color:#06b6d4;white-space:nowrap;transform:translate(-50%,-50%)">${d.toFixed(1)} km</div>`,
        iconSize: [0, 0]
      })
    }).addTo(L$.dist);

    distPts = [];
    toggleDist();
  }
});

// ══════════════════════════════════════════════════════════
// SIDEBAR HELPERS
// ══════════════════════════════════════════════════════════
function openSB(label, title, sub, body) {
  document.getElementById('sb-label').textContent = label;
  document.getElementById('sb-title').textContent = title;
  document.getElementById('sb-sub').innerHTML = sub;
  document.getElementById('sb-body').innerHTML = body;
  document.getElementById('sb').classList.add('open');
}

function closeSB() {
  document.getElementById('sb').classList.remove('open');
  clearOverlays();
}

function clearOverlays() {
  L$.ranges.clearLayers();
  L$.lines.clearLayers();
}

// ══════════════════════════════════════════════════════════
// TEMPLATE HELPERS
// ══════════════════════════════════════════════════════════
function makeSection(title, count, bodyHtml) {
  return `<div class="sec">
    <div class="sec-hd">
      <span class="sec-title">${title}</span>
      <span class="sec-cnt">${count}</span>
    </div>
    <div class="sec-body">${bodyHtml}</div>
  </div>`;
}

function scoreCard(label, val) {
  return `<div class="scard">
    <div class="scard-lbl">${label}</div>
    <div class="scard-val ${scoreClass(val)}">${val ?? '—'}</div>
  </div>`;
}

// ══════════════════════════════════════════════════════════
// UTILITY / LOOKUP FUNCTIONS
// ══════════════════════════════════════════════════════════
// Single haversine implementation for the entire file
function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function clamp(val, min, max) { return Math.max(min, Math.min(max, val)); }

// Inline toast for map page (common.js not loaded here)
function mapToast(message, type = 'info') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    container.style.cssText = 'position:fixed;top:70px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:8px;';
    document.body.appendChild(container);
  }
  const colors = { success: '#00ffaa', error: '#ff3366', info: '#22d3ee' };
  const t = document.createElement('div');
  t.style.cssText = `background:rgba(10,14,26,0.95);border:1px solid ${colors[type] || colors.info};color:${colors[type] || colors.info};padding:10px 18px;border-radius:8px;font-size:12px;font-weight:600;font-family:'Outfit',sans-serif;backdrop-filter:blur(12px);box-shadow:0 4px 20px rgba(0,0,0,0.4);animation:slideDown 0.3s ease;`;
  t.textContent = message;
  container.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; t.style.transition = 'opacity 0.3s'; setTimeout(() => t.remove(), 300); }, 3000);
}

function threatCfg(lvl) {
  // Used for tooltips and highlights — keep in sync with CSS gradient stops
  return {
    Critical: { color: '#ff2020', bg: 'rgba(255,32,32,0.25)' },
    High: { color: '#fb923c', bg: 'rgba(251,146,60,0.22)' },
    Medium: { color: '#fbbf24', bg: 'rgba(251,191,36,0.20)' },
    Low: { color: '#94a3b8', bg: 'rgba(148,163,184,0.18)' },
  }[lvl] || { color: '#94a3b8', bg: 'rgba(148,163,184,0.18)' };
}

function readinessColor(r) {
  return { 'Fully Ready': '#10b981', 'Ready with Support': '#f59e0b', 'Vulnerable': '#ef4444', 'Critical': '#dc2626' }[r] || '#64748b';
}

function readinessIcon(r) {
  return { 'Fully Ready': '🟢', 'Ready with Support': '🟡', 'Vulnerable': '🟠', 'Critical': '🔴' }[r] || '⚪';
}

function readinessClass(r) {
  return { 'Fully Ready': 'fr', 'Ready with Support': 'rs', 'Vulnerable': 'vul', 'Critical': 'crit' }[r] || '';
}

function scoreClass(s) { return !s ? '' : s >= 85 ? 'hi' : s >= 65 ? 'md' : 'lo'; }

// ══════════════════════════════════════════════════════════
// ══════════════════════════════════════════════════════════
// GLOBAL MISSILE COMMAND
// ══════════════════════════════════════════════════════════
window.openGlobalInventory = function () {
  clearOverlays();
  openSB('GLOBAL COMMAND', `🚀 Missile Inventory`, `Select a base to manage its arsenal`, '<div class="loader"><div class="spinner"></div></div>');

  let h = `<div class="global-inv-list">`;

  // Sort bases alphabetically
  const bases = [...allFriendly].sort((a, b) => a.base_name.localeCompare(b.base_name));

  bases.forEach(b => {
    const sym = b.force_type === 'Naval' ? '⚓' : '✈️';
    const warning = b.depleted_missiles > 0 ? `<div class="depleted-badge" style="display:inline-flex; margin-left:8px; font-size:8px;">⚠ Low Stock</div>` : '';

    h += `<div class="inv-row" style="cursor:default;">
      <div class="inv-row-header" style="margin-bottom:6px;">
        <span class="inv-m-name">${sym} ${b.base_name}</span>
        ${warning}
      </div>
      <div style="font-size:10px; color:var(--dim); margin-bottom: 10px;">${b.force_type} · ${b.status}</div>
      <button class="btn-manage" style="margin-top:0;" onclick="manageBaseInventory(${b.base_id})">⚙️ Manage Arsenal</button>
    </div>`;
  });

  h += `</div>`;
  document.getElementById('sb-body').innerHTML = h;
};

window.manageBaseInventory = async function (baseId) {
  const base = allFriendly.find(b => b.base_id === baseId);
  if (!base) return;

  await onFriendly(base);
  toggleInventoryView(); // Automatically open the edit view

  // Override the back button so it goes back to Global Inventory instead of single base overview
  const man = document.getElementById('sb-manage-view');
  const backBtn = man.querySelector('button.btn-manage');
  if (backBtn && backBtn.innerText.includes('Back')) {
    backBtn.innerText = '← Back to Global Command';
    backBtn.onclick = window.openGlobalInventory;
  }
};

init();

// ══════════════════════════════════════════════════════════
// MISSION MODE
// ══════════════════════════════════════════════════════════
let missionMode = false;
let missionFriendly = null;   // { base_id, base_name, latitude, longitude }
let missionEnemy = null;      // { enemy_base_id, enemy_base_name, latitude, longitude }
let missionStrikeLine = null;
let missionDistLabel = null;
let lastAnalysis = null;

function toggleMissionMode() {
  missionMode = !missionMode;
  const btn = document.getElementById('plan-strike-btn');
  const bar = document.getElementById('mission-bar');

  if (missionMode) {
    btn.classList.add('active');
    bar.classList.add('active');
    document.getElementById('map').classList.add('mission-mode');
    closeSB(); // close base sidebar so it doesn't overlap the mission panel
    resetMissionSelections();
  } else {
    btn.classList.remove('active');
    bar.classList.remove('active');
    document.getElementById('map').classList.remove('mission-mode');
    clearStrikeLine();
    closeDrawer();
    missionFriendly = null;
    missionEnemy = null;
  }
}

function resetMissionSelections() {
  missionFriendly = null;
  missionEnemy = null;
  document.getElementById('mb-step').textContent = 'STEP 1';
  document.getElementById('mb-inst').innerHTML = 'Click a <strong style="color:#22d3ee">friendly origin</strong> or <strong style="color:#ff3366">enemy target</strong>';
  document.getElementById('mb-sel').style.display = 'none';
  clearStrikeLine();
}

let missionRecLines = [];  // green suggestion lines only
let dotMarker = null;

function clearRecommendationLines() {
  missionRecLines.forEach(l => map.removeLayer(l));
  missionRecLines = [];
}

function clearStrikeLine() {
  if (missionStrikeLine) { map.removeLayer(missionStrikeLine); missionStrikeLine = null; }
  if (missionDistLabel) { map.removeLayer(missionDistLabel); missionDistLabel = null; }
  if (dotInterval) { clearInterval(dotInterval); dotInterval = null; }
  if (dotMarker) { map.removeLayer(dotMarker); dotMarker = null; }
  _strikeFb = null; _strikeEb = null; _strikeDist = null;
  clearRecommendationLines();
}

// Intercept the original onFriendly / onEnemy
const _origOnFriendly = onFriendly;
const _origOnEnemy = onEnemy;

window.onFriendly = async function (base) {
  if (missionMode) {
    missionFriendly = base;
    const sel = document.getElementById('mb-sel');

    if (!missionEnemy) {
      document.getElementById('mb-step').textContent = 'STEP 2';
      document.getElementById('mb-inst').innerHTML = 'Now click an <strong style="color:#ff3366">enemy target</strong>';
      sel.textContent = `Origin: ${base.base_name}`;
      sel.style.display = 'inline';
      clearStrikeLine();
    } else {
      sel.textContent = `Origin: ${base.base_name} · Target: ${missionEnemy.enemy_base_name}`;
      sel.style.display = 'inline';
      clearStrikeLine();
      drawStrikeLine(missionFriendly, missionEnemy);
      await runMissionAnalysis();
    }
    return;
  }
  return _origOnFriendly(base);
};

window.onEnemy = async function (base) {
  if (missionMode) {
    missionEnemy = base;
    const sel = document.getElementById('mb-sel');

    if (!missionFriendly) {
      document.getElementById('mb-step').textContent = 'STEP 2';
      sel.textContent = `Target: ${base.enemy_base_name}`;
      sel.style.display = 'inline';
      clearStrikeLine();
      await showRecommendedBasesForEnemy(base);
    } else {
      sel.textContent = `Origin: ${missionFriendly.base_name} · Target: ${base.enemy_base_name}`;
      sel.style.display = 'inline';
      clearStrikeLine();
      drawStrikeLine(missionFriendly, missionEnemy);
      await runMissionAnalysis();
    }
    return;
  }
  return _origOnEnemy(base);
};

async function showRecommendedBasesForEnemy(eb) {
  document.getElementById('mb-inst').innerHTML = '<em style="color:#64748b;">Finding recommended strike bases...</em>';
  const res = await fetch(`/api/mission/best-base?enemy_base_id=${eb.enemy_base_id}`);
  const bestBases = await res.json();

  if (bestBases.length === 0) {
    document.getElementById('mb-inst').innerHTML = '<strong style="color:#ff3366">No capable bases found.</strong> Select origin manually.';
    return;
  }

  document.getElementById('mb-inst').innerHTML = `Found <strong style="color:#00ffaa">${bestBases.length} recommended bases</strong>. Click one to test strike.`;
  const ebLatLng = [parseFloat(eb.latitude), parseFloat(eb.longitude)];

  bestBases.forEach(b => {
    const fbLatLng = [parseFloat(b.latitude), parseFloat(b.longitude)];
    const l = L.polyline([fbLatLng, ebLatLng], {
      color: '#00ffaa',
      weight: 1.5,
      dashArray: '5, 8',
      opacity: 0.6
    }).addTo(map);
    missionRecLines.push(l);

    const midLat = (fbLatLng[0] + ebLatLng[0]) / 2;
    const midLng = (fbLatLng[1] + ebLatLng[1]) / 2;
    const lbl = L.marker([midLat, midLng], {
      icon: L.divIcon({
        className: '',
        html: `<div style="background:rgba(5,7,14,0.7);border:1px solid #00ffaa;
                           border-radius:4px;padding:2px 6px;font-size:9px;
                           font-weight:700;color:#00ffaa;white-space:nowrap;">
                 ${b.distance_km} km
               </div>`,
        iconAnchor: [20, 10]
      }),
      interactive: false
    }).addTo(map);
    missionRecLines.push(lbl);
  });
}

// ── Bezier arc helpers ───────────────────────────────────
function bezQuad(t, p0, p1, p2) {
  const u = 1 - t;
  return u * u * p0 + 2 * u * t * p1 + t * t * p2;
}

function arcPoints(p0latLng, p2latLng, segments = 80) {
  // Convert to pixel space — Bezier in lat/lng looks wrong due to Mercator
  const px0 = map.latLngToLayerPoint(L.latLng(p0latLng));
  const px2 = map.latLngToLayerPoint(L.latLng(p2latLng));

  // Midpoint in pixel space
  const midX = (px0.x + px2.x) / 2;
  const midY = (px0.y + px2.y) / 2;

  // Distance in pixels between the two points
  const dx = px2.x - px0.x;
  const dy = px2.y - px0.y;
  const lenPx = Math.sqrt(dx * dx + dy * dy);

  // Control point: lift by 35% of pixel distance, perpendicular to the line (upward on screen = negative Y)
  // Perpendicular: (-dy, dx) normalised, then offset upward
  const lift = lenPx * 0.35;
  const nx = -dy / lenPx;  // perpendicular unit vector x
  const ny = dx / lenPx;  // perpendicular unit vector y
  // Pick the one that goes "upward" on screen (negative Y in screen coords)
  const sign = ny > 0 ? -1 : 1;
  const cpX = midX + sign * nx * lift;
  const cpY = midY + sign * ny * lift;

  const pts = [];
  for (let i = 0; i <= segments; i++) {
    const t = i / segments;
    const u = 1 - t;
    const x = u * u * px0.x + 2 * u * t * cpX + t * t * px2.x;
    const y = u * u * px0.y + 2 * u * t * cpY + t * t * px2.y;
    const ll = map.layerPointToLatLng(L.point(x, y));
    pts.push([ll.lat, ll.lng]);
  }

  // Apex = control point converted back to lat/lng (for label placement)
  const apexLL = map.layerPointToLatLng(L.point(cpX, cpY));
  return { pts, apex: [apexLL.lat, apexLL.lng] };
}

let dotInterval = null;

// Store current endpoints for zoom-level redraw
let _strikeFb = null;
let _strikeEb = null;
let _strikeDist = null;

function _renderStrikeArc(fbLatLng, ebLatLng, dist, fitBounds = false) {
  // Remove existing arc elements (but not the interval/dot — those are managed separately)
  if (missionStrikeLine) { map.removeLayer(missionStrikeLine); missionStrikeLine = null; }
  if (missionDistLabel) { map.removeLayer(missionDistLabel); missionDistLabel = null; }
  if (dotMarker) { map.removeLayer(dotMarker); dotMarker = null; }
  if (dotInterval) { clearInterval(dotInterval); dotInterval = null; }

  const { pts, apex } = arcPoints(fbLatLng, ebLatLng);

  // Draw glowing arc
  missionStrikeLine = L.polyline(pts, {
    color: '#ff3366',
    weight: 2,
    opacity: 0.85,
    className: 'strike-line'
  }).addTo(map);

  // Distance label at arc apex
  const labelHtml = `<div id="arc-dist-lbl" style="background:rgba(5,7,14,0.9);border:1px solid #ff3366;
                         border-radius:4px;padding:3px 10px;font-size:11px;
                         font-weight:700;color:#ff3366;white-space:nowrap;
                         font-family:monospace;box-shadow:0 0 12px rgba(255,51,102,0.4);">
               ◎ ${dist} km
             </div>`;
  missionDistLabel = L.marker(apex, {
    icon: L.divIcon({
      className: '',
      html: labelHtml,
      iconSize: [90, 24],
      iconAnchor: [45, 12]
    }),
    interactive: false
  }).addTo(map);

  // Animated missile dot traveling along arc
  let dotStep = 0;
  dotMarker = L.marker(pts[0], {
    icon: L.divIcon({
      className: '',
      html: `<div style="width:10px;height:10px;background:#ff3366;border-radius:50%;
                         box-shadow:0 0 10px #ff3366, 0 0 20px rgba(255,51,102,0.5);
                         transform:translate(-50%,-50%);"></div>`,
      iconAnchor: [0, 0]
    }),
    interactive: false
  }).addTo(map);

  dotInterval = setInterval(() => {
    dotStep = (dotStep + 1) % pts.length;
    dotMarker.setLatLng(pts[dotStep]);
  }, 30);

  if (fitBounds) {
    map.fitBounds(L.latLngBounds([fbLatLng, ebLatLng]), { padding: [120, 120], paddingTopLeft: [120, 120], paddingBottomRight: [460, 120], maxZoom: 6 });
  }
}

function drawStrikeLine(fb, eb) {
  clearStrikeLine();
  const fbLatLng = [parseFloat(fb.latitude), parseFloat(fb.longitude)];
  const ebLatLng = [parseFloat(eb.latitude), parseFloat(eb.longitude)];
  const dist = haversine(fbLatLng[0], fbLatLng[1], ebLatLng[0], ebLatLng[1]);

  // Store for zoom-redraw
  _strikeFb = fbLatLng;
  _strikeEb = ebLatLng;
  _strikeDist = dist;

  // Immediately remove any green suggestion lines
  clearRecommendationLines();

  _renderStrikeArc(fbLatLng, ebLatLng, dist, true);
}

// Redraw arc on zoom so Bezier stays correct
map.on('zoomend', () => {
  if (_strikeFb && _strikeEb && _strikeDist != null) {
    _renderStrikeArc(_strikeFb, _strikeEb, _strikeDist, false);
  }
});

// Duplicate haversine removed — using single definition above
// Duplicate clearStrikeLine removed — using single definition above

async function runMissionAnalysis() {
  // Update instruction bar to show "Analyzing..."
  document.getElementById('mb-step').textContent = 'ANALYZING';
  document.getElementById('mb-inst').innerHTML = `<em style="color:#64748b;">Running 7-check analysis...</em>`;

  const res = await fetch('/api/mission/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      friendly_base_id: missionFriendly.base_id,
      enemy_base_id: missionEnemy.enemy_base_id
    })
  });
  const data = await res.json();
  lastAnalysis = data;
  renderMissionDrawer(data);
}

function renderMissionDrawer(data) {
  document.getElementById('md-route').textContent = `${data.friendly_base} \u2192 ${data.enemy_base}`;
  document.getElementById('md-date').textContent = `Analysis: ${new Date().toLocaleString()}`;
  document.getElementById('md-dist').textContent = data.distance_km;
  document.getElementById('md-threat').textContent = data.threat_level;
  const tColors = { Critical: '#ff3366', High: '#fb923c', Medium: '#fbbf24', Low: '#22d3ee' };
  document.getElementById('md-threat').style.color = tColors[data.threat_level] || '#22d3ee';
  const passCount = data.checks.filter(c => c.status === 'PASS').length;
  document.getElementById('md-pass').textContent = `${passCount}/7`;

  const statusClass = { PASS: 'pass', WARNING: 'warning', FAIL: 'fail' };
  const statusLabel = { PASS: 'PASS', WARNING: 'WARN', FAIL: 'FAIL' };

  document.getElementById('md-checks').innerHTML = data.checks.map(c => `
    <div class="mc ${statusClass[c.status]}">
      <div class="mc-top">
        <span class="mc-num">CH${String(c.id).padStart(2, '0')}</span>
        <span class="mc-name">${c.name}</span>
        <span class="mc-badge ${statusClass[c.status]}">${statusLabel[c.status]}</span>
      </div>
      <div class="mc-result">${c.result}</div>
    </div>
  `).join('');

  const verdict = document.getElementById('md-verdict');
  verdict.className = `md-verdict ${data.decision_color}`;
  document.getElementById('mdv-decision').textContent = data.decision;
  document.getElementById('mdv-meta').textContent =
    `${data.failed_count} check(s) failed · ${data.warning_count} warning(s)`;
  document.getElementById('mdv-pkg-list').innerHTML = data.strike_package.length
    ? data.strike_package.map(p => `<span>◈ ${p}</span>`).join('')
    : '<span style="color:#475569;">Insufficient assets</span>';

  // Reset save button
  const saveBtn = document.getElementById('md-save-btn');
  saveBtn.disabled = false;
  saveBtn.textContent = 'Save Simulation';

  // Open drawer and hide zoom controls safely
  document.getElementById('mission-drawer').classList.add('open');
  const zc = document.getElementById('zoom-controls');
  if (zc) zc.style.display = 'none';

  // Update instruction bar
  document.getElementById('mb-step').textContent = 'DONE';
  document.getElementById('mb-inst').innerHTML =
    `<span style="color:#00ffaa;">Analysis complete.</span> Review results below.`;
}

function closeDrawer() {
  document.getElementById('mission-drawer').classList.remove('open');
  const zc = document.getElementById('zoom-controls');
  if (zc) zc.style.display = 'flex';
}

async function saveMissionFromDrawer() {
  if (!lastAnalysis || !missionFriendly || !missionEnemy) return;
  const btn = document.getElementById('md-save-btn');
  btn.disabled = true;
  btn.textContent = 'Saving...';

  const rec = lastAnalysis.strike_package.join('; ') || 'No package';
  const res = await fetch('/api/mission/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      friendly_base_id: missionFriendly.base_id,
      enemy_base_id: missionEnemy.enemy_base_id,
      decision: lastAnalysis.decision,
      recommendation: `${lastAnalysis.decision} — ${rec}`
    })
  });
  const d = await res.json();
  if (d.ok) {
    btn.textContent = `Saved #${d.simulation_id} ✓`;
  } else {
    btn.textContent = 'Save Simulation';
    btn.disabled = false;
  }
}
