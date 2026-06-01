// Calm to Camps — unified shell (post-QA rebuild).
// ONE page, three postures, two static pages. The frame never moves:
//   • Tier-1 site header (brand + Model / Methods / About)            — constant
//   • Tier-2 mode bar (Watch / Explore / Interventions + Pos/Affect)  — constant across postures
//   • body: [tray (slides in for Interventions)] · field · right rail(452)
//   • bottom bar (fixed height): unified timeline+transport, or hope-bar
// Watch and Explore share the SAME draggable timeline + transport. Interventions
// keeps its tweaks on the LEFT and a tab-appropriate narrative rail on the RIGHT.

const RAILW = 452;
const TRAYW = 344;
const BARH = 138;
const BEATS = window.STORY_BEATS;

// ── Tier 1 — site header (E1/E2). Pages, not pills. ────────────────────────
function SiteHeader({ page, setPage }) {
  const NavLink = ({ id, children }) => {
    const on = page === id;
    return (
      <button onClick={() => setPage(id)} style={{
        fontFamily: SANS, fontSize: DS.type.small, fontWeight: on ? 600 : 500, color: on ? CC.ink : CC.ink3,
        background: 'none', border: 'none', cursor: 'pointer', padding: '6px 2px', position: 'relative'
      }}>
        {children}
        <span style={{ position: 'absolute', left: 0, right: 0, bottom: -1, height: 2, borderRadius: 2, background: on ? CC.ink : 'transparent' }} />
      </button>);

  };
  return (
    <div style={{ height: 58, flexShrink: 0, display: 'flex', alignItems: 'center', gap: 14, padding: '0 clamp(24px, 4vw, 56px)', borderBottom: `1px solid ${CC.border}`, background: CC.chrome, position: 'relative', zIndex: 30 }}>
      <button onClick={() => setPage('model')} style={{ display: 'flex', alignItems: 'center', gap: 12, background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
        <Logo />
        <span style={{ width: 1, height: 18, background: CC.border }} />
        <span style={{ fontFamily: SERIF, fontStyle: 'italic', fontSize: 16, color: CC.ink2, whiteSpace: 'nowrap' }}>Calm to Camps</span>
      </button>
      <span style={{ flex: 1 }} />
      <nav style={{ display: 'flex', alignItems: 'center', gap: 22 }}>
        <NavLink id="model">Model</NavLink>
        <NavLink id="methods">Methods</NavLink>
        <NavLink id="about">About</NavLink>
      </nav>
    </div>);

}

// ── Tier 2 — mode bar (posture switch + Pos/Affect). Constant height. ───────
function ModeBar({ mode, setMode, layer, setLayer }) {
  return (
    <div style={{ height: 50, flexShrink: 0, display: 'flex', alignItems: 'center', gap: 14, padding: '0 clamp(24px, 4vw, 56px)', background: CC.bg, position: 'relative', zIndex: 20 }}>
      <div style={{ position: 'absolute', bottom: 0, left: 'clamp(24px, 4vw, 56px)', right: 'clamp(24px, 4vw, 56px)', height: 1, background: CC.border }} />
      <Segmented value={mode} onChange={setMode} options={[['watch', 'Story'], ['interventions', 'Interventions']]} />
      <span style={{ flex: 1 }} />
      <Segmented value={layer} onChange={setLayer} options={[['position', 'Position'], ['affect', 'Affect · animus']]} accent={layer === 'affect' ? CC.ink : CC.ink} />
    </div>);

}

// ── status chip floating over the field (one component, F2) ─────────────────
function FieldChip({ tone, children }) {
  const dot = tone === 'ended' ? '#3f7d54' : tone === 'paused' ? CC.ink3 : '#3f7d54';
  return (
    <div style={{ position: 'absolute', left: 24, top: 20, display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: DS.type.micro, color: CC.ink3, background: 'rgba(255,255,255,.85)', padding: '5px 12px', borderRadius: DS.rad.pill, border: `1px solid ${CC.border}` }}>
      <span style={{ width: 7, height: 7, borderRadius: DS.rad.pill, background: dot }} /> {children}
    </div>);

}

// ── full-bleed arrival overlays — a landing hero, and a beat before Interventions ─
function HeroOverlay({ variant, onDismiss }) {
  const isLanding = variant === 'landing';
  return (
    <div style={{ position: 'absolute', inset: 0, zIndex: 50, overflow: 'hidden', background: CC.bg }}>
      <div style={{ position: 'absolute', inset: 0, opacity: 0.55 }}>
        <Field run={D.runs.baseline} tick={LAST} layer="position" view="density" showGap={false} />
      </div>
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 80% 70% at 50% 46%, rgba(243,243,240,.62) 0%, rgba(243,243,240,.9) 70%, rgba(243,243,240,.97) 100%)' }} />
      <div style={{ position: 'relative', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0 32px' }}>
        <div style={{ maxWidth: isLanding ? 880 : 720, textAlign: 'center' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 11, marginBottom: 26 }}>
            <Logo size={15} />
            <span style={{ width: 1, height: 16, background: CC.borderS }} />
            <span style={{ fontFamily: SERIF, fontStyle: 'italic', fontSize: 16, color: CC.ink2 }}>Calm to Camps</span>
          </div>
          {isLanding ?
          <React.Fragment>
              <h1 style={{ margin: 0, fontFamily: SERIF, fontWeight: 600, fontSize: 'clamp(34px, 5vw, 56px)', lineHeight: 1.04, letterSpacing: '-.02em', color: CC.ink }}>
                In 1980, Americans disagreed about politics.<br />By 2025, they had stopped talking.
              </h1>
              <p style={{ margin: '22px auto 0', fontFamily: SERIF, fontStyle: 'italic', fontSize: 'clamp(16px, 2vw, 21px)', lineHeight: 1.45, color: CC.ink2, maxWidth: 620 }}>
                A simulation of how a country sorted itself into two camps that can barely speak — and what, if anything, could have pulled it back together.
              </p>
              <button onClick={onDismiss} style={{ ...primaryBtn, width: 'auto', marginTop: 34, padding: '15px 30px', fontSize: 16 }}>▶ &nbsp;Watch the journey</button>
              <p style={{ margin: '20px 0 0', fontSize: DS.type.micro, color: CC.ink4 }}>45 years · 250 simulated Americans · one political compass</p>
            </React.Fragment> :

          <React.Fragment>
              <div style={{ marginBottom: 16 }}><Eyebrow style={{ color: CC.ink3 }}>Now the experiment</Eyebrow></div>
              <h1 style={{ margin: 0, fontFamily: SERIF, fontWeight: 600, fontSize: 'clamp(32px, 4.4vw, 50px)', lineHeight: 1.05, letterSpacing: '-.02em', color: CC.ink }}>
                Could anything have stopped it?
              </h1>
              <p style={{ margin: '22px auto 0', fontSize: 'clamp(15px, 1.8vw, 19px)', lineHeight: 1.55, color: CC.ink2, maxWidth: 600 }}>
                You’ve watched the split happen. The obvious question is whether it had to. Researchers have tried to reverse it — exposure programs, media diets, voting reform. The results are <em>not</em> what most people expect.
              </p>
              <button onClick={onDismiss} style={{ ...primaryBtn, width: 'auto', marginTop: 32, padding: '15px 30px', fontSize: 16 }}>Try the interventions &nbsp;→</button>
              <p style={{ margin: '20px 0 0', fontSize: DS.type.micro, color: CC.ink4 }}>Predict each one before you run it. The interesting part is where you’re wrong.</p>
            </React.Fragment>
          }
        </div>
      </div>
    </div>);

}

// ── lead payoff morph — the answer BEFORE the lecture (§3.1) ─────────────────
// A ~3-second auto-played "1980 one cluster → 2025 two camps" sweep with a
// six-word caption, shown right after the landing and before the staged
// orientation. Uses the real baseline density, so the thinning-but-surviving
// middle stays honest (we don't fake a vanishing centre).
function PayoffMorph({ onDone }) {
  const [t, setT] = React.useState(0);
  React.useEffect(() => {
    let raf, t0 = null;const DUR = 3000;
    const loop = (ts) => {
      if (t0 == null) t0 = ts;
      const k = Math.min(1, (ts - t0) / DUR);
      const e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2; // easeInOut
      setT(e * LAST);
      if (k < 1) raf = requestAnimationFrame(loop);else onDone();
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [onDone]);
  return (
    <div style={{ position: 'absolute', inset: 0, zIndex: 55, background: CC.bg, overflow: 'hidden' }}>
      <Field run={D.runs.baseline} tick={t} layer="position" view="density" showGap />
      <button onClick={onDone} style={{
        position: 'absolute', right: 24, top: 20, zIndex: 2, fontFamily: SANS, fontSize: DS.type.micro, fontWeight: 500,
        color: CC.ink3, background: 'rgba(255,255,255,.82)', border: `1px solid ${CC.border}`, borderRadius: DS.rad.pill,
        padding: '6px 12px', cursor: 'pointer'
      }}>Skip →</button>
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: '11%', textAlign: 'center', pointerEvents: 'none' }}>
        <div style={{ fontFamily: MONO, fontSize: 13, color: CC.ink3, ...TNUM }}>{Math.floor(tickToYear(t))}</div>
        <h2 style={{ margin: '8px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: 'clamp(24px, 3.6vw, 42px)', letterSpacing: '-.02em', color: CC.ink }}>
          One crowd becomes two camps.
        </h2>
      </div>
    </div>);

}

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
    <div style={{ marginTop: 20, padding: '13px 15px 11px', background: CC.surface, border: `1px solid ${CC.border}`, borderRadius: DS.rad.inset }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <Eyebrow style={{ color: CC.ink4 }}>{data.label} · {Math.floor(tickToYear(tick))}</Eyebrow>
        <span style={{ display: 'inline-flex', alignItems: 'baseline', gap: 8 }}>
          <MonoVal size={DS.type.subhead} color={ac}>{data.fmt(cv)}</MonoVal>
          {data.note && <Caption>{data.note}</Caption>}
        </span>
      </div>
      <div ref={ref} style={{ marginTop: 9 }}>
        <svg viewBox={`0 0 ${w} ${H}`} width="100%" height={H} preserveAspectRatio="xMidYMid meet" style={{ display: 'block' }}>
          <path d={full} fill="none" stroke={CC.ink4} strokeWidth="1.2" strokeDasharray="2 3" opacity="0.7" />
          <line x1={cx} y1={top - 3} x2={cx} y2={H - bot + 5} stroke={CC.ink4} strokeWidth="1" strokeDasharray="1 3" />
          <path d={pastPath} fill="none" stroke={ac} strokeWidth="1.9" strokeLinejoin="round" strokeLinecap="round" />
          <circle cx={cx} cy={cy} r="3.6" fill={CC.surface} stroke={ac} strokeWidth="2" />
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
    <div style={{ marginTop: 20, padding: '14px 16px', background: CC.surface, border: `1px solid ${CC.border}`, borderRadius: DS.rad.inset }}>
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
const ORIENT_LAYERS = ['axes', 'labels', 'blobs', 'rings', 'entities'];
const ORIENT_STEPS = [
  {
    title: 'Two questions, two axes',
    lead: 'Every American lands somewhere on this cross.',
    body: 'Left to right is the economy — who should hold the money and the power. Top to bottom is culture — how fast the country should change.',
  },
  {
    title: 'What the directions mean',
    lead: 'Each way you can move has a name.',
    body: 'Left, government should even things out; right, leave it to the market. Up is traditional, down is progressive — and the corners blend the two.',
  },
  {
    title: 'Where people cluster',
    lead: 'Each soft cloud is a crowd of Americans.',
    body: 'The denser the colour, the more people sit there. Navy leans Democratic, oxblood Republican; where the two overlap the field turns grey — the middle.',
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
        <p style={{ margin: '16px 0 0', fontSize: DS.type.body, lineHeight: 1.6, color: CC.ink2, maxWidth: 460 }}>{s.body}</p>
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
function WatchRail({ phase, beat, beatI, total, nextBeat, tick, onBack, onContinue, onExplore }) {
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
          <p style={{ margin: '18px 0 0', fontSize: DS.type.body, lineHeight: 1.6, color: CC.ink2 }}>Watch forty-five years of Americans drift across the political compass. We’ll pause at the moments that moved the country — and say, plainly, what each one did.</p>
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
          <p style={{ margin: '14px 0 0', fontSize: DS.type.body, lineHeight: 1.6, color: CC.ink2 }}>The country is sorting itself in real time. We’ll stop at the next moment that matters.</p>
          {nextBeat &&
          <div style={{ marginTop: 20, padding: '14px 16px', background: CC.surface, border: `1px solid ${CC.border}`, borderRadius: DS.rad.inset }}>
              <Eyebrow style={{ color: CC.ink4 }}>Next stop · {Math.floor(tickToYear(nextBeat.tick))}</Eyebrow>
              <div style={{ fontFamily: SERIF, fontWeight: 600, fontSize: DS.type.subhead, marginTop: 5, letterSpacing: '-.01em' }}>{nextBeat.title}</div>
            </div>
          }
        </div>
        <div style={footer}><Caption>Use the timeline below to pause, scrub, or change speed.</Caption></div>
      </div>);

  }
  if (phase === 'ended') {
    return (
      <div style={{ background: 'transparent', display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, justifyContent: 'safe center', overflow: 'auto' }}>
        <div style={scrollWrap}>
          <Eyebrow>The story · 1980 → 2025</Eyebrow>
          <h2 style={{ margin: '12px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: DS.type.title, lineHeight: 1.05, letterSpacing: '-.015em' }}>That’s how the camps formed.</h2>
          <p style={{ margin: '18px 0 0', fontSize: DS.type.body, lineHeight: 1.6, color: CC.ink2 }}>Forty-five years, two hardening camps, a middle that thinned to almost nothing — and an out-party warmth that fell from the high-40s to the mid-20s.</p>
          <p style={{ margin: '14px 0 0', fontSize: DS.type.body, lineHeight: 1.6, color: CC.ink2 }}>Now the obvious question: <em>could anything have pulled them back together?</em> Take the wheel — scrub any year, flip position against animus, and try the interventions for yourself.</p>
        </div>
        <div style={footer}>
          <button onClick={onExplore} style={primaryBtn}>Explore it yourself &nbsp;→</button>
        </div>
      </div>);

  }
  // beat
  return (
    <div style={{ background: 'transparent', display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, justifyContent: 'safe center', overflow: 'auto' }}>
      <div style={scrollWrap}>
        <Eyebrow>Chapter {beatI + 1} of {total} · {Math.floor(tickToYear(beat.tick))}</Eyebrow>
        <h2 style={{ margin: '14px 0 24px', fontFamily: SERIF, fontWeight: 600, fontSize: 50, lineHeight: 1.02, letterSpacing: '-.022em' }}>{beat.title}</h2>
        <p style={{ margin: 0, fontFamily: SERIF, fontStyle: 'italic', fontSize: DS.type.subhead, lineHeight: 1.42, color: CC.ink }}>{beat.lead}</p>
        <p style={{ margin: '16px 0 0', fontSize: DS.type.body, lineHeight: 1.6, color: CC.ink2, maxWidth: 460 }}>{beat.body}</p>
        {beat.orient ?
        <MapLegend /> :
        beat.data ?
        <BeatMetric data={beat.data} tick={beat.tick} /> :

        <div style={{ marginTop: 20, padding: '12px 15px', background: CC.surface, border: `1px solid ${CC.border}`, borderRadius: DS.rad.inset, display: 'flex', alignItems: 'center', gap: 11 }}>
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
        <button onClick={onContinue} style={{ ...primaryBtn, width: 'auto', padding: '13px 26px' }}>{beatI === total - 1 ? 'See where it ends →' : 'Continue →'}</button>
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
{ tick: 108, year: 2016, event: 'Trump wins — a status-threat shock.', viz: 'Switch to Affect · animus: the camps cool sharply.' },
{ tick: 120, year: 2020, event: 'COVID and January 6th.', viz: 'Two separate masses, with almost nothing left between them.' }];

function ExploreAnnotation({ tick }) {
  let near = null,best = 1e9;
  for (const n of EXPLORE_NOTES) {const d = Math.abs(tick - n.tick);if (d < best) {best = d;near = n;}}
  const op = Math.max(0, Math.min(1, (7.5 - best) / 2.6));
  if (!near || op <= 0.02) return null;
  return (
    <div style={{
      position: 'absolute', left: 24, top: 20, width: 312, maxWidth: '42%', pointerEvents: 'none',
      background: 'rgba(255,255,255,.94)', backdropFilter: 'blur(3px)', border: `1px solid ${CC.borderS}`,
      borderRadius: DS.rad.inset, padding: '13px 15px', boxShadow: '0 6px 22px rgba(26,29,35,.1)',
      opacity: op, transform: `translateY(${(1 - op) * 5}px)`, transition: 'opacity .25s, transform .25s'
    }}>
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
    <div style={{ padding: '13px 15px', background: CC.surface, border: `1px solid ${CC.border}`, borderRadius: DS.rad.inset }}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 10 }}>
        <Eyebrow style={{ color: CC.ink4 }}>What that feels like · {Math.floor(tickToYear(tick))}</Eyebrow>
        <MonoVal size={DS.type.small} color={CC.ink}>{warmth}° warmth</MonoVal>
      </div>
      <p style={{ margin: '9px 0 0', fontSize: DS.type.small, lineHeight: 1.55, color: CC.ink2 }}>{line}</p>
    </div>);

}

function ExploreRail({ layer, tick }) {
  const isAffect = layer === 'affect';
  return (
    <div style={{ background: 'transparent', display: 'flex', flexDirection: 'column', minHeight: 0, height: '100%', justifyContent: 'safe center', overflow: 'auto' }}>
      <div style={{ flexShrink: 0, padding: `clamp(28px,4.5vh,52px) 44px clamp(28px,4.5vh,52px) clamp(64px,14vw,248px)`, display: 'flex', flexDirection: 'column', gap: 22 }}>
        <div>
          <Eyebrow>{isAffect ? 'Affective polarization' : 'Positional polarization'}</Eyebrow>
          <h3 style={{ margin: '12px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: 46, lineHeight: 1.02, letterSpacing: '-.022em' }}>
            {isAffect ? 'Do they hate each other?' : 'Are they far apart?'}
          </h3>
          <p style={{ margin: '18px 0 0', fontSize: DS.type.body, lineHeight: 1.62, color: CC.ink2, maxWidth: 460 }}>
            {isAffect ?
            <>Issue positions barely moved — but the feelings curdled. The clearest picture is the <strong>thermometer "scissors"</strong>: warmth toward your <em>own</em> side held roughly flat while warmth toward the <em>other</em> side fell off a cliff. On the map, both camps keep their colour but <strong>deepen as they cool</strong>, and the tether between them is the felt distance. <strong>Distance and animus are different axes.</strong></> :
            <>A smoothed density of where {D.meta.n_agents} Americans sit, drawn as <strong>two party-coloured fields</strong>. One shared lump in 1980; two camps by 2025. Where they overlap is the contested middle — thinning, but never quite gone.</>}
          </p>
        </div>
        {isAffect ?
        <div>
            <ScissorsChart tick={tick} />
            <div style={{ marginTop: 10 }}><ScissorsLegend tick={tick} /></div>
          </div> :
        <div>
            <Eyebrow style={{ color: CC.ink3 }}>One lump → two camps</Eyebrow>
            <div style={{ marginTop: 10 }}><SmallMultiples /></div>
          </div>
        }
        <CalibrationAnchor tick={tick} />
        <div style={{ height: 1, background: CC.border }} />
        <div>
          <Eyebrow style={{ color: CC.ink3 }}>Where the country is</Eyebrow>
          <div style={{ marginTop: 10 }}><ProtoSparklines tick={tick} run={D.runs.baseline} width={392} rowH={56} gap={34} /></div>
        </div>
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
      <div style={{ display: 'inline-flex', gap: 2, padding: 3, background: CC.bg2, borderRadius: DS.rad.pill, border: `1px solid ${CC.border}` }}>
        {[[0.5, '½×'], [1, '1×'], [2, '2×'], [4, '4×']].map(([v, l]) => {
          const on = speed === v;
          return (
            <button key={v} onClick={() => setSpeed(v)} style={{
              fontSize: 11, padding: '3px 7px', borderRadius: DS.rad.pill, fontFamily: MONO, cursor: 'pointer', border: 'none',
              color: on ? CC.ink : CC.ink3, fontWeight: on ? 600 : 400, background: on ? CC.surface : 'transparent',
              boxShadow: on ? '0 1px 3px rgba(26,29,35,.12)' : 'none', ...TNUM
            }}>{l}</button>);

        })}
      </div>
    </div>);

}

function TimelineBar({ tick, setTick, playing, toggle, speed, setSpeed, layer, mode, beatI, onPickBeat, ended }) {
  const year = Math.floor(tickToYear(tick));
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const monthLabel = `${months[Math.min(11, Math.floor((tickToYear(tick) - year) * 12))]} ${year}`;
  const accent = CC.ink;
  return (
    <div style={{ height: BARH, flexShrink: 0, background: CC.bg, position: 'relative', display: 'flex', alignItems: 'center', gap: 'clamp(20px, 3vw, 44px)', padding: '0 clamp(28px, 4vw, 56px)' }}>
      <div style={{ position: 'absolute', top: 0, left: 'clamp(28px, 4vw, 56px)', right: 'clamp(28px, 4vw, 56px)', height: 1, background: CC.border }} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, flexShrink: 0, width: 224 }}>
        <BarTransport playing={playing} toggle={toggle} setTick={setTick} speed={speed} setSpeed={setSpeed} />
        {mode === 'watch' ?
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <MonoVal size={DS.type.micro} color={CC.ink}>{monthLabel}</MonoVal>
            <span style={{ fontSize: DS.type.micro, color: CC.ink3 }}>
              <span style={{ color: CC.ink4 }}>Chapter {Math.min(beatI + 1, BEATS.length)}/{BEATS.length} · </span>{BEATS[beatI] ? BEATS[beatI].short : ''}
            </span>
          </div> :
        <MonoVal size={DS.type.micro} color={CC.ink}>{monthLabel} <span style={{ color: CC.ink4 }}>· tick {Math.round(tick)}/{LAST}</span></MonoVal>
        }
      </div>
      <div style={{ flex: 1, minWidth: 0, position: 'relative' }}>
        <Eyebrow style={{ color: CC.ink3 }}>{mode === 'watch' ? 'Chapters · click a pin to jump' : '1980 → 2025 · drag to scrub'}</Eyebrow>
        <div style={{ marginTop: 4, position: 'relative' }}>
          {/* chapter rail for Watch — labeled, click-to-jump diamonds; the active
              chapter carries its name as the "you are here" marker */}
          {mode === 'watch' && BEATS.map((b, k) => {
            const on = k === beatI && !ended;
            const left = `calc(14px + ${b.tick / LAST} * (100% - 28px))`;
            return (
              <React.Fragment key={k}>
                {on &&
                <span style={{ position: 'absolute', zIndex: 5, left, top: 20, transform: 'translateX(-50%)', whiteSpace: 'nowrap', fontFamily: SANS, fontSize: 10, fontWeight: 600, color: CC.ink, background: 'rgba(249,248,244,.9)', padding: '0 3px' }}>{b.short}</span>
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

function Unified() {
  const ph = useTick({ start: 0, autoplay: false, base: 2.25 });
  const { tick, setTick, playing, setPlaying, toggle, speed, setSpeed } = ph;
  const [page, setPage] = React.useState('model');
  const [mode, setMode] = React.useState('watch');
  const [layer, setLayer] = React.useState('position');
  const [beatI, setBeatI] = React.useState(0);
  const [orientStep, setOrientStep] = React.useState(0);
  const [orientSeen, setOrientSeen] = React.useState(false);
  const [paused, setPaused] = React.useState(false);
  const [ended, setEnded] = React.useState(false);
  const [started, setStarted] = React.useState(false);
  const [showLandmarks, setShowLandmarks] = React.useState(false);
  const [entered, setEntered] = React.useState(false);
  const [morphing, setMorphing] = React.useState(false);   // the lead payoff morph
  const [unlocked, setUnlocked] = React.useState(false);   // story finished → free explore on the SAME canvas
  const [showIvIntro, setShowIvIntro] = React.useState(false);
  const [ivIntroSeen, setIvIntroSeen] = React.useState(false);
  const seen = React.useRef(new Set());
  const iv = useInterventions();

  // Watch: auto-pause on first crossing of each beat; flip layer per beat; end card at the finish.
  // Once unlocked (free explore) the auto-pause stops — the user drives.
  React.useEffect(() => {
    if (mode !== 'watch' || ended || !entered || unlocked) return;
    for (let i = 0; i < BEATS.length; i++) {
      if (tick >= BEATS[i].tick && !seen.current.has(i)) {
        seen.current.add(i);setBeatI(i);setPaused(true);setPlaying(false);
        if (BEATS[i].layer) setLayer(BEATS[i].layer);
        return;
      }
    }
    if (tick >= LAST) {setEnded(true);setPlaying(false);}
  }, [tick, mode, ended, entered, setPlaying]);

  // keep paused state honest: any manual play clears the "parked at a beat" flag
  React.useEffect(() => {if (playing && paused) setPaused(false);}, [playing, paused]);

  const continueStory = () => {setStarted(true);setPaused(false);setEnded(false);setPlaying(true);};
  const backStory = () => {
    const i = Math.max(0, beatI - 1);
    seen.current.delete(beatI);setBeatI(i);setTick(BEATS[i].tick + 0.001);setStarted(true);setPaused(true);setPlaying(false);setEnded(false);
    if (BEATS[i].layer) setLayer(BEATS[i].layer);
  };
  const pickBeat = (k) => {
    seen.current = new Set(BEATS.map((_, j) => j).filter((j) => BEATS[j].tick <= BEATS[k].tick));
    setBeatI(k);setTick(BEATS[k].tick + 0.001);setStarted(true);setPaused(true);setPlaying(false);setEnded(false);
    if (BEATS[k].layer) setLayer(BEATS[k].layer);
  };
  // finishing the guided story hands the controls over ON THE SAME canvas
  // (no separate Explore tab) — free scrub, layer toggle, parties, scissors.
  const goExplore = () => {setUnlocked(true);setEnded(false);setPaused(false);setPlaying(false);};
  const switchMode = (m) => {
    if (m === 'watch') {seen.current = new Set();setUnlocked(false);setEnded(false);setStarted(false);setBeatI(0);setLayer('position');setTick(0);setPaused(false);setPlaying(false);setOrientStep(0);setOrientSeen(false);} else
    {setPlaying(false);}
    if (m === 'interventions' && !ivIntroSeen) setShowIvIntro(true);
    setMode(m);
  };
  // landing → a ~3s "1980 → 2025" payoff morph → the staged orientation
  const enterFromLanding = () => {setMorphing(true);};
  const finishMorph = () => {setMorphing(false);setEntered(true);setOrientStep(0);setOrientSeen(false);continueStory();};
  const orientNext = () => setOrientStep((s) => Math.min(ORIENT_LAYERS.length - 1, s + 1));
  const orientPrev = () => setOrientStep((s) => Math.max(0, s - 1));
  const finishOrient = () => {setOrientSeen(true);setOrientStep(ORIENT_LAYERS.length - 1);continueStory();};

  // ── static pages ──
  if (page !== 'model') {
    return (
      <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: CC.bg, minHeight: 0 }}
      onClick={(e) => {const g = e.target.closest('[data-goto]');if (g) {e.preventDefault();setPage(g.getAttribute('data-goto'));}}}>
        <SiteHeader page={page} setPage={setPage} />
        {page === 'about' ? <AboutPage /> : <MethodsPage />}
      </div>);

  }

  const isIv = mode === 'interventions';
  const isWatch = mode === 'watch' && !unlocked;   // guided story
  const isExplore = mode === 'watch' && unlocked;  // unlocked free-explore (same canvas)
  const beat = BEATS[beatI];
  const phase = ended ? 'ended' : paused ? 'beat' : started || seen.current.size > 0 ? 'playing' : 'intro';
  const stagedOrient = isWatch && phase === 'beat' && beat && beat.orient && !orientSeen;
  const watchReveal = stagedOrient ? ORIENT_LAYERS.slice(0, orientStep + 1) : null;
  const dimField = isWatch && (paused || ended) && !stagedOrient ? 0.24 : 0;

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: CC.bg, minHeight: 0, position: 'relative' }}>
      <SiteHeader page={page} setPage={setPage} />
      <ModeBar mode={mode} setMode={switchMode} layer={layer} setLayer={setLayer} />

      {/* body — Interventions is a borderless workbench; Watch/Explore is a full-bleed editorial collage */}
      {isIv ?
      <div style={{ flex: 1, minHeight: 0, display: 'grid', gridTemplateColumns: `${TRAYW}px minmax(0,1fr) ${RAILW}px`, background: CC.bg }}>
          <div style={{ overflow: 'hidden', minHeight: 0 }}>
            <div style={{ width: TRAYW, height: '100%' }}><IvTray iv={iv} /></div>
          </div>
          <div style={{ position: 'relative', minWidth: 0, minHeight: 0 }}>
            <Field run={D.runs.baseline} tick={LAST} layer={layer} view="density" showGap={false} dim={0} transform={iv.transform} landmarks={layer === 'position' ? 'fixed' : false} />
            <FieldChip tone="paused">{iv.isSandbox ? 'sandbox · illustrative' : iv.showResult ? `modeled at 2025 · released ${iv.releaseYear}` : iv.predicting ? 'today · 2025 — your call pending' : 'today · 2025'}</FieldChip>
          </div>
          <div style={{ minWidth: 0, minHeight: 0 }}><IvRail iv={iv} /></div>
        </div> :

      <div style={{ flex: 1, minHeight: 0, position: 'relative', overflow: 'hidden', background: CC.bg }}>
          {/* the compass — a fully contained square anchored right (no bleed; all axes & labels visible) */}
          <div style={{ position: 'absolute', top: '-6%', bottom: '-6%', right: '2%', aspectRatio: '1' }}>
            <Field run={D.runs.baseline} tick={tick} layer={layer} view="density" showGap dim={dimField} reveal={watchReveal} landmarks={layer === 'position' ? isExplore && showLandmarks ? 'all' : 'fixed' : false} />
          </div>

          {/* paper scrim — keeps the floating prose legible, feathers out before the map */}
          <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, width: '56%', background: `linear-gradient(90deg, ${CC.bg} 0%, ${CC.bg} 88%, rgba(249,248,244,0) 100%)`, pointerEvents: 'none', zIndex: 1 }} />

          {/* chips + annotations, anchored to the visible map region */}
          <div style={{ position: 'absolute', top: 0, bottom: 0, left: '50%', right: 0, pointerEvents: 'none', zIndex: 2 }}>
            {isExplore && <ExploreAnnotation tick={tick} />}
            {isExplore && layer === 'position' &&
          <button onClick={() => setShowLandmarks((v) => !v)} style={{
            position: 'absolute', right: 24, top: 20, pointerEvents: 'auto', display: 'inline-flex', alignItems: 'center', gap: 8,
            fontFamily: SANS, fontSize: DS.type.micro, fontWeight: 500, cursor: 'pointer',
            color: showLandmarks ? CC.ink : CC.ink3, background: showLandmarks ? CC.surface : 'rgba(255,255,255,.82)',
            padding: '6px 12px', borderRadius: DS.rad.pill, border: `1px solid ${showLandmarks ? CC.ink : CC.border}`,
            boxShadow: showLandmarks ? '0 1px 4px rgba(26,29,35,.12)' : 'none'
          }}>
                <span style={{ width: 7, height: 7, borderRadius: 2, background: showLandmarks ? CC.ink : 'transparent', border: `1.5px solid ${showLandmarks ? CC.ink : CC.ink4}` }} />
                {showLandmarks ? 'Parties on' : 'Show parties'}
              </button>
          }
          </div>

          {/* floating narrative — a centered editorial block on the left */}
          <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, width: 'min(54%, 820px)', display: 'flex', flexDirection: 'column', minHeight: 0, zIndex: 3 }}>
            {isWatch && (stagedOrient ?
              <OrientRail step={orientStep} onPrev={orientPrev} onNext={orientNext} onContinue={finishOrient} /> :
              <WatchRail phase={phase} beat={beat} beatI={beatI} total={BEATS.length} nextBeat={BEATS.find((b) => b.tick > tick) || null} tick={tick} onBack={backStory} onContinue={continueStory} onExplore={goExplore} />)}
            {isExplore && <ExploreRail layer={layer} tick={tick} />}
          </div>
        </div>
      }

      {/* bottom bar — fixed height across all postures */}
      {isIv ?
      <div style={{ height: BARH, flexShrink: 0, background: CC.bg, position: 'relative', display: 'flex', alignItems: 'center', padding: '0 clamp(28px, 4vw, 56px)' }}>
          <div style={{ position: 'absolute', top: 0, left: 'clamp(28px, 4vw, 56px)', right: 'clamp(28px, 4vw, 56px)', height: 1, background: CC.border }} />
          <IvBottom iv={iv} />
        </div> :

      <TimelineBar tick={tick} setTick={setTick} playing={playing} toggle={toggle} speed={speed} setSpeed={setSpeed}
      layer={layer} mode={isWatch ? 'watch' : 'explore'} beatI={beatI} onPickBeat={pickBeat} ended={ended} />
      }

      {!entered && !morphing && <HeroOverlay variant="landing" onDismiss={enterFromLanding} />}
      {morphing && <PayoffMorph onDone={finishMorph} />}
      {entered && showIvIntro && <HeroOverlay variant="interventions" onDismiss={() => {setIvIntroSeen(true);setShowIvIntro(false);}} />}
    </div>);

}

ReactDOM.createRoot(document.getElementById('root')).render(<Unified />);