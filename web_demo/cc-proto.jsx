// Calm to Camps — working prototype app.
// Intro (compass already playing) → player. One shared playhead carries across
// so it never resets. Transport drives compass + character + timeline +
// sparklines in lockstep. Intervention picker switches to a live counterfactual
// (baseline ghost vs intervention solid). Character tabs swap the spotlight.

const TAB_KEYS = ['linda', 'bob', 'james', 'maria'];
const HAS_RUN = { X7_perception_correction: true }; // only this run bundled in the sample

function SpeedControl({ speed, setSpeed }) {
  const opts = [[0.5, '½'], [1, '1×'], [2, '2×'], [4, '4×']];
  return (
    <div style={{ display: 'flex', gap: 3 }}>
      {opts.map(([v, l]) => {
        const on = speed === v;
        return (
          <button key={v} onClick={() => setSpeed(v)} style={{
            fontSize: 11, padding: '3px 8px', borderRadius: 999, fontFamily: MONO, cursor: 'pointer',
            border: `1px solid ${on ? CC.ink : CC.border}`, color: on ? CC.ink : CC.ink3,
            fontWeight: on ? 500 : 400, background: on ? CC.surface : 'transparent', ...TNUM,
          }}>{l}</button>
        );
      })}
    </div>
  );
}

function Transport({ playing, toggle, setTick, speed, setSpeed }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      <button onClick={toggle} aria-label={playing ? 'Pause' : 'Play'} style={{
        width: 34, height: 34, borderRadius: 999, background: CC.ink, color: '#fff', border: 'none',
        cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 12,
      }}>{playing ? '❚❚' : '▶'}</button>
      <button onClick={() => setTick(0)} aria-label="Restart" style={{
        width: 28, height: 28, borderRadius: 999, border: `1px solid ${CC.border}`, color: CC.ink2,
        cursor: 'pointer', background: 'transparent', fontSize: 12,
      }}>↺</button>
      <SpeedControl speed={speed} setSpeed={setSpeed} />
    </div>
  );
}

function InterventionPicker({ active, onPick }) {
  const [open, setOpen] = React.useState(false);
  const label = active ? D.interventions[active].label : 'No intervention (baseline)';
  return (
    <div style={{ position: 'relative' }}>
      <button onClick={() => setOpen((o) => !o)} style={{
        display: 'inline-flex', alignItems: 'center', gap: 9, padding: '7px 13px', border: `1px solid ${CC.borderS}`,
        borderRadius: 999, background: CC.surface, fontSize: 13.5, color: CC.ink, cursor: 'pointer', fontFamily: SANS,
      }}>
        <Eyebrow style={{ fontSize: 9.5, color: CC.ink3 }}>Intervention</Eyebrow>
        <span style={{ fontWeight: 500 }}>{label}</span>
        <span style={{ color: CC.ink3, fontSize: 11 }}>▾</span>
      </button>
      {open && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 8px)', left: 0, width: 340, zIndex: 50,
          background: CC.surface, border: `1px solid ${CC.border}`, borderRadius: 12,
          boxShadow: '0 12px 34px rgba(26,29,35,.14)', padding: 7,
        }}>
          <button onClick={() => { onPick(null); setOpen(false); }} style={pickItem(active === null)}>
            <span style={{ width: 9, height: 9, borderRadius: 999, border: `1.5px solid ${CC.ink4}` }} />
            <span style={{ flex: 1, textAlign: 'left' }}>No intervention (baseline)</span>
          </button>
          <div style={{ height: 1, background: CC.border, margin: '5px 0' }} />
          {Object.keys(D.interventions).map((id) => {
            const iv = D.interventions[id];
            const has = HAS_RUN[id];
            return (
              <button key={id} onClick={() => { onPick(id); setOpen(false); }} style={{ ...pickItem(active === id), opacity: has ? 1 : 0.55 }}>
                <span style={{ width: 9, height: 9, borderRadius: 999, background: iv.color, flexShrink: 0 }} />
                <span style={{ flex: 1, textAlign: 'left' }}>{iv.label}</span>
                <span style={{ fontSize: 10.5, color: CC.ink3, fontFamily: MONO }}>{has ? D.meta.release_years[D.runs[id].release_tick] : 'sample n/a'}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
function pickItem(on) {
  return {
    display: 'flex', alignItems: 'center', gap: 10, width: '100%', padding: '9px 11px', borderRadius: 8,
    border: 'none', background: on ? CC.bg2 : 'transparent', cursor: 'pointer', fontFamily: SANS,
    fontSize: 13, color: CC.ink,
  };
}

function ResultCard({ id, tick }) {
  const iv = D.interventions[id];
  const has = HAS_RUN[id];
  const bucketColor = { null: '#74797f', partial: '#c47a2c', real: '#3f7d54', backfire: '#8b2530' };
  const affB = iv.effect_buckets.affect, sepB = iv.effect_buckets.issue_sorting;
  let dSep = null, dAff = null;
  if (has) {
    const cf = D.runs[id];
    dSep = macroAt(cf, tick, 'sep') - macroAt(D.runs.baseline, tick, 'sep');
    dAff = (-macroAt(cf, tick, 'aff')) - (-macroAt(D.runs.baseline, tick, 'aff'));
  }
  const pv = iv.provenance_tags;
  const empirical = (pv['L:M'] || 0) + (pv['L:D'] || 0);
  return (
    <FloatCard style={{ right: 22, top: 22, width: 330, padding: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10 }}>
        <div>
          <Eyebrow style={{ color: CC.ink3, fontSize: 9.5 }}>Result{has ? ` · released ${D.meta.release_years[D.runs[id].release_tick]}` : ''}</Eyebrow>
          <div style={{ fontSize: 15.5, fontWeight: 600, marginTop: 4, letterSpacing: '-.01em' }}>{iv.label}</div>
        </div>
        <span style={{ flexShrink: 0, fontSize: 11, fontWeight: 600, color: '#fff', background: bucketColor[affB] || '#74797f', padding: '4px 10px', borderRadius: 999 }}>
          {affB === 'real' ? 'Real effect' : affB === 'partial' ? 'Partial' : affB === 'backfire' ? 'Backfire' : 'No effect'}
        </span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', marginTop: 14, borderTop: `1px solid ${CC.border}`, borderBottom: `1px solid ${CC.border}` }}>
        <div style={{ padding: '11px 12px 11px 0', borderRight: `1px solid ${CC.border}` }}>
          <div style={{ fontSize: 11, color: CC.ink3 }}>Δ party separation</div>
          <div style={{ fontSize: 22, fontWeight: 600, fontFamily: MONO, color: dSep == null ? CC.ink4 : (dSep < -0.01 ? '#3f7d54' : dSep > 0.01 ? '#8b2530' : CC.ink3), ...TNUM }}>{dSep == null ? '—' : (dSep >= 0 ? '+' : '') + dSep.toFixed(2)}</div>
        </div>
        <div style={{ padding: '11px 0 11px 14px' }}>
          <div style={{ fontSize: 11, color: CC.ink3 }}>Δ affective pol.</div>
          <div style={{ fontSize: 22, fontWeight: 600, fontFamily: MONO, color: dAff == null ? CC.ink4 : (dAff < -0.01 ? '#3f7d54' : dAff > 0.01 ? '#8b2530' : CC.ink3), ...TNUM }}>{dAff == null ? '—' : (dAff >= 0 ? '+' : '') + dAff.toFixed(2)}</div>
        </div>
      </div>
      <p style={{ margin: '12px 0 0', fontSize: 13, lineHeight: 1.5, color: CC.ink2 }}>
        <span style={{ color: CC.ink3 }}>The hope: </span>{iv.expected_naive_effect}
      </p>
      <div style={{ display: 'flex', gap: 8, marginTop: 13, alignItems: 'center', flexWrap: 'wrap', paddingTop: 12, borderTop: `1px solid ${CC.border}` }}>
        <Eyebrow style={{ fontSize: 9.5 }}>Provenance</Eyebrow>
        <span style={{ fontSize: 11.5, fontFamily: MONO, ...TNUM }}>
          <span style={{ color: '#3f7d54' }}>{empirical} empirical</span> <span style={{ color: CC.ink4 }}>·</span> <span style={{ color: CC.ink3 }}>{pv['T'] || 0} theoretical</span>{pv['C'] ? <span style={{ color: CC.ink3 }}> · {pv['C']} contested</span> : null}
        </span>
      </div>
      {!has && <p style={{ margin: '11px 0 0', fontSize: 11.5, color: CC.ink3, fontStyle: 'italic' }}>This run isn't bundled in the offline sample — buckets and provenance are live; the counterfactual cloud needs its precomputed file.</p>}
    </FloatCard>
  );
}

function CharLegend() {
  return (
    <FloatCard style={{ left: 22, bottom: 18, padding: '9px 15px' }}>
      <div style={{ display: 'flex', gap: 16, alignItems: 'center', fontSize: 12.5, color: CC.ink2 }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 7 }}><PartySwatch party="D" /> Democrat</span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 7 }}><PartySwatch party="I" /> Independent</span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 7 }}><PartySwatch party="R" /> Republican</span>
      </div>
    </FloatCard>
  );
}

function ProtoApp() {
  const ph = usePlayhead({ initial: 0, autoplay: true, baseTicksPerSec: 3 });
  const { tick, setTick, playing, setPlaying, toggle, speed, setSpeed } = ph;
  const [screen, setScreen] = React.useState('intro');
  const [charKey, setCharKey] = React.useState('linda');
  const [intervention, setIntervention] = React.useState(null);

  const idx = D.chars[charKey].agent_index;
  const isCF = intervention != null && HAS_RUN[intervention];
  const run = isCF ? D.runs[intervention] : D.runs.baseline;

  // intro plays at a calm ambient pace from 1980; stepping in carries the tick over
  const introInit = React.useRef(false);
  React.useEffect(() => {
    if (screen === 'intro' && !introInit.current) {
      introInit.current = true;
      setTick(0); setSpeed(0.3); setPlaying(true);
    }
  }, [screen, setTick, setSpeed, setPlaying]);
  const stepInside = () => { setScreen('player'); setTick(0); setSpeed(1); setPlaying(false); };
  // ambient loop: when the intro reaches 2025, pause a beat then replay from 1980
  React.useEffect(() => {
    if (screen === 'intro' && !playing && tick >= LAST) {
      const id = setTimeout(() => { setTick(0); setPlaying(true); }, 1400);
      return () => clearTimeout(id);
    }
  }, [screen, playing, tick, setTick, setPlaying]);
  const cfColor = intervention ? D.interventions[intervention].color : CC.ink;
  const year = Math.floor(tickToYear(tick));
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const frac = tickToYear(tick) - year;
  const monthLabel = `${months[Math.min(11, Math.floor(frac * 12))]} ${year}`;

  if (screen === 'intro') {
    return (
      <div style={{ width: '100vw', height: '100vh', background: CC.bg, color: CC.ink, fontFamily: SANS, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{ height: 60, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 40px', borderBottom: `1px solid ${CC.border}`, flexShrink: 0 }}>
          <Logo />
          <div style={{ display: 'flex', gap: 26, fontSize: 13.5, color: CC.ink3 }}>
            <span style={{ color: CC.ink, fontWeight: 500 }}>The story</span><span>Characters</span><span>Interventions</span><span>Methods</span><span>About</span>
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', flex: 1, minHeight: 0 }}>
          <div style={{ padding: '6vh 4vw', display: 'flex', flexDirection: 'column', maxWidth: 640 }}>
            <Eyebrow color={CC.ink3}>An interactive history of American polarization · 1980–2025</Eyebrow>
            <h1 style={{ margin: '22px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: 'clamp(48px, 5.5vw, 78px)', lineHeight: 0.98, letterSpacing: '-.025em' }}>Calm to Camps</h1>
            <p style={{ margin: '20px 0 0', fontFamily: SERIF, fontStyle: 'italic', fontSize: 'clamp(17px,1.5vw,21px)', lineHeight: 1.4, color: CC.ink2, maxWidth: 480 }}>How a country that mostly agreed to disagree sorted itself into two camps that can barely speak.</p>
            <p style={{ margin: '24px 0 0', fontSize: 15.5, lineHeight: 1.6, color: CC.ink2, maxWidth: 470 }}>Watch 250 Americans drift across the political compass over forty-five years. Follow four of them by name. See the events that pushed them — and try the interventions that were supposed to bring them back together.</p>
            <div style={{ marginTop: 34 }}>
              <Eyebrow>You'll follow</Eyebrow>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 12, maxWidth: 470 }}>
                {[['linda', 'Suburban swing voter'], ['bob', 'Tea Party → MAGA'], ['james', 'Stable left, cooling'], ['maria', 'Independent → left']].map(([id, desc]) => {
                  const c = D.chars[id];
                  const finalParty = D.runs.baseline.party[LAST][c.agent_index];
                  return (
                    <div key={id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', background: CC.surface, border: `1px solid ${CC.border}`, borderRadius: 10 }}>
                      <PartySwatch party={PARTY_CH[finalParty]} size={10} />
                      <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.2 }}>
                        <span style={{ fontSize: 14, fontWeight: 600 }}>{c.name}</span>
                        <span style={{ fontSize: 12, color: CC.ink3 }}>{desc}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            <div style={{ marginTop: 'auto', paddingTop: 36, display: 'flex', alignItems: 'center', gap: 18 }}>
              <button onClick={stepInside} style={{
                display: 'inline-flex', alignItems: 'center', gap: 11, padding: '14px 24px', background: CC.ink, color: '#fff',
                fontSize: 15, fontWeight: 500, borderRadius: 999, cursor: 'pointer', border: 'none', fontFamily: SANS,
              }}>Step inside the simulation <span style={{ fontSize: 11 }}>→</span></button>
              <span style={{ fontSize: 13, color: CC.ink3, fontFamily: MONO, ...TNUM }}>now showing {year}</span>
            </div>
          </div>
          <div style={{ position: 'relative', borderLeft: `1px solid ${CC.border}`, background: CC.surface, display: 'flex', flexDirection: 'column', padding: '3vh 2vw', minHeight: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexShrink: 0 }}>
              <span style={{ fontFamily: SERIF, fontStyle: 'italic', fontSize: 19, color: CC.ink2 }}>The United States, {year}</span>
              <span style={{ fontSize: 12.5, color: CC.ink3, display: 'inline-flex', alignItems: 'center', gap: 7 }}><span style={{ width: 7, height: 7, borderRadius: 999, background: '#3f7d54' }} /> playing</span>
            </div>
            <div style={{ flex: 1, position: 'relative', minHeight: 0, marginTop: 10 }}>
              <ProtoCompass tick={tick} run={D.runs.baseline} spotlightIdx={idx} />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // player
  return (
    <div style={{ width: '100vw', height: '100vh', background: CC.bg, color: CC.ink, fontFamily: SANS, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{ height: 56, flexShrink: 0, display: 'flex', alignItems: 'center', gap: 18, padding: '0 22px', borderBottom: `1px solid ${CC.border}`, position: 'relative', zIndex: 30 }}>
        <button onClick={() => setScreen('intro')} style={{ border: 'none', background: 'transparent', cursor: 'pointer', padding: 0 }}><Logo /></button>
        <span style={{ width: 1, height: 18, background: CC.border }} />
        <span style={{ fontFamily: SERIF, fontStyle: 'italic', fontSize: 16, color: CC.ink2, whiteSpace: 'nowrap' }}>Calm to Camps</span>
        <span style={{ flex: 1 }} />
        <InterventionPicker active={intervention} onPick={setIntervention} />
        <span style={{ fontSize: 13, color: CC.ink2, display: 'inline-flex', alignItems: 'center', gap: 7, padding: '6px 13px', border: `1px solid ${CC.border}`, borderRadius: 999 }}>About this model <InfoDot /></span>
      </div>

      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 420px', minHeight: 0 }}>
        <div style={{ position: 'relative', background: CC.surface, height: '100%', minHeight: 0 }}>
          <div style={{ position: 'absolute', inset: 0, padding: '18px 26px', display: 'flex' }}>
            <ProtoCompass tick={tick} run={run} baselineRun={isCF ? D.runs.baseline : null} spotlightIdx={idx} mode={isCF ? 'counterfactual' : 'normal'} />
          </div>
          {isCF && (
            <FloatCard style={{ left: 22, top: 22, width: 292 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Eyebrow style={{ color: CC.ink3 }}>Counterfactual vs actual</Eyebrow>
                <span style={{ display: 'flex', gap: 10, alignItems: 'center', fontSize: 10.5, color: CC.ink3 }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 12, borderTop: `1.5px dashed ${CC.ink4}` }} /> actual</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 12, height: 2, background: cfColor }} /> this</span>
                </span>
              </div>
              <div style={{ marginTop: 10 }}><ProtoSparklines tick={tick} run={D.runs.baseline} cfRun={run} color={cfColor} width={260} /></div>
            </FloatCard>
          )}
          {intervention && <ResultCard id={intervention} tick={tick} />}
          {!isCF && <CharLegend />}
        </div>

        <div style={{ padding: '18px 28px 22px', borderLeft: `1px solid ${CC.border}`, background: CC.bg, overflow: 'hidden', minHeight: 0 }}>
          <ProtoCharacter tick={tick} run={run} charKey={charKey} tabs={TAB_KEYS} onTab={setCharKey} />
        </div>
      </div>

      <div style={{ minHeight: 150, flexShrink: 0, borderTop: `1px solid ${CC.border}`, background: CC.bg, display: 'flex', alignItems: 'center', gap: 28, padding: '14px 32px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 9, flexShrink: 0 }}>
          <Transport playing={playing} toggle={toggle} setTick={setTick} speed={speed} setSpeed={setSpeed} />
          <span style={{ fontFamily: MONO, fontSize: 12.5, color: CC.ink, ...TNUM }}>{monthLabel} <span style={{ color: CC.ink4 }}>· tick {Math.round(tick)} / {LAST}</span></span>
        </div>
        <div style={{ width: 1, height: 100, background: CC.border }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <Eyebrow style={{ color: CC.ink3 }}>1980 → 2025 · drag to scrub</Eyebrow>
          <div style={{ marginTop: 4 }}><ProtoTimeline tick={tick} setTick={setTick} releaseTick={isCF ? run.release_tick : null} showReleases={isCF} color={cfColor} /></div>
        </div>
        <div style={{ width: 1, height: 100, background: CC.border }} />
        <div style={{ width: 300, flexShrink: 0 }}>
          <Eyebrow style={{ color: CC.ink3 }}>Where the country is</Eyebrow>
          <div style={{ marginTop: 2 }}><ProtoSparklines tick={tick} run={D.runs.baseline} width={300} /></div>
        </div>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<ProtoApp />);
