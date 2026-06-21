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
const _PLX = 'clamp(64px, 14vw, 248px)';

// engine-first chapters (tick-anchored, like STORY_BEATS) — no America, no events.
const PROLOGUE_BEATS = [
  { tick: 0, short: 'The engine', title: 'Meet the engine',
    lead: 'Start with the bare machine — its rules, running on nothing but themselves.',
    body: '250 simulated people, each a point on the compass and a node in a web of social ties. A handful of mechanisms from the polarization research move them: they drift toward the neighbours they’re close enough to actually hear (bounded-confidence influence); they lean toward their own side; their feeling toward the other side updates with every interaction — and can harden into backlash as readily as it eases; and the network itself slowly re-sorts, so people end up tied to the like-minded (homophily). Most are anchored and barely move; a restless few drift freely. There’s no partisan-media build-up, no elite prising the parties apart, no events — those are the historical forces, and here they’re switched off. This is just the mechanics, from a calm start. Scrub through 45 years. (On the map: the two parties show as navy and oxblood, grey is where they overlap, and the dashed line tracks the gap between them.)' },
  { tick: 48, short: 'It cools', title: 'On its own, it cools',
    lead: 'Left to themselves, the forces do something — but not everything.',
    body: 'Warmth toward the other side drains away, steadily, and the two leanings pull a little apart. This much the mechanism produces all by itself, with no help from the outside world.' },
  { tick: 96, short: 'It stalls', title: '…then it stalls',
    lead: 'And here is the ceiling of pure mechanism.',
    body: 'The split plateaus — it never hardens into two separate worlds, and it even drifts back a touch. The feelings keep cooling, but the positions settle. Forty-five years of nothing-but-forces land about here. Scrub to the end to see what that misses.' },
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
  const affSeries = FF.run.macro.map((m) => m.aff);
  const sepSeries = FF.run.macro.map((m) => m.sep);
  return (
    <div style={{ background: 'transparent', display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, justifyContent: 'safe center', overflow: 'auto' }}>
      <div style={{ flexShrink: 0, padding: `clamp(28px,4.5vh,52px) 44px 8px ${_PLX}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 12 }}>
          <Eyebrow>Prologue · the engine alone</Eyebrow>
          {onSkip && <button onClick={onSkip} style={_skipStyle}>skip ahead →</button>}
        </div>
        <h2 style={{ margin: '14px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: 'clamp(28px,3.2vw,40px)', lineHeight: 1.05, letterSpacing: '-.018em', maxWidth: 460 }}>{beat.title}</h2>
        <p style={{ margin: '16px 0 0', fontFamily: SERIF, fontStyle: 'italic', fontSize: DS.type.subhead, lineHeight: 1.42, color: CC.ink, maxWidth: 460 }}>{beat.lead}</p>
        <p style={{ margin: '16px 0 0', ...PROSE, color: CC.ink2, maxWidth: 470 }}>{beat.body}</p>
        <div style={{ marginTop: 24, maxWidth: 480 }}>
          <Eyebrow style={{ color: CC.ink3 }}>The engine, so far · {year}</Eyebrow>
          <PChart title="Out-party warmth" sub="cools on its own" series={affSeries} tick={tick} deg />
          <PChart title="Party separation" sub="drifts, then stalls" series={sepSeries} tick={tick} />
        </div>
      </div>
    </div>
  );
}

// the closing rail — all six forces at once (engine-alone) hit their ceiling;
// the comparison to a real country, and the three doors out of the tour.
function PrologueEndRail({ usArr, ffArr, onToStory, onPlayground, on3D }) {
  const doorAlt = {
    flex: 1, padding: '12px 14px', borderRadius: DS.rad.pill, border: `1px solid ${CC.border}`, background: CC.surface,
    color: CC.ink2, cursor: 'pointer', fontFamily: SANS, fontSize: DS.type.small, fontWeight: 500, whiteSpace: 'nowrap',
  };
  return (
    <div style={{ background: 'transparent', display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, justifyContent: 'safe center', overflow: 'auto' }}>
      <div style={{ flexShrink: 0, padding: `clamp(24px,4vh,44px) 44px 8px ${_PLX}` }}>
        <Eyebrow>The engine · all six forces, together</Eyebrow>
        <h2 style={{ margin: '12px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: 'clamp(26px,3vw,38px)', lineHeight: 1.05, letterSpacing: '-.018em', maxWidth: 460 }}>These forces alone aren’t enough</h2>
        <p style={{ margin: '14px 0 0', fontFamily: SERIF, fontStyle: 'italic', fontSize: DS.type.subhead, lineHeight: 1.4, color: CC.ink, maxWidth: 460 }}>Run the same mechanism against a country that actually polarized — say, the United States.</p>
        <p style={{ margin: '14px 0 0', ...PROSE, color: CC.ink2, maxWidth: 470 }}>
          The <strong>feelings</strong> line up almost exactly — animus is something the mechanism generates on its own, no outside help needed.
        </p>
        <p style={{ margin: '12px 0 0', ...PROSE, color: CC.ink2, maxWidth: 470 }}>
          But the real <strong>split</strong> runs far past anything the engine reaches alone, and keeps climbing after ~2010 while the engine stalls. That gap is what mechanisms can’t make by themselves — <strong>external shocks</strong>: partisan media, dated events, the timing of who mobilized when. The engine supplies the forces; history supplies the shove. (And the six you just toured are only a slice — the full model carries more dials still.)
        </p>
        <div style={{ marginTop: 18, maxWidth: 480 }}>
          <PChart title="Party separation — the split" sub="tracks, then peels away after ~2010" us={usArr('sep')} ff={ffArr('sep')} marker />
          <PChart title="Out-party warmth — the feelings" sub="nearly identical — the engine cools on its own" us={usArr('aff')} ff={ffArr('aff')} deg marker />
          <CompareLegend />
        </div>
        <div style={{ marginTop: 22, maxWidth: 480 }}>
          <Eyebrow style={{ color: CC.ink3 }}>Where to next</Eyebrow>
          <button onClick={onToStory} style={{ marginTop: 10, width: '100%', padding: '13px 18px', borderRadius: DS.rad.pill, border: 'none', background: CC.ink, color: '#fff', cursor: 'pointer', fontFamily: SANS, fontSize: 14, fontWeight: 500 }}>
            See it hit a real country — the U.S. story →
          </button>
          <div style={{ marginTop: 10, marginBottom: 12, display: 'flex', gap: 10 }}>
            <button onClick={on3D} style={doorAlt}>See it in three dimensions →</button>
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
  const toggle = () => { setHintSeen(true); setPlaying((p) => !p); };
  const skipToEnd = () => { setPlaying(false); setTick(LAST); };
  const wrapRef = React.useRef(null);
  const raf = React.useRef(0);

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
    const onWheel = (e) => { e.preventDefault(); setHintSeen(true); setPlaying(false); setTick((t) => Math.max(0, Math.min(LAST, t + e.deltaY * 0.06))); };
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
  const showHint = !hintSeen && !playing && !ended && tick < 1.5;   // first-run scrub helper
  const beatI = _pBeat(tick);
  const beat = PROLOGUE_BEATS[beatI];
  const sep = macroAt(run, tick, 'sep');
  const deg = Math.round((1 + macroAt(run, tick, 'aff')) * 50 + 12);
  const year = Math.floor(1980 + tick / 3);
  const usArr = (k) => D.runs.baseline.macro.map((m) => m[k]);
  const ffArr = (k) => run.macro_mean.map((m) => m[k]);

  return (
    <>
      <div ref={wrapRef} style={{ flex: 1, minHeight: 0, position: 'relative', overflow: 'hidden', background: CC.bg }}>
        {/* the compass — same geometry as the story surface; NO entity landmarks */}
        <div style={{ position: 'absolute', top: '-2%', bottom: '-2%', right: '2%', aspectRatio: '1' }}>
          <Field run={run} tick={tick} layer="position" view="density" showGap dim={ended ? 0.24 : 0} landmarks={false} />
        </div>
        {/* the engine-alone marker chip (mirrors the story's "paused at…" chip) */}
        <div style={{ position: 'absolute', right: 24, top: 20, zIndex: 2, display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: CC.ink3, background: 'rgba(249,248,244,.85)', padding: '5px 12px', borderRadius: 999, border: `1px solid ${CC.border}` }}>
          <span style={{ width: 7, height: 7, borderRadius: 999, background: '#9aa0a6' }} /> the engine alone · {ended ? '1980–2025' : year}
        </div>
        {/* paper scrim — keeps the floating prose legible */}
        <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, width: '56%', background: `linear-gradient(90deg, ${CC.bg} 0%, ${CC.bg} 88%, rgba(249,248,244,0) 100%)`, pointerEvents: 'none', zIndex: 1 }} />
        {/* floating narrative — same left column as the story */}
        <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, width: 'min(54%, 820px)', display: 'flex', flexDirection: 'column', minHeight: 0, zIndex: 3 }}>
          {ended
            ? <PrologueEndRail usArr={usArr} ffArr={ffArr} onToStory={onToStory} onPlayground={onPlayground} on3D={on3D} />
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
