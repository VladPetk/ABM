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
function HeaderNavLink({ id, page, setPage, children, target, active }) {
  const on = active != null ? active : page === id;
  return (
    <button onClick={() => setPage(target || id)} style={{
      fontFamily: SANS, fontSize: DS.type.small, fontWeight: on ? 600 : 500, color: on ? CC.ink : CC.ink3,
      background: 'none', border: 'none', cursor: 'pointer', padding: '6px 2px', position: 'relative'
    }}>
      {children}
      <span style={{ position: 'absolute', left: 0, right: 0, bottom: -1, height: 2, borderRadius: 2, background: on ? CC.ink : 'transparent' }} />
    </button>);

}
// Nav model shared by the desktop bar and the mobile sheet — one source of
// truth for the five destinations + their active rules.
const NAV_ITEMS = [
  { id: 'forces', target: 'forces', label: 'The Model', active: (p) => p === 'model' || p === 'forces' || p === 'prologue' },
  { id: 'story', target: 'story', label: 'The U.S. Story', active: (p) => p === 'story' },
  { id: 'playground', label: 'Playground' },
  { id: 'methods', label: 'Methods' },
  { id: 'about', label: 'About' },
];

function SiteHeader({ page, setPage, hidden = false, pgMode = null, onPgMode = null, mdMode = null, onMdMode = null }) {
  const isMobile = useIsMobile();
  const [open, setOpen] = React.useState(false);
  // close the sheet whenever we land on a new page
  React.useEffect(() => { setOpen(false); }, [page]);
  const brand = (
    <button onClick={() => setPage('model')} style={{ display: 'flex', alignItems: 'center', gap: 12, background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
      <Logo />
      <span style={{ fontFamily: SERIF, fontStyle: 'italic', fontSize: 16, color: CC.ink2, whiteSpace: 'nowrap' }}>The Divide</span>
    </button>);

  if (isMobile) {
    // collapse + slide up when `hidden` (scroll-down); the flex sibling below
    // grows into the freed space. Kept overflow-visible so the dropdown isn't
    // clipped (it only opens while the header is shown).
    return (
      <div style={{ flexShrink: 0, position: 'relative', zIndex: 40, height: hidden ? 0 : 52, transition: 'height .26s ease' }}>
        <div style={{ transform: hidden ? 'translateY(-100%)' : 'none', transition: 'transform .26s ease', background: CC.bg }}>
          <div style={{ height: 52, display: 'flex', alignItems: 'center', gap: 12, padding: '0 18px', background: CC.bg, borderBottom: `1px solid ${CC.border}` }}>
            {brand}
            <span style={{ flex: 1 }} />
            <button onClick={() => setOpen((v) => !v)} aria-label={open ? 'Close menu' : 'Open menu'} aria-expanded={open} style={{
              width: 40, height: 40, display: 'inline-flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 5,
              background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
              <span style={{ width: 21, height: 2, borderRadius: 2, background: CC.ink2, transition: 'transform .2s', transform: open ? 'translateY(7px) rotate(45deg)' : 'none' }} />
              <span style={{ width: 21, height: 2, borderRadius: 2, background: CC.ink2, opacity: open ? 0 : 1, transition: 'opacity .15s' }} />
              <span style={{ width: 21, height: 2, borderRadius: 2, background: CC.ink2, transition: 'transform .2s', transform: open ? 'translateY(-7px) rotate(-45deg)' : 'none' }} />
            </button>
          </div>
          {open &&
          <nav style={{ position: 'absolute', left: 0, right: 0, top: 52, background: CC.bg, borderBottom: `1px solid ${CC.border}`, boxShadow: '0 12px 28px rgba(26,29,35,.10)', display: 'flex', flexDirection: 'column', padding: '6px 0', animation: 'ccFadeUp .2s ease' }}>
            {NAV_ITEMS.map((it) => {
              const on = it.active ? it.active(page) : page === it.id;
              return (
                <React.Fragment key={it.id}>
                  <button onClick={() => setPage(it.target || it.id)} style={{
                    textAlign: 'left', padding: '14px 22px', background: on ? CC.bg2 : 'none', border: 'none', cursor: 'pointer',
                    fontFamily: SANS, fontSize: 16, fontWeight: on ? 600 : 500, color: on ? CC.ink : CC.ink2 }}>
                    {it.label}
                  </button>
                  {/* sub-choices that used to be on-page pills now live under their
                      section in the menu: Model → tour/engine · Playground → iv/sandbox */}
                  {it.id === 'forces' && (page === 'forces' || page === 'prologue') && mdMode &&
                    [['tour', 'Force by force'], ['engine', 'The whole engine']].map(([m, lab]) => {
                      const mon = mdMode === m;
                      return (
                        <button key={m} onClick={() => { onMdMode && onMdMode(m); setOpen(false); }} style={{
                          textAlign: 'left', padding: '11px 22px 11px 40px', background: 'none', border: 'none', cursor: 'pointer',
                          display: 'flex', alignItems: 'center', gap: 10, fontFamily: SANS, fontSize: 14.5, fontWeight: mon ? 600 : 450, color: mon ? CC.ink : CC.ink3 }}>
                          <span style={{ width: 6, height: 6, borderRadius: 9, flexShrink: 0, background: mon ? CC.ink : 'transparent', border: `1.5px solid ${mon ? CC.ink : CC.ink4}` }} />
                          {lab}
                        </button>);
                    })}
                  {it.id === 'playground' && page === 'playground' && pgMode &&
                    [['interventions', 'Interventions'], ['sandbox', 'Sandbox']].map(([m, lab]) => {
                      const mon = pgMode === m;
                      return (
                        <button key={m} onClick={() => { onPgMode && onPgMode(m); setOpen(false); }} style={{
                          textAlign: 'left', padding: '11px 22px 11px 40px', background: 'none', border: 'none', cursor: 'pointer',
                          display: 'flex', alignItems: 'center', gap: 10, fontFamily: SANS, fontSize: 14.5, fontWeight: mon ? 600 : 450, color: mon ? CC.ink : CC.ink3 }}>
                          <span style={{ width: 6, height: 6, borderRadius: 9, flexShrink: 0, background: mon ? CC.ink : 'transparent', border: `1.5px solid ${mon ? CC.ink : CC.ink4}` }} />
                          {lab}
                        </button>);
                    })}
                </React.Fragment>);
            })}
          </nav>}
        </div>
      </div>);
  }

  return (
    <div style={{ flexShrink: 0, position: 'relative', zIndex: 30, height: hidden ? 0 : 58, transition: 'height .26s ease' }}>
      <div style={{ height: 58, display: 'flex', alignItems: 'center', gap: 14, padding: '0 clamp(24px, 4vw, 56px)', background: CC.bg, transform: hidden ? 'translateY(-100%)' : 'none', transition: 'transform .26s ease' }}>
        {brand}
        <span style={{ flex: 1 }} />
        <nav style={{ display: 'flex', alignItems: 'center', gap: 22 }}>
          {NAV_ITEMS.map((it) => (
            <HeaderNavLink key={it.id} id={it.id} target={it.target} active={it.active ? it.active(page) : undefined} page={page} setPage={setPage}>{it.label}</HeaderNavLink>
          ))}
        </nav>
      </div>
    </div>);

}

// ── Tier 2 — Playground mode bar (Interventions / Sandbox). Constant height. ──
// Lives ONLY on the Playground page: the two ways to drive the model — the
// measured levers vs. free tinkering ("not a finding").
function ModeBar({ mode, setMode }) {
  const isMobile = useIsMobile();
  return (
    <div style={{ height: isMobile ? 46 : 50, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: isMobile ? 'center' : 'flex-start', gap: 14, padding: isMobile ? '0 16px' : '0 clamp(24px, 4vw, 56px)', background: CC.bg, position: 'relative', zIndex: 20 }}>
      <Segmented value={mode} onChange={setMode} options={[['interventions', 'Interventions'], ['sandbox', 'Sandbox']]} compact={isMobile} />
    </div>);

}

// ── Tier-2 — "The Forces" mode bar. Two views of the same engine: the guided
// force-by-force tour, and the whole engine running at once (the hub). Lives on
// both pages so the toggle is always the way between them (and back). ──
function ForcesModeBar({ mode, goPage }) {
  const isMobile = useIsMobile();
  return (
    <div style={{ height: isMobile ? 46 : 50, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: isMobile ? 'center' : 'flex-start', gap: 14, padding: isMobile ? '0 16px' : '0 clamp(24px, 4vw, 56px)', background: CC.bg, position: 'relative', zIndex: 20 }}>
      <Segmented value={mode} onChange={(v) => goPage(v === 'tour' ? 'forces' : 'prologue')}
        options={[['tour', 'Force by force'], ['engine', 'The whole engine']]} compact={isMobile} />
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
        <Item glyph={<Ring c={CC.r} />} label={<><strong style={{ color: CC.ink }}>Party centres</strong> — the live heart of each camp, moving with the engine.</>} />
        <Item glyph={<Diamond c={CC.r} />} label={<><strong style={{ color: CC.ink }}>Emergent factions</strong> — Tea Party, MAGA, Bernie, DSA — each appears the year it forms.</>} />
        <Item glyph={<Sq c={CC.ink2} />} label={<><strong style={{ color: CC.ink }}>News outlets</strong> — at the calibrated positions that actually pull people.</>} />
      </div>
      <p style={{ margin: '12px 0 0', paddingTop: 11, borderTop: `1px solid ${CC.border}`, fontSize: DS.type.micro, lineHeight: 1.5, color: CC.ink3 }}>
        Every marker is the engine’s own data, not an illustrative placement. Navy is Democratic, oxblood Republican.
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
// A single framing beat at the start of the U.S. story: same engine as the
// prologue (US-tuned forces), now with the real history switched on. (Replaces
// the old staged map-reading build — the map is already taught by the intro +
// forces tour; markers self-label as they appear.)
const ORIENT_STEPS = [
  {
    title: 'The same engine, now with the history switched on.',
    lead: 'Nothing about the forces changes here — only what’s driving them.',
    body: 'These are the same forces you watched stall short a moment ago, already tuned to the United States: their strengths were fit to decades of ANES survey data — where Americans actually stood, and how cold they’d grown toward the other side. What the prologue switched off, and this switches back on, is the history: the real drivers fed in on top of the mechanism — the spread of partisan media across the period, and the dated events that shaped it, from Fox News to the Tea Party to 2016 to COVID and January 6th. That’s what carries the engine the rest of the way, onto the actual 1980→2025 arc. From here you’re watching a reconstruction of the United States, and we’ll stop at the moments that moved it.',
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
        <Eyebrow>The U.S. story · 1980</Eyebrow>
        <h2 style={{ margin: '14px 0 18px', fontFamily: SERIF, fontWeight: 600, fontSize: 38, lineHeight: 1.05, letterSpacing: '-.02em', maxWidth: 460 }}>{s.title}</h2>
        <p style={{ margin: 0, fontFamily: SERIF, fontStyle: 'italic', fontSize: DS.type.subhead, lineHeight: 1.42, color: CC.ink, maxWidth: 440 }}>{s.lead}</p>
        <p style={{ margin: '16px 0 0', ...PROSE, color: CC.ink2, maxWidth: 460 }}>{s.body}</p>
        {total > 1 &&
        <div style={{ marginTop: 26, display: 'flex', alignItems: 'center', gap: 9 }}>
          {ORIENT_STEPS.map((_, i) => (
            <span key={i} style={{ height: 3, flex: i === step ? '0 0 26px' : '0 0 14px', borderRadius: 2, background: i <= step ? CC.ink : CC.border, transition: 'background .2s, flex-basis .2s' }} />
          ))}
          <span style={{ marginLeft: 4, fontFamily: MONO, fontSize: DS.type.micro, color: CC.ink4, ...TNUM }}>{step + 1}/{total}</span>
        </div>
        }
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
  const isMobile = useIsMobile();
  const LX = isMobile ? '20px' : 'clamp(64px, 14vw, 248px)';
  const RX = isMobile ? '20px' : '44px';
  const topPad = isMobile ? '22px' : 'clamp(28px,4.5vh,52px)';
  const botPad = isMobile ? '26px' : 'clamp(24px,4vh,40px)';
  const pad = `${topPad} ${RX} 8px ${LX}`;
  const scrollWrap = { flexShrink: 0, padding: pad };
  const footer = { flexShrink: 0, padding: `14px ${RX} ${botPad} ${LX}`, background: 'transparent' };
  // top-align on mobile (read top-down in the scroll pane); centered on desktop
  const wrap = { background: 'transparent', display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, justifyContent: isMobile ? 'flex-start' : 'safe center', overflow: 'auto' };
  const beatTitleSize = isMobile ? (beat && beat.orient ? 25 : 29) : (beat && beat.orient ? 38 : 50);

  // (the old phase==='intro' and phase==='playing' rails were removed — both
  // were unreachable once the prologue + enterStory() flow landed: the story
  // page always renders with started===true, so phase is only 'beat' or
  // 'ended'. The intro framing now lives in rc-intro.jsx + rc-prologue.jsx.)
  if (phase === 'ended') {
    const quiet = {
      background: 'none', border: 'none', cursor: 'pointer', padding: 0,
      fontFamily: SANS, fontSize: DS.type.micro, color: CC.ink3, textDecoration: 'underline', textUnderlineOffset: 3,
    };
    return (
      <div style={wrap}>
        <div style={scrollWrap}>
          <Eyebrow>The U.S. story · 1980 → 2025</Eyebrow>
          <h2 style={{ margin: '12px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: DS.type.title, lineHeight: 1.05, letterSpacing: '-.015em' }}>Now drive it yourself.</h2>
          <p style={{ margin: '18px 0 0', ...PROSE, color: CC.ink2 }}>You’ve just watched the engine reproduce the U.S. polarization story: an amorphous blob turning into two better-defined partisan blobs.</p>
          <p style={{ margin: '14px 0 0', ...PROSE, color: CC.ink2 }}>You might be wondering whether any of it had to play out this way, whether there is a vaccine for it. There are two ways to find out: try the things researchers have actually put to the test, or tinker with the dials yourself.</p>
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
    <div style={wrap}>
      <div key={beatI} style={{ ...scrollWrap, animation: 'ccFadeUp .42s ease' }}>
        <Eyebrow>{beat.orient ? `The U.S. story · ${Math.floor(tickToYear(beat.tick))}` : `Chapter ${beatI} of ${total - 1} · ${Math.floor(tickToYear(beat.tick))}`}</Eyebrow>
        <h2 style={{ margin: '14px 0 24px', fontFamily: SERIF, fontWeight: 600, fontSize: beatTitleSize, lineHeight: beat.orient ? 1.05 : 1.02, letterSpacing: '-.022em' }}>{beat.title}</h2>
        <p style={{ margin: 0, fontFamily: SERIF, fontStyle: 'italic', fontSize: DS.type.subhead, lineHeight: 1.42, color: CC.ink }}>{beat.lead}</p>
        <p style={{ margin: '16px 0 0', ...PROSE, color: CC.ink2, maxWidth: 460 }}>{beat.body}</p>
        {beat.orient ?
        null :
        beat.data ?
        <BeatMetric data={beat.data} tick={beat.tick} /> :
        beat.metric ?
        <div style={{ marginTop: 22, paddingTop: 13, borderTop: `1px solid ${CC.border}`, display: 'flex', alignItems: 'center', gap: 11 }}>
              <Eyebrow style={{ color: CC.ink4, letterSpacing: '.1em' }}>data</Eyebrow>
              <MonoVal size={DS.type.small} color={CC.ink}>{beat.metric(beat.tick)}</MonoVal>
            </div> : null
        }
      </div>
      <div style={{ ...footer, display: 'flex', gap: 10 }}>
        <button onClick={onBack} disabled={beatI === 0} style={{
          padding: '12px 16px', borderRadius: DS.rad.pill, border: `1px solid ${CC.border}`, background: CC.surface,
          color: beatI === 0 ? CC.ink4 : CC.ink2, cursor: beatI === 0 ? 'default' : 'pointer', fontFamily: SANS, fontSize: DS.type.small
        }}>← Back</button>
        <button onClick={onContinue} style={{ ...primaryBtn, width: 'auto', padding: '13px 26px' }}>{beat.orient ? 'Start the story →' : beatI === total - 1 ? 'Jump to the end →' : 'Jump to next →'}</button>
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
{ tick: 42, year: 1994, event: 'Gingrich: the parties split at the top.', viz: 'Elites lead — the heart of each camp begins to slide off-center, the right faster.' },
{ tick: 48, year: 1996, event: 'Fox News launches.', viz: 'A second lobe pulls toward the traditional-right corner.' },
{ tick: 60, year: 2000, event: 'Identities begin to stack.', viz: 'Party, faith and region align into one identity; the camps cool as they sort.' },
{ tick: 84, year: 2008, event: 'Social media reaches everyone; Obama is elected.', viz: 'Often blamed, rarely convicted — the split was already underway, and rose fastest among the least-online.' },
{ tick: 90, year: 2010, event: 'The base hardens; Citizens United lands.', viz: 'Primary challenges pull the right outward. Citizens United is an era marker here, not the cause.' },
{ tick: 105, year: 2015, event: 'MAGA emerges.', viz: 'A dense knot forms in the populist-right corner.' },
{ tick: 108, year: 2016, event: 'Trump wins — a contested status-threat shock.', viz: 'The camps harden into opposite corners; the contested middle keeps thinning.' },
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
  if (warmth >= 42) line = <>So what does a number like that feel like? Back here, only about <strong>1 in 20</strong> Americans said they’d mind if their child married someone from the other party.</>;else
  if (warmth >= 30) line = <>So what does a number like that feel like? By now it’s closer to <strong>a third</strong> who’d mind if their child married someone from the other party.</>;else
  line = <>So what does a number like that feel like? By now it’s getting on for <strong>half</strong> who’d mind if their child married someone from the other party.</>;
  return (
    <div style={{ paddingTop: 14, borderTop: `1px solid ${CC.border}` }}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 10 }}>
        <Eyebrow style={{ color: CC.ink4 }}>What that feels like · {Math.floor(tickToYear(tick))}</Eyebrow>
        <MonoVal size={DS.type.small} color={CC.ink}>{warmth}° warmth</MonoVal>
      </div>
      <p style={{ margin: '9px 0 0', fontSize: DS.type.small, lineHeight: 1.55, color: CC.ink2 }}>{line}</p>
      <p style={{ margin: '5px 0 0', fontSize: DS.type.micro, lineHeight: 1.45, color: CC.ink4 }}>Rough survey figures (ANES / Iyengar), not an engine output.</p>
    </div>);

}

function ExploreRail({ tick, onBackToStory }) {
  const isMobile = useIsMobile();
  const pad = isMobile
    ? `22px 20px 26px 20px`
    : `clamp(28px,4.5vh,52px) 44px clamp(28px,4.5vh,52px) clamp(64px,14vw,248px)`;
  return (
    <div style={{ background: 'transparent', display: 'flex', flexDirection: 'column', minHeight: 0, height: '100%', justifyContent: isMobile ? 'flex-start' : 'safe center', overflow: 'auto' }}>
      <div style={{ flexShrink: 0, padding: pad, display: 'flex', flexDirection: 'column', gap: 22 }}>
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
          <Eyebrow>Affective polarization</Eyebrow>
          <h3 style={{ margin: '12px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: isMobile ? 30 : 46, lineHeight: 1.02, letterSpacing: '-.022em' }}>
            Do they hate each other?
          </h3>
          <p style={{ margin: '18px 0 0', ...PROSE, color: CC.ink2, maxWidth: 460 }}>
            The positions pulled apart, but the feelings pulled apart faster. The map shows where people <em>stand</em>; this shows how they <em>feel</em>. Warmth toward your <em>own</em> side barely moved; toward the <em>other</em> side it fell sharply. <strong>Distance and animus are two different axes.</strong>
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

function TimelineBar({ tick, setTick, playing, toggle, speed, setSpeed, mode, beatI, onPickBeat, ended, beats = BEATS, events = true }) {
  const isMobile = useIsMobile();
  const year = Math.floor(tickToYear(tick));
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const monthLabel = `${months[Math.min(11, Math.floor((tickToYear(tick) - year) * 12))]} ${year}`;
  const accent = CC.ink;
  // chapter diamonds + the "you are here" name — shared between both layouts
  const chapterRail = (mode === 'watch' || mode === 'prologue') && beats.map((b, k) => {
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
  });

  // Mobile: stack the transport over a full-width timeline so neither gets
  // crushed at 390px (the desktop side-by-side leaves the track ~90px wide).
  if (isMobile) {
    return (
      <div style={{ flexShrink: 0, background: CC.bg, position: 'relative', borderTop: `1px solid ${CC.border}`, padding: '11px 16px 12px', display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <BarTransport playing={playing} toggle={toggle} setTick={setTick} speed={speed} setSpeed={setSpeed} />
          <span style={{ flex: 1 }} />
          <MonoVal size={DS.type.small} color={CC.ink}>{monthLabel}</MonoVal>
        </div>
        <div style={{ position: 'relative' }}>
          {chapterRail}
          <ProtoTimeline tick={tick} setTick={setTick} color={accent} altLabels events={events} />
        </div>
      </div>);
  }

  return (
    <div style={{ height: BARH, flexShrink: 0, background: CC.bg, position: 'relative', display: 'flex', alignItems: 'center', gap: 'clamp(20px, 3vw, 44px)', padding: '0 clamp(28px, 4vw, 56px)' }}>
      <div style={{ position: 'absolute', top: 0, left: 'clamp(28px, 4vw, 56px)', right: 'clamp(28px, 4vw, 56px)', height: 1, background: CC.border }} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, flexShrink: 0, width: 224 }}>
        <BarTransport playing={playing} toggle={toggle} setTick={setTick} speed={speed} setSpeed={setSpeed} />
        <MonoVal size={DS.type.micro} color={CC.ink}>{monthLabel}</MonoVal>
      </div>
      <div style={{ flex: 1, minWidth: 0, position: 'relative' }}>
        <div style={{ marginTop: 4, position: 'relative' }}>
          {chapterRail}
          <ProtoTimeline tick={tick} setTick={setTick} color={accent} altLabels events={events} />
        </div>
      </div>
    </div>);

}

// ── Mobile guided story — one pinned compass, one scroll ─────────────────────
// The phone story unifies reading and time into a single gesture. The compass
// pins to the top and collapses from a hero to a strip as you scroll; the seven
// chapters stack into one continuous scroll, and scroll position drives `tick`
// (the playhead). It's frozen when idle — pure scroll-driven, no autodrift —
// and the ▶ plays it for you, reflecting the playhead back onto the scroll.
function MobileScrollStory({ tick, setTick, playing, toggle, setPlaying, onInterventions, onSandbox, onExplore, on3D }) {
  const wrapRef = React.useRef(null);     // measures available height
  const scroller = React.useRef(null);    // the scrolling prose column
  const secRefs = React.useRef([]);       // chapter section elements
  const anchors = React.useRef([]);       // [{ top, tick }] scroll→tick table
  const reflecting = React.useRef(false);  // guards the playhead→scroll echo
  const [vh, setVh] = React.useState(0);
  const [vw, setVw] = React.useState(390);
  const [collapse, setCollapse] = React.useState(0);  // 0 hero · 1 strip
  const [expanded, setExpanded] = React.useState(false); // tap-to-study override
  const [trans, setTrans] = React.useState(false);    // animate height only on expand/collapse

  // The compass is square: its Field box is W×W in every state, only clipped /
  // padded by the (shorter or taller) pinned container — so the density never
  // stretches. Q = the square's edge (the column width).
  const Q = vw;
  const HERO = Q;                                   // arrival shows the whole square
  const STRIP = 180;                               // collapsed peek
  const EXPANDED_H = Math.min(Math.round(vh * 0.8), Q + 60); // tap-to-study view
  const COLLAPSE_PX = Math.max(120, HERO - STRIP);
  const compassH = expanded ? EXPANDED_H : HERO - (HERO - STRIP) * collapse;

  const flashTrans = () => { setTrans(true); setTimeout(() => setTrans(false), 340); };
  const toggleExpand = () => { flashTrans(); setExpanded((e) => !e); };

  // measure the live size of the story area (header/transport excluded). A
  // ResizeObserver catches the header sliding away, not just window resizes.
  React.useLayoutEffect(() => {
    const el = wrapRef.current; if (!el) return;
    const measure = () => { setVh(el.clientHeight); setVw(el.clientWidth); };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // build the scroll→tick anchor table from each chapter's offset. The reading
  // line sits ~halfway down the hero, so a chapter "arrives" as it rises into
  // view. The trailing end-card anchors to LAST.
  const READ = HERO * 0.42;
  React.useLayoutEffect(() => {
    if (!vh) return;
    const els = secRefs.current.filter(Boolean);
    anchors.current = els.map((el, i) => ({
      top: el.offsetTop,
      tick: i < BEATS.length ? BEATS[i].tick : LAST,
    }));
  }, [vh]);

  const scrollToTick = (sT) => {
    const a = anchors.current; if (a.length < 2) return 0;
    const p = sT + READ;
    if (p <= a[0].top) return a[0].tick;
    for (let i = 0; i < a.length - 1; i++) {
      if (p >= a[i].top && p < a[i + 1].top) {
        const f = (p - a[i].top) / (a[i + 1].top - a[i].top || 1);
        return a[i].tick + (a[i + 1].tick - a[i].tick) * f;
      }
    }
    return a[a.length - 1].tick;
  };
  const tickToScroll = (tk) => {
    const a = anchors.current; if (a.length < 2) return 0;
    for (let i = 0; i < a.length - 1; i++) {
      if (tk >= a[i].tick && tk <= a[i + 1].tick && a[i + 1].tick > a[i].tick) {
        const f = (tk - a[i].tick) / (a[i + 1].tick - a[i].tick);
        return a[i].top + (a[i + 1].top - a[i].top) * f - READ;
      }
    }
    return a[a.length - 1].top - READ;
  };

  const onScroll = () => {
    const el = scroller.current; if (!el) return;
    const sT = el.scrollTop;
    setCollapse(Math.min(1, sT / COLLAPSE_PX));    // expanded study view stays put
    if (reflecting.current || playing) return;     // ignore echo / let ▶ drive
    setTick(scrollToTick(sT));
  };
  const jumpToTick = (tk) => {
    const el = scroller.current; if (!el) return;
    setPlaying(false);
    el.scrollTo({ top: Math.max(0, tickToScroll(tk)), behavior: 'smooth' });
  };

  // ▶ playback: advance the playhead (useTick) and reflect it onto the scroll
  // so the prose follows the compass. Guard against the resulting scroll event.
  React.useEffect(() => {
    if (!playing) return;
    const el = scroller.current; if (!el) return;
    const target = tickToScroll(tick);
    if (Math.abs(target - el.scrollTop) > 0.5) {
      reflecting.current = true;
      el.scrollTop = target;
      requestAnimationFrame(() => { reflecting.current = false; });
    }
  }, [tick, playing]);

  const year = Math.floor(tickToYear(tick));
  const ci = beatIndexAt(tick);
  const stripMode = !expanded && collapse > 0.5;     // collapsed peek (no chrome)
  const showFull = expanded || !stripMode;           // hero or study view → full chrome
  const tlTrans = trans ? 'height .32s ease, top .32s ease' : 'none';

  // ── chapter block (mirrors WatchRail's beat copy, minus the nav footer) ──
  const beatBlock = (beat, i) => {
    const yr = Math.floor(tickToYear(beat.tick));
    return (
      <section key={i} ref={(el) => (secRefs.current[i] = el)}
        style={{ padding: i === 0 ? '0 20px' : '34px 20px 0', marginTop: i === 0 ? 0 : 38, borderTop: i === 0 ? 'none' : `1px solid ${CC.border}` }}>
        <Eyebrow>{beat.orient ? `The U.S. story · ${yr}` : `Chapter ${i} of ${BEATS.length - 1} · ${yr}`}</Eyebrow>
        <h2 style={{ margin: '13px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: beat.orient ? 25 : 29, lineHeight: 1.05, letterSpacing: '-.022em', textWrap: 'balance' }}>{beat.title}</h2>
        <p style={{ margin: '15px 0 0', fontFamily: SERIF, fontStyle: 'italic', fontSize: DS.type.subhead, lineHeight: 1.42, color: CC.ink }}>{beat.lead}</p>
        <p style={{ margin: '15px 0 0', ...PROSE, color: CC.ink2 }}>{beat.body}</p>
        {beat.orient ? null :
          beat.data ? <BeatMetric data={beat.data} tick={beat.tick} /> :
          beat.metric ?
            <div style={{ marginTop: 22, paddingTop: 13, borderTop: `1px solid ${CC.border}`, display: 'flex', alignItems: 'center', gap: 11 }}>
              <Eyebrow style={{ color: CC.ink4, letterSpacing: '.1em' }}>data</Eyebrow>
              <MonoVal size={DS.type.small} color={CC.ink}>{beat.metric(beat.tick)}</MonoVal>
            </div> : null}
      </section>);
  };

  // ── end card (scrolls in as the final section) ──
  const endI = BEATS.length;
  const endBlock = (
    <section key="end" ref={(el) => (secRefs.current[endI] = el)}
      style={{ padding: '38px 20px 0', marginTop: 40, borderTop: `1px solid ${CC.border}` }}>
      <Eyebrow>The U.S. story · 1980 → 2025</Eyebrow>
      <h2 style={{ margin: '12px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: 29, lineHeight: 1.05, letterSpacing: '-.015em' }}>Now drive it yourself.</h2>
      <p style={{ margin: '18px 0 0', ...PROSE, color: CC.ink2 }}>You’ve just watched the engine reproduce the U.S. polarization story: an amorphous blob turning into two better-defined partisan blobs.</p>
      <p style={{ margin: '14px 0 0', ...PROSE, color: CC.ink2 }}>You might be wondering whether any of it had to play out this way, whether there is a vaccine for it. There are two ways to find out: try the things researchers have actually put to the test, or tinker with the dials yourself.</p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 22 }}>
        <div style={{ display: 'flex', gap: 10 }}>
          <button onClick={onInterventions} style={{ ...primaryBtn, flex: 1, width: 'auto' }}>Try the interventions &nbsp;→</button>
          <button onClick={onSandbox} style={{ padding: '13px 22px', borderRadius: DS.rad.pill, border: `1px solid ${CC.border}`, background: CC.surface, color: CC.ink2, cursor: 'pointer', fontFamily: SANS, fontSize: DS.type.body }}>Sandbox</button>
        </div>
        <div style={{ display: 'flex', gap: 18 }}>
          <button onClick={onExplore} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, fontFamily: SANS, fontSize: DS.type.micro, color: CC.ink3, textDecoration: 'underline', textUnderlineOffset: 3 }}>keep scrubbing this map →</button>
          <button onClick={on3D} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, fontFamily: SANS, fontSize: DS.type.micro, color: CC.ink3, textDecoration: 'underline', textUnderlineOffset: 3 }}>see it in 3-D →</button>
        </div>
      </div>
    </section>);

  return (
    <div ref={wrapRef} style={{ flex: 1, minHeight: 0, position: 'relative', background: CC.bg, overflow: 'hidden' }}>
      {/* the scrolling prose column — the only thing that actually scrolls.
          the study view stays open until the reader taps minimize. */}
      <div ref={scroller} onScroll={onScroll}
        style={{ position: 'absolute', inset: 0, overflowY: 'auto', WebkitOverflowScrolling: 'touch' }}>
        <div style={{ height: HERO + 16, flexShrink: 0 }} />
        {BEATS.map(beatBlock)}
        {endBlock}
        <div style={{ height: '60vh' }} />
      </div>

      {/* pinned compass — collapses hero → strip, never leaves the screen. The
          collapse is a center-CROP (true proportions, no squash). Always
          non-interactive so a drag scrubs time through it; the expand/minimize
          buttons keep their own pointer events. In strip mode the axis labels +
          outlet markers drop out as clutter. */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: compassH, overflow: 'hidden', background: CC.bg, pointerEvents: 'none', zIndex: 2, transition: tlTrans }}>
        <div style={{ position: 'absolute', left: (vw - Q) / 2, width: Q, height: Q, top: (compassH - Q) / 2, transition: tlTrans }}>
          <Field run={D.runs.baseline} tick={tick} layer="position" view="density" showGap landmarks={showFull ? 'fixed' : false} chrome={showFull} compact />
        </div>
        {/* fade the bottom edge so prose dissolves under the strip */}
        <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: 56, background: `linear-gradient(180deg, rgba(249,248,244,0), ${CC.bg})`, pointerEvents: 'none' }} />
        {/* expand (strip) / minimize (study view) — SVG so the glyph is crisp
            and centered; child keeps pointer events through the inert compass */}
        {(stripMode || expanded) &&
          <button onClick={(e) => { e.stopPropagation(); toggleExpand(); }} aria-label={expanded ? 'Minimize the map' : 'Expand the map'}
            style={{ position: 'absolute', right: 12, top: 10, pointerEvents: 'auto', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 32, height: 32, borderRadius: DS.rad.pill, background: 'rgba(249,248,244,.9)', border: `1px solid ${CC.border}`, color: CC.ink2, cursor: 'pointer', padding: 0 }}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              {expanded
                ? <><polyline points="9 4 9 9 4 9" /><polyline points="15 4 15 9 20 9" /><polyline points="9 20 9 15 4 15" /><polyline points="15 20 15 15 20 15" /></>
                : <><polyline points="4 9 4 4 9 4" /><polyline points="20 9 20 4 15 4" /><polyline points="4 15 4 20 9 20" /><polyline points="20 15 20 20 15 20" /></>}
            </svg>
          </button>}
      </div>

      {/* transport — ▶ plays it for you; the rail carries the chapter markers
          (the only timeline now) and the playhead, with the year readout. */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, zIndex: 4, borderTop: `1px solid ${CC.border}`, background: 'rgba(249,248,244,.94)', backdropFilter: 'blur(8px)', padding: '12px 18px', display: 'flex', alignItems: 'center', gap: 12 }}>
        <button onClick={toggle} aria-label={playing ? 'Pause' : 'Play'} style={{ width: 40, height: 40, borderRadius: DS.rad.pill, background: CC.ink, color: '#fff', border: 'none', flexShrink: 0, fontSize: 12, cursor: 'pointer' }}>{playing ? '❚❚' : '▶'}</button>
        <div style={{ flex: 1, position: 'relative', height: 16 }}>
          <div style={{ position: 'absolute', left: 0, right: 0, top: 7, height: 2, background: CC.border, borderRadius: 2 }} />
          <div style={{ position: 'absolute', left: 0, top: 7, height: 2, width: `${(tick / LAST) * 100}%`, background: CC.ink, borderRadius: 2 }} />
          {BEATS.map((b, k) => (
            <button key={k} onClick={() => jumpToTick(b.tick)} title={b.short || b.title} aria-label={b.short || b.title}
              style={{ position: 'absolute', left: `${(b.tick / LAST) * 100}%`, top: 8, transform: 'translate(-50%,-50%) rotate(45deg)', width: 8, height: 8, padding: 0, background: k <= ci ? CC.ink : CC.surface, border: `1.5px solid ${k <= ci ? CC.ink : CC.ink3}`, borderRadius: 2, cursor: 'pointer' }} />
          ))}
          <div style={{ position: 'absolute', left: `${(tick / LAST) * 100}%`, top: 8, transform: 'translate(-50%,-50%)', width: 14, height: 14, borderRadius: 999, background: '#fff', border: `3px solid ${CC.ink}`, boxShadow: '0 2px 6px rgba(26,29,35,.18)', pointerEvents: 'none' }} />
        </div>
        <MonoVal size={DS.type.small} color={CC.ink}>{year}</MonoVal>
      </div>
    </div>);
}

// hash ↔ page mapping (deep links; review amendment #8). '#model' is the
// canonical landing hash; unknown hashes fall back to the intro.
const HASH2PAGE = { '#model': 'model', '#forces': 'forces', '#prologue': 'prologue', '#story': 'story', '#playground': 'playground', '#methods': 'methods', '#about': 'about', '#3d': 'agents' };
const PAGE2HASH = { model: '#model', forces: '#forces', prologue: '#prologue', story: '#story', playground: '#playground', methods: '#methods', about: '#about', agents: '#3d' };

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
  const [hdrHidden, setHdrHidden] = React.useState(false); // mobile story: hide header on scroll-down
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
  const isMobile = useIsMobile();
  // touch scrubbing — phones have no wheel, so a vertical drag on the map band
  // moves time (swipe up = forward). The band carries `touchAction:'none'`, so
  // these read raw deltas without the page trying to scroll underneath.
  const touchRef = React.useRef(null);
  const TOUCH_SENS = 0.085;                                 // ticks advanced per px of drag

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

  // site-wide auto-hiding header: a single capture-phase scroll listener catches
  // whichever element is scrolling and hides the header on the way down, brings
  // it back on the way up. Reset to shown on every page change.
  React.useEffect(() => { setHdrHidden(false); }, [page]);
  React.useEffect(() => {
    let lastY = 0, lastT = null;
    const onScroll = (e) => {
      const el = e.target; if (!el || typeof el.scrollTop !== 'number') return;
      const y = el.scrollTop;
      if (el !== lastT) { lastT = el; lastY = y; return; }   // new scroller — just record
      if (y < 8) setHdrHidden(false);
      else if (y - lastY > 6) setHdrHidden(true);
      else if (y - lastY < -6) setHdrHidden(false);
      lastY = y;
    };
    window.addEventListener('scroll', onScroll, true);        // capture: catches nested scrollers
    return () => window.removeEventListener('scroll', onScroll, true);
  }, []);

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

  // entering the story lands on STORY_BEATS[0] — the orientation beat at tick 0
  // (a normal, navigable chapter; the old staged OrientRail is retired). Paused
  // at 1980; scroll / ▶ / "Start the story →" advance to the next beat.
  const enterStory = () => {
    setStarted(true);setOrientStep(0);setOrientSeen(true);setBeatI(0);
    setTick(0);setPaused(false);setPlaying(false);setEnded(false);setHintSeen(false);
  };
  // Self-heal: any path that lands on the story page without initialising it —
  // a deep-link/refresh on #story, or a navigation race — would leave `started`
  // false, so `inStory` is false, the copy sticks on the orientation beat, and
  // the wheel stays dead (the intermittent bug). This guarantees the story is
  // entered whenever it's shown. Fires only when not yet started.
  React.useEffect(() => {
    if (page === 'story' && !started) enterStory();
  }, [page, started]);
  // Back / Continue step discretely between chapters (for readers who'd rather
  // click than scroll); the wheel and ▶ remain the primary ways through.
  const stepBeat = (dir) => {
    setHintSeen(true);setPlaying(false);setEnded(false);
    const k = beatIndexAt(tick) + dir;
    if (dir > 0 && k >= BEATS.length) {setTick(LAST);return;}
    setTick(BEATS[Math.max(0, Math.min(BEATS.length - 1, k))].tick + 0.001);
  };
  const railContinue = () => stepBeat(1);   // phase is only ever 'beat'/'ended' on the story page
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
    if (p === 'story' && !started) {setCcFlag(CC_INTRO_SEEN);enterStory();}
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
  // the prologue ("the engine with America switched off") plays before the
  // guided story; its closing CTA routes into the story via goPage('story').
  const startPrologue = () => {
    if (morphingIntro) return;
    setCcFlag(CC_INTRO_SEEN);
    setPlaying(false);
    setPage('prologue');
  };
  const watchStory = () => {
    if (morphingIntro) return;
    setCcFlag(CC_INTRO_SEEN);
    morphCancel.current = animateIntroMorph({
      fromTick: introTick, setTick: setIntroTick, setMorphT: setIntroMorphT,
      onDone: () => {
        morphCancel.current = null;
        setSettling(true);setSettleIn(false);
        enterStory();
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
  const stagedOrient = false;   // orientation is now STORY_BEATS[0] (tick 0), a normal beat; staged OrientRail retired
  const watchReveal = null;   // staged map-build retired; the field shows in full
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

  // touch-scrub handlers for the mobile map band (no-op unless a tick is live).
  const touchScrubs = isWatch || isExplore;
  const onBandTouchStart = (e) => {
    if (!touchScrubs || e.touches.length !== 1) return;
    touchRef.current = { y: e.touches[0].clientY, tick: tickRef.current, moved: false };
  };
  const onBandTouchMove = (e) => {
    const s = touchRef.current; if (!s) return;
    const dy = s.y - e.touches[0].clientY;        // swipe up → forward
    if (!s.moved && Math.abs(dy) > 4) { s.moved = true; setHintSeen(true); setPlaying(false); }
    if (s.moved) setTick(Math.max(0, Math.min(LAST, s.tick + dy * TOUCH_SENS)));
  };
  const onBandTouchEnd = () => { touchRef.current = null; };
  const bandHandlers = isMobile && touchScrubs
    ? { onTouchStart: onBandTouchStart, onTouchMove: onBandTouchMove, onTouchEnd: onBandTouchEnd }
    : {};
  const bandTouchAction = isMobile && touchScrubs ? 'none' : undefined;

  // ── static pages (Methods / About / the demoted 3D view) ──
  if (page === 'methods' || page === 'about' || page === 'agents') {
    return (
      <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: CC.bg, minHeight: 0 }}
      onClick={(e) => {const g = e.target.closest('[data-goto]');if (g) {e.preventDefault();goPage(g.getAttribute('data-goto'));}}}>
        <SiteHeader page={page} setPage={goPage} hidden={hdrHidden} />
        {page === 'about' ? <AboutPage /> : page === 'agents' ? <Agents3DPage /> : <MethodsPage />}
      </div>);

  }

  // ── The Forces — the engine, force by force (orientation → 6 toys → finale).
  // The main act: each force is a self-contained, pokeable mini-sim. ──
  if (page === 'forces') {
    return (
      <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: CC.bg, minHeight: 0, position: 'relative' }}>
        <SiteHeader page={page} setPage={goPage} hidden={hdrHidden}
          mdMode="tour" onMdMode={(m) => goPage(m === 'engine' ? 'prologue' : 'forces')} />
        {!isMobile && <ForcesModeBar mode="tour" goPage={goPage} />}
        <ForcesTour onFinale={() => goPage('prologue')} />
      </div>);

  }

  // ── All together / the hub — every force at once, engine-alone (it stalls);
  // the two doors out: the U.S. story · the 3-D view (Playground stays in the header). ──
  if (page === 'prologue') {
    return (
      <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: CC.bg, minHeight: 0, position: 'relative' }}
      onClick={(e) => {const g = e.target.closest('[data-goto]');if (g) {e.preventDefault();goPage(g.getAttribute('data-goto'));}}}>
        <SiteHeader page={page} setPage={goPage} hidden={hdrHidden}
          mdMode="engine" onMdMode={(m) => goPage(m === 'engine' ? 'prologue' : 'forces')} />
        {!isMobile && <ForcesModeBar mode="engine" goPage={goPage} />}
        <ProloguePage onToStory={() => goPage('story')} onPlayground={() => goPlayground('interventions')} on3D={() => goPage('agents')} />
      </div>);

  }

  // ── Playground — Interventions | Sandbox (Tier-2), the model's two driving
  // modes. A separate page from the sim canvas; the workbench brings its own
  // playback surface. ──
  if (page === 'playground') {
    return (
      <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: CC.bg, minHeight: 0, position: 'relative' }}
      onClick={(e) => {const g = e.target.closest('[data-goto]');if (g) {e.preventDefault();goPage(g.getAttribute('data-goto'));}}}>
        <SiteHeader page={page} setPage={goPage} hidden={hdrHidden}
          pgMode={iv.isSandbox ? 'sandbox' : 'interventions'}
          onPgMode={(m) => { m === 'sandbox' ? iv.openSandbox() : iv.back(); }} />
        {/* the Interventions | Sandbox toggle lives in the menu now; desktop keeps
            the on-page pill for quick switching. */}
        {!isMobile &&
          <ModeBar mode={iv.isSandbox ? 'sandbox' : 'interventions'} setMode={(m) => {m === 'sandbox' ? iv.openSandbox() : iv.back();}} />}
        <IvWorkbench iv={iv} layer={layer} />
      </div>);

  }

  // ── mobile guided story — the collapsing header (site-wide) gives the compass
  // the full screen height as you scroll. ──
  if (isMobile && isWatch && !stagedOrient) {
    return (
      <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: CC.bg, minHeight: 0 }}>
        <SiteHeader page={page} setPage={goPage} hidden={hdrHidden} />
        <MobileScrollStory tick={tick} setTick={setTick} playing={playing} toggle={toggle} setPlaying={setPlaying}
          onInterventions={() => goPlayground('interventions')} onSandbox={() => goPlayground('sandbox')}
          onExplore={goExplore} on3D={() => goPage('agents')} />
      </div>);
  }

  // ── the simulation surface — one canvas, two labels (model = Act 0 intro,
  // story = the guided chapters / unlocked explore) ──
  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: CC.bg, minHeight: 0, position: 'relative' }}>
      <SiteHeader page={page} setPage={goPage} hidden={hdrHidden} />

      {isMobile ? (
        /* ── mobile intro + unlocked explore: map band on top (swipe to scrub),
           rail beneath. The guided story has its own surface above. ── */
        <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', background: CC.bg, overflow: 'hidden' }}>
          <div {...bandHandlers} style={{ position: 'relative', height: isIntro ? '46%' : '40%', flexShrink: 0, overflow: 'hidden', borderBottom: `1px solid ${CC.border}`, touchAction: bandTouchAction }}>
            <div style={{ position: 'absolute', inset: 0 }}>
              {isIntro ?
              <Field run={D.runs.baseline} tick={introTick} layer="position" view="dots" morphT={introMorphT} showGap={false} landmarks={false} /> :
              <Field run={D.runs.baseline} tick={tick} layer="position" view="density" showGap dim={dimField} reveal={watchReveal} landmarks={isExplore && showLandmarks ? 'all' : 'fixed'} />}
            </div>
            {isExplore &&
            <button onClick={() => setShowLandmarks((v) => !v)} style={{
              position: 'absolute', right: 14, top: 12, display: 'inline-flex', alignItems: 'center', gap: 7,
              fontFamily: SANS, fontSize: DS.type.micro, fontWeight: 500, cursor: 'pointer',
              color: showLandmarks ? CC.ink : CC.ink3, background: showLandmarks ? 'transparent' : 'rgba(249,248,244,.8)',
              padding: '6px 11px', borderRadius: DS.rad.pill, border: `1px solid ${showLandmarks ? CC.ink : CC.border}`
            }}>
              <span style={{ width: 7, height: 7, borderRadius: 2, background: showLandmarks ? CC.ink : 'transparent', border: `1.5px solid ${showLandmarks ? CC.ink : CC.ink4}` }} />
              {showLandmarks ? 'Parties on' : 'Show parties'}
            </button>}
            {showHint &&
            <div style={{ position: 'absolute', left: 0, right: 0, bottom: 12, display: 'flex', justifyContent: 'center', pointerEvents: 'none' }}>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: 9, padding: '8px 15px', background: CC.ink, color: '#fff', borderRadius: DS.rad.pill, boxShadow: '0 6px 20px rgba(26,29,35,.22)', fontFamily: SANS, fontSize: 12.5, fontWeight: 500, animation: 'ccFadeUp .55s ease both' }}>
                <span style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', lineHeight: 0.5, animation: 'ccHintBob 1.5s ease-in-out infinite' }}>
                  <span style={{ fontSize: 9 }}>⌃</span><span style={{ fontSize: 9 }}>⌄</span>
                </span>
                Swipe the map to move through time
              </div>
            </div>}
            {settling &&
            <div style={{ position: 'absolute', inset: 0, zIndex: 6, pointerEvents: 'none', background: CC.bg, overflow: 'hidden', opacity: settleFrom ? 1 : 0, transition: 'opacity 1s ease' }}>
              <div style={{ position: 'absolute', inset: 0 }}>
                <Field run={D.runs.baseline} tick={0} layer="position" view="density" showGap={false} />
              </div>
            </div>}
          </div>
          <div style={{ flex: 1, minHeight: 0, overflow: 'auto', position: 'relative' }}>
            {isIntro &&
              <IntroRail tick={introTick} storyDone={storyDone} onWatch={() => goPage('forces')}
                onSandbox={() => goPlayground('sandbox')} onAbout={() => goPage('about')} on3D={() => goPage('agents')} />}
            {isWatch && (stagedOrient ?
              <OrientRail step={orientStep} onPrev={orientPrev} onNext={orientNext} onContinue={finishOrient} /> :
              <WatchRail phase={phase} beat={beat} beatI={dispBeatI} total={BEATS.length} nextBeat={BEATS.find((b) => b.tick > tick) || null} tick={tick} onBack={() => stepBeat(-1)} onContinue={railContinue} onExplore={goExplore}
                onInterventions={() => goPlayground('interventions')} onSandbox={() => goPlayground('sandbox')} on3D={() => goPage('agents')} />)}
            {isExplore && <ExploreRail tick={tick} onBackToStory={() => {setUnlocked(false);setPlaying(false);}} />}
          </div>
        </div>
      ) : (
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
              <IntroRail tick={introTick} storyDone={storyDone} onWatch={() => goPage('forces')}
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
      )}

      {/* bottom bar — the story's transport + chapter rail. The intro drives
          itself (ambient loop), and the mobile scroll-story carries its own
          transport, so neither shows the shared bar. */}
      {isIntro || (isMobile && isWatch && !stagedOrient) ? null :

      <TimelineBar tick={tick} setTick={setTick} playing={playing} toggle={toggle} speed={speed} setSpeed={setSpeed}
      mode={isWatch ? 'watch' : 'explore'} beatI={dispBeatI} onPickBeat={pickBeat} ended={ended} events={!isWatch} />
      }

      {/* first-run helper — black, gently bobbing, dismissed on the first scroll
          or play. Tells the reader the two ways through the story. (Mobile shows
          its own swipe hint inside the map band.) */}
      {showHint && !isMobile &&
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
