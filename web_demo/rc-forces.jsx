// Calm to Camps — FORCE TOYS (experiment): "how the engine works, force by force".
//
// LIVE, SCHEMATIC mini-sims — not cc-data.js playback. Each toy runs one mechanism,
// alone, on a small population of individual dots, so you can watch a single force
// act and even poke it. Faithful in FORM to the engine's rules (the math shape),
// but illustrative, not a calibrated run — every real RESULT on this site still
// comes from the engine export. Keep that boundary loud in the chrome.
//
// ── ONE 3-D SPACE, A LOCKED CAMERA ──────────────────────────────────────────
// The scene is the same 3-D space as the "for the brave" view (rc-agents3d.jsx):
// a floor = the political compass (econ × cultural), and a VERTICAL axis = affect
// (out-party animus; Democrats rise, Republicans sink). We borrow that view's
// projection + styling directly. The camera is LOCKED straight-down (top-down),
// so the affect axis points at the viewer and the scene looks exactly 2-D — which
// is all forces 1–2 (position-only) ever need. For force 3 (affect) the camera
// TILTS to the oblique angle, revealing the hidden third axis the cooling has been
// happening along all along. The scissors, staged: same views, opposite feelings.
//
// ── ONE CHASSIS, MANY FORCES ────────────────────────────────────────────────
// `ForceToy` owns everything generic (canvas, 3-D draw, camera, transport,
// pointer, knob, readout, headless hooks). A FORCE is a descriptor:
//   { seed, step, lift?, overlay?, metric, knob, reveal?, focusable, copy }
// `lift(agent)` returns its height on the affect axis (0 = on the floor).
//
// Headless: the draw is synchronous (deterministic first frame though RAF is
// paused in the preview). window.__forceStep(n) / __forceMetric() / __forceReset()
// / __forceReveal(bool) drive the mechanism + camera without RAF, so every claim
// is checkable in a headless eval.

const { useState, useRef, useEffect, useLayoutEffect, useCallback } = React;

// ── helpers ─────────────────────────────────────────────────────────────────
const _hexA = (hex, a) => { const n = parseInt(hex.replace('#', ''), 16); return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`; };
const _clamp = (lo, hi, v) => (v < lo ? lo : v > hi ? hi : v);
const _fRgb = (hex) => { const n = parseInt(hex.replace('#', ''), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };
const _rgba = (c, a) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;
const _fLerp = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];

// scene constants (mirrors rc-agents3d.jsx)
const CAM = 4.2;                 // camera distance along +Z
const HEIGHT = 1.05;             // world lift for animus = 1
const CAM_TOP = { yaw: 0, pitch: Math.PI / 2 };   // straight down → looks 2-D
const CAM_OBL = { yaw: -0.62, pitch: 0.46 };      // the agents3d oblique reveal
const C_BORDER = [193, 188, 176], C_INK = [26, 29, 35], C_BG = [249, 248, 244];
const PRGB = { D: _fRgb(CC.d), R: _fRgb(CC.r), I: _fRgb(CC.i) };
const PSGN = { D: 1, R: -1, I: 0 };   // Democrats rise, Republicans sink

// editorial range-slider styling (the native blue control clashes with the
// palette). Injected once so it travels with the component through integration.
if (typeof document !== 'undefined' && !document.getElementById('cc-forces-style')) {
  const st = document.createElement('style');
  st.id = 'cc-forces-style';
  st.textContent = `
.cc-range{-webkit-appearance:none;appearance:none;height:3px;border-radius:999px;outline:none;cursor:pointer;}
.cc-range::-webkit-slider-thumb{-webkit-appearance:none;width:13px;height:13px;border-radius:999px;background:${CC.ink};border:2px solid ${CC.bg};box-shadow:0 1px 3px rgba(26,29,35,.28);cursor:pointer;}
.cc-range::-moz-range-thumb{width:13px;height:13px;border-radius:999px;background:${CC.ink};border:2px solid ${CC.bg};box-shadow:0 1px 3px rgba(26,29,35,.28);cursor:pointer;}
.cc-range::-moz-range-track{height:3px;border-radius:999px;background:transparent;}`;
  document.head.appendChild(st);
}

// ── populations ──────────────────────────────────────────────────────────────
// Party assigned INDEPENDENTLY of position → no camps at the start. Force 1 keeps
// the colours mixed (party-blind); force 2 is the one that pulls them apart.
function seedMixed(n, seed) {
  const rng = ccRng(seed);
  const out = [];
  for (let i = 0; i < n; i++) {
    const x = (rng() * 2 - 1) * 0.82, y = (rng() * 2 - 1) * 0.82;
    const r = rng();
    out.push({ x, y, party: r < 0.18 ? 'I' : r < 0.59 ? 'D' : 'R' });
  }
  return out;
}
// affect: a MODERATE, overlapping cloud (×0.55) with a per-agent out-party warmth
// that starts mildly warm. Moderate on purpose — the scissors point is "they're
// not even far apart in views, yet they come to loathe each other."
function seedAffect(n, seed) {
  const ags = seedMixed(n, seed);
  const rng = ccRng(seed + 99);
  for (const a of ags) { a.x *= 0.55; a.y *= 0.55; a.warm = 0.20 + (rng() - 0.5) * 0.2; }
  return ags;
}

// network: two loose camps (positions FIXED) wired by a party-blind web of ties.
// Rewiring changes only the EDGES — the dots never move. No independents here: the
// echo-chamber story is about the two camps sealing off from each other.
function seedNetwork(n, seed) {
  const rng = ccRng(seed);
  const out = [];
  for (let i = 0; i < n; i++) {
    const D = rng() < 0.5;
    const ctr = D ? { x: -0.44, y: -0.34 } : { x: 0.44, y: 0.34 };
    out.push({
      x: _clamp(-0.95, 0.95, ctr.x + (rng() - 0.5) * 0.7),
      y: _clamp(-0.95, 0.95, ctr.y + (rng() - 0.5) * 0.7),
      party: D ? 'D' : 'R', ties: new Set(), locked: new Set(),
    });
  }
  const K = 5;
  for (let i = 0; i < n; i++) {
    let tries = 0;
    while (out[i].ties.size < K && tries < 50) {
      const j = Math.floor(rng() * n);
      if (j !== i) { out[i].ties.add(j); out[j].ties.add(i); }
      tries++;
    }
  }
  // a fraction of ties are INVOLUNTARY (work, family, shared spaces) — they never
  // rewire, so a residue of cross-cutting bridges always survives.
  const LOCK = 0.15;
  for (let i = 0; i < n; i++) for (const j of out[i].ties) if (j > i && rng() < LOCK) { out[i].locked.add(j); out[j].locked.add(i); }
  return out;
}

// media: two moderate camps, each with a partisan OUTLET parked out past the
// corner (more extreme than anyone). Each agent has a `diet` — how heavily it
// consumes — skewed so most are light and a tail are heavy. Selective exposure:
// you only tune into your own side.
const MEDIA_OUTLET = { D: { x: -0.85, y: -0.68 }, R: { x: 0.85, y: 0.68 } };
function seedMedia(n, seed) {
  const rng = ccRng(seed);
  const out = [];
  for (let i = 0; i < n; i++) {
    const D = rng() < 0.5;
    const ctr = D ? { x: -0.32, y: -0.26 } : { x: 0.32, y: 0.26 };
    out.push({
      x: _clamp(-0.95, 0.95, ctr.x + (rng() - 0.5) * 0.5),
      y: _clamp(-0.95, 0.95, ctr.y + (rng() - 0.5) * 0.5),
      party: D ? 'D' : 'R',
      diet: rng() < 0.7 ? 0 : (0.5 + rng() * 0.5),   // ~30% tune in; the rest don't move
      outletKey: D ? 'D' : 'R',
    });
  }
  return out;
}

// backfire: a heavily-overlapping, party-mixed crowd (only a faint initial tilt),
// each carrying a warmth offset. The `hostility` knob sets the shared warmth level;
// `bias` gives per-agent spread so the threshold is crossed unevenly.
function seedBackfire(n, seed) {
  const rng = ccRng(seed);
  const out = [];
  for (let i = 0; i < n; i++) {
    const D = rng() < 0.5;
    const ctr = D ? { x: -0.1, y: -0.08 } : { x: 0.1, y: 0.08 };
    out.push({
      x: _clamp(-0.95, 0.95, ctr.x + (rng() - 0.5) * 0.6),
      y: _clamp(-0.95, 0.95, ctr.y + (rng() - 0.5) * 0.6),
      party: D ? 'D' : 'R', bias: (rng() - 0.5) * 0.2, warm: (rng() - 0.5) * 0.12,
    });
  }
  return out;
}

// ── mechanisms (faithful in form) ────────────────────────────────────────────
// 1 — graded-logistic bounded confidence (HK as the all-to-all case).
function stepBC(ags, R, mu, tau, sigma = 0) {
  const n = ags.length;
  const nx = new Float64Array(n), ny = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const ax = ags[i].x, ay = ags[i].y;
    let sx = 0, sy = 0, sw = 0;
    for (let j = 0; j < n; j++) {
      const dx = ags[j].x - ax, dy = ags[j].y - ay;
      const w = 1 / (1 + Math.exp((Math.sqrt(dx * dx + dy * dy) - R) / tau));
      sx += ags[j].x * w; sy += ags[j].y * w; sw += w;
    }
    nx[i] = ax + mu * (sx / sw - ax); ny[i] = ay + mu * (sy / sw - ay);
  }
  for (let i = 0; i < n; i++) {
    let x = nx[i], y = ny[i];
    if (sigma) { x += (Math.random() * 2 - 1) * sigma; y += (Math.random() * 2 - 1) * sigma; }
    ags[i].x = _clamp(-1, 1, x); ags[i].y = _clamp(-1, 1, y);
  }
}
// 2 — party pull (elite-cue drift toward the party pole). Poles come in as draggable
// anchors, so moving a pole re-aims its whole side. Independents feel no cue.
function stepParty(ags, pull, anchors, sigma = 0) {
  const P = {}; for (const an of anchors) P[an.key] = an;
  for (const a of ags) {
    const pole = P[a.party];
    let x = a.x, y = a.y;
    if (pole) { x += pull * (pole.x - a.x); y += pull * (pole.y - a.y); }
    if (sigma) { x += (Math.random() * 2 - 1) * sigma; y += (Math.random() * 2 - 1) * sigma; }
    a.x = _clamp(-1, 1, x); a.y = _clamp(-1, 1, y);
  }
}
// 3 — affective update (out-party animus): contact-driven, negativity-biased.
// NEVER touches position — feelings move, views don't. (Independents stay neutral.)
function stepAffect(ags, bias, rate = 0.035, sigma = 0) {
  const n = ags.length;
  const nw = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const a = ags[i];
    if (a.party === 'I') { nw[i] = a.warm + rate * (0 - a.warm); continue; }
    let inW = 0, outW = 0;
    for (let j = 0; j < n; j++) {
      if (j === i) continue;
      const o = ags[j]; if (o.party === 'I') continue;
      const dx = o.x - a.x, dy = o.y - a.y;
      const w = 1 / (1 + ((dx * dx + dy * dy) / 0.25));
      if (o.party === a.party) inW += w; else outW += w;
    }
    const exposure = outW / (inW + outW + 1e-9);
    const rest = 0.3 - (0.3 + 1.7 * _clamp(0, 1, bias)) * exposure;
    let v = a.warm + rate * (rest - a.warm);
    if (sigma) v += (Math.random() * 2 - 1) * sigma;
    nw[i] = _clamp(-1, 1, v);
  }
  for (let i = 0; i < n; i++) ags[i].warm = nw[i];
}

// 4 — tie rewiring (homophily): swap a cross-aisle tie for a same-side one. Slow,
// degree-preserving, positions untouched. Faithful in form to TieRewiring.
// One swap: drop a cross-aisle tie `j` for a fresh same-side one. `unlock` lets the
// move sever an involuntary tie (clearing its lock) — used only at high homophily.
function rewireOne(ags, i, cross, n, unlock) {
  if (!cross.length) return;
  const a = ags[i];
  const cand = [];
  for (let k = 0; k < n; k++) if (k !== i && ags[k].party === a.party && !a.ties.has(k)) cand.push(k);
  if (!cand.length) return;
  const j = cross[Math.floor(Math.random() * cross.length)];
  const k = cand[Math.floor(Math.random() * cand.length)];
  a.ties.delete(j); ags[j].ties.delete(i);
  if (unlock) { a.locked.delete(j); ags[j].locked.delete(i); }
  a.ties.add(k); ags[k].ties.add(i);
}
function stepRewire(ags, rate) {
  const n = ags.length;
  // involuntary ties (work, family, neighbours) are the ratchet's floor — at a
  // normal pace they never rewire, so a residue of cross-cutting bridges survives.
  // But cranking homophily up wears even those down: their per-step break chance
  // climbs from ~0 at the low end of the dial (default 0.02 → exactly 0).
  const lockBreak = Math.max(0, rate - 0.04) * 0.25;
  for (let i = 0; i < n; i++) {
    const a = ags[i];
    // the usual move: trade a voluntary cross-aisle tie for a same-side one.
    if (Math.random() < rate) {
      rewireOne(ags, i, [...a.ties].filter((j) => ags[j].party !== a.party && !a.locked.has(j)), n);
    }
    // at higher homophily, even an involuntary cross tie can snap (rarely).
    if (lockBreak > 0 && Math.random() < lockBreak) {
      rewireOne(ags, i, [...a.ties].filter((j) => ags[j].party !== a.party && a.locked.has(j)), n, true);
    }
  }
}

// 5 — partisan media (selective-exposure drift toward your side's outlet). Heavy
// consumers get hauled out to the extremes; light ones barely move → the tails
// stretch. Faithful in form to MediaConsumption. A Layer-2 forcing, not a
// universal mechanism.
function stepMedia(ags, pull, anchors, sigma = 0) {
  const O = {}; for (const an of anchors) O[an.key] = an;
  for (const a of ags) {
    const o = O[a.outletKey];
    let x = a.x + pull * a.diet * (o.x - a.x), y = a.y + pull * a.diet * (o.y - a.y);
    if (sigma) { x += (Math.random() * 2 - 1) * sigma; y += (Math.random() * 2 - 1) * sigma; }
    a.x = _clamp(-1, 1, x); a.y = _clamp(-1, 1, y);
  }
}

// 6 — backlash repulsion (Bail 2018): affect-gated. Warmth toward the out-party is
// set by the `hostility` knob (+ per-agent bias). Only when warmth < −0.3 does a
// cross-party neighbour within range push you AWAY; warm/neutral contact does
// nothing. The dark twin of bounded confidence. Faithful in form to the engine's
// BacklashRepulsion.
function stepBackfire(ags, hostility, coolRate, mu, range, sigma = 0) {
  const n = ags.length;
  const floorBase = 0.3 - hostility * 1.2;    // warm at hostility 0, cold at 1
  // warmth cools toward the hostility floor — so backfire engages gradually as the
  // crowd turns cold, rather than all at once.
  for (let i = 0; i < n; i++) ags[i].warm += coolRate * ((floorBase + ags[i].bias) - ags[i].warm);
  const dxs = new Float64Array(n), dys = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const a = ags[i];
    const depth = -0.3 - a.warm;              // how far below the threshold (ramps from 0)
    if (depth <= 0) continue;                 // warm/neutral → no backfire
    let px = 0, py = 0;
    for (let j = 0; j < n; j++) {
      if (j === i) continue;
      const b = ags[j];
      if (b.party === a.party) continue;       // out-party encounters only
      const dx = a.x - b.x, dy = a.y - b.y, d = Math.hypot(dx, dy);
      if (d > 1e-3 && d < range) {
        const mag = depth * (1 - d / range);   // ∝ coldness-below-threshold × closeness
        px += (dx / d) * mag; py += (dy / d) * mag;
      }
    }
    dxs[i] = px; dys[i] = py;
  }
  for (let i = 0; i < n; i++) {
    let x = ags[i].x + mu * dxs[i], y = ags[i].y + mu * dys[i];
    if (sigma) { x += (Math.random() * 2 - 1) * sigma; y += (Math.random() * 2 - 1) * sigma; }
    ags[i].x = _clamp(-1, 1, x); ags[i].y = _clamp(-1, 1, y);
  }
}

// ── metrics ───────────────────────────────────────────────────────────────────
function spreadOf(ags) {
  let mx = 0, my = 0;
  for (const a of ags) { mx += a.x; my += a.y; }
  mx /= ags.length; my /= ags.length;
  let s = 0;
  for (const a of ags) s += Math.hypot(a.x - mx, a.y - my);
  return s / ags.length;
}
function partyGap(ags) {
  let dx = 0, dy = 0, dn = 0, rx = 0, ry = 0, rn = 0;
  for (const a of ags) {
    if (a.party === 'D') { dx += a.x; dy += a.y; dn++; }
    else if (a.party === 'R') { rx += a.x; ry += a.y; rn++; }
  }
  return (!dn || !rn) ? 0 : Math.hypot(dx / dn - rx / rn, dy / dn - ry / rn);
}
function meanWarmth(ags) {
  let s = 0, n = 0;
  for (const a of ags) if (a.party !== 'I') { s += a.warm; n++; }
  return n ? s / n : 0;
}
function crossTieFrac(ags) {
  let total = 0, cross = 0;
  for (let i = 0; i < ags.length; i++) for (const j of ags[i].ties) if (j > i) { total++; if (ags[j].party !== ags[i].party) cross++; }
  return total ? cross / total : 0;
}
function meanExtremity(ags) { let s = 0; for (const a of ags) s += Math.hypot(a.x, a.y); return s / ags.length; }

// ── force-specific floor overlays (drawn on the plane, under the dots).
//    Signature: (ctx, H, ags, knob, focalIdx), H = { p3, hexA, PCOL, mscale } ──
function bcOverlay(ctx, H, ags, R, fi) {
  const f = ags[fi]; if (!f) return;
  const fp = H.p3(f.x, 0, f.y);
  ctx.beginPath(); ctx.arc(fp[0], fp[1], R * H.mscale, 0, 6.283);
  ctx.fillStyle = H.hexA('#1a1d23', 0.035); ctx.fill();
  ctx.setLineDash([4, 4]); ctx.strokeStyle = H.hexA('#1a1d23', 0.32); ctx.lineWidth = 1.2; ctx.stroke(); ctx.setLineDash([]);
  for (let j = 0; j < ags.length; j++) {
    if (j === fi) continue;
    const d = Math.hypot(ags[j].x - f.x, ags[j].y - f.y);
    if (d <= R) {
      const jp = H.p3(ags[j].x, 0, ags[j].y);
      ctx.beginPath(); ctx.moveTo(fp[0], fp[1]); ctx.lineTo(jp[0], jp[1]);
      ctx.strokeStyle = H.hexA('#1a1d23', 0.10 * (1 - d / R) + 0.04); ctx.lineWidth = 1; ctx.stroke();
    }
  }
}
function partyOverlay(ctx, H, ags, pull, fi, anchors) {
  const P = {};
  for (const an of anchors) {
    P[an.key] = an;
    const pp = H.p3(an.x, 0, an.y);
    ctx.setLineDash([3, 3]); ctx.strokeStyle = H.hexA(an.hex, 0.5); ctx.lineWidth = 1.4;
    ctx.beginPath(); ctx.arc(pp[0], pp[1], 11, 0, 6.283); ctx.stroke(); ctx.setLineDash([]);
    ctx.beginPath(); ctx.arc(pp[0], pp[1], 2.6, 0, 6.283); ctx.fillStyle = H.hexA(an.hex, 0.9); ctx.fill();
    ctx.font = `italic 11px ${SERIF}`; ctx.fillStyle = H.hexA(an.hex, 0.9); ctx.textAlign = 'center';
    ctx.fillText(an.label, pp[0], pp[1] - 17);
  }
  const f = ags[fi]; const Pp = f && P[f.party];
  if (Pp) {
    const fp = H.p3(f.x, 0, f.y), pp = H.p3(Pp.x, 0, Pp.y);
    ctx.setLineDash([2, 3]); ctx.strokeStyle = H.hexA(Pp.hex, 0.35); ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.moveTo(fp[0], fp[1]); ctx.lineTo(pp[0], pp[1]); ctx.stroke(); ctx.setLineDash([]);
  }
}

function networkOverlay(ctx, H, ags, knob, fi) {
  for (let i = 0; i < ags.length; i++) {
    const a = ags[i];
    for (const j of a.ties) {
      if (j <= i) continue;
      const b = ags[j];
      const cross = a.party !== b.party;            // a tie across the aisle
      const locked = a.locked.has(j);               // involuntary — survives rewiring
      const foc = i === fi || j === fi;
      const p = H.p3(a.x, 0, a.y), q = H.p3(b.x, 0, b.y);
      ctx.strokeStyle = cross
        ? H.hexA('#1a1d23', foc ? 0.55 : (locked ? 0.30 : 0.16))   // locked bridges read stronger
        : H.hexA(a.party === 'D' ? CC.d : CC.r, foc ? 0.5 : 0.13);
      ctx.lineWidth = foc ? 1.7 : (cross && locked ? 1.3 : 1);
      ctx.beginPath(); ctx.moveTo(p[0], p[1]); ctx.lineTo(q[0], q[1]); ctx.stroke();
    }
  }
}

function mediaOverlay(ctx, H, ags, knob, fi, anchors) {
  const O = {};
  for (const an of anchors) {
    O[an.key] = an;
    const p = H.p3(an.x, 0, an.y), s = 6;
    ctx.save(); ctx.translate(p[0], p[1]); ctx.rotate(Math.PI / 4);
    ctx.fillStyle = H.hexA(an.hex, 0.9); ctx.fillRect(-s, -s, 2 * s, 2 * s); ctx.restore();
    ctx.font = `italic 11px ${SERIF}`; ctx.fillStyle = H.hexA(an.hex, 0.92); ctx.textAlign = 'center';
    ctx.fillText(an.label, p[0], p[1] - 15);
  }
  const f = ags[fi]; const o = f && O[f.outletKey];
  if (o) {
    const fp = H.p3(f.x, 0, f.y), op = H.p3(o.x, 0, o.y);
    ctx.setLineDash([2, 3]); ctx.strokeStyle = H.hexA(o.hex, 0.35); ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.moveTo(fp[0], fp[1]); ctx.lineTo(op[0], op[1]); ctx.stroke(); ctx.setLineDash([]);
  }
}

function backfireOverlay(ctx, H, ags, hostility, fi) {
  const f = ags[fi]; if (!f) return;
  const range = 0.4;
  const fp = H.p3(f.x, 0, f.y);
  ctx.setLineDash([2, 4]); ctx.strokeStyle = H.hexA('#8b2530', 0.25); ctx.lineWidth = 1;
  ctx.beginPath(); ctx.arc(fp[0], fp[1], range * H.mscale, 0, 6.283); ctx.stroke(); ctx.setLineDash([]);
  for (let j = 0; j < ags.length; j++) {
    if (j === fi) continue;
    const b = ags[j]; if (b.party === f.party) continue;
    const d = Math.hypot(b.x - f.x, b.y - f.y);
    if (d < range) {
      const jp = H.p3(b.x, 0, b.y);
      ctx.strokeStyle = H.hexA('#8b2530', 0.10 + 0.18 * (1 - d / range));   // tense red contacts
      ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(fp[0], fp[1]); ctx.lineTo(jp[0], jp[1]); ctx.stroke();
    }
  }
}

// ── the chassis ────────────────────────────────────────────────────────────────
// Controlled, canvas-only: the transport / knob / reveal toggle live in the
// tour's bottom bar and arrive as props. `toyRef` exposes step/reset/metric.
function ForceToy({ force, knob = 0, playing = false, revealed = false, onAutoReveal, toyRef, n = 80, seed = 11 }) {
  const wrapRef = useRef(null);
  const cvRef = useRef(null);
  const szRef = useRef({ w: 520, h: 520 });
  const agsRef = useRef(null);
  if (!agsRef.current) agsRef.current = force.seed(n, seed);
  const anchorsRef = useRef(null);
  if (force.anchors && !anchorsRef.current) anchorsRef.current = force.anchors();
  const knobRef = useRef(knob); knobRef.current = knob;
  const focalRef = useRef(0);
  const drawRef = useRef(() => {});
  const camTRef = useRef(0);                 // 0 = top-down, 1 = oblique
  const tickRef = useRef(0);                 // ticks since reset (for auto-reveal)
  const autoRevealedRef = useRef(false);     // auto-reveal fires once; manual toggle claims it
  const appearRef = useRef(force.ambient ? 0 : 99);  // orientation fade clock (seconds); forces start fully shown
  const fromRef = useRef(null);     // interpolation: agent state at the start of the current step
  const targetRef = useRef(null);   // …and the target state it's easing toward
  const dragRef = useRef(null);     // index of the agent being dragged (skipped by the play interp)
  const yawRef = useRef(CAM_TOP.yaw), pitchRef = useRef(CAM_TOP.pitch);
  const applyCam = (t) => {
    yawRef.current = CAM_TOP.yaw + (CAM_OBL.yaw - CAM_TOP.yaw) * t;
    pitchRef.current = CAM_TOP.pitch + (CAM_OBL.pitch - CAM_TOP.pitch) * t;
  };

  const geom = () => {
    const { w, h } = szRef.current;
    return { cx: w / 2, cy: h / 2 + Math.min(w, h) * 0.02, Smin: Math.min(w, h), w, h };
  };

  // synchronous draw — self-measures (cold-load flex height resolves a frame late).
  const draw = useCallback(() => {
    const cv = cvRef.current; if (!cv) return;
    const w = cv.clientWidth || szRef.current.w, h = cv.clientHeight || szRef.current.h;
    if (w < 40 || h < 40) return;
    szRef.current = { w, h };
    const ctx = cv.getContext('2d');
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    if (cv.width !== Math.round(w * dpr)) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);

    const g = geom();
    const ags = agsRef.current;
    const yaw = yawRef.current, pitch = pitchRef.current;
    const cyaw = Math.cos(yaw), syaw = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
    const F = g.Smin * 0.40 * CAM;
    // world (econ X, affect-lift Y, cultural Z) → screen. cultural negated so +cultural is UP at top-down.
    const project = (X, Y, Z) => {
      const X1 = X * cyaw + Z * syaw, Z1 = -X * syaw + Z * cyaw;
      const Y2 = Y * cp - Z1 * sp, Z2 = Y * sp + Z1 * cp;
      const depth = CAM - Z2, s = F / Math.max(0.25, depth);
      return [g.cx + X1 * s, g.cy - Y2 * s, depth, s];
    };
    const p3 = (e, lift, c) => project(e, lift, -c);
    const mscale = F / CAM;                                // model→px at the floor (top-down)
    const fadeSeg = (p, q, rgb, wid, edge, peak) => {
      const grd = ctx.createLinearGradient(p[0], p[1], q[0], q[1]);
      grd.addColorStop(0, _rgba(rgb, 0)); grd.addColorStop(edge, _rgba(rgb, peak));
      grd.addColorStop(1 - edge, _rgba(rgb, peak)); grd.addColorStop(1, _rgba(rgb, 0));
      ctx.strokeStyle = grd; ctx.lineWidth = wid; ctx.beginPath(); ctx.moveTo(p[0], p[1]); ctx.lineTo(q[0], q[1]); ctx.stroke();
    };
    const revealing = camTRef.current > 0.02;
    const ap = force.ambient ? appearRef.current : 99;       // seconds into the orientation fade
    const axisAp = _clamp(0, 1, ap / 1.2);                   // axes fade in over ~1.2s…
    const dotAp = _clamp(0, 1, (ap - 2.2) / 1.2);            // …then a ~1s pause, then the dots

    // ── the compass floor ──
    ctx.globalAlpha = axisAp;
    fadeSeg(p3(-1.12, 0, 0), p3(1.12, 0, 0), C_BORDER, 1.3, 0.05, 0.82);   // econ axis
    fadeSeg(p3(0, 0, -1.12), p3(0, 0, 1.12), C_BORDER, 1.3, 0.05, 0.82);   // cultural axis
    [-0.5, 0.5].forEach((u) => {
      fadeSeg(p3(u, 0, -0.92), p3(u, 0, 0.92), C_BORDER, 0.8, 0.12, 0.28);
      fadeSeg(p3(-0.92, 0, u), p3(0.92, 0, u), C_BORDER, 0.8, 0.12, 0.28);
    });
    // ── the affect axis — only once the camera has begun to reveal it ──
    if (revealing) {
      const aA = Math.min(1, (camTRef.current - 0.02) / 0.4);
      fadeSeg(p3(0, -HEIGHT - 0.1, 0), p3(0, HEIGHT + 0.1, 0), C_BORDER, 1.3, 0.04, 0.6 * aA);
    }
    ctx.globalAlpha = 1;

    // ── force-specific floor overlay (BC ring / party poles) ──
    if (force.overlay) force.overlay(ctx, { p3, hexA: _hexA, mscale }, ags, knobRef.current, focalRef.current, anchorsRef.current);

    // ── agents (lifted by affect) — footprints + stems first, painter-sorted dots on top ──
    ctx.globalAlpha = dotAp;
    const items = ags.map((a, i) => {
      const lift = force.lift ? force.lift(a) : 0;
      return { i, pr: p3(a.x, lift, a.y), gr: p3(a.x, 0, a.y), rgb: PRGB[a.party] || PRGB.I, lifted: Math.abs(lift) > 0.02 };
    });
    items.sort((u, v) => v.pr[2] - u.pr[2]);     // far → near
    for (const it of items) {
      if (it.lifted) { ctx.strokeStyle = _rgba(it.rgb, 0.10); ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(it.gr[0], it.gr[1]); ctx.lineTo(it.pr[0], it.pr[1]); ctx.stroke(); }
      if (revealing) { ctx.fillStyle = _rgba(C_INK, 0.05); ctx.beginPath(); ctx.ellipse(it.gr[0], it.gr[1], 2.4, 1.2, 0, 0, 6.283); ctx.fill(); }
    }
    const rBase = g.Smin * 0.0066;
    for (const it of items) {
      const nd = _clamp(0, 1, (it.pr[2] - (CAM - 1.7)) / 3.4);   // 0 near … 1 far
      const r = _clamp(2.2, 7, rBase * (CAM / it.pr[2]));
      // full party saturation when flat (top-down); depth-wash fades in only as
      // the camera tilts for the 3-D reveal, where it aids legibility.
      const tilt = camTRef.current;
      ctx.fillStyle = _rgba(_fLerp(it.rgb, C_BG, nd * 0.45 * tilt), 1 - nd * 0.35 * tilt);
      ctx.beginPath(); ctx.arc(it.pr[0], it.pr[1], r, 0, 6.283); ctx.fill();
    }
    // focal ring
    if (force.focusable) {
      const fa = ags[_clamp(0, ags.length - 1, focalRef.current)];
      const fp = p3(fa.x, force.lift ? force.lift(fa) : 0, fa.y);
      ctx.beginPath(); ctx.arc(fp[0], fp[1], 5.4, 0, 6.283);
      ctx.fillStyle = _rgba(PRGB[fa.party] || PRGB.I, 1); ctx.fill();
      ctx.lineWidth = 2; ctx.strokeStyle = '#fff'; ctx.stroke();
      ctx.lineWidth = 1.4; ctx.strokeStyle = _hexA('#1a1d23', 0.5); ctx.stroke();
    }

    // ── labels (billboard, upright; measured + clamped so an edge never clips
    //    them — the econ tip is right-aligned so it grows inward, not off-canvas) ──
    const LPAD = 7;
    const label = (p, text, dy, hex, align = 'center') => {
      ctx.font = `italic 11px ${SERIF}`; ctx.textAlign = align; ctx.textBaseline = 'middle';
      const tw = ctx.measureText(text).width;
      let x = p[0];
      if (align === 'right') x = _clamp(tw + LPAD, w - LPAD, x);
      else if (align === 'left') x = _clamp(LPAD, w - tw - LPAD, x);
      else x = _clamp(tw / 2 + LPAD, w - tw / 2 - LPAD, x);
      const y = _clamp(9, h - 9, p[1] + dy);
      ctx.lineJoin = 'round'; ctx.strokeStyle = 'rgba(249,248,244,.9)'; ctx.lineWidth = 3.2; ctx.strokeText(text, x, y);
      ctx.fillStyle = hex || '#9aa0a6'; ctx.fillText(text, x, y);
    };
    ctx.globalAlpha = axisAp;
    label(p3(1.08, 0, 0), 'economic →', -10, null, 'right');
    label(p3(0, 0, 1.08), 'cultural →', -10);
    if (revealing) {
      label(p3(0, HEIGHT + 0.1, 0), 'Democrats cool ↑', -8, CC.d);
      label(p3(0, -HEIGHT - 0.1, 0), 'Republicans cool ↓', 12, CC.r);
    }
    ctx.globalAlpha = 1;
  }, [force]);
  drawRef.current = draw;

  const advance = useCallback((k = 1) => {
    const ags = agsRef.current;
    for (let s = 0; s < k; s++) force.step(ags, knobRef.current, anchorsRef.current);
    tickRef.current += k;
    draw();
    return force.metric ? force.metric.fn(ags) : 0;   // for the headless hook; no on-screen readout
  }, [draw, force]);

  const reset = useCallback(() => {
    agsRef.current = force.seed(n, seed); focalRef.current = 0;
    anchorsRef.current = force.anchors ? force.anchors() : null;
    tickRef.current = 0; autoRevealedRef.current = false;
    camTRef.current = 0; applyCam(0);
    fromRef.current = null; targetRef.current = null;   // drop any in-flight interp so a running loop can't overwrite the fresh seed
    drawRef.current();
  }, [force, n, seed]);

  // mount paint (+ 0ms fallback for late flex height) + seed the readout
  useLayoutEffect(() => {
    drawRef.current();
    const t = setTimeout(() => drawRef.current(), 0);
    return () => clearTimeout(t);
  }, [knob]);

  useEffect(() => {
    const el = wrapRef.current; if (!el) return;
    const ro = new ResizeObserver(() => drawRef.current()); ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // play loop (RAF — paused headlessly; Step + __forceStep cover that).
  // Each logical step jumps the mechanism to its next target, but the DRAWN
  // positions ease from the old state to the new one over STEP_DUR every frame —
  // so the motion is smooth, and overlays (which read the same agent state) stay
  // in lock-step. STEP_DUR is ~30% slower than the old 0.06s cadence.
  useEffect(() => {
    if (!playing) return;
    const STEP_DUR = 0.086;
    let raf, prev = null, stepClock = 0;
    fromRef.current = null; targetRef.current = null;   // fresh interpolation on each (re)play
    const snap = () => agsRef.current.map((a) => ({ x: a.x, y: a.y, warm: a.warm }));
    const restore = (s) => agsRef.current.forEach((a, i) => { a.x = s[i].x; a.y = s[i].y; a.warm = s[i].warm; });
    const loop = (ts) => {
      if (prev == null) prev = ts; const dt = Math.min(0.05, (ts - prev) / 1000); prev = ts;
      stepClock += dt;
      if (!targetRef.current || stepClock >= STEP_DUR) {
        // the dragged dot is user-controlled: capture it and re-pin it across every
        // snapshot/step/restore so the boundary never yanks it off the cursor.
        const d = dragRef.current;
        const held = d != null ? { x: agsRef.current[d].x, y: agsRef.current[d].y, warm: agsRef.current[d].warm } : null;
        const pin = () => { if (held) { const a = agsRef.current[d]; a.x = held.x; a.y = held.y; a.warm = held.warm; } };
        if (targetRef.current) { restore(targetRef.current); stepClock = Math.min(stepClock - STEP_DUR, STEP_DUR); }
        else stepClock = 0;
        pin();
        fromRef.current = snap();
        force.step(agsRef.current, knobRef.current, anchorsRef.current);
        pin();                                  // undo any move the step applied to the held dot
        tickRef.current += 1;
        if (force.autoReveal && !autoRevealedRef.current && tickRef.current >= force.autoReveal) { autoRevealedRef.current = true; onAutoReveal && onAutoReveal(); }
        targetRef.current = snap();
        restore(fromRef.current);
      }
      const prog = _clamp(0, 1, stepClock / STEP_DUR);
      const from = fromRef.current, to = targetRef.current;
      if (from && to) agsRef.current.forEach((a, i) => {
        if (i === dragRef.current) return;   // leave the dragged dot under the user's control
        a.x = from[i].x + (to[i].x - from[i].x) * prog;
        a.y = from[i].y + (to[i].y - from[i].y) * prog;
        if (to[i].warm != null && from[i].warm != null) a.warm = from[i].warm + (to[i].warm - from[i].warm) * prog;
      });
      drawRef.current();
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [playing, force, onAutoReveal]);

  // ambient loop (orientation only) — a slow fade-in of the map, then idle.
  // No drift: the orientation is a still map you read, not a moving thing.
  // RAF; paused headlessly.
  useEffect(() => {
    if (!force.ambient) return;
    let raf, prev = null;
    const loop = (ts) => {
      if (prev == null) prev = ts; const dt = Math.min(0.05, (ts - prev) / 1000); prev = ts;
      appearRef.current += dt;                       // advance the fade clock (seconds)
      drawRef.current();
      if (appearRef.current < 3.6) raf = requestAnimationFrame(loop);  // stop once the dots are fully in
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [force]);

  // camera reveal tween (RAF; headless uses __forceReveal to set it directly)
  useEffect(() => {
    if (!force.reveal) return;
    const target = revealed ? 1 : 0;
    let raf, prev = null;
    const loop = (ts) => {
      if (prev == null) prev = ts; const dt = (ts - prev) / 1000; prev = ts;
      const cur = camTRef.current;
      let nx = cur + (target - cur) * Math.min(1, dt * 3.5);
      if (Math.abs(target - nx) < 0.004) nx = target;
      camTRef.current = nx; applyCam(nx); drawRef.current();
      if (nx !== target) raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [revealed, force]);

  // pointer → drag an ANCHOR (pole / outlet — bigger targets, checked first) or, on
  // focusable forces, set/drag the focal agent. Top-down only (floor inverts cleanly).
  useEffect(() => {
    if (!force.focusable && !force.anchors) return;
    const el = cvRef.current; if (!el) return;
    let mode = null, anchor = null;                 // mode: 'anchor' | 'agent'
    const at = (e) => {
      const r = el.getBoundingClientRect();
      const g = geom(), ms = g.Smin * 0.40;          // model→px at the floor
      return { px: e.clientX - r.left, py: e.clientY - r.top, g, ms };
    };
    const pickAnchor = (px, py, g, ms) => {
      if (!anchorsRef.current) return null;
      for (const an of anchorsRef.current) {
        const sx = g.cx + an.x * ms, sy = g.cy - an.y * ms;
        if ((sx - px) ** 2 + (sy - py) ** 2 < 20 * 20) return an;
      }
      return null;
    };
    const pickAgent = (px, py, g, ms) => {
      const ags = agsRef.current; let best = 0, bd = Infinity;
      for (let i = 0; i < ags.length; i++) {
        const sx = g.cx + ags[i].x * ms, sy = g.cy - ags[i].y * ms;
        const d = (sx - px) ** 2 + (sy - py) ** 2;
        if (d < bd) { bd = d; best = i; }
      }
      return { best, bd };
    };
    const onDown = (e) => {
      const { px, py, g, ms } = at(e);
      const an = pickAnchor(px, py, g, ms);
      if (an) { anchor = an; mode = 'anchor'; el.style.cursor = 'grabbing'; return; }
      if (force.focusable) { const { best, bd } = pickAgent(px, py, g, ms); if (bd < 26 * 26) { focalRef.current = best; mode = 'agent'; dragRef.current = best; drawRef.current(); } }
    };
    const onMove = (e) => {
      const { px, py, g, ms } = at(e);
      if (mode && camTRef.current < 0.05) {
        const tx = _clamp(-1, 1, (px - g.cx) / ms), ty = _clamp(-1, 1, (g.cy - py) / ms);
        if (mode === 'anchor') { anchor.x = tx; anchor.y = ty; }
        else { const a = agsRef.current[focalRef.current]; a.x = tx; a.y = ty; }
        drawRef.current();
      } else if (!mode) {
        // hover: grab cursor over an anchor; otherwise highlight nearest agent
        const overAnchor = !!pickAnchor(px, py, g, ms);
        el.style.cursor = overAnchor ? 'grab' : (force.focusable ? 'default' : 'default');
        if (force.focusable && !overAnchor) { const { best, bd } = pickAgent(px, py, g, ms); if (bd < 26 * 26 && focalRef.current !== best) { focalRef.current = best; drawRef.current(); } }
      }
    };
    const onUp = () => { mode = null; anchor = null; dragRef.current = null; targetRef.current = null; el.style.cursor = 'default'; };
    el.addEventListener('pointermove', onMove); el.addEventListener('pointerdown', onDown); window.addEventListener('pointerup', onUp);
    return () => { el.removeEventListener('pointermove', onMove); el.removeEventListener('pointerdown', onDown); window.removeEventListener('pointerup', onUp); };
  }, [force]);

  // headless hooks
  useEffect(() => {
    window.__forceStep = (k = 1) => advance(k);
    window.__forceMetric = () => (force.metric ? force.metric.fn(agsRef.current) : 0);
    window.__forceReset = reset;
    window.__forceReveal = (b) => { camTRef.current = b ? 1 : 0; applyCam(camTRef.current); drawRef.current(); };
    return () => { delete window.__forceStep; delete window.__forceMetric; delete window.__forceReset; delete window.__forceReveal; };
  }, [advance, reset, force]);

  // expose imperative controls so the shared bottom bar can drive this toy
  React.useImperativeHandle(toyRef, () => ({
    step: () => advance(1),
    reset,
    metric: () => (force.metric ? force.metric.fn(agsRef.current) : 0),
  }), [advance, reset, force]);

  // canvas only — transport, knob, and reveal toggle live in the tour's bottom bar
  return (
    <div ref={wrapRef} style={{ width: '100%', height: '100%', minHeight: 0, position: 'relative' }}>
      <canvas ref={cvRef} style={{ width: '100%', height: '100%', display: 'block', cursor: force.focusable ? 'grab' : 'default', touchAction: 'none' }} />
    </div>
  );
}

// TEXTW (the shared responsive prose width) + RAIL_LX/RAIL_W live in rc-shared.jsx
// now, so every floating-prose page shares one column geometry.

// ── force descriptors ────────────────────────────────────────────────────────
const FORCE_BC = {
  id: 'bc',
  eyebrow: 'How the engine works · force 1 of 5',
  title: 'Interaction builds consensus, in some cases.',
  lead: 'Talking helps, but only if some agreement is already there.',
  body: (
    <>
      <p style={{ margin: '16px 0 0', ...PROSE, color: CC.ink2, maxWidth: TEXTW }}>
        Each person moves toward those close enough to them to have a constructive conversation. Hence the <em>bounded confidence</em> name - confidence in other people’s opinions bounded by how much they agree - anything out of those bounds gets ignored. On the compass this is represented by each person’s <strong>confidence radius</strong> (the dashed ring). Dots with overlapping rings mingle and build consensus. If the rings don’t overlap - conversations don’t happen or go nowhere. Think about it - do we often genuinely try to understand people who hold views that are anathema to us?
      </p>
      <p style={{ margin: '14px 0 0', ...PROSE, color: CC.ink2, maxWidth: TEXTW }}>
        See the force in action. The crowd clumps into <strong>shared clusters</strong> and the party colors <em>mix</em>. Left to itself, listening to your neighbors tends toward <strong>agreement</strong> (albeit in your own circle) rather than division. Widen the radius (increase confidence) and everyone converges on one big blob; narrow it and the crowd splits into islands.
      </p>
    </>
  ),
  caption: 'Nerdy note: the engine recovers classic Hegselmann–Krause as the all-to-all special case.',
  seed: seedMixed,
  step: (ags, knob) => stepBC(ags, knob, 0.05, 0.05, 0.020),
  knob: { label: 'confidence radius', min: 0.12, max: 0.9, step: 0.01, def: 0.34 },
  metric: { label: 'spread', fn: spreadOf, fmt: (v) => v.toFixed(3) },
  overlay: bcOverlay,
  focusable: true,
};

const FORCE_PARTY = {
  id: 'party',
  eyebrow: 'How the engine works · force 4 of 5',
  title: 'Party pull: following your side’s lead.',
  lead: 'Influence that comes not from your circle, but from above.',
  body: (
    <>
      <p style={{ margin: '16px 0 0', ...PROSE, color: CC.ink2, maxWidth: TEXTW }}>
        A lot of our politics comes from the top. A party’s leaders take a stance, and over time their electorate drifts closer to it. Political scientists call it an <strong>elite cue</strong>, but you may have felt it yourself: an issue you’ve hardly thought about suddenly feels salient and you know where <em>you</em> stand on it. Of course, it’s not a one-way street and there’s a feedback element to it, but research is clear on the power of elite cues. Each party has its pole here (the two dashed targets); independents, with no team to follow, stay put.
      </p>
      <p style={{ margin: '14px 0 0', ...PROSE, color: CC.ink2, maxWidth: TEXTW }}>
        <strong>Drag a pole</strong> and you swing a whole side with it; pull a person away and watch their side drag them back. As it runs, the mixed crowd comes apart, the colors peeling into two camps with the middle thinning between them. Crank the pull up and each side snaps tight to its pole; ease it back down and they drift toward the center again.
      </p>
    </>
  ),
  caption: 'Nerdy note: faithful in form to PartyPull — elite-cue drift toward each party’s own emergent pole.',
  seed: seedMixed,
  step: (ags, knob, anchors) => stepParty(ags, knob, anchors, 0.012),
  anchors: () => [
    { key: 'D', x: POLE_D.x, y: POLE_D.y, hex: CC.d, label: 'Democratic pull' },
    { key: 'R', x: POLE_R.x, y: POLE_R.y, hex: CC.r, label: 'Republican pull' },
  ],
  knob: { label: 'party pull', min: 0, max: 0.06, step: 0.005, def: 0.01 },
  metric: { label: 'party gap', fn: partyGap, fmt: (v) => v.toFixed(2) },
  overlay: partyOverlay,
  focusable: true,
};

const FORCE_AFFECT = {
  id: 'affect',
  eyebrow: 'How the engine works · the second axis',
  title: 'Disagreeing is only half the story',
  lead: 'Affect: not a force in itself, but the feeling the forces before fail to capture.',
  body: (
    <>
      <p style={{ margin: '16px 0 0', ...PROSE, color: CC.ink2, maxWidth: TEXTW }}>
        Affect isn’t really a force at all — rather it’s another <strong>result</strong>. It’s the feeling the other forces breed which becomes the second, different dimension that polarization gets measured on. Look straight down at the compass and almost nothing seems to be happening. Then the axes tilt and a new movement path becomes apparent - it’s the emotional side of polarization. Two things drive it: <strong>contact</strong> (the more of the other side around you, the faster you sour) and a <strong>negativity bias</strong> (people’s disproportionate reaction to negative information).
      </p>
      <p style={{ margin: '14px 0 0', ...PROSE, color: CC.ink2, maxWidth: TEXTW }}>
        On screen, Democrats lift up, Republicans sink down, and the vertical gap between them is their mutual animosity.
      </p>
    </>
  ),
  caption: 'Nerdy note: In the shipped model, affect is about 83% emergent.',
  seed: seedAffect,
  step: (ags, knob) => stepAffect(ags, knob, 0.022, 0.004),
  lift: (a) => (PSGN[a.party] || 0) * Math.max(0, -(a.warm == null ? 0 : a.warm)) * HEIGHT,
  knob: { label: 'negativity bias', min: 0, max: 1, step: 0.05, def: 0.7 },
  metric: { label: 'out-party warmth', fn: meanWarmth, fmt: (v) => v.toFixed(2) },
  reveal: true,
  autoReveal: 16,            // ticks of play before the camera tilts on its own
  focusable: true,
};

const FORCE_NETWORK = {
  id: 'network',
  eyebrow: 'How the engine works · force 3 of 5',
  title: 'Homophily - literally love of the same',
  lead: 'You slowly lose touch with those you disagree with.',
  body: (
    <>
      <p style={{ margin: '16px 0 0', ...PROSE, color: CC.ink2, maxWidth: TEXTW }}>
        Every dot sits in a web of social ties (the lines). At first it’s mixed: plenty of links cross the aisle. But people don’t want to constantly find themselves arguing and defending their positions; so they slowly trade ties that irritate for ones that soothe. Over time this tendency largely erodes the cross-aisle links, leaving only what cannot be given up easily (colleagues, neighbors, fellow commuters).
      </p>
      <p style={{ margin: '14px 0 0', ...PROSE, color: CC.ink2, maxWidth: TEXTW }}>
        Look at the compass. Most of the bridges thin out as people trade them away, while the <strong>involuntary</strong> ties nobody chooses - work, family, neighbors - hold out longest. That residue is the <strong>ratchet</strong>: your network seals itself, but at an ordinary pace some outside influence tends to survive. Crank homophily high, though, and even those stubborn ties begin to give. Turn it down to keep it mixed; up to close the bubbles fast.
      </p>
    </>
  ),
  caption: 'Nerdy note: faithful in form to Tie Rewiring — slow homophilous network co-evolution.',
  seed: seedNetwork,
  step: (ags, knob) => stepRewire(ags, knob),
  knob: { label: 'homophily', min: 0, max: 0.2, step: 0.01, def: 0.02 },
  metric: { label: 'across-aisle ties', fn: crossTieFrac, fmt: (v) => (v * 100).toFixed(0) + '%' },
  overlay: networkOverlay,
  focusable: true,
};

const FORCE_MEDIA = {
  id: 'media',
  eyebrow: 'How the engine works · force 5 of 5',
  title: 'The news doesn’t have to mean new opinions',
  lead: (<>Heavy media users exposed to <strong>partisan media</strong> are influenced.</>),
  body: (
    <>
      <p style={{ margin: '16px 0 0', ...PROSE, color: CC.ink2, maxWidth: TEXTW }}>
        Each party has its outlets (the diamonds). People tune in to their preferred ones, often based on political affiliation — what researchers call selective exposure. The more of partisan media they watch, the harder their outlet pulls them toward it. <strong>Drag an outlet</strong> to change where it pulls; drag a person to see which outlet they’re wired to.
      </p>
      <p style={{ margin: '14px 0 0', ...PROSE, color: CC.ink2, maxWidth: TEXTW }}>
        As it runs, most people barely move; it’s the heavy consumers who get drawn toward their outlet, coming out more partisan the more they watch — how far, and which way, depends on where the outlets sit. Dial the diet up and the pull strengthens (and vice versa).
      </p>
    </>
  ),
  caption: 'Nerdy note: Unlike the universal mechanisms on the other pages, this one is country-specific and uses a media-penetration curve tailored per country (the U.S. in the story that follows).',
  seed: seedMedia,
  step: (ags, knob, anchors) => stepMedia(ags, knob, anchors, 0.004),
  anchors: () => [
    { key: 'D', x: MEDIA_OUTLET.D.x, y: MEDIA_OUTLET.D.y, hex: CC.d, label: 'left media' },
    { key: 'R', x: MEDIA_OUTLET.R.x, y: MEDIA_OUTLET.R.y, hex: CC.r, label: 'right media' },
  ],
  knob: { label: 'media diet', min: 0, max: 0.12, step: 0.005, def: 0.02 },
  metric: { label: 'extremity', fn: meanExtremity, fmt: (v) => v.toFixed(2) },
  overlay: mediaOverlay,
  focusable: true,
};

const FORCE_BACKFIRE = {
  id: 'backfire',
  eyebrow: 'How the engine works · force 2 of 5',
  title: 'The same contact, but now it shoves people apart.',
  lead: 'Backfire: the flip side of bounded confidence.',
  body: (
    <>
      <p style={{ margin: '16px 0 0', ...PROSE, color: CC.ink2, maxWidth: TEXTW }}>
        Bounded confidence pulled people together, but only when they could still <em>hear</em> each other. What happens if you do talk to someone from ‘the other side’? The backfiring force describes exactly that. Each cross-party encounter is now checked against how hostile you feel: up until a certain threshold the contact is harmless; but cross it and talking to someone you disagree with propels you <strong>away</strong>.
      </p>
      <p style={{ margin: '14px 0 0', ...PROSE, color: CC.ink2, maxWidth: TEXTW }}>
        Reach for the <strong>hostility</strong> knob. With it low, the mixed crowd just sits there, not much happening; turn it high and the <em>same</em> encounters become repellent, quickly forming a schism in the crowd. Drag a dot toward the other side and watch it recoil. This is what makes fostering constructive debates such an ambitious goal.
      </p>
    </>
  ),
  caption: 'Nerdy note: faithful in form to Backlash Repulsion (Bail 2018) — gated by affect and fires only when warmth is already low.',
  seed: seedBackfire,
  step: (ags, knob) => stepBackfire(ags, knob, 0.022, 0.05, 0.7, 0.004),
  knob: { label: 'hostility', min: 0, max: 1, step: 0.05, def: 0.8 },
  metric: { label: 'party gap', fn: partyGap, fmt: (v) => v.toFixed(2) },
  overlay: backfireOverlay,
  focusable: true,
};

// order: peer dynamics (1–3) → pulls from above (4–5) → the felt result (affect).
const FORCES = [FORCE_BC, FORCE_BACKFIRE, FORCE_NETWORK, FORCE_PARTY, FORCE_MEDIA, FORCE_AFFECT];

// ── orientation: the first stop — the map itself, no force moving yet ─────────
const FORCE_ORIENT = {
  id: 'orient',
  eyebrow: 'How the engine works · orientation',
  title: 'People as dots, opinions as positions',
  lead: 'First, what you are looking at.',
  body: (
    <>
      <p style={{ margin: '16px 0 0', ...PROSE, color: CC.ink2, maxWidth: TEXTW }}>
        The graph you see is a <strong>political compass</strong>: left to right is the <strong>economic</strong> axis (from centralized to free-market), up–down the <strong>cultural</strong> one (from traditional to progressive). Every dot is one simulated person, their beliefs dictating their position on the compass. <strong>Navy</strong> leans Democratic, <strong>oxblood</strong> Republican, <strong>gray</strong> sits independent in the middle.
      </p>
      <p style={{ margin: '14px 0 0', ...PROSE, color: CC.ink2, maxWidth: TEXTW }}>
        For now everyone is still. On the following pages you’ll see the forces that move them <strong>one at a time</strong>, starting with the smart-sounding ‘bounded confidence’.
      </p>
    </>
  ),
  caption: 'The same compass the rest of the site uses: economic and cultural axes create the political space.',
  seed: seedMixed,
  step: () => {},          // nothing moves — the orientation is a still map you read
  knob: null,
  metric: null,
  focusable: true,
  static: true,
  ambient: true,           // self-animates (fade-in + drift) without the transport
};

// short chapter labels for the bottom bar (the descriptors' eyebrows carry the long form)
const FORCE_TAB = { orient: 'Orientation', bc: 'Bounded confidence', backfire: 'Backfire', network: 'Homophily', party: 'Party pull', media: 'Media', affect: 'Affect' };

// ── the shared bottom bar — transport (left) · force buttons (center) · knob
// (right). Named buttons, not a timeline; the controls sit where the story's do.
function ForceBar({ stops, fi, goStop, force, playing, setPlaying, onStep, onReset, knob, setKnob, onCommit, revealed, setRevealed }) {
  const isMobile = useIsMobile();
  const round = { width: 32, height: 32, borderRadius: DS.rad.pill, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', flexShrink: 0, fontFamily: SANS };
  const pill = (label, active, onClick, muted) => (
    <button key={label} onClick={onClick} style={{
      flexShrink: 0, padding: '7px 13px', borderRadius: DS.rad.pill, border: 'none', cursor: 'pointer', fontFamily: SANS,
      fontSize: DS.type.small, fontWeight: active ? 600 : 500,
      background: active ? CC.ink : 'transparent', color: active ? '#fff' : muted ? CC.ink3 : CC.ink2,
    }}>{label}</button>
  );
  const kpct = force.knob ? ((knob - force.knob.min) / (force.knob.max - force.knob.min)) * 100 : 0;
  // transport cluster + knob/reveal — reused in both layouts
  const transport = force.static ? (
    <Caption>the map — no force yet</Caption>
  ) : (
    <>
      <button onClick={() => setPlaying((p) => !p)} aria-label={playing ? 'Pause' : 'Play'} style={{ ...round, background: CC.ink, color: '#fff', border: 'none', fontSize: 11 }}>{playing ? '❚❚' : '▶'}</button>
      <button onClick={onStep} title="Step" style={{ ...round, background: 'transparent', color: CC.ink2, border: `1px solid ${CC.borderS}`, fontSize: 12 }}>▷</button>
      <button onClick={onReset} title="Reset" style={{ ...round, background: 'transparent', color: CC.ink2, border: `1px solid ${CC.borderS}`, fontSize: 13 }}>↺</button>
    </>
  );
  const controls = (force.knob || force.reveal) && (
    <div style={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: 12 }}>
      {force.reveal &&
        <button onClick={() => setRevealed((r) => !r)} style={{
          padding: '7px 12px', borderRadius: DS.rad.pill, cursor: 'pointer', fontFamily: SANS, fontSize: 12.5, fontWeight: 500,
          border: `1px solid ${revealed ? CC.ink : CC.borderS}`, background: 'transparent', color: revealed ? CC.ink : CC.ink2,
        }}>{revealed ? '⤡ Flatten' : '⤢ Reveal'}</button>}
      {force.knob &&
        <label style={{ display: 'flex', alignItems: 'center', gap: 9, fontFamily: SANS, fontSize: 13, color: CC.ink2 }}>
          {force.knob.label}
          <input type="range" className="cc-range" min={force.knob.min} max={force.knob.max} step={force.knob.step} value={knob}
            onChange={(e) => setKnob(parseFloat(e.target.value))} onPointerUp={onCommit} onKeyUp={onCommit}
            style={{ width: isMobile ? 104 : 140, background: `linear-gradient(90deg, ${CC.ink} 0 ${kpct}%, ${CC.border} ${kpct}% 100%)` }} />
          <MonoVal size={12}>{knob.toFixed(2)}</MonoVal>
        </label>}
    </div>
  );

  // Mobile: the three desktop sections can't share a row at 390px — stack the
  // force-picker strip over a transport+knob row.
  if (isMobile) {
    return (
      <div style={{ flexShrink: 0, background: CC.bg, borderTop: `1px solid ${CC.border}`, padding: '8px 14px 12px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 3, overflowX: 'auto', whiteSpace: 'nowrap' }}>
          {stops.map((s, i) => pill(i === 0 ? 'Orientation' : s.id === 'affect' ? FORCE_TAB[s.id] : `${i} · ${FORCE_TAB[s.id] || s.id}`, i === fi, () => goStop(i)))}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>{transport}</div>
          <span style={{ flex: 1 }} />
          {controls}
        </div>
      </div>
    );
  }

  return (
    <div style={{ height: 96, flexShrink: 0, background: CC.bg, position: 'relative', display: 'flex', alignItems: 'center', gap: 'clamp(16px,2.5vw,36px)', padding: '0 clamp(28px,4vw,56px)' }}>
      <div style={{ position: 'absolute', top: 0, left: 'clamp(28px,4vw,56px)', right: 'clamp(28px,4vw,56px)', height: 1, background: CC.border }} />
      {/* transport (left) — hidden on the orientation map (nothing to play) */}
      <div style={{ width: 150, flexShrink: 0, display: 'flex', alignItems: 'center', gap: 9 }}>{transport}</div>
      {/* force buttons (center) — named, the active one filled */}
      <div style={{ flex: 1, minWidth: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 3, overflowX: 'auto', whiteSpace: 'nowrap' }}>
        {stops.map((s, i) => pill(i === 0 ? 'Orientation' : s.id === 'affect' ? FORCE_TAB[s.id] : `${i} · ${FORCE_TAB[s.id] || s.id}`, i === fi, () => goStop(i)))}
      </div>
      {/* knob + reveal (right) */}
      {controls}
    </div>
  );
}

// ── mobile "one long scroll" feed (concept C) ───────────────────────────────
// Every force is its own section in one continuous scroll: heading → viz →
// full-width knob line → description. Each viz auto-plays as it scrolls into
// view (and pauses when it leaves); a sticky index up top tracks/jumps.
function ForceFeedItem({ force, idx, assignRef, onActive }) {
  const [knob, setKnob] = React.useState(force.knob ? force.knob.def : 0);
  const [playing, setPlaying] = React.useState(false);
  const [revealed, setRevealed] = React.useState(false);
  const toyRef = React.useRef(null);
  const ref = React.useRef(null);
  React.useEffect(() => {
    const el = ref.current; if (!el) return;
    assignRef(el);
    const io = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) { onActive(idx); if (!force.static && !force.ambient) setPlaying(true); }
      else setPlaying(false);
    }, { rootMargin: '-45% 0px -45% 0px', threshold: 0 });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  const kpct = force.knob ? ((knob - force.knob.min) / (force.knob.max - force.knob.min)) * 100 : 0;
  // a new dial value only shows its effect from a fresh start — but wait for the
  // finger to LIFT before re-seeding + replaying, so a drag doesn't restart on
  // every tick. The value still tracks live (setKnob) during the drag.
  const commitKnob = () => {
    if (force.reveal) setRevealed(false);
    toyRef.current && toyRef.current.reset();
    setPlaying(true);
  };
  return (
    <section ref={ref} style={{ padding: '30px 20px 10px', borderTop: idx === 0 ? 'none' : `1px solid ${CC.border}` }}>
      <Eyebrow>{force.eyebrow}</Eyebrow>
      <h2 style={{ margin: '11px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: 27, lineHeight: 1.05, letterSpacing: '-.02em', color: CC.ink, textWrap: 'balance' }}>{force.title}</h2>
      <p style={{ margin: '13px 0 0', fontFamily: SERIF, fontStyle: 'italic', fontSize: 19, lineHeight: 1.4, color: CC.ink }}>{force.lead}</p>
      <div style={{ margin: '14px 0 0', position: 'relative', height: 236 }}>
        <ForceToy key={force.id} force={force} knob={knob} playing={playing} revealed={revealed} onAutoReveal={() => setRevealed(true)} toyRef={toyRef} />
      </div>
      {/* the poke control — play / reset + an elegant slider line under the viz */}
      {force.knob &&
        <div style={{ padding: '14px 2px 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 9 }}>
            <span style={{ fontFamily: SANS, fontSize: 12, fontWeight: 500, letterSpacing: '.02em', color: CC.ink3 }}>{force.knob.label}</span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 14 }}>
              {force.reveal &&
                <button onClick={() => setRevealed((r) => !r)} style={{ fontFamily: SANS, fontSize: 11.5, fontWeight: 600, color: revealed ? CC.ink : CC.ink3, background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>{revealed ? '⤡ flatten' : '⤢ reveal'}</button>}
              <MonoVal size={12}>{(+knob).toFixed(2)}</MonoVal>
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
            <button onClick={() => setPlaying((p) => !p)} aria-label={playing ? 'Pause' : 'Play'}
              style={{ width: 34, height: 34, borderRadius: DS.rad.pill, flexShrink: 0, background: CC.ink, color: '#fff', border: 'none', fontSize: 11, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>{playing ? '❚❚' : '▶'}</button>
            <button onClick={() => { setRevealed(false); setKnob(force.knob.def); toyRef.current && toyRef.current.reset(); setPlaying(true); }} aria-label="Reset"
              style={{ width: 34, height: 34, borderRadius: DS.rad.pill, flexShrink: 0, background: 'transparent', color: CC.ink2, border: `1px solid ${CC.borderS}`, fontSize: 13, cursor: 'pointer' }}>↺</button>
            <input type="range" className="cc-range" min={force.knob.min} max={force.knob.max} step={force.knob.step} value={knob}
              onChange={(e) => setKnob(parseFloat(e.target.value))} onPointerUp={commitKnob} onKeyUp={commitKnob}
              style={{ flex: 1, minWidth: 0, display: 'block', background: `linear-gradient(90deg, ${CC.ink} 0 ${kpct}%, ${CC.border} ${kpct}% 100%)` }} />
          </div>
        </div>}
      <div style={{ marginTop: 14 }}>{force.body}</div>
      <Caption style={{ marginTop: 14 }}>{force.caption}</Caption>
    </section>
  );
}

function ForcesFeed({ STOPS, onFinale }) {
  const [active, setActive] = React.useState(0);
  const secRefs = React.useRef([]);
  const jump = (i) => { const el = secRefs.current[i]; if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' }); };
  const name = (i) => i === 0 ? 'Orientation' : (FORCE_TAB[STOPS[i].id] || STOPS[i].id);
  return (
    <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', background: CC.bg }}>
      <div style={{ flex: 1, minHeight: 0, overflow: 'auto', position: 'relative' }}>
        {/* sticky index — current force + jump dots */}
        <div style={{ position: 'sticky', top: 0, zIndex: 6, display: 'flex', alignItems: 'center', gap: 10, padding: '11px 20px', background: 'rgba(249,248,244,.96)', backdropFilter: 'blur(8px)', borderBottom: `1px solid ${CC.border}` }}>
          <span style={{ fontFamily: SANS, fontSize: 11, fontWeight: 600, letterSpacing: '.12em', textTransform: 'uppercase', color: CC.ink2 }}>{name(active)}</span>
          <span style={{ marginLeft: 'auto', display: 'inline-flex', gap: 5, alignItems: 'center' }}>
            {STOPS.map((s, i) => (
              <button key={i} onClick={() => jump(i)} title={name(i)} aria-label={name(i)} style={{
                width: i === active ? 16 : 6, height: 6, borderRadius: 9, padding: 0, border: 'none', cursor: 'pointer',
                background: i === active ? CC.ink : CC.ink4, opacity: i === active ? 1 : 0.5, transition: 'all .25s' }} />
            ))}
          </span>
        </div>
        {STOPS.map((force, i) => (
          <ForceFeedItem key={force.id} force={force} idx={i} assignRef={(el) => (secRefs.current[i] = el)} onActive={setActive} />
        ))}
        {/* finale → the whole engine */}
        <div style={{ padding: '34px 20px 90px', textAlign: 'center', borderTop: `1px solid ${CC.border}`, marginTop: 22 }}>
          <Eyebrow style={{ color: CC.ink3 }}>That’s the engine</Eyebrow>
          <button onClick={onFinale} style={{ marginTop: 14, background: CC.ink, color: '#fff', border: 'none', borderRadius: DS.rad.pill, padding: '14px 26px', fontFamily: SANS, fontSize: 15, fontWeight: 500, cursor: 'pointer' }}>See it run, all at once →</button>
        </div>
      </div>
    </div>
  );
}

// ── the integration container: orientation → 6 forces → finale.
// Same surface geometry as the U.S. story: a square compass anchored right, a
// paper scrim, and the floating editorial copy on the left.
function ForcesTour({ onFinale }) {
  const STOPS = React.useMemo(() => [FORCE_ORIENT, ...FORCES], []);
  const [fi, setFi] = useState(0);
  const force = STOPS[fi];
  const [knob, setKnob] = useState(FORCE_ORIENT.knob ? FORCE_ORIENT.knob.def : 0);
  const [playing, setPlaying] = useState(false);
  const [revealed, setRevealed] = useState(false);
  const toyRef = useRef(null);
  const narrRef = useRef(null);   // the floating prose column (desktop) — scrolled
                                  // via the wheel handler below so short viewports
                                  // can reach the rest of the body + the nav buttons.
  const isMobile = useIsMobile();
  const LX = isMobile ? '20px' : RAIL_LX;
  const RX = isMobile ? '20px' : '44px';

  const goStop = (i) => {
    const f = STOPS[i];
    setFi(i); setKnob(f.knob ? f.knob.def : 0); setRevealed(false);
    setPlaying(!f.static && !f.ambient);   // real forces auto-play on arrival
    if (narrRef.current) narrRef.current.scrollTop = 0;   // new force → read from the top
  };
  const onStep = () => { setPlaying(false); toyRef.current && toyRef.current.step(); };
  const onReset = () => {
    setRevealed(false); setKnob(force.knob ? force.knob.def : 0);
    toyRef.current && toyRef.current.reset();
    setPlaying(!force.static && !force.ambient);   // reset = watch it again from the top
  };
  // a new dial value only shows its effect from a fresh start. The value tracks live
  // while you drag (setKnob), but the re-seed + replay waits until you RELEASE the
  // slider (commitKnob) — restarting on every tick would never let a run play out.
  const commitKnob = () => {
    if (force.static) return;
    if (force.reveal) setRevealed(false);
    toyRef.current && toyRef.current.reset();
    setPlaying(true);
  };

  const lastForce = fi === STOPS.length - 1;
  const navBtn = (label, onClick, primary) => (
    <button onClick={onClick} style={{
      padding: '13px 22px', borderRadius: DS.rad.pill, cursor: 'pointer', fontFamily: SANS, fontSize: DS.type.body, fontWeight: 500,
      border: primary ? 'none' : `1px solid ${CC.border}`, background: primary ? CC.ink : CC.surface, color: primary ? '#fff' : CC.ink2,
    }}>{label}</button>
  );

  // the editorial column — shared between layouts; padding differs per device.
  const narrative = (
    <div ref={narrRef} style={{ background: 'transparent', display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, justifyContent: isMobile ? 'flex-start' : 'safe center', overflow: 'auto' }}>
      <div style={{ flexShrink: 0, padding: `${isMobile ? '22px' : 'clamp(28px,4.5vh,52px)'} ${RX} 8px ${LX}` }}>
        <Eyebrow>{force.eyebrow}</Eyebrow>
        <h1 style={{ margin: '14px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: isMobile ? 28 : 'clamp(30px,3.4vw,46px)', lineHeight: 1.04, letterSpacing: '-.02em', maxWidth: TEXTW }}>{force.title}</h1>
        <p style={{ margin: '16px 0 0', fontFamily: SERIF, fontStyle: 'italic', fontSize: DS.type.subhead, lineHeight: 1.42, color: CC.ink, maxWidth: TEXTW }}>{force.lead}</p>
        {force.body}
        <Caption style={{ marginTop: 18 }}>{force.caption}</Caption>
      </div>
      <div style={{ flexShrink: 0, padding: `14px ${RX} ${isMobile ? '26px' : 'clamp(24px,4vh,40px)'} ${LX}`, display: 'flex', gap: 10, pointerEvents: 'auto' }}>
        {fi > 0 && navBtn('← Back', () => goStop(fi - 1), false)}
        {fi === 0 ? navBtn('Meet the first force →', () => goStop(1), true)
          : lastForce ? navBtn('All together →', onFinale, true)
            : navBtn('Next force →', () => goStop(fi + 1), true)}
      </div>
    </div>
  );

  if (isMobile) {
    // one long scroll: a section per force (heading → viz → poke line → read),
    // each viz auto-plays as it enters view. (Desktop keeps the guided stepper.)
    return <ForcesFeed STOPS={STOPS} onFinale={onFinale} />;
  }

  return (
    <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', background: CC.bg }}>
      {/* the prose floats pointer-transparent (so the map stays draggable), which
          also blocks wheel-scroll — so forward wheel over the whole area to the
          prose column, letting short viewports reach the body + nav buttons. */}
      <div onWheel={(e) => { const n = narrRef.current; if (n && n.scrollHeight > n.clientHeight + 1) n.scrollTop += (e.deltaMode === 1 ? e.deltaY * 16 : e.deltaY); }}
        style={{ flex: 1, minHeight: 0, position: 'relative', overflow: 'hidden', background: CC.bg }}>
        {/* the compass — a contained square anchored right (matches the story field) */}
        <div style={{ position: 'absolute', top: '-2%', bottom: '-2%', right: '2%', aspectRatio: '1' }}>
          <ForceToy key={force.id} force={force} knob={knob} playing={playing} revealed={revealed}
            onAutoReveal={() => setRevealed(true)} toyRef={toyRef} />
        </div>
        {/* paper scrim — keeps the floating prose legible, feathers out before the map */}
        <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, width: '56%', background: `linear-gradient(90deg, ${CC.bg} 0%, ${CC.bg} 88%, rgba(249,248,244,0) 100%)`, pointerEvents: 'none', zIndex: 1 }} />
        {/* floating narrative — a centered editorial block on the left (pointer-
            transparent so the map stays draggable; only the buttons catch clicks) */}
        <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, width: RAIL_W, display: 'flex', flexDirection: 'column', minHeight: 0, zIndex: 3, pointerEvents: 'none' }}>
          {narrative}
        </div>
      </div>
      <ForceBar stops={STOPS} fi={fi} goStop={goStop} force={force}
        playing={playing} setPlaying={setPlaying} onStep={onStep} onReset={onReset}
        knob={knob} setKnob={setKnob} onCommit={commitKnob} revealed={revealed} setRevealed={setRevealed} />
    </div>
  );
}

Object.assign(window, {
  ForceToy, ForceBar, ForcesTour, FORCES, FORCE_ORIENT,
  seedMixed, seedAgents: seedMixed, seedAffect, seedNetwork, seedMedia, seedBackfire,
  stepBC, stepParty, stepAffect, stepRewire, stepMedia, stepBackfire,
  spreadOf, partyGap, meanWarmth, crossTieFrac, meanExtremity,
});
