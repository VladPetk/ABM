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

// ── jumpiness taming (docs/demo_jumpiness.md Step 1) ──────────────────────
// The raw per-tick positions oscillate hard (~3% of the compass every tick,
// half of step-pairs reverse >90°). We render an EMA of the position series
// instead of the raw cloud: a short window for the crowd, a longer one for
// the spotlighted character. Cohort replacement is a different beast — a slot
// reused by a new person — so the EMA RESETS at each replacement tick (no
// glide across the compass) and the compass ghost-fades those moments.
const CROWD_WIN = 4;     // EMA window for the crowd dots
const SPOT_WIN = 9;      // longer window for the spotlighted character
const FADE_TICKS = 6;    // ghost-fade duration after a replacement (~2 yr)

// replacement lookup: agentId → sorted ticks[], and tick → agentIds[]
function replacementSets(run) {
  if (run._repl) return run._repl;
  const byAgent = new Map();
  const events = run.replacement_events || [];
  for (const [t, a] of events) {
    if (!byAgent.has(a)) byAgent.set(a, []);
    byAgent.get(a).push(t);
  }
  for (const arr of byAgent.values()) arr.sort((x, y) => x - y);
  run._repl = { byAgent };
  return run._repl;
}

// EMA position series for a given window, cached per run. Resets to the raw
// position at any tick where that agent was replaced, so a teleport reads as
// a cut (new person), never a smear across the compass.
function emaSeries(run, win) {
  if (!run._ema) run._ema = {};
  if (run._ema[win]) return run._ema[win];
  const alpha = 2 / (win + 1);
  const P = run.pos, T = P.length, N = P[0].length;
  const { byAgent } = replacementSets(run);
  const isReset = new Array(T);                 // isReset[t] = Set(agentIds replaced at t)
  for (let t = 0; t < T; t++) isReset[t] = null;
  for (const [a, ticks] of byAgent) {
    for (const t of ticks) {
      // A replacement logged at tick t means pos[t] is still the OLD
      // person; the NEW person first appears at pos[t+1]. Reset the EMA
      // at t+1 so the new track starts clean — resetting at t (old pos)
      // left the t→t+1 step to smear across the compass (a visible slide
      // that read as a single-tick teleport).
      const rt = t + 1;
      if (rt < 0 || rt >= T) continue;
      if (!isReset[rt]) isReset[rt] = new Set();
      isReset[rt].add(a);
    }
  }
  const S = new Array(T);
  S[0] = P[0].map((p) => [p[0], p[1]]);
  for (let t = 1; t < T; t++) {
    const prev = S[t - 1], cur = P[t], reset = isReset[t], row = new Array(N);
    for (let i = 0; i < N; i++) {
      if (reset && reset.has(i)) { row[i] = [cur[i][0], cur[i][1]]; continue; }
      row[i] = [
        alpha * cur[i][0] + (1 - alpha) * prev[i][0],
        alpha * cur[i][1] + (1 - alpha) * prev[i][1],
      ];
    }
    S[t] = row;
  }
  run._ema[win] = S;
  return S;
}

// interpolate the EMA-smoothed cloud at fractional tick f (crowd window)
function posAt(run, f) {
  const S = emaSeries(run, CROWD_WIN);
  const t0 = Math.max(0, Math.min(LAST, Math.floor(f)));
  const t1 = Math.min(LAST, t0 + 1);
  const a = f - t0;
  const A = S[t0], B = S[t1];
  const out = new Array(A.length);
  for (let i = 0; i < A.length; i++) {
    out[i] = [A[i][0] + (B[i][0] - A[i][0]) * a, A[i][1] + (B[i][1] - A[i][1]) * a];
  }
  return out;
}
// EMA position of one agent at fractional tick. `win` defaults to the longer
// spotlight window; pass CROWD_WIN to match the crowd cloud.
function agentPosAt(run, f, idx, win = SPOT_WIN) {
  const S = emaSeries(run, win);
  const t0 = Math.max(0, Math.min(LAST, Math.floor(f)));
  const t1 = Math.min(LAST, t0 + 1);
  const a = f - t0;
  const A = S[t0][idx], B = S[t1][idx];
  return [A[0] + (B[0] - A[0]) * a, A[1] + (B[1] - A[1]) * a];
}

// Agents mid-replacement at fractional tick f (within FADE_TICKS of a slot
// reuse). A replacement is a person leaving and a different person arriving
// in the same slot — so the viz CROSSFADES: the departing person fades out
// at their last position (in their party colour), the arriving person fades
// in at the new position. Returns a Map(idx → {fromPos, fromParty, outAlpha,
// inAlpha}); the caller draws both dots, weighting by these alphas.
function replacementFades(run, f) {
  const { byAgent } = replacementSets(run);
  const map = new Map();
  if (byAgent.size === 0) return map;
  for (const [idx, ticks] of byAgent) {
    for (let k = ticks.length - 1; k >= 0; k--) {
      const tr = ticks[k];
      const age = f - tr;
      if (age < 0) continue;
      if (age > FADE_TICKS) break;       // older events only further back
      const j = tr;                      // pos[tr] = last frame of departing person
      const prevPos = run.pos[j][idx];
      const frac = age / FADE_TICKS;      // 0 at the splice → 1 at fade end
      map.set(idx, {
        fromPos: [prevPos[0], prevPos[1]],
        fromParty: run.party[j][idx],
        outAlpha: 1 - frac,               // departing dot fades out
        inAlpha: frac,                    // arriving dot fades in
      });
      break;                             // most-recent replacement only
    }
  }
  return map;
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
  CROWD_WIN, SPOT_WIN, FADE_TICKS, replacementFades, emaSeries,
});
