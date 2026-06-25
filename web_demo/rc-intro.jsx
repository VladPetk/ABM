// Calm to Camps — Act 0: meet the model.
// The landing state of the unified simulation surface (one canvas, two nav
// labels — see docs in _temp/web_experience_flow_plan.md). Shows the 250
// agents as individual DOTS on the same compass the story uses, running a
// slow ambient 1980→2025 sweep on loop behind the copy. Two CTAs: the nudge
// follows what the visitor hasn't done yet (story first; sandbox once the
// story has been completed — `cc_story_done`).
//
// Exports: IntroRail (left column), useIntroLoop (ambient sweep driver),
// animateIntroMorph (the dots→density handoff into the story), ccFlag/setCcFlag
// (localStorage, same spirit as usePlayhead's cc_tick persistence).
// RAF note: the loop and the morph are motion — NOT verifiable in the headless
// preview; their static endpoints (tick 0 dots / tick 0 density) are.

function ccFlag(key) {
  try { return window.localStorage.getItem(key) === '1'; } catch (e) { return false; }
}
function setCcFlag(key, v = true) {
  try { window.localStorage.setItem(key, v ? '1' : '0'); } catch (e) { /* private mode etc. */ }
}
const CC_INTRO_SEEN = 'cc_intro_seen';
const CC_STORY_DONE = 'cc_story_done';
// the landing headline + live-run caption — shared so the desktop rail and the
// mobile hero overlay (cc-unified) never drift apart.
const INTRO_HEAD = 'Simulating political polarization, visually';
const INTRO_RUN_NOTE = '45 years of political interactions';

// ── ambient sweep — loops 1980→2025 with a short hold on the 2025 frame, so
// the ending is shown before any lecture (review amendment #1). ─────────────
function useIntroLoop({ active, setTick, base = 5 }) {
  React.useEffect(() => {
    if (!active) return;
    let raf, prev = null, hold = 0;
    const loop = (ts) => {
      if (prev == null) prev = ts;
      const dt = Math.min(0.1, (ts - prev) / 1000); prev = ts;
      setTick((t) => {
        if (hold > 0) { hold -= dt; return hold <= 0 ? 0 : t; }
        const nt = t + dt * base;
        if (nt >= LAST) { hold = 1.6; return LAST; }
        return nt;
      });
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [active, setTick, base]);
}

// ── the dots→density handoff (nudged path only; nav clicks jump-cut) ────────
// Eases the ambient sweep back to 1980 while the dots dissolve into the
// density clouds — same canvas, same positions, different representation.
// Returns a cancel function.
function animateIntroMorph({ fromTick, setTick, setMorphT, onDone, dur = 1500 }) {
  let raf, t0 = null;
  const step = (ts) => {
    if (t0 == null) t0 = ts;
    const k = Math.min(1, (ts - t0) / dur);
    const e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2; // easeInOut
    // tick settles to 1980 in the first ~half; the crossfade runs the full span
    const tk = Math.min(1, k / 0.55);
    setTick(fromTick * (1 - (tk < 0.5 ? 2 * tk * tk : 1 - Math.pow(-2 * tk + 2, 2) / 2)));
    setMorphT(e);
    if (k < 1) raf = requestAnimationFrame(step);
    else onDone();
  };
  raf = requestAnimationFrame(step);
  return () => cancelAnimationFrame(raf);
}

// ── Act 0 left rail — stakes first, mechanics second, then the two doors ────
// variant 'full' = desktop / fallback (eyebrow + headline + body + ticker, all
// floated over the field). variant 'mobile' = the body half only; the mobile
// landing renders the headline + live ticker as a hero OVER the dots above this,
// so here we drop the eyebrow, headline and ticker to avoid repeating them.
function IntroRail({ tick, storyDone, onWatch, onSandbox, onAbout, on3D, variant = 'full' }) {
  const isMobile = useIsMobile();
  const hero = variant === 'mobile';
  const LX = isMobile ? '20px' : RAIL_LX;
  const RX = isMobile ? '20px' : '44px';
  const pillBase = {
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
    padding: '13px 26px', borderRadius: DS.rad.pill, cursor: 'pointer',
    fontFamily: SANS, fontSize: DS.type.body, fontWeight: 500,
  };
  const black = { ...pillBase, background: CC.ink, color: '#fff', border: `1px solid ${CC.ink}` };
  const white = { ...pillBase, background: CC.surface, color: CC.ink2, fontWeight: 400, border: `1px solid ${CC.border}` };
  const quiet = {
    background: 'none', border: 'none', cursor: 'pointer', padding: 0,
    fontFamily: SANS, fontSize: DS.type.micro, color: CC.ink3, textDecoration: 'underline', textUnderlineOffset: 3,
  };
  // the nudge follows what the visitor hasn't done yet
  const watchStyle = storyDone ? white : black;
  const sandboxStyle = storyDone ? black : white;
  // on the mobile hero the two pills share the row as equal halves (auto-width
  // wraps them into an ugly column at phone widths); tighter padding + nowrap so
  // the labels never clip in half a screen.
  const ctaHero = hero ? { flex: 1, padding: '13px 12px', fontSize: 15, whiteSpace: 'nowrap' } : null;
  return (
    <div style={hero
      ? { background: 'transparent' }
      : { background: 'transparent', display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, justifyContent: isMobile ? 'flex-start' : 'safe center', overflow: 'auto' }}>
      <div style={{ flexShrink: 0, padding: hero ? `18px ${RX} 40px ${LX}` : `${isMobile ? '22px' : 'clamp(28px,4.5vh,52px)'} ${RX} 8px ${LX}` }}>
        {!hero && <Eyebrow>An agent-based model</Eyebrow>}
        {!hero &&
        <h2 style={{ margin: '14px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: 'clamp(30px, 3.4vw, 44px)', lineHeight: 1.06, letterSpacing: '-.02em', maxWidth: TEXTW }}>
          {INTRO_HEAD}
        </h2>}
        <p style={{ margin: hero ? 0 : '20px 0 0', ...PROSE, color: CC.ink2, maxWidth: TEXTW }}>
          This is a simulation of how politics polarizes. It runs on
          tried-and-tested mechanisms from polarization research: we don't trust
          people we disagree with, maintain ties with the ones we agree with,
          consume media that sits well with us, and so on. Pretty basic stuff,
          but that's what makes it interesting - turns out you don't need complex
          calculations or vast datasets to model polarization. A lot of it
          follows from first principles. What's a little unusual here is that
          this model brings these mechanisms - often studied in isolation -
          together.
        </p>
        <p style={{ margin: '14px 0 0', ...PROSE, color: CC.ink2, maxWidth: TEXTW }}>
          Take the tour of the engine and watch polarization unfold — in the
          process learning what drives it, what stalls it, and what it even means
          to be 'polarized'. You'll meet the forces (and get to play with them), get
          a visual feel for how a society comes apart, and see the engine tuned
          to one real case — the U.S. Afterwards (or now, if feeling rebellious),
          dive into the sandbox to see what happens when we tinker with the
          forces driving the divide.
        </p>
        <div style={{ marginTop: 28, display: 'flex', gap: 10, alignItems: 'center', flexWrap: hero ? 'nowrap' : 'wrap' }}>
          <button onClick={onWatch} style={{ ...watchStyle, ...ctaHero }}>Take the tour &nbsp;→</button>
          <button onClick={onSandbox} style={{ ...sandboxStyle, ...ctaHero }}>Open the sandbox</button>
        </div>
        <div style={{ marginTop: 22, display: 'flex', gap: 18, alignItems: 'baseline', flexWrap: 'wrap' }}>
          <button onClick={on3D} style={quiet}>see it in three dimensions →</button>
          <button onClick={onAbout} style={quiet}>Why did I build it? →</button>
        </div>
      </div>
      {!hero &&
      <div style={{ flexShrink: 0, padding: `18px ${RX} ${isMobile ? '26px' : 'clamp(24px,4vh,40px)'} ${LX}` }}>
        <span style={{ fontFamily: MONO, fontSize: DS.type.micro, color: CC.ink3, ...TNUM }}>
          {Math.floor(tickToYear(tick))} · {INTRO_RUN_NOTE}
        </span>
      </div>}
    </div>);

}

Object.assign(window, { IntroRail, useIntroLoop, animateIntroMorph, ccFlag, setCcFlag, CC_INTRO_SEEN, CC_STORY_DONE, INTRO_HEAD, INTRO_RUN_NOTE });
