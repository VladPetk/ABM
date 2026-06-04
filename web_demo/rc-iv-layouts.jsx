// Calm to Camps — Interventions "Narrative" layout.
//
// Restructures the screen to match the Story page's composition instead of the
// old three-rail workbench: a floating editorial column on the left, the compass
// breathing free on the right (no rails), and a full-width "two futures" timeline
// along the bottom — baseline = what happened, the branch = the counterfactual
// once you pick a lever, the gap at 2025 IS the effect. The result lives INLINE
// in the left column (no third rail).
//
// All the interventions logic (state, buckets, counterfactuals, sandbox) is
// reused from rc-interventions.jsx via window exports; nothing is re-derived.

const _ivD = window.CC_DATA;
const BUCKET_COL = { null: CC.ink4, partial: '#c47a2c', real: '#3f7d54', backfire: CC.r };

// ── shared furniture ─────────────────────────────────────────────────────────
// black "Try Sandbox" pill that sits beside the heading
function SandboxPill({ iv }) {
  const open = iv.isSandbox;
  return (
    <button onClick={open ? iv.closeSandbox : iv.openSandbox} style={{
      flexShrink: 0, cursor: 'pointer', fontFamily: SANS, fontSize: DS.type.small, fontWeight: 500,
      color: open ? CC.ink : '#fff', background: open ? 'transparent' : CC.ink,
      border: `1px solid ${CC.ink}`, borderRadius: DS.rad.pill, padding: '8px 16px',
      display: 'inline-flex', alignItems: 'center', gap: 8, whiteSpace: 'nowrap',
    }}>
      {open ? 'Close sandbox' : 'Try Sandbox'}
    </button>
  );
}

// the lever row used by Narrative — hairline rows, status dot
// (hollow = not run · fills with outcome colour once run), hover reveals the
// naive expectation.
function LeverRow({ id, iv }) {
  const [hov, setHov] = React.useState(false);
  const meta = window.IVMETA[id];
  const run = iv.revealed.has(id);
  const active = iv.activeId === id && !iv.isSandbox;
  const bucket = window.bucketAt(id, iv.releaseYear);
  const o = window.OUTCOME[bucket];
  return (
    <button onClick={() => iv.pick(id)} onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)} style={{
      display: 'block', width: '100%', textAlign: 'left', cursor: 'pointer', fontFamily: SANS,
      background: active ? CC.surface : (hov ? 'rgba(255,255,255,.55)' : 'transparent'),
      border: 'none', borderBottom: `1px solid ${CC.border}`, padding: '13px 12px', transition: 'background .12s',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ width: 9, height: 9, flexShrink: 0, borderRadius: DS.rad.pill,
          background: run ? BUCKET_COL[bucket] : 'transparent',
          border: run ? 'none' : `1.5px solid ${active ? CC.ink : CC.ink4}` }} />
        <span style={{ flex: 1, fontSize: DS.type.body, fontWeight: active ? 600 : 450, color: active || run ? CC.ink : CC.ink2 }}>{meta.label}</span>
        {run
          ? <Tag tone={o.tone}>{o.label}</Tag>
          : <span style={{ fontFamily: SANS, fontSize: 10, fontWeight: 600, letterSpacing: '.08em', textTransform: 'uppercase', color: active ? CC.ink2 : CC.ink4 }}>{active ? 'your call' : 'not run'}</span>}
      </div>
      <div style={{ maxHeight: hov ? 44 : 0, opacity: hov ? 1 : 0, overflow: 'hidden', transition: 'max-height .2s ease, opacity .2s ease', marginLeft: 21 }}>
        <span style={{ display: 'block', marginTop: 7, fontSize: DS.type.micro, lineHeight: 1.45, color: CC.ink3 }}>{meta.expected_naive_effect}</span>
      </div>
    </button>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
//  THE "TWO FUTURES" TIMELINE  — the screen's spine (bottom band)
// ═══════════════════════════════════════════════════════════════════════════
// Baseline trajectory of the headline metric across 1980→2025 (solid = "what
// happened"). When a result is revealed, the counterfactual branches off at the
// release tick (coloured by outcome; dashed if it does nothing) and the wedge
// between them is the effect. Decade marks are clickable to move WHEN it was
// tried.
function TwoFutures({ iv, play }) {
  const ref = React.useRef(null);
  const [w, setW] = React.useState(1100);
  React.useEffect(() => {
    if (!ref.current) return;
    const ro = new ResizeObserver((e) => { for (const en of e) setW(en.contentRect.width); });
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, []);

  const macro = _ivD.runs.baseline.macro;
  const LAST = window.LAST;
  const eff = iv.eff;
  const revealed = iv.showResult && eff && !iv.isSandbox;
  const metric = eff ? eff.metric : 'sep';
  const bVal = (m) => metric === 'aff' ? -m.aff : m.sep;
  const cVal = (k) => metric === 'aff' ? -eff.cf.aff[k] : eff.cf.sep[k];

  let lo = Infinity, hi = -Infinity;
  for (const m of macro) { const v = bVal(m); if (v < lo) lo = v; if (v > hi) hi = v; }
  if (revealed) for (let k = 0; k < eff.cf.sep.length; k++) { const v = cVal(k); if (v < lo) lo = v; if (v > hi) hi = v; }
  const pad = (hi - lo) * 0.16 || 0.05; lo -= pad; hi += pad;

  const H = 150, padL = 16, padR = 16, padT = 16, padB = 26;
  const W = Math.max(360, w);
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const X = (t) => padL + (t / LAST) * plotW;
  const Y = (v) => padT + plotH - ((v - lo) / (hi - lo || 1)) * plotH;
  const toPath = (pts) => pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');

  const basePts = macro.map((m, t) => [X(t), Y(bVal(m))]);
  let cfPts = null, col = CC.ink3, rt = null, wedge = null, branchPt = null;
  if (revealed) {
    rt = eff.releaseTick; col = window._bucketCol(eff.bucket);
    const nK = eff.cf.sep.length;
    // when playing, only draw the branch up to the playhead tick (it grows on)
    const headK = play ? Math.max(1, Math.min(nK, Math.round(play.tick - rt) + 1)) : nK;
    cfPts = []; for (let k = 0; k < headK; k++) cfPts.push([X(rt + k), Y(cVal(k))]);
    branchPt = [X(rt), Y(bVal(macro[rt]))];
    const baseTail = basePts.slice(rt, rt + headK);
    wedge = toPath(baseTail) + ' ' + cfPts.slice().reverse().map((p) => `L${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ') + ' Z';
  }

  const DECADES = [['1985', 15], ['1990', 30], ['1995', 45], ['2000', 60], ['2005', 75], ['2010', 90], ['2015', 105], ['2020', 120]];
  const axisLabel = metric === 'aff' ? 'Out-party animus' : 'Party separation';
  // decade marks are only an interactive "when did we try it?" control where
  // timing actually changes the outcome (X5/X6); elsewhere they're plain labels.
  const varies = !!(eff && eff.varies);

  // drag anywhere on the chart to scrub the playhead (Story-style "drag to scrub")
  const onScrubDown = (e) => {
    if (!play) return;
    const r = e.currentTarget.getBoundingClientRect();
    const toTick = (cx) => Math.max(play.rt, Math.min(window.LAST, ((((cx - r.left) * (W / r.width)) - padL) / plotW) * LAST));
    play.pause(); play.setTick(toTick(e.clientX));
    const mv = (ev) => play.setTick(toTick(ev.clientX));
    const up = () => { window.removeEventListener('pointermove', mv); window.removeEventListener('pointerup', up); };
    window.addEventListener('pointermove', mv); window.addEventListener('pointerup', up);
  };

  return (
    <div style={{ display: 'flex', alignItems: 'stretch', height: '100%', width: '100%' }}>
      {/* left gutter — transport (when a branch is playing) + legend */}
      <div style={{ width: 224, flexShrink: 0, padding: '16px 0 16px 4px', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 10, borderRight: `1px solid ${CC.border}` }}>
        {play
          ? <IvTransport play={play} />
          : <Eyebrow style={{ color: CC.ink3 }}>The two futures</Eyebrow>}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: DS.type.micro, color: CC.ink2 }}>
            <span style={{ width: 18, height: 0, borderTop: `2px solid ${CC.ink2}` }} /> what happened
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: DS.type.micro, color: revealed ? CC.ink2 : CC.ink4 }}>
            <span style={{ width: 18, height: 0, borderTop: `2.4px ${revealed && eff.bucket === 'null' ? 'dashed' : 'solid'} ${revealed ? col : CC.ink4}` }} />
            {revealed ? `if tried in ${iv.releaseYear}` : 'if we’d intervened'}
          </div>
        </div>
        {!play && <div style={{ fontSize: DS.type.micro, color: CC.ink4, marginTop: 2 }}>{axisLabel} · 1980 → 2025</div>}
      </div>

      {/* the chart */}
      <div ref={ref} style={{ flex: 1, minWidth: 0, position: 'relative' }}>
        <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} preserveAspectRatio="none"
          onPointerDown={play ? onScrubDown : undefined}
          style={{ display: 'block', cursor: play ? 'ew-resize' : 'default', touchAction: 'none' }}>
          {/* decade gridlines */}
          {DECADES.map(([lab, t]) => (
            <line key={t} x1={X(t)} y1={padT} x2={X(t)} y2={padT + plotH} stroke={CC.border} strokeWidth="1" strokeDasharray="2 4" opacity="0.5" vectorEffect="non-scaling-stroke" />
          ))}
          {/* baseline axis */}
          <line x1={padL} y1={padT + plotH} x2={W - padR} y2={padT + plotH} stroke={CC.borderS} strokeWidth="1" vectorEffect="non-scaling-stroke" />
          {/* the divergence wedge */}
          {revealed && <path d={wedge} fill={col} opacity="0.1" />}
          {/* baseline trajectory — what happened */}
          <path d={toPath(basePts)} fill="none" stroke={CC.ink2} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
          {/* counterfactual branch */}
          {revealed && <React.Fragment>
            <path d={toPath(cfPts)} fill="none" stroke={col} strokeWidth="2.6" strokeLinejoin="round" strokeLinecap="round" strokeDasharray={eff.bucket === 'null' ? '5 4' : 'none'} vectorEffect="non-scaling-stroke" />
            <circle cx={branchPt[0]} cy={branchPt[1]} r="3.4" fill={CC.surface} stroke={CC.ink2} strokeWidth="1.6" vectorEffect="non-scaling-stroke" />
          </React.Fragment>}
          {/* the moving playhead — in sync with the compass below (baseline
              before a result is revealed, the branch after) */}
          {play && <line x1={X(play.tick)} y1={padT} x2={X(play.tick)} y2={padT + plotH} stroke={revealed ? col : CC.ink3} strokeWidth="1" strokeDasharray="2 3" opacity="0.7" vectorEffect="non-scaling-stroke" />}
          {revealed && play && cfPts.length > 0 && <circle cx={cfPts[cfPts.length - 1][0]} cy={cfPts[cfPts.length - 1][1]} r="3" fill={col} vectorEffect="non-scaling-stroke" />}
        </svg>
        {/* clickable decade marks + year labels (HTML so they stay crisp & tappable) */}
        <div style={{ position: 'absolute', left: padL, right: padR, bottom: 4, height: padB - 6, pointerEvents: 'none' }}>
          {DECADES.map(([lab, t]) => {
            const on = revealed && rt === t;
            const left = `${((t / LAST) * 100)}%`;
            return (
              <button key={t} onClick={() => varies && iv.setReleaseYear(lab)} style={{
                position: 'absolute', left, transform: 'translateX(-50%)', bottom: 0, pointerEvents: varies ? 'auto' : 'none',
                fontFamily: MONO, fontSize: 9.5, color: on ? CC.ink : CC.ink4, fontWeight: on ? 600 : 400,
                background: 'transparent', border: 'none', cursor: varies ? 'pointer' : 'default', padding: '2px 3px', ...TNUM,
              }}>{lab.slice(2)}</button>
            );
          })}
          <span style={{ position: 'absolute', left: 0, bottom: 0, fontFamily: SANS, fontSize: 9.5, color: CC.ink4 }}>1980</span>
          <span style={{ position: 'absolute', right: 0, bottom: 0, fontFamily: SANS, fontSize: 9.5, color: CC.ink4 }}>2025</span>
        </div>
      </div>
    </div>
  );
}

// A calm editorial Δ readout — big serif numeral, a directional glyph, and a
// qualitative sub-label. No progress bar (it reads as broken at 0.000); the
// sign + colour + word carry the meaning. Two of these flank a centre hairline.
function DeltaReadout({ label, v, helpfulSign, side = 'l' }) {
  const flat = v == null || Math.abs(v) < 0.05;
  const good = !flat && v * helpfulSign > 0;
  const col = v == null ? CC.ink4 : flat ? CC.ink2 : good ? '#3f7d54' : CC.r;
  const arrow = v == null ? '' : v > 0.005 ? '↑' : v < -0.005 ? '↓' : '→';
  const txt = v == null ? '—' : (v > 0 ? '+' : '') + (+v).toFixed(3);
  const note = v == null ? '—' : flat ? 'no measurable change' : good ? 'helpful direction' : 'harmful direction';
  return (
    <div style={{ padding: side === 'l' ? '0 24px 0 0' : '0 0 0 24px' }}>
      <Eyebrow style={{ color: CC.ink3 }}>{label}</Eyebrow>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginTop: 9 }}>
        <span style={{ fontFamily: SERIF, fontWeight: 600, fontSize: 32, letterSpacing: '-.02em', lineHeight: 1, color: col, ...TNUM }}>{txt}</span>
        <span style={{ fontFamily: SANS, fontSize: 15, color: col }}>{arrow}</span>
      </div>
      <div style={{ marginTop: 9, fontSize: DS.type.micro, color: CC.ink3, fontStyle: flat ? 'italic' : 'normal' }}>{note}</div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
//  DIRECTION — NARRATIVE  (the Story-aligned rethink)
// ═══════════════════════════════════════════════════════════════════════════
function NarrativeDetail({ iv }) {
  // Only interventions whose bucket actually changes across release decades
  // (X5 ranked-choice + X6 shared-institutions today) get the "when did we try
  // it?" control; for the rest, timing is immaterial, so we hide it and say so.
  const varies = !!(iv.eff && iv.eff.varies);
  // predict gate
  if (iv.predicting) {
    return (
      <React.Fragment>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16 }}>
          <div>
            <Eyebrow>Your call · before the run</Eyebrow>
            <h2 style={{ margin: '10px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: DS.type.title, lineHeight: 1.06, letterSpacing: '-.015em', color: CC.ink }}>{iv.active.label}</h2>
          </div>
          <SandboxPill iv={iv} />
        </div>
        {varies && (
          <div style={{ marginTop: 20, paddingTop: 18, borderTop: `1px solid ${CC.border}` }}>
            <ReleaseSelector year={iv.releaseYear} onPick={iv.setReleaseYear} />
          </div>
        )}
        <p style={{ margin: '18px 0 14px', fontSize: DS.type.body, lineHeight: 1.55, color: CC.ink2 }}>{varies ? `If we’d actually done this in ${iv.releaseYear}, what happens by 2025?` : 'If we’d actually done this, what happens by 2025?'}</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
          <BetButton g={{ ...GUESS.help, key: 'help' }} onClick={() => iv.submitGuess('help')} />
          <BetButton g={{ ...GUESS.none, key: 'none' }} onClick={() => iv.submitGuess('none')} />
          <BetButton g={{ ...GUESS.backfire, key: 'backfire' }} onClick={() => iv.submitGuess('backfire')} />
        </div>
        <p style={{ margin: '14px 0 0', fontSize: DS.type.micro, lineHeight: 1.5, color: CC.ink4 }}>The branch on the timeline below appears once you commit.</p>
      </React.Fragment>
    );
  }

  // revealed result
  const eff = iv.eff, o = iv.o;
  return (
    <React.Fragment>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <Eyebrow>Modeled effect · released {iv.releaseYear}</Eyebrow>
            {o && <Tag tone={o.tone}>{o.label}</Tag>}
          </div>
          <h2 style={{ margin: '10px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: DS.type.title, lineHeight: 1.06, letterSpacing: '-.015em', color: CC.ink }}>{eff.name}</h2>
        </div>
        <SandboxPill iv={iv} />
      </div>

      <p style={{ margin: '16px 0 0', fontSize: DS.type.body, lineHeight: 1.6, color: CC.ink }}>{eff.take}</p>
      {eff.caveat && (
        <p style={{ margin: '14px 0 0', fontFamily: SERIF, fontStyle: 'italic', fontSize: DS.type.small + 0.5, lineHeight: 1.62, color: CC.ink3, maxWidth: 520 }}>
          <span style={{ fontFamily: SANS, fontStyle: 'normal', fontSize: 10, fontWeight: 600, letterSpacing: '.12em', textTransform: 'uppercase', color: CC.ink4, marginRight: 9 }}>Note</span>
          {eff.caveat}
        </p>
      )}

      <div style={{ marginTop: 22, paddingTop: 18, borderTop: `1px solid ${CC.border}` }}>
        <Eyebrow style={{ color: CC.ink3 }}>What it changed by 2025</Eyebrow>
        <div style={{ marginTop: 15, display: 'grid', gridTemplateColumns: '1fr 1px 1fr' }}>
          <DeltaReadout label="Δ party gap" v={eff.dSep} helpfulSign={-1} side="l" />
          <div style={{ background: CC.border }} />
          <DeltaReadout label="Δ out-party warmth" v={eff.dAff} helpfulSign={1} side="r" />
        </div>
        <p style={{ margin: '15px 0 0', fontSize: DS.type.micro, lineHeight: 1.5, color: CC.ink3 }}>
          Helpful means a <span style={{ color: '#3f7d54' }}>smaller party gap</span> or <span style={{ color: '#3f7d54' }}>warmer feelings</span> toward the other side. Δ vs. no intervention, ~10 years out — single representative run.
        </p>
      </div>

      <div style={{ marginTop: 20, paddingTop: 18, borderTop: `1px solid ${CC.border}` }}>
        {varies ? (
          <React.Fragment>
            <ReleaseSelector year={iv.releaseYear} onPick={iv.setReleaseYear} />
            <p style={{ margin: '13px 0 0', fontSize: DS.type.micro, lineHeight: 1.5, color: CC.ink3 }}>
              This one depends on <em>when</em>. Change the decade and watch the branch below flip.
            </p>
          </React.Fragment>
        ) : (
          <React.Fragment>
            <Eyebrow style={{ color: CC.ink3 }}>When you try it</Eyebrow>
            <p style={{ margin: '9px 0 0', fontSize: DS.type.small, lineHeight: 1.55, color: CC.ink3 }}>
              Barely matters — the result holds steady across every decade we tested.
            </p>
          </React.Fragment>
        )}
      </div>
    </React.Fragment>
  );
}

// a quiet editorial "back to the picker" affordance — used in the Narrative
// layout, where the detail/sandbox replaces the lever list entirely.
function BackToList({ onClick }) {
  const [hov, setHov] = React.useState(false);
  return (
    <button onClick={onClick} onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)} style={{
      display: 'inline-flex', alignItems: 'center', gap: 8, marginBottom: 20, cursor: 'pointer',
      fontFamily: SANS, fontSize: 11, fontWeight: 600, letterSpacing: '.12em', textTransform: 'uppercase',
      color: hov ? CC.ink : CC.ink3, background: 'none', border: 'none', padding: 0, transition: 'color .12s',
    }}>
      <span style={{ fontSize: 14, fontWeight: 400, transform: hov ? 'translateX(-2px)' : 'none', transition: 'transform .12s' }}>←</span>
      All interventions
    </button>
  );
}

// The sandbox as the FINAL row of the lever list — deliberately black with a
// light font so it reads as a different kind of thing (it changes the model, not
// a policy; "not a finding"). On the individual intervention screens the sandbox
// stays a pill (SandboxPill) instead.
function SandboxRow({ iv }) {
  const [hov, setHov] = React.useState(false);
  return (
    <button onClick={iv.openSandbox} onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)} style={{
      display: 'block', width: '100%', textAlign: 'left', cursor: 'pointer', fontFamily: SANS,
      background: hov ? '#000' : CC.ink, border: 'none', padding: '13px 12px', transition: 'background .12s',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ fontSize: 13, width: 9, flexShrink: 0, color: 'rgba(255,255,255,.75)', textAlign: 'center' }}>⚠︎</span>
        <span style={{ flex: 1, fontSize: DS.type.body, fontWeight: 500, color: '#fff' }}>Sandbox</span>
        <span style={{ fontFamily: SANS, fontSize: 10, fontWeight: 600, letterSpacing: '.08em', textTransform: 'uppercase', color: 'rgba(255,255,255,.55)' }}>not a finding</span>
      </div>
    </button>
  );
}

function NarrativeLeft({ iv }) {
  // Matches the Story page's WatchRail: large left indent, vertically centred,
  // scrolls when content is tall.
  const LX = 'clamp(64px, 14vw, 248px)';
  const wrap = { height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'safe center', overflow: 'auto', minHeight: 0 };
  const pad = { flexShrink: 0, padding: `clamp(28px,4.5vh,52px) 44px clamp(24px,4vh,40px) ${LX}` };

  // sandbox reuses the existing self-contained panel
  if (iv.isSandbox) return <div style={{ height: '100%', overflow: 'auto' }}><div style={pad}><BackToList onClick={iv.back} /><IvRail iv={iv} /></div></div>;

  return (
    <div style={wrap}>
      <div style={pad}>
      {iv.activeId
        ? <React.Fragment><BackToList onClick={iv.back} /><NarrativeDetail iv={iv} /></React.Fragment>
        : <React.Fragment>
            <Eyebrow>The experiment</Eyebrow>
            <h2 style={{ margin: '12px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: DS.type.display, lineHeight: 1.04, letterSpacing: '-.02em', color: CC.ink }}>Could anything have stopped it?</h2>
            <p style={{ margin: '16px 0 0', fontSize: DS.type.body, lineHeight: 1.6, color: CC.ink2, maxWidth: 460 }}>
              Seven things people have actually tried. Most do less than you’d think, one backfires, and the win isn’t the obvious one. Pick one and call it before you run it.
            </p>
            <div style={{ marginTop: DS.sp.lg, background: CC.surface, border: `1px solid ${CC.border}`, borderRadius: DS.rad.card, overflow: 'hidden', maxWidth: 480 }}>
              <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', padding: '13px 16px 11px', borderBottom: `1px solid ${CC.border}` }}>
                <span style={{ fontFamily: SANS, fontSize: DS.type.small, fontWeight: 600, color: CC.ink }}>Pick a lever</span>
                <MonoVal size={DS.type.micro} color={CC.ink3} weight={400}>{iv.revealedCount}/{iv.total} run</MonoVal>
              </div>
              <div>{window.IV_ORDER.map((id) => <LeverRow key={id} id={id} iv={iv} />)}</div>
              <SandboxRow iv={iv} />
            </div>
          </React.Fragment>}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
//  INTERVENTIONS PLAYBACK — the compass is always playable
// ═══════════════════════════════════════════════════════════════════════════
// A single playhead drives the compass across 1980→2025. With no engine result
// revealed it plays the BASELINE ("what happened"), paused on 2025 by default;
// once a lever is revealed it lazily fetches that branch's per-tick positions
// (cc-proto-engine.loadBranch), stitches baseline-before-release + branch-after,
// jumps to the release year and autoplays the divergence. Returns null only in
// the sandbox (a cosmetic spread, not a time series). RAF is paused in the
// headless preview, so motion can't be verified there, but scrubbing is
// deterministic.
function useIvPlayback(iv) {
  const wantBranch = iv.showResult && !iv.isSandbox && iv.eff ? iv.eff.id : null;
  const year = iv.releaseYear;
  const [branch, setBranch] = React.useState(null);   // stitched branch run, or null
  const [tick, setTickRaw] = React.useState(window.LAST);
  const [playing, setPlaying] = React.useState(false);
  const [speed, setSpeed] = React.useState(1);
  const tickRef = React.useRef(tick); tickRef.current = tick;
  const speedRef = React.useRef(speed); speedRef.current = speed;
  const activeRef = React.useRef(false);               // wheel-scrub gate (set each render)
  const rtRef = React.useRef(0);                        // lower scrub bound (release tick)

  const setTick = React.useCallback((v) => {
    const nv = typeof v === 'function' ? v(tickRef.current) : v;
    const c = Math.max(0, Math.min(window.LAST, nv));
    tickRef.current = c; setTickRaw(c);
  }, []);

  // load the branch when a result is revealed; clear it (back to baseline) otherwise
  React.useEffect(() => {
    if (!wantBranch) { setBranch(null); return; }
    let alive = true;
    setBranch(null);
    window.loadBranch(wantBranch, year).then((r) => {
      if (!alive) return;
      setBranch(r); setTick(r.release_tick); setPlaying(true);   // autoplay the divergence
    }).catch(() => { if (alive) setBranch(null); });
    return () => { alive = false; };
  }, [wantBranch, year, setTick]);

  // advance the playhead (paused headlessly; scrub still works)
  React.useEffect(() => {
    if (!playing) return;
    let raf, prev = null;
    const loop = (ts) => {
      if (prev == null) prev = ts;
      const dt = (ts - prev) / 1000; prev = ts;
      const nt = tickRef.current + dt * 7 * speedRef.current;
      if (nt >= window.LAST) { setTick(window.LAST); setPlaying(false); return; }
      setTick(nt); raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [playing, setTick]);

  // wheel-scrub — roll to move the playhead through time, the same gesture as the
  // Story page. Free scrub (no chapter snap, like Explore); one non-passive
  // global listener gated to the interventions canvas via activeRef.
  React.useEffect(() => {
    const WHEEL_SENS = 0.0175;                          // matches Story's WHEEL_SENS
    const onWheel = (e) => {
      if (!activeRef.current) return;
      e.preventDefault();
      setPlaying(false);
      setTick((t) => Math.max(rtRef.current, Math.min(window.LAST, t + e.deltaY * WHEEL_SENS)));
    };
    window.addEventListener('wheel', onWheel, { passive: false });
    return () => window.removeEventListener('wheel', onWheel);
  }, [setTick]);

  const rt = branch ? branch.release_tick : 0;
  activeRef.current = !iv.isSandbox;                    // gate the wheel listener
  rtRef.current = rt;

  if (iv.isSandbox) return null;                       // no transport in the sandbox
  const run = branch || window.D.runs.baseline;        // baseline until a branch loads
  const toggle = () => {
    if (tickRef.current >= window.LAST) { setTick(rt); setPlaying(true); }
    else setPlaying((p) => !p);
  };
  const pause = () => setPlaying(false);
  return { run, tick, rt, playing, toggle, setTick, pause, speed, setSpeed, isBranch: !!branch };
}

// Play / speed / year transport for the interventions bottom band — inherits
// the Story-mode BarTransport language (filled-ink ▶/❚❚ button that becomes ↺ at
// the end, compact ½×/1×/2×/4× speed selector) so the two timelines read the
// same. Lives in the TwoFutures left gutter, NOT floating on the compass; the
// chart body itself scrubs the playhead.
function IvTransport({ play }) {
  const yr = Math.round(window.Y0 + play.tick / window.TPY);
  const startYr = Math.round(window.Y0 + play.rt / window.TPY);
  const round = { width: 30, height: 30, borderRadius: DS.rad.pill, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', flexShrink: 0, fontFamily: SANS };
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <button onClick={play.toggle} aria-label={play.playing ? 'Pause' : 'Play'}
          style={{ ...round, background: CC.ink, color: '#fff', border: 'none', fontSize: 11 }}>
          {play.playing ? '❚❚' : '▶'}
        </button>
        <button onClick={() => play.setTick(play.rt)} aria-label="Restart"
          style={{ ...round, background: 'transparent', color: CC.ink2, border: `1px solid ${CC.borderS}`, fontSize: 13 }}>↺</button>
        <span style={{ width: 1, height: 20, background: CC.border, margin: '0 1px', flexShrink: 0 }} />
        <div style={{ display: 'inline-flex', gap: 2, padding: 3, background: CC.bg2, borderRadius: DS.rad.pill, border: `1px solid ${CC.border}` }}>
          {[[0.5, '½×'], [1, '1×'], [2, '2×'], [4, '4×']].map(([v, l]) => {
            const on = play.speed === v;
            return (
              <button key={v} onClick={() => play.setSpeed(v)} style={{
                fontSize: 10.5, padding: '3px 6px', borderRadius: DS.rad.pill, fontFamily: MONO, cursor: 'pointer', border: 'none',
                color: on ? CC.ink : CC.ink3, fontWeight: on ? 600 : 400, background: on ? CC.surface : 'transparent',
                boxShadow: on ? '0 1px 3px rgba(26,29,35,.12)' : 'none', ...TNUM,
              }}>{l}</button>);
          })}
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 7 }}>
        <MonoVal size={DS.type.body} color={CC.ink} weight={600}>{yr}</MonoVal>
        <span style={{ fontFamily: SANS, fontSize: 9.5, color: CC.ink4 }}>from {startYr} · drag the chart to scrub</span>
      </div>
    </div>
  );
}

function IvNarrative({ iv, layer }) {
  const play = useIvPlayback(iv);
  const hasPlay = !!play;
  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: CC.bg }}>
      {/* top region — the Story page's exact composition: a right-anchored square
          compass that bleeds top/bottom, a feathered paper scrim over the left,
          and the prose floating at the same left indent. */}
      <div style={{ flex: 1, minHeight: 0, position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', top: '-6%', bottom: '-6%', right: '2%', aspectRatio: '1' }}>
          <Field run={hasPlay ? play.run : _ivD.runs.baseline} tick={hasPlay ? play.tick : window.LAST}
            layer="position" view="density"
            showGap={hasPlay} dim={0}
            transform={hasPlay ? null : (iv.isSandbox ? iv.transform : null)}
            landmarks="fixed" />
        </div>
        <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, width: '56%', background: `linear-gradient(90deg, ${CC.bg} 0%, ${CC.bg} 88%, rgba(249,248,244,0) 100%)`, pointerEvents: 'none', zIndex: 1 }} />
        <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, width: 'min(54%, 820px)', display: 'flex', flexDirection: 'column', minHeight: 0, zIndex: 3 }}>
          <NarrativeLeft iv={iv} />
        </div>
      </div>
      <div style={{ flexShrink: 0, height: 152, borderTop: `1px solid ${CC.border}`, background: CC.bg, padding: '0 clamp(20px, 3vw, 44px)' }}>
        <TwoFutures iv={iv} play={play} />
      </div>
    </div>
  );
}

// ═══ workbench shell ═════════════════════════════════════════════════════════
function IvWorkbench({ iv, layer }) {
  return (
    <div style={{ flex: 1, minHeight: 0, position: 'relative', background: CC.bg }}>
      <IvNarrative iv={iv} layer={layer} />
    </div>
  );
}

Object.assign(window, { IvWorkbench });
