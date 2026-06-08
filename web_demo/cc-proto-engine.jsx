// Calm to Camps — prototype engine
// Thin layer over window.CC_DATA (the real polarlab export, repacked compact).
// Provides party/colour mapping, fractional-tick interpolation of agent
// positions and macro metrics, network-snapshot lookup, and the usePlayhead
// hook that drives play / pause / speed / scrub with localStorage persistence.

const D = window.CC_DATA;
const NT = D.meta.n_ticks;             // 136
const TPY = D.meta.ticks_per_year;     // 3
const Y0 = D.meta.tick_0_year;         // 1980
const LAST = NT - 1;                   // 135

const tickToYear = (t) => Y0 + t / TPY;
const yearToTick = (y) => (y - Y0) * TPY;
const PARTY_CH = { 0: 'D', 1: 'R', 2: 'I' };
function partyColor(p) { return p === 0 ? CC.d : p === 1 ? CC.r : CC.i; }
function partyName(p) { return p === 0 ? 'Democrat' : p === 1 ? 'Republican' : 'Independent'; }

// interpolate the full position cloud at fractional tick f
function posAt(run, f) {
  const t0 = Math.max(0, Math.min(LAST, Math.floor(f)));
  const t1 = Math.min(LAST, t0 + 1);
  const a = f - t0;
  const A = run.pos[t0], B = run.pos[t1];
  const out = new Array(A.length);
  for (let i = 0; i < A.length; i++) {
    out[i] = [A[i][0] + (B[i][0] - A[i][0]) * a, A[i][1] + (B[i][1] - A[i][1]) * a];
  }
  return out;
}
// position of one agent at fractional tick
function agentPosAt(run, f, idx) {
  const t0 = Math.max(0, Math.min(LAST, Math.floor(f)));
  const t1 = Math.min(LAST, t0 + 1);
  const a = f - t0;
  const A = run.pos[t0][idx], B = run.pos[t1][idx];
  return [A[0] + (B[0] - A[0]) * a, A[1] + (B[1] - A[1]) * a];
}
// party / faction are step values — take the nearest integer tick
const partyAt = (run, f, idx) => run.party[Math.round(f)][idx];
const factionAt = (run, f, idx) => run.charFaction[idx] ? run.charFaction[idx][Math.round(f)] : null;
function affectAt(run, f, idx) {
  const s = run.charAffect[idx]; if (!s) return null;
  const t0 = Math.max(0, Math.min(LAST, Math.floor(f))), t1 = Math.min(LAST, t0 + 1), a = f - t0;
  return s[t0] + (s[t1] - s[t0]) * a;
}
// macro metric interpolation
function macroAt(run, f, key) {
  const t0 = Math.max(0, Math.min(LAST, Math.floor(f))), t1 = Math.min(LAST, t0 + 1), a = f - t0;
  return run.macro[t0][key] + (run.macro[t1][key] - run.macro[t0][key]) * a;
}

// ── lazy counterfactual BRANCH loader ───────────────────────────────────────
// The bundle ships counterfactuals LEAN (macro + 2025 endpoint). The per-tick
// agent positions needed to PLAY a branch forward live in small static files
// (web_demo/cf/<id>_<year>.json, see scripts/build_branch_data.py), fetched only
// when a lever+year is actually opened. Promise-cached so each branch loads once.
const _branchCache = {};
// Stitch baseline frames 0..release_tick-1 in front of the branch's
// release->end frames → a full-length run <Field> can play from 1980 to 2025
// that is identical to baseline until the release year, then diverges.
function stitchBranch(branch) {
  const rt = branch.release_tick;
  const base = D.runs.baseline;
  return {
    release_tick: rt,
    pos: base.pos.slice(0, rt).concat(branch.pos),
    party: base.party.slice(0, rt).concat(branch.party),
    macro: base.macro,
  };
}
function loadBranch(id, year) {
  const k = id + '_' + year;
  if (!_branchCache[k]) {
    _branchCache[k] = fetch('cf/' + k + '.json')
      .then((r) => { if (!r.ok) throw new Error('branch fetch failed: ' + r.status); return r.json(); })
      .then((b) => stitchBranch(b));
  }
  return _branchCache[k];
}

// ── lazy SANDBOX loader (the 5^5 pre-rendered alternate-history grid) ─────────
// Files (web_demo/cf/sandbox/sandbox_<key>.json, see scripts/build_sandbox_data.py)
// store DECIMATED frames at `ticks` (every other tick, ~160 agents) plus the four
// macro series. We expand them once into a full LAST+1 run object so <Field> /
// posAt / macroAt work unchanged. Promise-cached per key.
const _sandboxCache = {};
function expandSandbox(sb) {
  const ticks = sb.ticks, nF = ticks.length, nA = sb.pos[0].length, full = NT;
  const pos = new Array(full), party = new Array(full), macro = new Array(full);
  const MK = ['sep', 'aff', 'spread', 'align'];
  let fi = 0;
  for (let t = 0; t < full; t++) {
    while (fi < nF - 2 && ticks[fi + 1] < t) fi++;
    const j = Math.min(nF - 1, fi + 1);
    const t0 = ticks[fi], t1 = ticks[j];
    const a = t1 > t0 ? (t - t0) / (t1 - t0) : 0;
    const A = sb.pos[fi], B = sb.pos[j], row = new Array(nA);
    for (let i = 0; i < nA; i++) row[i] = [A[i][0] + (B[i][0] - A[i][0]) * a, A[i][1] + (B[i][1] - A[i][1]) * a];
    pos[t] = row;
    party[t] = sb.party[a < 0.5 ? fi : j];
    const m0 = sb.macro[fi], m1 = sb.macro[j], mm = {};
    for (const k of MK) mm[k] = m0[k] + (m1[k] - m0[k]) * a;
    macro[t] = mm;
  }
  return { pos, party, macro, knobs: sb.knobs, key: sb.key };
}
function loadSandbox(key) {
  if (!_sandboxCache[key]) {
    _sandboxCache[key] = fetch('cf/sandbox/sandbox_' + key + '.json')
      .then((r) => { if (!r.ok) throw new Error('sandbox fetch failed: ' + r.status); return r.json(); })
      .then(expandSandbox);
  }
  return _sandboxCache[key];
}

// network snapshot at-or-before fractional tick f (event-cadence)
function netSnapshotKey(run, f) {
  const keys = Object.keys(run.net).map(Number).sort((x, y) => x - y);
  let k = keys[0];
  for (const kk of keys) if (kk <= f) k = kk;
  return k;
}
function egoEdges(run, f, idx) {
  const k = netSnapshotKey(run, f);
  const edges = run.net[String(k)] || [];
  return edges.filter((e) => e[0] === idx || e[1] === idx);
}

// metric display domains (computed once from baseline)
const baseMacro = D.runs.baseline.macro;
function domainOf(key, transform) {
  let lo = Infinity, hi = -Infinity;
  for (const m of baseMacro) { const v = transform ? transform(m[key]) : m[key]; if (v < lo) lo = v; if (v > hi) hi = v; }
  return [lo, hi];
}
// affective polarization = magnitude of (negative) out-party warmth
const METRICS = {
  sep: { key: 'sep', label: 'Party separation', transform: (v) => v, domain: domainOf('sep') },
  aff: { key: 'aff', label: 'Affective polarization', transform: (v) => -v, domain: domainOf('aff', (v) => -v) },
};

// ── playhead hook ────────────────────────────────────────────────────────
function usePlayhead({ initial = 0, autoplay = true, baseTicksPerSec = 6, storageKey = 'cc_tick' } = {}) {
  const [tick, setTickRaw] = React.useState(() => {
    try { const s = localStorage.getItem(storageKey); if (s != null) return Math.max(0, Math.min(LAST, parseFloat(s))); } catch (e) {}
    return initial;
  });
  const [playing, setPlaying] = React.useState(autoplay);
  const [speed, setSpeed] = React.useState(1);
  const tickRef = React.useRef(tick);
  tickRef.current = tick;

  const setTick = React.useCallback((v) => {
    const nv = typeof v === 'function' ? v(tickRef.current) : v;
    const c = Math.max(0, Math.min(LAST, nv));
    tickRef.current = c;
    setTickRaw(c);
    try { localStorage.setItem(storageKey, String(c)); } catch (e) {}
  }, [storageKey]);

  React.useEffect(() => {
    if (!playing) return;
    let raf, prev = null;
    const loop = (ts) => {
      if (prev == null) prev = ts;
      const dt = (ts - prev) / 1000; prev = ts;
      let nt = tickRef.current + dt * baseTicksPerSec * speed;
      if (nt >= LAST) { nt = LAST; setTick(nt); setPlaying(false); return; }
      setTick(nt);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [playing, speed, baseTicksPerSec, setTick]);

  const toggle = React.useCallback(() => {
    if (tickRef.current >= LAST) setTick(0);
    setPlaying((p) => !p);
  }, [setTick]);

  return { tick, setTick, playing, setPlaying, toggle, speed, setSpeed };
}

Object.assign(window, {
  D, NT, TPY, Y0, LAST, tickToYear, yearToTick, PARTY_CH, partyColor, partyName,
  posAt, agentPosAt, partyAt, factionAt, affectAt, macroAt,
  netSnapshotKey, egoEdges, METRICS, usePlayhead,
  loadBranch, stitchBranch, loadSandbox,
});
