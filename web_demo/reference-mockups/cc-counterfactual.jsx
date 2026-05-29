// Calm to Camps — counterfactual / intervention result state.
// Reuses the Layout-A shell, but: an intervention is active, the timeline
// shows the release marker + candidates, the compass draws de-polarization
// trails, the sparklines overlay baseline (grey) vs counterfactual (colour),
// and a result card reports the outcome.

function ResultCard({ intervention, release, dSep, dAff, style }) {
  const meta = BUCKET_META[intervention.bucket];
  return (
    <FloatCard style={{ width: 320, padding: 16, ...style }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10 }}>
        <div>
          <Eyebrow style={{ color: CC.ink3, fontSize: 9.5 }}>Result · released {release}</Eyebrow>
          <div style={{ fontSize: 15.5, fontWeight: 600, marginTop: 4, letterSpacing: '-.01em' }}>{intervention.name}</div>
        </div>
        <span style={{ flexShrink: 0, fontSize: 11, fontWeight: 600, color: '#fff', background: meta.color, padding: '4px 10px', borderRadius: 999 }}>{meta.label}</span>
      </div>

      {/* deltas */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 0, marginTop: 14, borderTop: `1px solid ${CC.border}`, borderBottom: `1px solid ${CC.border}` }}>
        <div style={{ padding: '11px 12px 11px 0', borderRight: `1px solid ${CC.border}` }}>
          <div style={{ fontSize: 11, color: CC.ink3 }}>Δ party separation</div>
          <div style={{ fontSize: 23, fontWeight: 600, fontFamily: MONO, color: meta.color, ...TNUM }}>{dSep}</div>
        </div>
        <div style={{ padding: '11px 0 11px 14px' }}>
          <div style={{ fontSize: 11, color: CC.ink3 }}>Δ affective pol.</div>
          <div style={{ fontSize: 23, fontWeight: 600, fontFamily: MONO, color: meta.color, ...TNUM }}>{dAff}</div>
        </div>
      </div>

      {/* literature anchor */}
      <p style={{ margin: '13px 0 0', fontFamily: SERIF, fontSize: 14, lineHeight: 1.4, color: CC.ink2, fontStyle: 'italic' }}>
        “Cross-cutting contact through shared institutions durably lowers out-group animus.” — anchored to the contact-hypothesis literature.
      </p>

      {/* provenance tally */}
      <div style={{ display: 'flex', gap: 8, marginTop: 16, alignItems: 'center', flexWrap: 'wrap' }}>
        <Eyebrow style={{ fontSize: 9.5 }}>Provenance</Eyebrow>
        <span style={{ fontSize: 11.5, fontFamily: MONO, color: CC.ink2, ...TNUM }}>
          <span style={{ color: '#3f7d54' }}>3 empirical [L]</span> · <span style={{ color: CC.ink3 }}>1 theoretical [T]</span>
        </span>
      </div>

      {/* what this means */}
      <div style={{ marginTop: 13, paddingTop: 13, borderTop: `1px solid ${CC.border}` }}>
        <Eyebrow style={{ color: CC.ink4, fontSize: 9.5 }}>What this means</Eyebrow>
        <p style={{ margin: '6px 0 0', fontSize: 13.5, lineHeight: 1.5, color: CC.ink }}>
          One of only two interventions that move the needle — and it works by changing who people live and work beside, not what they’re told.
        </p>
      </div>
    </FloatCard>
  );
}

function CounterfactualScreen({ year: initialYear = 2025, character = 'linda', animate = true }) {
  const W = 1440, H = 900;
  const SIDEBAR = 420;
  const release = 2010;
  const intervention = INTERVENTIONS.find((i) => i.id === 'X6');
  const color = BUCKET_META[intervention.bucket].color;
  const footerH = 126;

  // animate the playhead 1980→2025 on a loop so the two clouds visibly diverge
  const [year, setYear] = React.useState(animate ? 1980 : initialYear);
  React.useEffect(() => {
    if (!animate) return;
    let raf, start = null;
    const period = 30; // seconds for the full sweep
    const loop = (ts) => {
      if (start == null) start = ts;
      const t = ((ts - start) / 1000) % period;
      setYear(YEAR0 + (YEAR1 - YEAR0) * (t / period));
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [animate]);

  // divergence ramps over 15 years after release, capped
  const damp = Math.max(0, Math.min(1, (year - release) / 15)) * 0.5;

  return (
    <div style={{ width: W, height: H, background: CC.bg, color: CC.ink, fontFamily: SANS, display: 'flex', flexDirection: 'column', overflow: 'hidden', letterSpacing: '-.005em' }} data-screen-label="Counterfactual">
      <PlayerHeader active="X6" />
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: `1fr ${SIDEBAR}px`, minHeight: 0 }}>
        <div style={{ position: 'relative', background: CC.surface, height: '100%' }}>
          <div style={{ position: 'absolute', inset: 0, padding: '20px 28px 16px' }}>
            <Compass year={year} spotlight={true} mode="counterfactual" damp={damp} />
          </div>
          {/* sparklines with counterfactual overlay */}
          <FloatCard style={{ left: 22, top: 22, width: 290 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Eyebrow style={{ color: CC.ink3 }}>Counterfactual vs actual</Eyebrow>
              <span style={{ display: 'flex', gap: 10, alignItems: 'center', fontSize: 10.5, color: CC.ink3 }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 12, height: 0, borderTop: `1.5px dashed ${CC.ink4}` }} /> actual</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 12, height: 2, background: color }} /> this</span>
              </span>
            </div>
            <div style={{ marginTop: 10 }}><MacroSparklines width={258} year={year} counterfactualRelease={release} color={color} compact /></div>
          </FloatCard>
          {/* ghost/solid caption */}
          <FloatCard style={{ left: 22, bottom: 18, width: 320, padding: '10px 14px' }}>
            <span style={{ fontSize: 12.5, color: CC.ink2, display: 'flex', alignItems: 'center', gap: 9, lineHeight: 1.3 }}>
              <span style={{ display: 'inline-flex', gap: 5, flexShrink: 0 }}>
                <span style={{ width: 9, height: 9, borderRadius: 999, border: `1.5px solid ${CC.ink3}` }} />
                <span style={{ width: 9, height: 9, borderRadius: 999, background: CC.ink3 }} />
              </span>
              hollow = without the intervention · solid = with it
            </span>
          </FloatCard>
          {/* result card */}
          <ResultCard intervention={intervention} release={release} dSep="−0.21" dAff="−0.30" style={{ right: 22, top: 22 }} />
        </div>
        <div style={{ padding: '18px 30px 24px', borderLeft: `1px solid ${CC.border}`, background: CC.bg, overflow: 'hidden' }}>
          <CharacterPanel year={year} character={character} />
        </div>
      </div>
      {/* footer */}
      <div style={{ height: footerH, flexShrink: 0, borderTop: `1px solid ${CC.border}`, background: CC.bg, display: 'flex', alignItems: 'center', gap: 28, padding: '0 32px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 7, flexShrink: 0 }}>
          <Transport year={year} />
          <span style={{ fontFamily: MONO, fontSize: 12.5, color: CC.ink, ...TNUM }}>{monthYear(year)} <span style={{ color: CC.ink4 }}>· tick {Math.round(yearToFrac(year) * 135)} / 135</span></span>
        </div>
        <div style={{ width: 1, height: 64, background: CC.border }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <TimelineBar width={900} year={year} releaseYear={release} showReleaseMarkers={true} color={color} />
        </div>
      </div>
    </div>
  );
}

window.CounterfactualScreen = CounterfactualScreen;
window.ResultCard = ResultCard;
