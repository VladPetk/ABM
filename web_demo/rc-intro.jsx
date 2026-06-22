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
function IntroRail({ tick, storyDone, onWatch, onSandbox, onAbout, on3D }) {
  const LX = 'clamp(64px, 14vw, 248px)';
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
  return (
    <div style={{ background: 'transparent', display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, justifyContent: 'safe center', overflow: 'auto' }}>
      <div style={{ flexShrink: 0, padding: `clamp(28px,4.5vh,52px) 44px 8px ${LX}` }}>
        <Eyebrow>An agent-based model · 250 simulated citizens</Eyebrow>
        <h2 style={{ margin: '14px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: 'clamp(30px, 3.4vw, 44px)', lineHeight: 1.06, letterSpacing: '-.02em', maxWidth: 520 }}>
          Simulating political polarization, visually
        </h2>
        <p style={{ margin: '20px 0 0', ...PROSE, color: CC.ink2, maxWidth: 470 }}>
          This is a (rather accurate) simulation of how politics polarize. It's
          built using well-established mechanisms from polarization research and
          real-world survey data. The website allows you to interact with the
          engine and see polarization unfold - in the process learning more about
          what drives it, what stalls it, and what it actually means to be
          'polarized'.
        </p>
        <p style={{ margin: '14px 0 0', ...PROSE, color: CC.ink2, maxWidth: 470 }}>
          I invite you to take the tour of the simulation engine. You'll be
          introduced to the forces (and get a chance to play around with them),
          get a visual feel for how society polarizes, and get a chance to see
          the engine tuned to a specific case - the U.S. Afterwards (or now if
          feeling rebellious), you can dive into the sandbox to see what happens
          if we tinker with the forces driving the divide.
        </p>
        <div style={{ marginTop: 28, display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <button onClick={onWatch} style={watchStyle}>Take the tour &nbsp;→</button>
          <button onClick={onSandbox} style={sandboxStyle}>Open the sandbox</button>
        </div>
        <div style={{ marginTop: 22, display: 'flex', gap: 18, alignItems: 'baseline', flexWrap: 'wrap' }}>
          <button onClick={on3D} style={quiet}>see it in three dimensions →</button>
          <button onClick={onAbout} style={quiet}>Why did I build it? →</button>
        </div>
      </div>
      <div style={{ flexShrink: 0, padding: `18px 44px clamp(24px,4vh,40px) ${LX}`, display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ width: 7, height: 7, borderRadius: DS.rad.pill, background: '#c47a2c', flexShrink: 0 }} />
        <span style={{ fontFamily: MONO, fontSize: DS.type.micro, color: CC.ink3, ...TNUM }}>
          {Math.floor(tickToYear(tick))} · 45 years of polarization on a loop.
        </span>
      </div>
    </div>);

}

Object.assign(window, { IntroRail, useIntroLoop, animateIntroMorph, ccFlag, setCcFlag, CC_INTRO_SEEN, CC_STORY_DONE });
