// Calm to Camps — PROLOGUE: "the engine, on its own" (plays BEFORE the US story).
//
// Same surface format as the guided story: a full compass field on the right,
// floating editorial copy on the left, the shared TimelineBar at the bottom,
// wheel / scrub through 45 simulated years. It just drives the FREE-FLOWING run
// (window.CC_FREEFLOW) instead of the US baseline, and carries no dated events.
//
// The framing is ENGINE-FIRST and presupposes nothing about America:
//   beats   meet the engine + NAME its forces → watch 45 years of pure mechanism
//           (it cools, the split stalls). No US, no events, no calendar shocks.
//   end     "these forces alone aren't enough" — NOW compare to a country that
//           actually polarized (the US): the feelings match, the split doesn't;
//           the gap is external shocks. CTA → the real story.
//
// Honesty: the animated cloud is one representative run (seed 0); the comparison
// LINES are the 6-seed mean (CC_FREEFLOW.run.macro_mean), matching the Methods
// honesty budget. An illustrative counterfactual, not a second "result".

const FF = window.CC_FREEFLOW || null;
const _FF_OK = !!(FF && FF.run && FF.run.pos);
const _PLX = RAIL_LX;   // shared trimmed indent (rc-shared)

// inline prose link — routes via the prologue page wrapper's data-goto handler
// (cc-unified). `goto` is a page id ('forces' / 'methods'). Defined BEFORE
// PROLOGUE_BEATS because the beat bodies reference it at array-build time.
const _PLink = ({ goto, children }) => (
  <button data-goto={goto} style={{ background: 'none', border: 'none', padding: 0, fontFamily: 'inherit', fontSize: 'inherit', color: CC.ink, fontWeight: 500, textDecoration: 'underline', textUnderlineOffset: 2, cursor: 'pointer' }}>{children}</button>
);

// engine-first chapters (tick-anchored, like STORY_BEATS) — no America, no events.
const PROLOGUE_BEATS = [
  { tick: 0, short: 'The engine', title: 'The engine, on its own',
    lead: 'All the forces at once.',
    body: (
      <>
        Same dots-as-people you've just seen, but now rendered as density clouds - the more people in a given area the denser the cloud there. This way it's easier to spot the trends. On the forces tour you switched the mechanisms on one at a time. Here they all run together — the ones you've seen and a handful more (things like cohort replacement and so on; all laid out in the <_PLink goto="methods">Methods</_PLink>). No external data is fed in here — only the forces themselves. The mechanism is general in form, applicable in principle to any democratic country, with its strengths fit to the U.S. Here you can scrub through 45 years of engine running and see where these fundamental forces take the society on their own. (On the map: navy and oxblood are the two parties and the dashed line measures the gap between them.)
      </>
    ) },
  { tick: 48, short: 'It cools', title: 'On its own, it pulls apart',
    lead: 'Left alone, does anything happen? Something does.',
    body: 'Warmth toward the other side drains away steadily, and the two leanings do pull a little apart. The mechanism manages this much by itself, with nothing fed in from the outside world.' },
  { tick: 96, short: 'It stalls', title: 'But then it stalls',
    lead: 'And here is about as far as the bare forces reach.',
    body: 'From this point onwards the split flattens out, it even slips back a tad. Though the feelings keep cooling, the positions settle into a sort of optimum. Society never hardens into two genuinely separate worlds. That\'s roughly as far as forty-five years of engine-only forces can take us. But is it enough to model the real-world situation? Scrub to the end - the answer might surprise you.*', footnote: '* click-bait used exclusively ironically' },
];
const _pBeat = (t) => {
  let i = 0;
  for (let k = 0; k < PROLOGUE_BEATS.length; k++) if (PROLOGUE_BEATS[k].tick <= t + 1e-6) i = k;
  return i;
};

// One chart, two modes — used for BOTH the per-chapter scrub sparklines and the
// end-card comparison, so they share width + editorial chrome (title · readout ·
// sub · ~2000 marker · 1980–2025 axis).
//   compare mode: pass us + ff   → US solid vs engine dashed, readout "x vs y".
//   scrub mode:   pass series + tick → engine traced solid up to a moving dot,
//                 the un-traced tail faint, readout = the value at the dot.
function PChart({ title, sub, deg = false, width = 470, height = 132, us, ff, series, tick, marker = false }) {
  const padL = 30, padR = 12, padT = 12, padB = 20;
  const plotW = width - padL - padR, plotH = height - padT - padB;
  const xf = deg ? (v) => (1 + v) * 50 + 12 : (v) => v;
  const scrub = series != null;
  const lines = scrub ? [series.map(xf)] : [us.map(xf), ff.map(xf)];
  let lo = Infinity, hi = -Infinity;
  for (const L of lines) for (const v of L) { if (v < lo) lo = v; if (v > hi) hi = v; }
  const pad = (hi - lo) * 0.12 || 0.05; lo -= pad; hi += pad;
  const X = (t) => padL + (t / LAST) * plotW;
  const Y = (v) => padT + plotH - ((v - lo) / (hi - lo || 1)) * plotH;
  const path = (arr, n) => arr.slice(0, n == null ? arr.length : n + 1)
    .map((v, t) => `${t ? 'L' : 'M'}${X(t).toFixed(1)},${Y(v).toFixed(1)}`).join(' ');
  const fmt = (v) => deg ? `${Math.round(v)}°` : v.toFixed(2);
  const TDIV = 90;   // ~2010 — the arc lifts off the engine just after here (sep gap triples 2010→2011; 2011 is the first divergent point)
  const ti = scrub ? Math.max(0, Math.min(LAST, Math.round(tick))) : null;
  const readout = scrub
    ? fmt(lines[0][ti])
    : <>{fmt(lines[0][LAST])} <span style={{ color: CC.ink4 }}>vs</span> {fmt(lines[1][LAST])}</>;
  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
        <span style={{ fontFamily: SANS, fontSize: DS.type.small, fontWeight: 600, color: CC.ink }}>{title}</span>
        <span style={{ fontFamily: MONO, fontSize: DS.type.micro, color: CC.ink3, ...TNUM }}>{readout}</span>
      </div>
      {sub && <div style={{ fontSize: DS.type.micro, color: CC.ink3, marginTop: 2 }}>{sub}</div>}
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={height} preserveAspectRatio="xMidYMid meet" style={{ display: 'block', marginTop: 5 }}>
        {marker && <line x1={X(TDIV)} y1={padT} x2={X(TDIV)} y2={padT + plotH} stroke={CC.ink4} strokeWidth="1" strokeDasharray="1 3" />}
        {marker && <text x={X(TDIV) + 3} y={padT + 8} style={{ fontFamily: MONO, fontSize: 8.5, fill: CC.ink4 }}>~2010</text>}
        {scrub ? [
          <path key="full" d={path(lines[0])} fill="none" stroke={CC.ink4} strokeWidth="1.2" opacity="0.45" strokeLinejoin="round" strokeLinecap="round" />,
          <path key="trace" d={path(lines[0], ti)} fill="none" stroke={CC.ink} strokeWidth="2.4" strokeLinejoin="round" strokeLinecap="round" />,
          <circle key="dot" cx={X(ti)} cy={Y(lines[0][ti])} r="4" fill={CC.ink} stroke="#fff" strokeWidth="1.6" />,
        ] : [
          <path key="ff" d={path(lines[1])} fill="none" stroke={CC.ink3} strokeWidth="2" strokeDasharray="5 4" strokeLinejoin="round" strokeLinecap="round" />,
          <path key="us" d={path(lines[0])} fill="none" stroke={CC.ink} strokeWidth="2.4" strokeLinejoin="round" strokeLinecap="round" />,
        ]}
        <text x={padL} y={height - 5} style={{ fontFamily: SANS, fontSize: 9, fill: CC.ink4 }}>1980</text>
        <text x={width - padR} y={height - 5} textAnchor="end" style={{ fontFamily: SANS, fontSize: 9, fill: CC.ink4 }}>2025</text>
      </svg>
    </div>
  );
}
function CompareLegend() {
  return (
    <div style={{ display: 'flex', gap: 18, fontSize: DS.type.micro, color: CC.ink3, marginTop: 6, flexWrap: 'wrap' }}>
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}>
        <span style={{ width: 18, height: 0, borderTop: `2.4px solid ${CC.ink}` }} /> a real country that polarized (the US)
      </span>
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}>
        <span style={{ width: 18, height: 0, borderTop: `2px dashed ${CC.ink3}` }} /> the engine alone
      </span>
    </div>
  );
}

const _skipStyle = { background: 'none', border: 'none', cursor: 'pointer', fontFamily: SANS, fontSize: DS.type.micro, color: CC.ink3, textDecoration: 'underline', textUnderlineOffset: 3, whiteSpace: 'nowrap' };

// the scrub-chapter rail (matches the story's floating left copy)
function PrologueBeatRail({ beat, tick, year, onSkip }) {
  const isMobile = useIsMobile();
  const affSeries = FF.run.macro.map((m) => m.aff);
  const sepSeries = FF.run.macro.map((m) => m.sep);
  return (
    <div style={{ background: 'transparent', display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, justifyContent: isMobile ? 'flex-start' : 'safe center', overflow: 'auto' }}>
      <div style={{ flexShrink: 0, padding: isMobile ? '22px 20px 8px 20px' : `clamp(18px,3vh,44px) 44px 8px ${_PLX}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 12 }}>
          <Eyebrow>The engine, on its own</Eyebrow>
          {onSkip && <button onClick={onSkip} style={_skipStyle}>skip ahead →</button>}
        </div>
        <h2 style={{ margin: '10px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: isMobile ? 27 : 'clamp(30px, 4vh, 40px)', lineHeight: 1.05, letterSpacing: '-.018em', maxWidth: TEXTW }}>{beat.title}</h2>
        <p style={{ margin: '12px 0 0', fontFamily: SERIF, fontStyle: 'italic', fontSize: DS.type.subhead, lineHeight: 1.42, color: CC.ink, maxWidth: TEXTW }}>{beat.lead}</p>
        <p style={{ margin: '12px 0 0', ...PROSE, color: CC.ink2, maxWidth: TEXTW }}>{beat.body}</p>
        {/* the "engine so far" readouts run side-by-side (they'd be too tall stacked
            on a short screen) and only appear past the long intro beat, where they
            actually show a trend — at the 1980 start they're flat. */}
        {beat.tick > 0 &&
        <div style={{ marginTop: 14, maxWidth: TEXTW }}>
          <Eyebrow style={{ color: CC.ink3 }}>The engine, so far · {year}</Eyebrow>
          <div style={{ display: 'flex', gap: 18, marginTop: 2 }}>
            <div style={{ flex: 1, minWidth: 0 }}><PChart title="Out-party warmth" sub="cools on its own" series={affSeries} tick={tick} deg width={320} height={104} /></div>
            <div style={{ flex: 1, minWidth: 0 }}><PChart title="Party separation" sub="drifts, then stalls" series={sepSeries} tick={tick} width={320} height={104} /></div>
          </div>
          {beat.footnote && <p style={{ margin: '12px 0 0', fontSize: DS.type.micro, lineHeight: 1.4, color: CC.ink4, fontStyle: 'italic' }}>{beat.footnote}</p>}
        </div>}
      </div>
    </div>
  );
}

// the closing rail — every force at once (engine-alone) hits its ceiling;
// the comparison to a real country, and the two doors out: the U.S. story · the 3-D view.
function PrologueEndRail({ usArr, ffArr, onToStory, onPlayground, on3D, scrollRef }) {
  const doorAlt = {
    flex: 1, padding: '12px 14px', borderRadius: DS.rad.pill, border: `1px solid ${CC.border}`, background: CC.surface,
    color: CC.ink2, cursor: 'pointer', fontFamily: SANS, fontSize: DS.type.small, fontWeight: 500, whiteSpace: 'nowrap',
  };
  const isMobile = useIsMobile();
  return (
    <div ref={scrollRef} style={{ background: 'transparent', display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, justifyContent: isMobile ? 'flex-start' : 'safe center', overflow: 'auto' }}>
      <div style={{ flexShrink: 0, padding: isMobile ? '22px 20px 8px 20px' : `clamp(16px,2.6vh,40px) 44px 8px ${_PLX}` }}>
        <Eyebrow>The engine · every force at once</Eyebrow>
        <h2 style={{ margin: '10px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: isMobile ? 27 : 'clamp(26px, 3.4vh, 38px)', lineHeight: 1.05, letterSpacing: '-.018em', maxWidth: TEXTW }}>The forces alone do not get us all the way</h2>
        <p style={{ margin: '10px 0 0', fontFamily: SERIF, fontStyle: 'italic', fontSize: DS.type.subhead, lineHeight: 1.4, color: CC.ink, maxWidth: TEXTW }}>Compare the in-engine polarization against a country that <em>did</em> polarize — the United States.</p>
        <p style={{ margin: '10px 0 0', ...PROSE, color: CC.ink2, maxWidth: TEXTW }}>
          So how far does the bare engine reach? On the <strong>feelings</strong>, pretty far — north of 80 percent. The engine-only line and the real one nearly meet, suggesting that animus can be modeled largely from quite fundamental psychological forces.
        </p>
        <p style={{ margin: '10px 0 0', ...PROSE, color: CC.ink2, maxWidth: TEXTW }}>
          The <strong>position split</strong> is a different story. Alone, the engine reaches only about a third of it, tracking the data well until c. 2010 but then stalling while the real split climbs rapidly. This sharp rise is caused by external factors (<strong>forcings</strong>) that are switched off in this view: the build-up of partisan media, momentous events, the timing of who mobilized when. The engine supplies the forces; history supplies the rest.
        </p>
        <div style={{ marginTop: 12, maxWidth: TEXTW }}>
          <div style={{ display: 'flex', gap: 18 }}>
            <div style={{ flex: 1, minWidth: 0 }}><PChart title="Party separation — the split" sub="tracks, then peels away after ~2010" us={usArr('sep')} ff={ffArr('sep')} marker width={320} height={104} /></div>
            <div style={{ flex: 1, minWidth: 0 }}><PChart title="Out-party warmth — the feelings" sub="close, not identical" us={usArr('aff')} ff={ffArr('aff')} deg marker width={320} height={104} /></div>
          </div>
          <CompareLegend />
        </div>
        <div style={{ marginTop: 14, maxWidth: TEXTW }}>
          <Eyebrow style={{ color: CC.ink3 }}>Where to next</Eyebrow>
          <button onClick={onToStory} style={{ marginTop: 10, width: '100%', padding: '13px 18px', borderRadius: DS.rad.pill, border: 'none', background: CC.ink, color: '#fff', cursor: 'pointer', fontFamily: SANS, fontSize: 14, fontWeight: 500 }}>
            See what actually happened in the U.S. →
          </button>
          <div style={{ marginTop: 10, marginBottom: 12, display: 'flex', gap: 10 }}>
            <button onClick={on3D} style={doorAlt}>See the engine in three dimensions →</button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ProloguePage({ onToStory, onPlayground, on3D }) {
  const [tick, setTick] = React.useState(0);
  const [playing, setPlaying] = React.useState(false);
  const [speed, setSpeed] = React.useState(1);
  const [hintSeen, setHintSeen] = React.useState(false);   // first scrub-timeline they meet
  const isMobile = useIsMobile();
  const toggle = () => { setHintSeen(true); setPlaying((p) => !p); };
  const skipToEnd = () => { setPlaying(false); setTick(LAST); };
  const wrapRef = React.useRef(null);
  const endRailRef = React.useRef(null);   // the terminal end-card scroller (it's too dense to fit short)
  const endedRef = React.useRef(false);    // when ended, wheel scrolls that card instead of scrubbing
  const raf = React.useRef(0);
  // touch-scrub: phones have no wheel, so a vertical drag on the map band moves
  // time (swipe up = forward), mirroring the story canvas.
  const touchRef = React.useRef(null);
  const onBandTouchStart = (e) => { if (e.touches.length === 1) touchRef.current = { y: e.touches[0].clientY, tick, moved: false }; };
  const onBandTouchMove = (e) => {
    const s = touchRef.current; if (!s) return;
    const dy = s.y - e.touches[0].clientY;
    if (!s.moved && Math.abs(dy) > 4) { s.moved = true; setHintSeen(true); setPlaying(false); }
    if (s.moved) setTick(Math.max(0, Math.min(LAST, s.tick + dy * 0.085)));
  };
  const onBandTouchEnd = () => { touchRef.current = null; };

  // play loop (RAF — paused headlessly; the timeline + wheel are the deterministic paths)
  React.useEffect(() => {
    if (!playing) return;
    let last = null;
    const step = (ts) => {
      if (last == null) last = ts;
      const dt = (ts - last) / 1000; last = ts;
      setTick((p) => { const n = p + dt * 3 * speed; if (n >= LAST) { setPlaying(false); return LAST; } return n; });
      raf.current = requestAnimationFrame(step);
    };
    raf.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf.current);
  }, [playing, speed]);

  // wheel-scrub through time (parity with the story's scroll-to-move-time)
  React.useEffect(() => {
    const el = wrapRef.current; if (!el) return;
    const onWheel = (e) => {
      // beats scrub cleanly (no scroll). On the terminal end card — which is too
      // dense to fit a short screen and where there's nothing left to scrub — the
      // wheel scrolls the card instead; scrubbing back only at its very top.
      const sc = endRailRef.current;
      if (endedRef.current && sc && sc.contains(e.target) && sc.scrollHeight > sc.clientHeight + 1) {
        const atTop = sc.scrollTop <= 0;
        if (!(e.deltaY < 0 && atTop)) return;
      }
      e.preventDefault(); setHintSeen(true); setPlaying(false); setTick((t) => Math.max(0, Math.min(LAST, t + e.deltaY * 0.06)));
    };
    el.addEventListener('wheel', onWheel, { passive: false });
    return () => el.removeEventListener('wheel', onWheel);
  }, []);

  if (!_FF_OK) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: CC.ink3, fontFamily: SANS, fontSize: 14 }}>
        Free-flowing run not loaded (cc-freeflow.js). Run scripts/build_freeflow_data.py.
      </div>
    );
  }

  const run = FF.run;
  const ended = tick >= LAST - 1e-6;
  endedRef.current = ended;
  const showHint = !hintSeen && !playing && !ended && tick < 1.5;   // first-run scrub helper
  const beatI = _pBeat(tick);
  const beat = PROLOGUE_BEATS[beatI];
  const sep = macroAt(run, tick, 'sep');
  const deg = Math.round((1 + macroAt(run, tick, 'aff')) * 50 + 12);
  const year = Math.floor(1980 + tick / 3);
  const usArr = (k) => D.runs.baseline.macro.map((m) => m[k]);
  const ffArr = (k) => run.macro_mean.map((m) => m[k]);

  if (isMobile) {
    // the whole-engine page rides the story's pinned-compass shell: scroll the
    // engine chapters → drives time; tap-to-expand the map; one bottom timeline.
    const affSeries = FF.run.macro.map((m) => m.aff);
    const sepSeries = FF.run.macro.map((m) => m.sep);
    // liveTick is the scroll-driven tick MobileScrollStory feeds each section (the
    // same one driving the compass), so the sparklines animate with the scroll
    // instead of sitting frozen at the chapter's anchor. Falls back to beat.tick.
    const renderBeat = (beat, i, liveTick = beat.tick) => {
      const yr = Math.floor(1980 + liveTick / 3);
      return (<>
        <Eyebrow>The engine, on its own · {yr}</Eyebrow>
        <h2 style={{ margin: '13px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: 27, lineHeight: 1.05, letterSpacing: '-.02em', textWrap: 'balance' }}>{beat.title}</h2>
        <p style={{ margin: '15px 0 0', fontFamily: SERIF, fontStyle: 'italic', fontSize: DS.type.subhead, lineHeight: 1.42, color: CC.ink }}>{beat.lead}</p>
        <p style={{ margin: '15px 0 0', ...PROSE, color: CC.ink2 }}>{beat.body}</p>
        <div style={{ marginTop: 22, paddingTop: 16, borderTop: `1px solid ${CC.border}` }}>
          <Eyebrow style={{ color: CC.ink3 }}>The engine, so far · {yr}</Eyebrow>
          <PChart title="Out-party warmth" sub="cools on its own" series={affSeries} tick={liveTick} deg />
          <PChart title="Party separation" sub="drifts, then stalls" series={sepSeries} tick={liveTick} />
          {beat.footnote && <p style={{ margin: '12px 0 0', fontSize: DS.type.micro, lineHeight: 1.4, color: CC.ink4, fontStyle: 'italic' }}>{beat.footnote}</p>}
        </div>
      </>);
    };
    const endContent = (<>
      <Eyebrow>The engine · every force at once</Eyebrow>
      <h2 style={{ margin: '12px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: 27, lineHeight: 1.05, letterSpacing: '-.018em', textWrap: 'balance' }}>The forces alone do not get us all the way</h2>
      <p style={{ margin: '14px 0 0', fontFamily: SERIF, fontStyle: 'italic', fontSize: DS.type.subhead, lineHeight: 1.4, color: CC.ink }}>Compare the in-engine polarization against a country that <em>did</em> polarize — the United States.</p>
      <p style={{ margin: '14px 0 0', ...PROSE, color: CC.ink2 }}>So how far does the bare engine reach? On the <strong>feelings</strong>, pretty far — north of 80 percent. The engine-only line and the real one nearly meet, suggesting that animus can be modeled largely from quite fundamental psychological forces.</p>
      <p style={{ margin: '12px 0 0', ...PROSE, color: CC.ink2 }}>The <strong>position split</strong> is a different story. Alone, the engine reaches only about a third of it, tracking the data well until c. 2010 but then stalling while the real split climbs rapidly. This sharp rise is caused by external <strong>forcings</strong> switched off in this view: the build-up of partisan media, momentous events, the timing of who mobilized when. The engine supplies the forces; history supplies the rest.</p>
      <div style={{ marginTop: 18 }}>
        <PChart title="Party separation — the split" sub="tracks for a while, then peels away after ~2010" us={usArr('sep')} ff={ffArr('sep')} marker />
        <PChart title="Out-party warmth — the feelings" sub="close, not identical — the engine cools mostly on its own" us={usArr('aff')} ff={ffArr('aff')} deg marker />
        <CompareLegend />
      </div>
      <div style={{ marginTop: 22 }}>
        <Eyebrow style={{ color: CC.ink3 }}>Where to next</Eyebrow>
        <button onClick={onToStory} style={{ marginTop: 10, width: '100%', padding: '14px 18px', borderRadius: DS.rad.pill, border: 'none', background: CC.ink, color: '#fff', cursor: 'pointer', fontFamily: SANS, fontSize: 14, fontWeight: 500 }}>See what actually happened in the U.S. →</button>
        <button onClick={on3D} style={{ marginTop: 10, width: '100%', padding: '13px 14px', borderRadius: DS.rad.pill, border: `1px solid ${CC.border}`, background: CC.surface, color: CC.ink2, cursor: 'pointer', fontFamily: SANS, fontSize: DS.type.small, fontWeight: 500 }}>See the engine in three dimensions →</button>
      </div>
    </>);
    return (
      <MobileScrollStory
        tick={tick} setTick={setTick} playing={playing} toggle={toggle} setPlaying={setPlaying}
        beats={PROLOGUE_BEATS} run={run} landmarks={false} beatIndexAtFn={_pBeat}
        renderBeat={renderBeat} endContent={endContent} on3D={on3D} />
    );
  }

  return (
    <>
      <div ref={wrapRef} style={{ flex: 1, minHeight: 0, position: 'relative', overflow: 'hidden', background: CC.bg }}>
        {/* the compass — same geometry as the story surface; NO entity landmarks */}
        <div style={{ position: 'absolute', top: '-2%', bottom: '-2%', right: '2%', aspectRatio: '1' }}>
          <Field run={run} tick={tick} layer="position" view="density" showGap dim={ended ? 0.24 : 0} landmarks={false} />
        </div>
        {/* paper scrim — keeps the floating prose legible */}
        <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, width: '56%', background: `linear-gradient(90deg, ${CC.bg} 0%, ${CC.bg} 88%, rgba(249,248,244,0) 100%)`, pointerEvents: 'none', zIndex: 1 }} />
        {/* floating narrative — same left column as the story */}
        <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, width: RAIL_W, display: 'flex', flexDirection: 'column', minHeight: 0, zIndex: 3 }}>
          {ended
            ? <PrologueEndRail usArr={usArr} ffArr={ffArr} onToStory={onToStory} onPlayground={onPlayground} on3D={on3D} scrollRef={endRailRef} />
            : <PrologueBeatRail beat={beat} tick={tick} year={year} onSkip={skipToEnd} />}
        </div>
        {/* first-run helper — the scrub timeline is new here; same pill as the story */}
        {showHint &&
        <div style={{ position: 'absolute', left: 0, right: 0, bottom: 20, zIndex: 8, display: 'flex', justifyContent: 'center', pointerEvents: 'none' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 7, animation: 'ccFadeUp .55s ease both' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '10px 18px', background: CC.ink, color: '#fff', borderRadius: DS.rad.pill, boxShadow: '0 8px 26px rgba(26,29,35,.22)', fontFamily: SANS, fontSize: 14, fontWeight: 500, letterSpacing: '-.005em' }}>
              <span style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', lineHeight: 0.62, animation: 'ccHintBob 1.5s ease-in-out infinite' }}>
                <span style={{ fontSize: 10 }}>⌃</span><span style={{ fontSize: 10 }}>⌄</span>
              </span>
              Scroll to move through time
            </div>
            <span style={{ fontSize: 13, color: CC.ink3, fontFamily: SANS }}>or press <span style={{ color: CC.ink2, fontWeight: 600 }}>▶</span> to play it for you</span>
          </div>
        </div>}
      </div>
      {/* the shared bottom transport + chapter rail */}
      <TimelineBar tick={tick} setTick={setTick} playing={playing} toggle={toggle} speed={speed} setSpeed={setSpeed}
        mode="prologue" beatI={beatI} onPickBeat={(k) => { setPlaying(false); setTick(PROLOGUE_BEATS[k].tick); }} ended={ended} beats={PROLOGUE_BEATS} events={false} />
    </>
  );
}

window.ProloguePage = ProloguePage;
