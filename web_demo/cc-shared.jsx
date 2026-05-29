// Calm to Camps — shared foundation
// Tokens (inherited from Direction E, light mode), seeded RNG, the
// agent-generation model for the compass, historical events, macro-metric
// series, and a handful of small UI primitives. Everything here is exported
// to window at the bottom so the other babel files can use it.

// ── Palette ───────────────────────────────────────────────────────────
// Light mode only for this round. Party colours: navy = Democrat,
// oxblood = Republican, warm-grey = Independent.
const CC = {
  bg:      '#f3f3f0',   // warm paper
  bg2:     '#ebe8df',
  surface: '#ffffff',
  ink:     '#1a1d23',
  ink2:    '#3d4148',
  ink3:    '#74797f',
  ink4:    '#adb1b5',
  border:  '#e0ddd3',
  borderS: '#cdc9bd',
  d:       '#1f3565',   // Democrat — navy
  r:       '#8b2530',   // Republican — oxblood
  i:       '#9a958a',   // Independent — warm grey
  dSoft:   '#d4d9e3',
  rSoft:   '#ead7d9',
  iSoft:   '#e4e1d8',
  dLine:   '#2f4a86',
  rLine:   '#a23a3a',
};
const SANS = "'Geist', system-ui, -apple-system, sans-serif";
const MONO = "'Geist Mono', ui-monospace, monospace";
const SERIF = "'Newsreader', Georgia, serif";
const TNUM = { fontFeatureSettings: '"tnum", "ss01"' };

// ── Seeded RNG (own name to avoid colliding with the old wireframes) ────
function ccRng(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ── Timeline math ───────────────────────────────────────────────────────
const YEAR0 = 1980, YEAR1 = 2025;
const yearToFrac = (y) => (y - YEAR0) / (YEAR1 - YEAR0);

// Separation grows over time — calm in 1980, hard camps by 2025.
// Accelerates after the mid-90s. Returns 0..1.
function separationAt(yf) {
  const e = Math.pow(yf, 1.35);          // gentle early, steeper late
  return 0.12 + 0.82 * e;
}

// ── Agent generation ─────────────────────────────────────────────────────
// 2D ideology plane in [-1,1]^2. x = economic (left/right),
// y = cultural (top = progressive/open, bottom = traditional).
// Democrats sort toward the bottom-left, Republicans toward top-right —
// the classic diagonal. y is flipped to match the literature: traditional /
// authoritarian at top, progressive / libertarian at bottom.
const POLE_D = { x: -0.64, y: -0.50 };
const POLE_R = { x:  0.64, y:  0.50 };

function genAgents(year, seed = 7, n = 240) {
  const yf = yearToFrac(year);
  const sep = separationAt(yf);
  const rng = ccRng(seed);
  const out = [];
  for (let i = 0; i < n; i++) {
    // latent lean in [-1,1]; sign = party tendency, magnitude = intensity
    const u = rng() * 2 - 1;
    const lean = Math.sign(u) * Math.pow(Math.abs(u), 0.85);
    const intensity = Math.abs(lean);
    const pole = lean >= 0 ? POLE_R : POLE_D;
    // target sits along the agent's pole, proportional to intensity
    const tx = pole.x * intensity;
    const ty = pole.y * intensity;
    // centre jitter for the un-sorted early world
    const cj = 0.30;
    const jx = (rng() - 0.5) * cj;
    const jy = (rng() - 0.5) * cj;
    // perpendicular spread that tightens as camps form
    const spread = 0.34 * (1 - 0.55 * sep);
    const px0 = jx * (1 - sep) + tx * sep + (rng() - 0.5) * spread;
    const py0 = jy * (1 - sep) + ty * sep + (rng() - 0.5) * spread;
    const x = Math.max(-0.96, Math.min(0.96, px0));
    const y = Math.max(-0.96, Math.min(0.96, py0));
    // party: weak leaners stay Independent early, sort later
    let party;
    const indepThresh = 0.20 * (1 - 0.6 * sep);
    if (intensity < indepThresh) party = 'I';
    else party = lean >= 0 ? 'R' : 'D';
    out.push({ id: i, x, y, party, intensity });
  }
  return out;
}

// Linda — the headline character. Hand-authored trajectory: centrist
// Democrat in the mid-80s, drifts to a Republican partisan by 2016+.
const LINDA_KEYS = [
  { y: 1985, x: -0.16, y2:  0.02, party: 'D' },
  { y: 1996, x: -0.05, y2:  0.10, party: 'D' },
  { y: 2001, x:  0.10, y2:  0.14, party: 'I' },
  { y: 2008, x:  0.24, y2:  0.22, party: 'I' },
  { y: 2016, x:  0.46, y2:  0.40, party: 'R' },
  { y: 2025, x:  0.58, y2:  0.50, party: 'R' },
];
function lindaAt(year) {
  const k = LINDA_KEYS;
  if (year <= k[0].y) return { x: k[0].x, y: k[0].y2, party: k[0].party };
  if (year >= k[k.length - 1].y) { const l = k[k.length - 1]; return { x: l.x, y: l.y2, party: l.party }; }
  for (let i = 0; i < k.length - 1; i++) {
    if (year >= k[i].y && year <= k[i + 1].y) {
      const t = (year - k[i].y) / (k[i + 1].y - k[i].y);
      return {
        x: k[i].x + (k[i + 1].x - k[i].x) * t,
        y: k[i].y2 + (k[i + 1].y2 - k[i].y2) * t,
        party: t < 0.5 ? k[i].party : k[i + 1].party,
      };
    }
  }
  return { x: k[0].x, y: k[0].y2, party: 'D' };
}

// Linda's ego network at a given year — homogenises over time.
// Returns ~8 neighbours as offsets around her, with party.
function lindaNetwork(year) {
  const rng = ccRng(99);
  const yf = yearToFrac(year);
  const rOut = lindaAt(year).party === 'R';
  // fraction of neighbours that match her party grows over time
  const matchFrac = 0.45 + 0.5 * yf;
  const nodes = [];
  const N = 9;
  for (let i = 0; i < N; i++) {
    const ang = (i / N) * Math.PI * 2 + rng() * 0.5;
    const rad = 0.10 + rng() * 0.13;
    const matches = rng() < matchFrac;
    let party;
    if (matches) party = rOut ? 'R' : 'D';
    else party = rng() < 0.4 ? 'I' : (rOut ? 'D' : 'R');
    nodes.push({ dx: Math.cos(ang) * rad, dy: Math.sin(ang) * rad, party, i });
  }
  return nodes;
}

// ── Historical events ────────────────────────────────────────────────────
const EVENTS = [
  { id: 'reagan',  year: 1981.0, label: 'Reagan inaugurated', short: 'Reagan' },
  { id: 'cw_end',  year: 1991.0, label: 'Cold War ends',      short: 'Cold War ends' },
  { id: 'fox',     year: 1996.8, label: 'Fox News launches',  short: 'Fox News' },
  { id: 'sept11',  year: 2001.7, label: 'September 11',        short: '9/11' },
  { id: 'obama',   year: 2008.85, label: 'Obama elected',      short: 'Obama' },
  { id: 'teaparty',year: 2009.3, label: 'Tea Party rises',    short: 'Tea Party' },
  { id: 'trump',   year: 2016.85, label: 'Trump elected',      short: 'Trump' },
  { id: 'covid',   year: 2020.2, label: 'COVID-19',            short: 'COVID' },
  { id: 'jan6',    year: 2021.05, label: 'January 6',           short: 'Jan 6' },
];

// Interventions (lay names + bucket outcome). Two structural ones work.
const INTERVENTIONS = [
  { id: 'X1', name: 'Show people the other side', bucket: 'backfire' },
  { id: 'X2', name: 'Fix the algorithm',          bucket: 'partial' },
  { id: 'X3', name: 'Quit cable news',            bucket: 'partial' },
  { id: 'X4', name: 'Bipartisan dialogue programs', bucket: 'null' },
  { id: 'X5', name: 'Ranked-choice voting',       bucket: 'real' },
  { id: 'X6', name: 'Shared neighborhoods & workplaces', bucket: 'real' },
  { id: 'X7', name: 'Correct the perception gap', bucket: 'partial' },
];
const BUCKET_META = {
  null:     { label: 'No effect',  color: '#74797f' },
  partial:  { label: 'Partial',    color: '#c47a2c' },
  real:     { label: 'Real effect',color: '#3f7d54' },
  backfire: { label: 'Backfire',   color: '#8b2530' },
};

// ── Macro metric series (Iyengar) — sampled paths over 1980..2025 ─────────
// Returns array of {year, sep, aff} in 0..1. Both rise, accelerating.
function macroSeries() {
  const pts = [];
  for (let y = YEAR0; y <= YEAR1; y += 1) {
    const yf = yearToFrac(y);
    const sep = 0.18 + 0.66 * Math.pow(yf, 1.4);
    // affect lags then overtakes — the "affect drifts faster" finding
    const aff = 0.14 + 0.74 * Math.pow(yf, 1.8) + 0.05 * Math.sin(yf * 6);
    pts.push({ year: y, sep: Math.min(1, sep), aff: Math.min(1, Math.max(0, aff)) });
  }
  return pts;
}
// Counterfactual: a "real effect" intervention bends affect down after release.
function macroCounterfactual(releaseYear, strength = 0.42) {
  const base = macroSeries();
  return base.map((p) => {
    if (p.year < releaseYear) return { ...p };
    const t = (p.year - releaseYear) / (YEAR1 - releaseYear);
    const damp = strength * (1 - Math.exp(-t * 2.2));
    return { year: p.year, sep: Math.max(0, p.sep - damp * 0.7), aff: Math.max(0, p.aff - damp) };
  });
}

// Build an SVG polyline path string from series + accessor, mapped into a box.
function seriesPath(series, key, x0, y0, w, h) {
  const n = series.length;
  return series.map((p, i) => {
    const px = x0 + (i / (n - 1)) * w;
    const py = y0 + h - p[key] * h;
    return `${i === 0 ? 'M' : 'L'}${px.toFixed(1)},${py.toFixed(1)}`;
  }).join(' ');
}

// ── Small primitives ──────────────────────────────────────────────────────
function Logo({ size = 13.5, color = CC.ink }) {
  return (
    <span style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: size, fontWeight: 600, letterSpacing: '-.015em', color }}>
      <span style={{ display: 'inline-flex', gap: 3 }}>
        <span style={{ width: 7, height: 7, borderRadius: 999, background: CC.d }} />
        <span style={{ width: 7, height: 7, borderRadius: 999, background: CC.r }} />
      </span>
      polarlab
    </span>
  );
}

function InfoDot({ size = 12 }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      width: size, height: size, borderRadius: 999,
      border: `1px solid ${CC.ink4}`, color: CC.ink3,
      fontSize: size * 0.66, fontWeight: 500, lineHeight: 1, fontStyle: 'italic', cursor: 'default',
    }}>i</span>
  );
}

function Eyebrow({ children, color = CC.ink3, style }) {
  return (
    <span style={{
      fontSize: 11, color, letterSpacing: '.14em', textTransform: 'uppercase',
      fontWeight: 500, ...style,
    }}>{children}</span>
  );
}

function FloatCard({ style, children }) {
  return (
    <div style={{
      position: 'absolute',
      background: 'rgba(255,255,255,.9)',
      backdropFilter: 'blur(18px) saturate(140%)',
      WebkitBackdropFilter: 'blur(18px) saturate(140%)',
      border: `1px solid ${CC.border}`, borderRadius: 12, padding: 13,
      boxShadow: '0 6px 22px rgba(26,29,35,.07)',
      ...style,
    }}>{children}</div>
  );
}

function PartySwatch({ party, size = 8 }) {
  const col = party === 'D' ? CC.d : party === 'R' ? CC.r : CC.i;
  return <span style={{ width: size, height: size, borderRadius: 999, background: col, display: 'inline-block', flex: '0 0 auto' }} />;
}

Object.assign(window, {
  CC, SANS, MONO, SERIF, TNUM, ccRng,
  YEAR0, YEAR1, yearToFrac, separationAt,
  genAgents, lindaAt, lindaNetwork, POLE_D, POLE_R,
  EVENTS, INTERVENTIONS, BUCKET_META, macroSeries, macroCounterfactual, seriesPath,
  Logo, InfoDot, Eyebrow, FloatCard, PartySwatch,
});
