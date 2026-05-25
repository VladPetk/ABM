// Direction E — Fullscreen variant
// What happens when the user clicks "Open fullscreen ↗" on the landing.
// The whole viewport becomes the sim. Just the viz and the controls.
//
//   ┌─────────────────────────────────────────────────────────────┐
//   │ polarlab  ·  KPIs inline   ·   Scenarios ▾   ·  Exit ⤓      │  44px
//   ├─────────────────────────────────────────────────────────────┤
//   │                                                             │
//   │  [Parameters]              dot field            [Inspector] │
//   │                                                             │
//   │  [Sparkline]                                       [Legend] │
//   │                                                             │
//   ├─────────────────────────────────────────────────────────────┤
//   │ ▶ ⏭ ↺  Speed ½ 1× 2× 4×   ─────●─────   t = 2,460 / 5,000   │  44px
//   └─────────────────────────────────────────────────────────────┘

function WireframeEFull({ accent = true, mode = 'light' }) {
  const W = 1440, H = 900;
  const dark = mode === 'dark';
  const G = dark
    ? {
        bg: '#18181b', bg2: '#1f1f23', surface: '#1f1f23',
        ink: '#ecebe4', ink2: '#b6b6b0', ink3: '#86878a', ink4: '#54565a',
        border: '#2c2c30', borderS: '#3a3a40',
        r: '#c25c5c', b: '#7993cf', rSoft: '#2b1c1f', bSoft: '#1b2030',
      }
    : {
        bg: '#f3f3f0', bg2: '#ebe8df', surface: '#ffffff',
        ink: '#1a1d23', ink2: '#3d4148', ink3: '#74797f', ink4: '#adb1b5',
        border: '#e0ddd3', borderS: '#cdc9bd',
        r: '#8b2530', b: '#1f3565', rSoft: '#ead7d9', bSoft: '#d4d9e3',
      };
  const sans = "'Geist', system-ui, -apple-system, sans-serif";
  const mono = "'Geist Mono', ui-monospace, monospace";
  const tnum = { fontFeatureSettings: '"tnum", "ss01"' };
  const STRIP = 44;

  return (
    <div style={{
      width: W, height: H,
      background: dark ? G.bg : G.surface,
      color: G.ink, fontFamily: sans,
      position: 'relative', overflow: 'hidden',
      letterSpacing: '-.005em',
      display: 'flex', flexDirection: 'column',
    }}>

      {/* ── Top strip: logo · inline KPIs · scenarios · exit ─────────── */}
      <div style={{
        height: STRIP, flexShrink: 0,
        display: 'flex', alignItems: 'center', gap: 22,
        padding: '0 24px',
        borderBottom: `1px solid ${G.border}`,
        background: dark ? G.bg : G.bg,
      }}>
        {/* logo */}
        <span style={{ display: 'flex', alignItems: 'center', gap: 8,
          fontSize: 13.5, fontWeight: 600, letterSpacing: '-.015em' }}>
          <span style={{ display: 'inline-flex', gap: 3 }}>
            <span style={{ width: 7, height: 7, borderRadius: 999, background: G.b }} />
            <span style={{ width: 7, height: 7, borderRadius: 999, background: G.r }} />
          </span>
          polarlab
        </span>

        <span style={{ width: 1, height: 18, background: G.border }} />

        {/* inline KPIs */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 22, fontSize: 12.5 }}>
          <MiniStat tokens={G} label="polarization"    value="0.81"  accent />
          <MiniStat tokens={G} label="cross-talk"      value="3%"    trend="↓" />
          <MiniStat tokens={G} label="largest faction" value="54%" />
          <MiniStat tokens={G} label="bimodality"      value="0.92" />
        </div>

        <span style={{ flex: 1 }} />

        {/* scenarios menu */}
        <span style={{
          fontSize: 13, color: G.ink2, display: 'inline-flex',
          alignItems: 'center', gap: 6, padding: '6px 12px',
          border: `1px solid ${G.border}`, borderRadius: 999, cursor: 'default',
        }}>
          <span style={{ color: G.r, fontSize: 9 }}>●</span>
          Echo chamber
          <span style={{ color: G.ink3, fontSize: 11 }}>▾</span>
        </span>

        {/* exit fullscreen */}
        <span style={{
          fontSize: 13, color: G.ink, fontWeight: 500,
          display: 'inline-flex', alignItems: 'center', gap: 7,
          padding: '6px 14px',
          border: `1px solid ${G.ink}`, borderRadius: 999, cursor: 'default',
        }}>
          <ExitIcon color={G.ink} />
          Exit fullscreen
        </span>
      </div>

      {/* ── Stage ───────────────────────────────────────────────────── */}
      <div style={{
        position: 'relative', flex: 1,
        background: dark ? G.bg2 : G.surface,
      }}>
        <ModernSimGrid tokens={G} accent={accent} dark={dark} />

        {/* Parameters — fuller in fullscreen */}
        <FloatingCard tokens={G} dark={dark} style={{ left: 28, top: 28, width: 288 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: 12.5, fontWeight: 600, color: G.ink, letterSpacing: '-.005em' }}>Parameters</span>
            <span style={{ fontSize: 11, color: G.ink3, fontFamily: mono, ...tnum }}>6 / 12</span>
          </div>
          <ModernSlider tokens={G} label="homophily"   value={0.72} display="0.72" info />
          <ModernSlider tokens={G} label="tolerance"   value={0.28} display="0.28" info />
          <ModernSlider tokens={G} label="persuasion"  value={0.12} display="0.12" info />
          <ModernSlider tokens={G} label="media bias"  value={0.55} display="+0.10" centered info />
          <ModernSlider tokens={G} label="noise"       value={0.05} display="0.05" info />
          <div style={{ marginBottom: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 5 }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12.5, color: G.ink2 }}>
                topology
                <span style={{
                  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                  width: 13, height: 13, borderRadius: 999,
                  border: `1px solid ${G.ink4}`, color: G.ink3,
                  fontSize: 9, fontWeight: 500, lineHeight: 1, fontStyle: 'italic',
                }}>i</span>
              </span>
              <span style={{ fontSize: 11, color: G.ink3, fontFamily: mono }}>small-world ▾</span>
            </div>
            <div style={{ display: 'flex', gap: 3 }}>
              {['lattice','random','small-world','scale-free'].map((s, i) => (
                <span key={s} style={{
                  fontSize: 10.5, padding: '3px 7px', borderRadius: 999,
                  border: `1px solid ${i === 2 ? G.ink : G.border}`,
                  color: i === 2 ? G.ink : G.ink3,
                  background: i === 2 ? (dark ? G.bg2 : '#fff') : 'transparent',
                  fontWeight: i === 2 ? 500 : 400,
                }}>{s}</span>
              ))}
            </div>
          </div>
          <div style={{
            marginTop: 12, paddingTop: 10, borderTop: `1px solid ${G.border}`,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            fontSize: 12, color: G.ink3,
          }}>
            <span>Show advanced (6 more)</span>
            <span style={{ fontFamily: mono }}>+</span>
          </div>
        </FloatingCard>

        {/* Inspector — same as landing */}
        <FloatingCard tokens={G} dark={dark} style={{ right: 28, top: 28, width: 288 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: 12.5, fontWeight: 600, color: G.ink, letterSpacing: '-.005em' }}>
              Agent <span style={{ fontFamily: mono, color: G.ink2, ...tnum }}>#1287</span>
            </span>
            <span style={{
              fontSize: 10.5, color: accent ? G.r : G.ink2,
              background: accent ? G.rSoft : G.bg2,
              padding: '2px 8px', borderRadius: 999, letterSpacing: '.04em',
            }}>position B</span>
          </div>
          <InspectorRow tokens={G} label="opinion"    value="+0.68" mono={mono} />
          <InspectorRow tokens={G} label="certainty"  value="0.41"  mono={mono} />
          <InspectorRow tokens={G} label="neighbours" value="6"     mono={mono} />
          <InspectorRow tokens={G} label="last shift" value="+0.04" mono={mono} last />
          <div style={{ marginTop: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 6 }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6,
                fontSize: 11, color: G.ink3, letterSpacing: '.02em' }}>
                Neighbourhood
                <span style={{
                  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                  width: 12, height: 12, borderRadius: 999,
                  border: `1px solid ${G.ink4}`, color: G.ink3,
                  fontSize: 8.5, fontWeight: 500, lineHeight: 1,
                  fontStyle: 'italic', cursor: 'default',
                }}>i</span>
              </span>
              <span style={{ fontSize: 11, color: G.ink3 }}>
                diversity{' '}
                <span style={{ color: G.ink, fontFamily: mono, fontFeatureSettings: '"tnum"' }}>0.17</span>
              </span>
            </div>
            <NeighbourhoodMap tokens={G} accent={accent} dark={dark} agentOp={0.68} />
            <div style={{
              marginTop: 4, fontSize: 11.5, color: G.ink3,
              display: 'flex', justifyContent: 'space-between',
            }}>
              <span>5 alike · 1 outlier</span>
              <span style={{ color: accent ? G.r : G.ink2 }}>echo-chamber risk ↑</span>
            </div>
          </div>
          <div style={{ marginTop: 12 }}>
            <div style={{ fontSize: 11, color: G.ink3, marginBottom: 6, letterSpacing: '.02em' }}>Belief over time</div>
            <svg viewBox="0 0 252 56" width="100%" height="56" style={{ display: 'block' }}>
              <line x1="0" y1="28" x2="252" y2="28" stroke={G.border} strokeDasharray="2 3" />
              <path d="M0,40 C30,38 50,34 80,28 S160,10 252,5"
                    fill="none" stroke={accent ? G.r : G.ink} strokeWidth="1.5" />
            </svg>
          </div>
          <div style={{ marginTop: 10, fontSize: 11.5, color: G.ink3, display: 'flex', justifyContent: 'space-between' }}>
            <span>Pinned · click sim to unpin</span>
            <span style={{ color: G.ink }}>✕</span>
          </div>
        </FloatingCard>

        {/* Sparkline — bigger in fullscreen */}
        <FloatingCard tokens={G} dark={dark} style={{ left: 28, bottom: 28, width: 288, padding: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 }}>
            <span style={{ fontSize: 12.5, color: G.ink, fontWeight: 500 }}>Polarization over time</span>
            <span style={{ fontSize: 12, color: G.ink, fontFamily: mono, ...tnum }}>0.81</span>
          </div>
          <svg viewBox="0 0 260 70" width="100%" height="70" style={{ display: 'block' }}>
            <line x1="0" y1="35" x2="260" y2="35" stroke={G.border} strokeDasharray="2 3" />
            <line x1="0" y1="58" x2="260" y2="58" stroke={G.border} />
            <text x="0" y="68" fontSize="9" fill={G.ink4} fontFamily="'Geist Mono', monospace">0</text>
            <text x="240" y="68" fontSize="9" fill={G.ink4} fontFamily="'Geist Mono', monospace">2.5k</text>
            <path d="M0,56 C20,54 40,48 70,40 S140,12 260,5" fill="none"
                  stroke={accent ? G.r : G.ink} strokeWidth="1.75" />
            {/* current tick */}
            <line x1="180" y1="0" x2="180" y2="58" stroke={G.ink4} strokeDasharray="1 3" />
          </svg>
        </FloatingCard>

        {/* Legend — bottom right */}
        <FloatingCard tokens={G} dark={dark} style={{ right: 28, bottom: 28, padding: '12px 18px' }}>
          <div style={{ display: 'flex', gap: 18, alignItems: 'center', fontSize: 12.5, color: G.ink2 }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
              <span style={{ width: 9, height: 9, borderRadius: 999, background: accent ? G.b : G.ink }} /> Position A
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
              <span style={{ width: 9, height: 9, borderRadius: 999, background: G.ink4 }} /> Undecided
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
              <span style={{ width: 9, height: 9, borderRadius: 999, background: accent ? G.r : '#888' }} /> Position B
            </span>
          </div>
        </FloatingCard>
      </div>

      {/* ── Transport ───────────────────────────────────────────────── */}
      <div style={{
        height: STRIP, flexShrink: 0,
        display: 'flex', alignItems: 'center', gap: 14,
        padding: '0 24px',
        borderTop: `1px solid ${G.border}`,
        background: dark ? G.bg : G.bg,
      }}>
        <CircleBtn tokens={G} icon="▶" filled small />
        <CircleBtn tokens={G} icon="⏭" small />
        <CircleBtn tokens={G} icon="↺" small />
        <div style={{ width: 1, height: 14, background: G.border, margin: '0 2px' }} />
        <span style={{ fontSize: 11.5, color: G.ink3 }}>Speed</span>
        <div style={{ display: 'flex', gap: 3 }}>
          {['½','1×','2×','4×'].map((s, i) => (
            <span key={s} style={{
              fontSize: 11, padding: '2px 8px', borderRadius: 999,
              border: `1px solid ${i === 1 ? G.ink : G.border}`,
              color: i === 1 ? G.ink : G.ink3,
              fontFamily: mono, fontWeight: i === 1 ? 500 : 400, ...tnum,
              background: i === 1 ? (dark ? G.bg2 : '#fff') : 'transparent',
            }}>{s}</span>
          ))}
        </div>
        <div style={{ flex: 1, position: 'relative', height: 3,
          background: dark ? G.bg2 : G.bg2, borderRadius: 999, marginLeft: 6 }}>
          <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: '49%',
            background: G.ink, borderRadius: 999 }} />
          <div style={{ position: 'absolute', left: '49%', top: -4, width: 11, height: 11,
            background: dark ? G.surface : '#fff', border: `1.5px solid ${G.ink}`,
            borderRadius: 999, transform: 'translateX(-50%)' }} />
        </div>
        <span style={{ fontFamily: mono, fontSize: 11.5, color: G.ink2,
          minWidth: 110, textAlign: 'right', ...tnum }}>t = 2,460 / 5,000</span>
      </div>
    </div>
  );
}

// Small inline KPI for the top strip in fullscreen.
function MiniStat({ tokens, label, value, trend, accent }) {
  const G = tokens;
  return (
    <span style={{ display: 'inline-flex', alignItems: 'baseline', gap: 6 }}>
      <span style={{ color: G.ink3, fontSize: 11.5 }}>{label}</span>
      <span style={{
        color: G.ink, fontSize: 13.5, fontWeight: 500,
        fontFeatureSettings: '"tnum"',
      }}>{value}</span>
      {trend && (
        <span style={{ color: accent ? G.r : G.ink3, fontSize: 11 }}>{trend}</span>
      )}
    </span>
  );
}

// Exit-fullscreen glyph (two opposing corners pointing inward).
function ExitIcon({ color }) {
  return (
    <svg width="13" height="13" viewBox="0 0 13 13" style={{ display: 'block' }}>
      <path d="M5 1 V5 H1 M8 12 V8 H12 M1 5 L5 5 L5 1 M12 8 L8 8 L8 12"
            fill="none" stroke={color} strokeWidth="1.4" strokeLinecap="square" />
      <path d="M5 5 L1 1 M8 8 L12 12" fill="none" stroke={color} strokeWidth="1.4" />
    </svg>
  );
}

window.WireframeEFull = WireframeEFull;
