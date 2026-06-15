// Calm to Camps — unified shell (post-QA rebuild).
// ONE simulation surface, two nav labels (model/story) + Playground + pages.
//   • Tier-1 site header (brand + Model / Methods / About)            — constant
//   • Tier-2 mode bar (Story / Interventions)  — constant across postures
//   • body: [tray (slides in for Interventions)] · field · right rail(452)
//   • bottom bar (fixed height): unified timeline+transport, or hope-bar
// Watch and Explore share the SAME draggable timeline + transport. Interventions
// keeps its tweaks on the LEFT and a tab-appropriate narrative rail on the RIGHT.

const RAILW = 452;
const TRAYW = 344;
const BARH = 138;
const BEATS = window.STORY_BEATS;
// wheel scrubbing: ticks advanced per unit of wheel deltaY (tune for feel).
const WHEEL_SENS = 0.0175;
// after the wheel goes idle this long (ms), ease onto the nearest chapter —
// but only if you stopped within SNAP_RANGE ticks of one (a gentle magnet, not
// a forced snap). Stop farther away and you stay exactly where you left off.
const SNAP_IDLE_MS = 170;
const SNAP_RANGE = 2.25;
// the active chapter is derived purely from the tick — the single source of truth
// the wheel, the ▶ autoplay, and the timeline drag all write to.
const beatIndexAt = (t) => {let k = 0;for (let i = 0; i < BEATS.length; i++) if (t + 1e-6 >= BEATS[i].tick) k = i;return k;};

// ── Tier 1 — site header (E1/E2). Pages, not pills. ────────────────────────
// NavLink lives at MODULE scope — defining it inside SiteHeader created a new
// component type on every render, so React remounted the buttons each frame
// while the intro's ambient loop ran, eating every click (mousedown/mouseup
// never hit the same node). Hoisted = stable type = clickable.
function HeaderNavLink({ id, page, setPage, children }) {
  const on = page === id;
  return (
    <button onClick={() => setPage(id)} style={{
      fontFamily: SANS, fontSize: DS.type.small, fontWeight: on ? 600 : 500, color: on ? CC.ink : CC.ink3,
      background: 'none', border: 'none', cursor: 'pointer', padding: '6px 2px', position: 'relative'
    }}>
      {children}
      <span style={{ position: 'absolute', left: 0, right: 0, bottom: -1, height: 2, borderRadius: 2, background: on ? CC.ink : 'transparent' }} />
    </button>);

}
function SiteHeader({ page, setPage }) {
  return (
    <div style={{ height: 58, flexShrink: 0, display: 'flex', alignItems: 'center', gap: 14, padding: '0 clamp(24px, 4vw, 56px)', background: CC.bg, position: 'relative', zIndex: 30 }}>
      <button onClick={() => setPage('model')} style={{ display: 'flex', alignItems: 'center', gap: 12, background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
        <Logo />
        <span style={{ width: 1, height: 18, background: CC.border }} />
        <span style={{ fontFamily: SERIF, fontStyle: 'italic', fontSize: 16, color: CC.ink2, whiteSpace: 'nowrap' }}>Calm to Camps</span>
      </button>
      <span style={{ flex: 1 }} />
      <nav style={{ display: 'flex', alignItems: 'center', gap: 22 }}>
        <HeaderNavLink id="model" page={page} setPage={setPage}>The Model</HeaderNavLink>
        <HeaderNavLink id="story" page={page} setPage={setPage}>The Story</HeaderNavLink>
        <HeaderNavLink id="playground" page={page} setPage={setPage}>Playground</HeaderNavLink>
        <HeaderNavLink id="methods" page={page} setPage={setPage}>Methods</HeaderNavLink>
        <HeaderNavLink id="about" page={page} setPage={setPage}>About</HeaderNavLink>
      </nav>
    </div>);

}

// ── Tier 2 — Playground mode bar (Interventions / Sandbox). Constant height. ──
// Lives ONLY on the Playground page: the two ways to drive the model — the
// measured levers vs. free tinkering ("not a finding").
function ModeBar({ mode, setMode }) {
  return (
    <div style={{ height: 50, flexShrink: 0, display: 'flex', alignItems: 'center', gap: 14, padding: '0 clamp(24px, 4vw, 56px)', background: CC.bg, position: 'relative', zIndex: 20 }}>
      <Segmented value={mode} onChange={setMode} options={[['interventions', 'Interventions'], ['sandbox', 'Sandbox']]} />
    </div>);

}

// ── status chip floating over the field (one component, F2) ─────────────────
function FieldChip({ tone, children }) {
  const dot = tone === 'ended' ? '#3f7d54' : tone === 'paused' ? CC.ink3 : '#3f7d54';
  return (
    <div style={{ position: 'absolute', left: 24, top: 20, display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: DS.type.micro, color: CC.ink3, background: 'rgba(249,248,244,.72)', padding: '5px 12px', borderRadius: DS.rad.pill, border: `1px solid ${CC.border}` }}>
      <span style={{ width: 7, height: 7, borderRadius: DS.rad.pill, background: dot }} /> {children}
    </div>);

}

// (The arrival interstitials are gone: the landing hero's job moved to Act 0 —
// the dots intro in rc-intro.jsx — and the pre-Interventions overlay was cut
// because its premise broke on the intro→Playground path; the picker's empty
// state and the story-end card do its framing now.)

// ── chapter data as a minimalist sparkline (C6) ─────────────────────────────
function BeatMetric({ data, tick }) {
  const ref = React.useRef(null);
  const [w, setW] = React.useState(360);
  React.useEffect(() => {
    const el = ref.current;if (!el) return;
    const u = () => setW(Math.max(220, el.clientWidth));
    u();const ro = new ResizeObserver(u);ro.observe(el);return () => ro.disconnect();
  }, []);
  const H = 60,top = 10,bot = 18,padL = 3,padR = 3;
  const samples = React.useMemo(() => {
    const a = [];const N = 90;
    for (let i = 0; i <= N; i++) {const t = i / N * LAST;a.push([t, data.valueAt(t)]);}
    return a;
  }, [data]);
  const vals = samples.map((s) => s[1]);
  let lo = Math.min(...vals),hi = Math.max(...vals);const pad = (hi - lo) * 0.14 || 1;lo -= pad;hi += pad;
  const plotW = w - padL - padR,plotH = H - top - bot;
  const X = (t) => padL + t / LAST * plotW;
  const Y = (v) => top + plotH - (v - lo) / (hi - lo) * plotH;
  const full = samples.map((s, i) => `${i ? 'L' : 'M'}${X(s[0]).toFixed(1)},${Y(s[1]).toFixed(1)}`).join(' ');
  const cv = data.valueAt(tick);
  const past = samples.filter((s) => s[0] <= tick + 1e-6);
  const pastPath = [...past.map((s, i) => `${i ? 'L' : 'M'}${X(s[0]).toFixed(1)},${Y(s[1]).toFixed(1)}`), `L${X(tick).toFixed(1)},${Y(cv).toFixed(1)}`].join(' ');
  const cx = X(tick),cy = Y(cv);
  const ac = data.color === 'd' ? CC.d : CC.ink;
  return (
    <div style={{ marginTop: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <Eyebrow style={{ color: CC.ink4 }}>{data.label} · {Math.floor(tickToYear(tick))}</Eyebrow>
        <span style={{ display: 'inline-flex', alignItems: 'baseline', gap: 8 }}>
          <MonoVal size={DS.type.subhead} color={ac}>{data.fmt(cv)}</MonoVal>
          {data.note && <Caption>{data.note}</Caption>}
        </span>
      </div>
      <div ref={ref} style={{ marginTop: 9 }}>
        <svg viewBox={`0 0 ${w} ${H}`} width="100%" height={H} preserveAspectRatio="xMidYMid meet" style={{ display: 'block' }}>
          <path d={full} fill="none" stroke={CC.borderS} strokeWidth="1.1" strokeDasharray="2 3" opacity="0.8" />
          <path d={pastPath} fill="none" stroke={ac} strokeWidth="1.9" strokeLinejoin="round" strokeLinecap="round" />
          <circle cx={cx} cy={cy} r="3.6" fill={CC.bg} stroke={ac} strokeWidth="2" />
        </svg>
      </div>
    </div>);

}

// ── orientation legend — only on the first Watch chapter ────────────────────
function MapLegend() {
  const Item = ({ glyph, label }) =>
  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <span style={{ width: 18, flexShrink: 0, display: 'inline-flex' }}>{glyph}</span>
      <span style={{ fontSize: DS.type.small, color: CC.ink2, lineHeight: 1.4 }}>{label}</span>
    </div>;

  const Ring = ({ c }) => <span style={{ width: 12, height: 12, borderRadius: 999, border: `2.4px solid ${c}`, display: 'inline-block' }} />;
  const Diamond = ({ c }) => <span style={{ width: 9, height: 9, background: c, display: 'inline-block', transform: 'rotate(45deg)', border: '1.5px solid #fff', boxShadow: `0 0 0 1px ${c}` }} />;
  const Sq = ({ c }) => <span style={{ width: 8, height: 8, background: '#fff', border: `1.6px solid ${c}`, display: 'inline-block' }} />;
  return (
    <div style={{ marginTop: 22, paddingTop: 14, borderTop: `1px solid ${CC.border}` }}>
      <Eyebrow style={{ color: CC.ink4 }}>Reading the map</Eyebrow>
      <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
        <Item glyph={<Ring c={CC.r} />} label={<><strong style={{ color: CC.ink }}>Party centres</strong> — the live heart of each camp, moving with the simulation.</>} />
        <Item glyph={<Diamond c={CC.r} />} label={<><strong style={{ color: CC.ink }}>Emergent factions</strong> — Tea Party, MAGA, Bernie, DSA — each appears the year it forms.</>} />
        <Item glyph={<Sq c={CC.ink2} />} label={<><strong style={{ color: CC.ink }}>News outlets</strong> — at the calibrated positions that actually pull people.</>} />
      </div>
      <p style={{ margin: '12px 0 0', paddingTop: 11, borderTop: `1px solid ${CC.border}`, fontSize: DS.type.micro, lineHeight: 1.5, color: CC.ink3 }}>
        Every marker is the model’s own data, not an illustrative placement. Navy is Democratic, oxblood Republican.
      </p>
    </div>);

}

// ── staged orientation — the first Watch chapter builds the map one layer at a
// time so the reader learns the vocabulary before the story moves. Each step
// adds the next element to the canvas (see Field `reveal`). ────────────────
// Axes + direction labels are taught by Act 0 (the dots intro) now, so the
// staged build starts where the morph lands: on the clouds. The base layers
// ('axes', 'labels') are always revealed during orientation — only these
// three stack step by step.
const ORIENT_LAYERS = ['blobs', 'rings', 'entities'];
const ORIENT_BASE = ['axes', 'labels'];
const ORIENT_STEPS = [
  {
    title: 'Where people cluster',
    lead: 'The dots you just met, read as a crowd.',
    body: 'Each soft cloud is many Americans; the denser the colour, the more people sit there. Navy leans Democratic, oxblood Republican; where the two overlap the field turns grey — the middle.',
  },
  {
    title: 'The centre of each camp',
    lead: 'The two markers track the heart of each party.',
    body: 'Each sits at the average position of all its members. The dashed line between them is the gap — keep an eye on it as the years run.',
  },
  {
    title: 'Landmarks from the model',
    lead: 'A few markers the simulation places itself.',
    body: 'Hollow squares are news outlets at their measured positions; small diamonds are factions that emerge mid-story — Tea Party, MAGA — each appearing only in the year it forms. Every marker is the model’s own, not hand-placed.',
  },
];

function OrientRail({ step, onPrev, onNext, onContinue }) {
  const LX = 'clamp(64px, 14vw, 248px)';
  const total = ORIENT_STEPS.length;
  const s = ORIENT_STEPS[step];
  const last = step === total - 1;
  return (
    <div style={{ background: 'transparent', display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, justifyContent: 'safe center', overflow: 'auto' }}>
      <div style={{ flexShrink: 0, padding: `clamp(28px,4.5vh,52px) 44px 8px ${LX}` }}>
        <Eyebrow>What you’re looking at · 1980</Eyebrow>
        <h2 style={{ margin: '14px 0 18px', fontFamily: SERIF, fontWeight: 600, fontSize: 40, lineHeight: 1.04, letterSpacing: '-.02em', maxWidth: 440 }}>{s.title}</h2>
        <p style={{ margin: 0, fontFamily: SERIF, fontStyle: 'italic', fontSize: DS.type.subhead, lineHeight: 1.42, color: CC.ink, maxWidth: 440 }}>{s.lead}</p>
        <p style={{ margin: '16px 0 0', ...PROSE, color: CC.ink2, maxWidth: 460 }}>{s.body}</p>
        {/* progress — one tick per element being introduced */}
        <div style={{ marginTop: 26, display: 'flex', alignItems: 'center', gap: 9 }}>
          {ORIENT_STEPS.map((_, i) => (
            <span key={i} style={{ height: 3, flex: i === step ? '0 0 26px' : '0 0 14px', borderRadius: 2, background: i <= step ? CC.ink : CC.border, transition: 'background .2s, flex-basis .2s' }} />
          ))}
          <span style={{ marginLeft: 4, fontFamily: MONO, fontSize: DS.type.micro, color: CC.ink4, ...TNUM }}>{step + 1}/{total}</span>
        </div>
      </div>
      <div style={{ flexShrink: 0, padding: `14px 44px clamp(24px,4vh,40px) ${LX}`, display: 'flex', gap: 10 }}>
        <button onClick={onPrev} disabled={step === 0} style={{
          padding: '12px 16px', borderRadius: DS.rad.pill, border: `1px solid ${CC.border}`, background: CC.surface,
          color: step === 0 ? CC.ink4 : CC.ink2, cursor: step === 0 ? 'default' : 'pointer', fontFamily: SANS, fontSize: DS.type.small
        }}>← Back</button>
        <button onClick={last ? onContinue : onNext} style={{ ...primaryBtn, width: 'auto', padding: '13px 26px' }}>{last ? 'Start the story →' : 'Next →'}</button>
      </div>
    </div>);

}

// ── Watch rail — sticky action footer (D2); transport now lives in the bar ──
function WatchRail({ phase, beat, beatI, total, nextBeat, tick, onBack, onContinue, onExplore, onInterventions, onSandbox, on3D }) {
  const LX = 'clamp(64px, 14vw, 248px)';
  const pad = `clamp(28px,4.5vh,52px) 44px 8px ${LX}`;
  const scrollWrap = { flexShrink: 0, padding: pad };
  const footer = { flexShrink: 0, padding: `14px 44px clamp(24px,4vh,40px) ${LX}`, background: 'transparent' };

  if (phase === 'intro') {
    return (
      <div style={{ background: 'transparent', display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, justifyContent: 'safe center', overflow: 'auto' }}>
        <div style={scrollWrap}>
          <Eyebrow>An interactive history · 1980–2025</Eyebrow>
          <h2 style={{ margin: '14px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: DS.type.display, lineHeight: 0.98, letterSpacing: '-.025em' }}>Calm to Camps</h2>
          <p style={{ margin: '16px 0 0', fontFamily: SERIF, fontStyle: 'italic', fontSize: DS.type.subhead, lineHeight: 1.4, color: CC.ink2 }}>How a country that mostly agreed to disagree sorted itself into two camps that can barely speak.</p>
          <p style={{ margin: '18px 0 0', ...PROSE, color: CC.ink2 }}>Watch forty-five years of Americans drift across the political compass. We’ll pause at the moments that moved the country — and say, plainly, what each one did.</p>
        </div>
        <div style={footer}>
          <button onClick={onContinue} style={primaryBtn}>▶ &nbsp;Start the story</button>
        </div>
      </div>);

  }
  if (phase === 'playing') {
    return (
      <div style={{ background: 'transparent', display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, justifyContent: 'safe center', overflow: 'auto' }}>
        <div style={scrollWrap}>
          <Eyebrow style={{ color: CC.ink3 }}>The story · playing</Eyebrow>
          <h2 style={{ margin: '12px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: DS.type.title, letterSpacing: '-.015em' }}>{Math.floor(tickToYear(tick))}</h2>
          <p style={{ margin: '14px 0 0', ...PROSE, color: CC.ink2 }}>The country is sorting itself in real time. We’ll stop at the next moment that matters.</p>
          {nextBeat &&
          <div style={{ marginTop: 22, paddingTop: 14, borderTop: `1px solid ${CC.border}` }}>
              <Eyebrow style={{ color: CC.ink4 }}>Next stop · {Math.floor(tickToYear(nextBeat.tick))}</Eyebrow>
              <div style={{ fontFamily: SERIF, fontWeight: 600, fontSize: DS.type.subhead, marginTop: 5, letterSpacing: '-.01em' }}>{nextBeat.title}</div>
            </div>
          }
        </div>
        <div style={footer}><Caption>Use the timeline below to pause, scrub, or change speed.</Caption></div>
      </div>);

  }
  if (phase === 'ended') {
    const quiet = {
      background: 'none', border: 'none', cursor: 'pointer', padding: 0,
      fontFamily: SANS, fontSize: DS.type.micro, color: CC.ink3, textDecoration: 'underline', textUnderlineOffset: 3,
    };
    return (
      <div style={{ background: 'transparent', display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, justifyContent: 'safe center', overflow: 'auto' }}>
        <div style={scrollWrap}>
          <Eyebrow>The story · 1980 → 2025</Eyebrow>
          <h2 style={{ margin: '12px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: DS.type.title, lineHeight: 1.05, letterSpacing: '-.015em' }}>Now drive it yourself.</h2>
          <p style={{ margin: '18px 0 0', ...PROSE, color: CC.ink2 }}>Forty-five years, two hardening camps, a middle that thinned — and an out-party warmth that fell from the high-50s to the high-20s.</p>
          <p style={{ margin: '14px 0 0', ...PROSE, color: CC.ink2 }}>You’ve watched the model reproduce the real arc. Two ways to take the wheel: try the things researchers have actually tested, or turn the dials freely.</p>
        </div>
        <div style={{ ...footer, display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'flex-start' }}>
          <div style={{ display: 'flex', gap: 10, width: '100%' }}>
            <button onClick={onInterventions} style={{ ...primaryBtn, flex: 1, width: 'auto' }}>Try the interventions &nbsp;→</button>
            <button onClick={onSandbox} style={{
              padding: '13px 22px', borderRadius: DS.rad.pill, border: `1px solid ${CC.border}`, background: CC.surface,
              color: CC.ink2, cursor: 'pointer', fontFamily: SANS, fontSize: DS.type.body
            }}>Open the sandbox</button>
          </div>
          <div style={{ display: 'flex', gap: 18 }}>
            <button onClick={onExplore} style={quiet}>keep scrubbing this map →</button>
            <button onClick={on3D} style={quiet}>see it in three dimensions →</button>
          </div>
        </div>
      </div>);

  }
  // beat
  return (
    <div style={{ background: 'transparent', display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, justifyContent: 'safe center', overflow: 'auto' }}>
      <div key={beatI} style={{ ...scrollWrap, animation: 'ccFadeUp .42s ease' }}>
        <Eyebrow>Chapter {beatI + 1} of {total} · {Math.floor(tickToYear(beat.tick))}</Eyebrow>
        <h2 style={{ margin: '14px 0 24px', fontFamily: SERIF, fontWeight: 600, fontSize: 50, lineHeight: 1.02, letterSpacing: '-.022em' }}>{beat.title}</h2>
        <p style={{ margin: 0, fontFamily: SERIF, fontStyle: 'italic', fontSize: DS.type.subhead, lineHeight: 1.42, color: CC.ink }}>{beat.lead}</p>
        <p style={{ margin: '16px 0 0', ...PROSE, color: CC.ink2, maxWidth: 460 }}>{beat.body}</p>
        {beat.orient ?
        <MapLegend /> :
        beat.data ?
        <BeatMetric data={beat.data} tick={beat.tick} /> :

        <div style={{ marginTop: 22, paddingTop: 13, borderTop: `1px solid ${CC.border}`, display: 'flex', alignItems: 'center', gap: 11 }}>
              <Eyebrow style={{ color: CC.ink4, letterSpacing: '.1em' }}>data</Eyebrow>
              <MonoVal size={DS.type.small} color={CC.ink}>{beat.metric(beat.tick)}</MonoVal>
            </div>
        }
      </div>
      <div style={{ ...footer, display: 'flex', gap: 10 }}>
        <button onClick={onBack} disabled={beatI === 0} style={{
          padding: '12px 16px', borderRadius: DS.rad.pill, border: `1px solid ${CC.border}`, background: CC.surface,
          color: beatI === 0 ? CC.ink4 : CC.ink2, cursor: beatI === 0 ? 'default' : 'pointer', fontFamily: SANS, fontSize: DS.type.small
        }}>← Back</button>
        <button onClick={onContinue} style={{ ...primaryBtn, width: 'auto', padding: '13px 26px' }}>{beatI === total - 1 ? 'Jump to the end →' : 'Jump to next →'}</button>
      </div>
    </div>);

}
const primaryBtn = {
  display: 'inline-flex', alignItems: 'center', justifyContent: 'center', padding: '13px 22px', background: CC.ink, color: '#fff',
  fontSize: DS.type.body, fontWeight: 500, borderRadius: DS.rad.pill, cursor: 'pointer', border: 'none', fontFamily: SANS, width: '100%'
};

// ── live annotations that surface over the field as Explore plays ───────────
// Each fires near its tick and fades out between moments, so the map narrates
// itself without clutter. Pairs a real-world event with what's visible.
const EXPLORE_NOTES = [
{ tick: 0, year: 1980, event: 'One country, one cluster.', viz: 'Almost everyone piles into a single warm blob near the center — no camps yet.' },
{ tick: 21, year: 1987, event: 'The Fairness Doctrine is repealed.', viz: 'Broadcasters can take a side. The blob starts to stretch.' },
{ tick: 42, year: 1994, event: 'Gingrich: the parties pull apart at the top.', viz: 'Elites lead — the heart of each camp begins to slide off-center, the right faster.' },
{ tick: 48, year: 1996, event: 'Fox News launches.', viz: 'A second lobe pulls toward the traditional-right corner.' },
{ tick: 60, year: 2000, event: 'Identities start to stack.', viz: 'Party, faith and region align into one identity; the camps cool as they sort.' },
{ tick: 84, year: 2008, event: 'Social media reaches everyone; Obama elected.', viz: 'Often blamed, rarely convicted — the split was already underway, and rose fastest among the least-online.' },
{ tick: 90, year: 2010, event: 'The base hardens; Citizens United lands.', viz: 'Primary challenges pull the right outward. Citizens United is an era marker here, not the cause.' },
{ tick: 105, year: 2015, event: 'MAGA emerges.', viz: 'A dense knot forms in the populist-right corner.' },
{ tick: 108, year: 2016, event: 'Trump wins — a status-threat shock.', viz: 'The camps harden into opposite corners; the contested middle keeps thinning.' },
{ tick: 120, year: 2020, event: 'COVID and January 6th.', viz: 'Two separate masses, with almost nothing left between them.' }];

// Live "on the map" block — folded out of the old floating card and into the
// Explore rail. Reads the nearest annotation to the current tick and updates as
// the reader scrubs, so the commentary stays in sync without cluttering the map.
function ExploreNow({ tick }) {
  let near = null, best = 1e9;
  for (const n of EXPLORE_NOTES) { const d = Math.abs(tick - n.tick); if (d < best) { best = d; near = n; } }
  if (!near) return null;
  return (
    <div style={{ paddingTop: 14, borderTop: `1px solid ${CC.border}` }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ width: 6, height: 6, borderRadius: 999, background: CC.r }} />
        <Eyebrow style={{ color: CC.ink3 }}>{near.year} · on the map</Eyebrow>
      </div>
      <p style={{ margin: '8px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: 16, lineHeight: 1.3, letterSpacing: '-.01em', color: CC.ink }}>{near.event}</p>
      <p style={{ margin: '7px 0 0', fontSize: DS.type.small, lineHeight: 1.5, color: CC.ink2 }}>{near.viz}</p>
    </div>);

}

// ── Explore rail — scrolls cleanly (D2) ─────────────────────────────────────
// Calibration anchor — pins an abstract metric to something a person can feel.
// Tied to the live out-party-warmth reading so it escalates as the camps cool.
// (Illustrative figures in the spirit of the cross-party-marriage finding —
// discomfort with a child marrying across the aisle rose from ~5% to ~40%+.)
function CalibrationAnchor({ tick }) {
  const warmth = warmthDegAt(tick);
  let line;
  if (warmth >= 42) line = <>Back here, only about <strong>1 in 20</strong> Americans said they'd be unhappy if their child married someone from the other party.</>;else
  if (warmth >= 30) line = <>By now, roughly <strong>a third</strong> say a cross-party marriage in the family would bother them.</>;else
  line = <>At this level, close to <strong>half</strong> of Americans say they'd be uncomfortable if their child married someone from the other party.</>;
  return (
    <div style={{ paddingTop: 14, borderTop: `1px solid ${CC.border}` }}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 10 }}>
        <Eyebrow style={{ color: CC.ink4 }}>What that feels like · {Math.floor(tickToYear(tick))}</Eyebrow>
        <MonoVal size={DS.type.small} color={CC.ink}>{warmth}° warmth</MonoVal>
      </div>
      <p style={{ margin: '9px 0 0', fontSize: DS.type.small, lineHeight: 1.55, color: CC.ink2 }}>{line}</p>
    </div>);

}

function ExploreRail({ tick, onBackToStory }) {
  return (
    <div style={{ background: 'transparent', display: 'flex', flexDirection: 'column', minHeight: 0, height: '100%', justifyContent: 'safe center', overflow: 'auto' }}>
      <div style={{ flexShrink: 0, padding: `clamp(28px,4.5vh,52px) 44px clamp(28px,4.5vh,52px) clamp(64px,14vw,248px)`, display: 'flex', flexDirection: 'column', gap: 22 }}>
        <div>
          {onBackToStory &&
          <div style={{ marginBottom: 18 }}>
            <button onClick={onBackToStory} style={{
              display: 'inline-flex', alignItems: 'center', gap: 8, cursor: 'pointer',
              fontFamily: SANS, fontSize: 11, fontWeight: 600, letterSpacing: '.12em', textTransform: 'uppercase',
              color: CC.ink3, background: 'none', border: 'none', padding: 0,
            }}>← Back to the chapters</button>
          </div>
          }
          <h3 style={{ margin: '12px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: 46, lineHeight: 1.02, letterSpacing: '-.022em' }}>
            Do they hate each other?
          </h3>
          <p style={{ margin: '18px 0 0', ...PROSE, color: CC.ink2, maxWidth: 460 }}>
            Issue positions barely moved — the feelings curdled. The map shows where people <em>stand</em>; this shows how they <em>feel</em>. Warmth toward your <em>own</em> side barely budged; toward the <em>other</em> it fell off a cliff. <strong>Distance and animus are different axes.</strong>
          </p>
        </div>
        <ExploreNow tick={tick} />
        <div><ProtoSparklines tick={tick} run={D.runs.baseline} rowH={56} gap={34} /></div>
        <CalibrationAnchor tick={tick} />
      </div>
    </div>);

}

// ── Unified timeline + transport (Watch & Explore share this — A3/B1) ───────
// Local transport: round play/restart pair + a clearly-grouped speed segment,
// sized so nothing collides with the divider (C9).
function BarTransport({ playing, toggle, setTick, speed, setSpeed }) {
  const round = { width: 32, height: 32, borderRadius: DS.rad.pill, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', flexShrink: 0, fontFamily: SANS };
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
      <button onClick={toggle} aria-label={playing ? 'Pause' : 'Play'} style={{ ...round, background: CC.ink, color: '#fff', border: 'none', fontSize: 11 }}>{playing ? '❚❚' : '▶'}</button>
      <button onClick={() => setTick(0)} aria-label="Restart" style={{ ...round, background: 'transparent', color: CC.ink2, border: `1px solid ${CC.borderS}`, fontSize: 13 }}>↺</button>
      <span style={{ width: 1, height: 20, background: CC.border, margin: '0 3px', flexShrink: 0 }} />
      <div style={{ display: 'inline-flex', gap: 2, padding: 3, background: 'transparent', borderRadius: DS.rad.pill, border: `1px solid ${CC.borderS}` }}>
        {[[0.5, '½×'], [1, '1×'], [2, '2×'], [4, '4×']].map(([v, l]) => {
          const on = speed === v;
          return (
            <button key={v} onClick={() => setSpeed(v)} style={{
              fontSize: 11, padding: '3px 7px', borderRadius: DS.rad.pill, fontFamily: MONO, cursor: 'pointer',
              border: `1px solid ${on ? CC.borderS : 'transparent'}`,
              color: on ? CC.ink : CC.ink3, fontWeight: on ? 600 : 400, background: 'transparent', ...TNUM
            }}>{l}</button>);

        })}
      </div>
    </div>);

}

function TimelineBar({ tick, setTick, playing, toggle, speed, setSpeed, mode, beatI, onPickBeat, ended }) {
  const year = Math.floor(tickToYear(tick));
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const monthLabel = `${months[Math.min(11, Math.floor((tickToYear(tick) - year) * 12))]} ${year}`;
  const accent = CC.ink;
  return (
    <div style={{ height: BARH, flexShrink: 0, background: CC.bg, position: 'relative', display: 'flex', alignItems: 'center', gap: 'clamp(20px, 3vw, 44px)', padding: '0 clamp(28px, 4vw, 56px)' }}>
      <div style={{ position: 'absolute', top: 0, left: 'clamp(28px, 4vw, 56px)', right: 'clamp(28px, 4vw, 56px)', height: 1, background: CC.border }} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, flexShrink: 0, width: 224 }}>
        <BarTransport playing={playing} toggle={toggle} setTick={setTick} speed={speed} setSpeed={setSpeed} />
        <MonoVal size={DS.type.micro} color={CC.ink}>{monthLabel}</MonoVal>
      </div>
      <div style={{ flex: 1, minWidth: 0, position: 'relative' }}>
        <div style={{ marginTop: 4, position: 'relative' }}>
          {/* chapter rail for Watch — labeled, click-to-jump diamonds; the active
              chapter carries its name as the "you are here" marker */}
          {mode === 'watch' && BEATS.map((b, k) => {
            const on = k === beatI && !ended;
            const left = `calc(14px + ${b.tick / LAST} * (100% - 28px))`;
            return (
              <React.Fragment key={k}>
                {on &&
                <span style={{ position: 'absolute', zIndex: 5, left, top: 54, transform: 'translateX(-50%)', whiteSpace: 'nowrap', fontFamily: SANS, fontSize: 10, fontWeight: 600, color: CC.ink, background: 'rgba(249,248,244,.9)', padding: '0 3px' }}>{b.short}</span>
                }
                <button title={b.title} onClick={() => onPickBeat(k)} style={{
                  position: 'absolute', zIndex: 4, left,
                  top: 38, transform: 'translate(-50%,-50%) rotate(45deg)',
                  width: on ? 13 : 10, height: on ? 13 : 10, background: b.tick <= tick ? CC.ink : CC.surface,
                  border: `2px solid ${b.tick <= tick ? CC.ink : CC.ink3}`, cursor: 'pointer', padding: 0, borderRadius: 2
                }} />
              </React.Fragment>);

          })}
          <ProtoTimeline tick={tick} setTick={setTick} color={accent} altLabels />
        </div>
      </div>
    </div>);

}

// hash ↔ page mapping (deep links; review amendment #8). '#model' is the
// canonical landing hash; unknown hashes fall back to the intro.
const HASH2PAGE = { '#model': 'model', '#story': 'story', '#playground': 'playground', '#methods': 'methods', '#about': 'about', '#3d': 'agents' };
const PAGE2HASH = { model: '#model', story: '#story', playground: '#playground', methods: '#methods', about: '#about', agents: '#3d' };

function Unified() {
  const ph = useTick({ start: 0, autoplay: false, base: 2.25 });
  const { tick, setTick, playing, setPlaying, toggle, speed, setSpeed } = ph;
  const [page, setPage] = React.useState(() => HASH2PAGE[(window.location.hash || '').toLowerCase()] || 'model');
  const layer = 'position';   // affect compass removed — position is the only field
  const [beatI, setBeatI] = React.useState(0);
  const [orientStep, setOrientStep] = React.useState(0);
  const [orientSeen, setOrientSeen] = React.useState(false);
  const [paused, setPaused] = React.useState(false);
  const [ended, setEnded] = React.useState(false);
  const [started, setStarted] = React.useState(false);
  const [showLandmarks, setShowLandmarks] = React.useState(false);
  const [settling, setSettling] = React.useState(false);   // intro morph → story crossfade
  const [settleIn, setSettleIn] = React.useState(false);   // flips on the next frame to fire the fade
  const [unlocked, setUnlocked] = React.useState(false);   // story finished → free explore on the SAME canvas
  const [hintSeen, setHintSeen] = React.useState(false);   // first-run "scroll or play" helper
  // ── Act 0 (the dots intro) — its own playhead, so the ambient loop never
  // fights the story's tick; the morph hands off between them. ──
  const [introTick, setIntroTick] = React.useState(0);
  const [introMorphT, setIntroMorphT] = React.useState(null); // null = idle dots · 0..1 = handoff
  const morphCancel = React.useRef(null);
  const [storyDone, setStoryDone] = React.useState(() => ccFlag(CC_STORY_DONE));
  const wheelActiveRef = React.useRef(false);              // gates wheel-scrubbing to the story canvas
  const snapActiveRef = React.useRef(false);               // gates snap-to-chapter to the guided story
  const tickRef = React.useRef(0);                         // latest tick for the snap reader
  const snapRaf = React.useRef(0);                         // in-flight snap animation frame
  const wheelIdle = React.useRef(0);                       // idle timer that triggers the snap
  const iv = useInterventions();

  const isIntro = page === 'model';
  const morphingIntro = introMorphT != null;
  useIntroLoop({ active: isIntro && !morphingIntro, setTick: setIntroTick });
  React.useEffect(() => () => { if (morphCancel.current) morphCancel.current(); }, []);

  // keep the address bar honest (replaceState — no history spam while browsing)
  React.useEffect(() => {
    const h = PAGE2HASH[page] || '#model';
    if (window.location.hash !== h) { try { history.replaceState(null, '', h); } catch (e) { window.location.hash = h; } }
  }, [page]);

  // Story end: reaching the last tick (by ▶ or by wheel) reveals the end card;
  // scrubbing back below it restores the story. Completing the story flips the
  // intro's CTA nudge for future visits (cc_story_done).
  React.useEffect(() => {
    if (page !== 'story' || unlocked || !started || !orientSeen) return;
    if (tick >= LAST - 1e-6) {if (!ended) {setEnded(true);setPlaying(false);setStoryDone(true);setCcFlag(CC_STORY_DONE);}}
    else if (ended) setEnded(false);
  }, [tick, page, unlocked, started, orientSeen, ended, setPlaying]);

  // dismiss the first-run hint as soon as the reader plays.
  React.useEffect(() => {if (playing) setHintSeen(true);}, [playing]);

  // wheel scrubbing — roll to move the needle through time, then ease onto the
  // nearest chapter when the wheel goes idle so it always lands on a beat. One
  // global, non-passive listener gated by `wheelActiveRef` (story canvas only).
  React.useEffect(() => {
    const TARGETS = [...BEATS.map((b) => b.tick), LAST]; // chapters + the end
    const cancelSnap = () => {if (snapRaf.current) cancelAnimationFrame(snapRaf.current);snapRaf.current = 0;};
    const snapToNearest = () => {
      if (!snapActiveRef.current) return;
      const from = tickRef.current;
      let target = TARGETS[0];
      for (const t of TARGETS) if (Math.abs(t - from) < Math.abs(target - from)) target = t;
      const dist = Math.abs(target - from);
      if (dist < 0.02 || dist > SNAP_RANGE) return;  // already there, or too far → stay put
      let t0 = null;const dur = 320;
      cancelSnap();
      const step = (ts) => {
        if (t0 == null) t0 = ts;
        const k = Math.min(1, (ts - t0) / dur);
        const e = 1 - Math.pow(1 - k, 3); // easeOutCubic
        setTick(from + (target - from) * e);
        snapRaf.current = k < 1 ? requestAnimationFrame(step) : 0;
      };
      snapRaf.current = requestAnimationFrame(step);
    };
    const onWheel = (e) => {
      if (!wheelActiveRef.current) return;
      e.preventDefault();
      cancelSnap();
      setHintSeen(true);setPlaying(false);
      setTick((t) => Math.max(0, Math.min(LAST, t + e.deltaY * WHEEL_SENS)));
      if (wheelIdle.current) clearTimeout(wheelIdle.current);
      wheelIdle.current = setTimeout(snapToNearest, SNAP_IDLE_MS);
    };
    window.addEventListener('wheel', onWheel, { passive: false });
    return () => {window.removeEventListener('wheel', onWheel);cancelSnap();if (wheelIdle.current) clearTimeout(wheelIdle.current);};
  }, [setTick, setPlaying]);

  // settle crossfade: hold the morph's final frame for one frame, then fade it
  // out (revealing the assembled story underneath) and tear it down when done.
  React.useEffect(() => {
    if (!settling) return;
    const raf = requestAnimationFrame(() => setSettleIn(true));
    const to = setTimeout(() => {setSettling(false);setSettleIn(false);}, 1050);
    return () => {cancelAnimationFrame(raf);clearTimeout(to);};
  }, [settling]);

  // entering the story drops the reader at orientation (the staged map-build),
  // paused at 1980 — they then scroll, or press ▶, to move through time.
  const enterOrientation = () => {
    setStarted(true);setOrientStep(0);setOrientSeen(false);setBeatI(0);
    setTick(0);setPaused(true);setPlaying(false);setEnded(false);setHintSeen(false);
  };
  // Back / Continue step discretely between chapters (for readers who'd rather
  // click than scroll); the wheel and ▶ remain the primary ways through.
  const stepBeat = (dir) => {
    setHintSeen(true);setPlaying(false);setEnded(false);
    const k = beatIndexAt(tick) + dir;
    if (dir > 0 && k >= BEATS.length) {setTick(LAST);return;}
    setTick(BEATS[Math.max(0, Math.min(BEATS.length - 1, k))].tick + 0.001);
  };
  const railContinue = () => {phase === 'intro' ? enterOrientation() : stepBeat(1);};
  const pickBeat = (k) => {setHintSeen(true);setPlaying(false);setEnded(false);setTick(BEATS[k].tick + 0.001);};
  // finishing the guided story hands the controls over ON THE SAME canvas
  // (no separate Explore tab) — free scrub on the position field, parties toggle.
  const goExplore = () => {setUnlocked(true);setEnded(false);setPaused(false);setPlaying(false);};
  const orientNext = () => setOrientStep((s) => Math.min(ORIENT_LAYERS.length - 1, s + 1));
  const orientPrev = () => setOrientStep((s) => Math.max(0, s - 1));
  const finishOrient = () => {setOrientSeen(true);setOrientStep(ORIENT_LAYERS.length - 1);setPaused(false);setPlaying(false);};

  // ── navigation. The Model and The Story are two labels over ONE mounted
  // canvas; a nav click is a jump-cut (no morph). The morph plays only on the
  // nudged path (the intro's "Watch the story"). ──
  const goPage = (p) => {
    if (morphingIntro) return;                 // ignore nav during the handoff
    if (p === 'story' && !started) {setCcFlag(CC_INTRO_SEEN);enterOrientation();}
    // clicking The Story while free-scrubbing relocks to the chaptered story
    // (the end-card effect re-derives `ended` from the current tick).
    if (p === 'story' && unlocked) {setUnlocked(false);setPlaying(false);}
    if (p !== 'story') setPlaying(false);
    setPage(p);
  };
  const goPlayground = (tab) => {
    if (morphingIntro) return;
    setPlaying(false);
    if (tab === 'sandbox') {iv.openSandbox();} else {iv.closeSandbox();}
    setPage('playground');
  };
  // the nudged path: ambient dots ease back to 1980 and dissolve into the
  // density clouds, then the staged orientation takes over (same canvas).
  const watchStory = () => {
    if (morphingIntro) return;
    setCcFlag(CC_INTRO_SEEN);
    morphCancel.current = animateIntroMorph({
      fromTick: introTick, setTick: setIntroTick, setMorphT: setIntroMorphT,
      onDone: () => {
        morphCancel.current = null;
        setSettling(true);setSettleIn(false);
        enterOrientation();
        setIntroMorphT(null);
        setPage('story');
      },
    });
  };

  const isWatch = page === 'story' && !unlocked;   // guided story
  const isExplore = page === 'story' && unlocked;  // unlocked free-explore (same canvas)
  // chapter derived from the tick once the story is running; orientation and the
  // intro keep using beat 0.
  const inStory = isWatch && started && orientSeen && !ended;
  const dispBeatI = inStory ? beatIndexAt(tick) : beatI;
  const beat = BEATS[dispBeatI];
  const phase = ended ? 'ended' : started ? 'beat' : 'intro';
  const stagedOrient = isWatch && started && beat && beat.orient && !orientSeen;
  const watchReveal = stagedOrient ? [...ORIENT_BASE, ...ORIENT_LAYERS.slice(0, orientStep + 1)] : null;
  const dimField = isWatch && ended && !stagedOrient ? 0.24 : 0;
  // wheel-scrub gates — computed BEFORE any early return, so leaving the story
  // for a static page can never strand a stale `true` in the refs (the old
  // hijacked-page-scroll leak). Only the running story / unlocked explore scrub.
  wheelActiveRef.current = (isWatch && started && orientSeen && !stagedOrient && !settling) || isExplore;
  snapActiveRef.current = isWatch && started && orientSeen && !ended;  // free-scrub in explore stays un-snapped
  tickRef.current = tick;
  const showHint = isWatch && started && orientSeen && !stagedOrient && !ended && !playing && !hintSeen && tick < 1.5;
  // morph → story crossfade: `settleFrom` holds the morph frame at full opacity
  // for a single frame; once `settleIn` flips, it fades out over 1s.
  const settleFrom = settling && !settleIn;

  // ── static pages (Methods / About / the demoted 3D view) ──
  if (page === 'methods' || page === 'about' || page === 'agents') {
    return (
      <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: CC.bg, minHeight: 0 }}
      onClick={(e) => {const g = e.target.closest('[data-goto]');if (g) {e.preventDefault();goPage(g.getAttribute('data-goto'));}}}>
        <SiteHeader page={page} setPage={goPage} />
        {page === 'about' ? <AboutPage /> : page === 'agents' ? <Agents3DPage /> : <MethodsPage />}
      </div>);

  }

  // ── Playground — Interventions | Sandbox (Tier-2), the model's two driving
  // modes. A separate page from the sim canvas; the workbench brings its own
  // playback surface. ──
  if (page === 'playground') {
    return (
      <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: CC.bg, minHeight: 0, position: 'relative' }}>
        <SiteHeader page={page} setPage={goPage} />
        <ModeBar mode={iv.isSandbox ? 'sandbox' : 'interventions'} setMode={(m) => {m === 'sandbox' ? iv.openSandbox() : iv.back();}} />
        <IvWorkbench iv={iv} layer={layer} />
      </div>);

  }

  // ── the simulation surface — one canvas, two labels (model = Act 0 intro,
  // story = the guided chapters / unlocked explore) ──
  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: CC.bg, minHeight: 0, position: 'relative' }}>
      <SiteHeader page={page} setPage={goPage} />

      {
      <div style={{ flex: 1, minHeight: 0, position: 'relative', overflow: 'hidden', background: CC.bg }}>
          {/* the compass — a fully contained square anchored right (no bleed; all axes & labels visible) */}
          <div style={{ position: 'absolute', top: '-2%', bottom: '-2%', right: '2%', aspectRatio: '1' }}>
            {isIntro ?
            <Field run={D.runs.baseline} tick={introTick} layer="position" view="dots" morphT={introMorphT} showGap={false} landmarks={false} /> :
            <Field run={D.runs.baseline} tick={tick} layer="position" view="density" showGap dim={dimField} reveal={watchReveal} landmarks={isExplore && showLandmarks ? 'all' : 'fixed'} />}
          </div>

          {/* paper scrim — keeps the floating prose legible, feathers out before the map */}
          <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, width: '56%', background: `linear-gradient(90deg, ${CC.bg} 0%, ${CC.bg} 88%, rgba(249,248,244,0) 100%)`, pointerEvents: 'none', zIndex: 1 }} />

          {/* chips + annotations, anchored to the visible map region */}
          <div style={{ position: 'absolute', top: 0, bottom: 0, left: '50%', right: 0, pointerEvents: 'none', zIndex: 2 }}>
            {isExplore &&
          <button onClick={() => setShowLandmarks((v) => !v)} style={{
            position: 'absolute', right: 24, top: 20, pointerEvents: 'auto', display: 'inline-flex', alignItems: 'center', gap: 8,
            fontFamily: SANS, fontSize: DS.type.micro, fontWeight: 500, cursor: 'pointer',
            color: showLandmarks ? CC.ink : CC.ink3, background: showLandmarks ? 'transparent' : 'rgba(249,248,244,.72)',
            padding: '6px 12px', borderRadius: DS.rad.pill, border: `1px solid ${showLandmarks ? CC.ink : CC.border}`
          }}>
                <span style={{ width: 7, height: 7, borderRadius: 2, background: showLandmarks ? CC.ink : 'transparent', border: `1.5px solid ${showLandmarks ? CC.ink : CC.ink4}` }} />
                {showLandmarks ? 'Parties on' : 'Show parties'}
              </button>
          }
          </div>

          {/* floating narrative — a centered editorial block on the left */}
          <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, width: 'min(54%, 820px)', display: 'flex', flexDirection: 'column', minHeight: 0, zIndex: 3 }}>
            {isIntro &&
              <IntroRail tick={introTick} storyDone={storyDone} onWatch={watchStory}
                onSandbox={() => goPlayground('sandbox')} onAbout={() => goPage('about')} on3D={() => goPage('agents')} />}
            {isWatch && (stagedOrient ?
              <OrientRail step={orientStep} onPrev={orientPrev} onNext={orientNext} onContinue={finishOrient} /> :
              <WatchRail phase={phase} beat={beat} beatI={dispBeatI} total={BEATS.length} nextBeat={BEATS.find((b) => b.tick > tick) || null} tick={tick} onBack={() => stepBeat(-1)} onContinue={railContinue} onExplore={goExplore}
                onInterventions={() => goPlayground('interventions')} onSandbox={() => goPlayground('sandbox')} on3D={() => goPage('agents')} />)}
            {isExplore && <ExploreRail tick={tick} onBackToStory={() => {setUnlocked(false);setPlaying(false);}} />}
          </div>

          {/* settle crossfade — the intro morph's final frame (1980, density)
              held on top of THIS container (matching geometry), fading out
              over 1s while the staged orientation assembles underneath. */}
          {settling &&
          <div style={{ position: 'absolute', inset: 0, zIndex: 6, pointerEvents: 'none', background: CC.bg, overflow: 'hidden',
            opacity: settleFrom ? 1 : 0, transition: 'opacity 1s ease' }}>
              <div style={{ position: 'absolute', top: '-2%', bottom: '-2%', right: '2%', aspectRatio: '1' }}>
                <Field run={D.runs.baseline} tick={0} layer="position" view="density" showGap={false} />
              </div>
            </div>
          }
        </div>
      }

      {/* bottom bar — the story's transport + chapter rail. The intro drives
          itself (ambient loop, year readout in the rail), so no bar there. */}
      {isIntro ? null :

      <TimelineBar tick={tick} setTick={setTick} playing={playing} toggle={toggle} speed={speed} setSpeed={setSpeed}
      mode={isWatch ? 'watch' : 'explore'} beatI={dispBeatI} onPickBeat={pickBeat} ended={ended} />
      }

      {/* first-run helper — black, gently bobbing, dismissed on the first scroll
          or play. Tells the reader the two ways through the story. */}
      {showHint &&
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: BARH + 20, zIndex: 8, display: 'flex', justifyContent: 'center', pointerEvents: 'none' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 7, animation: 'ccFadeUp .55s ease both' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '10px 18px', background: CC.ink, color: '#fff', borderRadius: DS.rad.pill, boxShadow: '0 8px 26px rgba(26,29,35,.22)', fontFamily: SANS, fontSize: 14, fontWeight: 500, letterSpacing: '-.005em' }}>
              <span style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', lineHeight: 0.62, animation: 'ccHintBob 1.5s ease-in-out infinite' }}>
                <span style={{ fontSize: 10 }}>⌃</span><span style={{ fontSize: 10 }}>⌄</span>
              </span>
              Scroll to move through time
            </div>
            <span style={{ fontSize: 13, color: CC.ink3, fontFamily: SANS }}>or press <span style={{ color: CC.ink2, fontWeight: 600 }}>▶</span> to play it for you</span>
          </div>
        </div>
      }

    </div>);

}

ReactDOM.createRoot(document.getElementById('root')).render(<Unified />);
