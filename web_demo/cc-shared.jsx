// Calm to Camps — shared foundation
// Tokens (inherited from Direction E, light mode), seeded RNG, the
// agent-generation model for the compass, historical events, macro-metric
// series, and a handful of small UI primitives. Everything here is exported
// to window at the bottom so the other babel files can use it.

// ── Palette ───────────────────────────────────────────────────────────
// Light mode only for this round. Party colours: navy = Democrat,
// oxblood = Republican, warm-grey = Independent.
const CC = {
  bg:      '#f9f8f4',   // near-white canvas
  chrome:  '#f3f3f0',   // warm paper — top header only
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
// Reading prose (pairing F1): Literata at 14.5/1.62 — a low-contrast text
// serif beside Newsreader's display cuts. Geist stays for UI furniture
// (eyebrows, buttons, chips, timeline); MONO for data. Spread `PROSE` onto
// reading paragraphs instead of hand-setting size/leading.
const BODY_SERIF = "'Literata', Georgia, serif";
const PROSE = { fontFamily: BODY_SERIF, fontSize: 14.5, lineHeight: 1.62 };
const TNUM = { fontFeatureSettings: '"tnum", "ss01"' };

// ── Responsive foundation ─────────────────────────────────────────────────
// The whole site was built desktop-first (a prose column floating over a
// compass anchored right). `useIsMobile` is the single switch every view reads
// to fall back to a stacked, touch-friendly layout. One breakpoint, matchMedia
// driven so it tracks orientation changes without a resize listener storm.
const MOBILE_BP = 760;
function useIsMobile(bp = MOBILE_BP) {
  const q = `(max-width: ${bp}px)`;
  const get = () => (typeof window !== 'undefined' && window.matchMedia ? window.matchMedia(q).matches : false);
  const [m, setM] = React.useState(get);
  React.useEffect(() => {
    const mq = window.matchMedia(q);
    const on = () => setM(mq.matches);
    on();
    mq.addEventListener ? mq.addEventListener('change', on) : mq.addListener(on);
    return () => { mq.removeEventListener ? mq.removeEventListener('change', on) : mq.removeListener(on); };
  }, [q]);
  return m;
}

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

// NOTE (Step 4): the legacy hardcoded intervention table (INTERVENTIONS,
// BUCKET_META) and the synthetic macroCounterfactual() lived here and were one
// of the "three conflicting intervention tables" flagged in the audit. They are
// deleted — the interventions screen now derives everything live from
// D.interventions + D.counterfactuals (the engine's own re-measured output).

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
// The brand mark: two dots (navy Democrat · oxblood Republican). The wordmark
// text lives next to it in the header (SiteHeader), so the mark stays text-free.
function Logo({ size = 13.5, color = CC.ink }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3 }}>
      <span style={{ width: 7, height: 7, borderRadius: 999, background: CC.d }} />
      <span style={{ width: 7, height: 7, borderRadius: 999, background: CC.r }} />
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
      background: 'rgba(249,248,244,.82)',
      backdropFilter: 'blur(14px) saturate(120%)',
      WebkitBackdropFilter: 'blur(14px) saturate(120%)',
      border: `1px solid ${CC.border}`, borderRadius: 12, padding: 13,
      ...style,
    }}>{children}</div>
  );
}

function PartySwatch({ party, size = 8 }) {
  const col = party === 'D' ? CC.d : party === 'R' ? CC.r : CC.i;
  return <span style={{ width: size, height: size, borderRadius: 999, background: col, display: 'inline-block', flex: '0 0 auto' }} />;
}

Object.assign(window, {
  CC, SANS, MONO, SERIF, BODY_SERIF, PROSE, TNUM, ccRng,
  MOBILE_BP, useIsMobile,
  YEAR0, YEAR1, yearToFrac, separationAt,
  genAgents, POLE_D, POLE_R,
  EVENTS, macroSeries, seriesPath,
  Logo, InfoDot, Eyebrow, FloatCard, PartySwatch,
});
