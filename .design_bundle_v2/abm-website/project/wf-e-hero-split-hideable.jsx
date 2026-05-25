// Direction E — "Hero split" with HIDEABLE parameters panel.
//
// Two states:
//   1. Collapsed (default) — small pill in the top-left of the sim, showing
//      "Parameters · 4 set" with a chevron. The sim is unobstructed.
//   2. Expanded — full panel with an explicit × close affordance.
//
// Plus a third variant: parameters docked as a bottom rail beneath the sim
// (never overlaps, always visible — for comparison).

function WireframeEHeroSplitHideable({
  accent = true, mode = 'light',
  paramsState = 'collapsed', // 'collapsed' | 'expanded' | 'rail'
}) {
  const W = 1440, H = 810;
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

  const isRail = paramsState === 'rail';
  // When parameters are docked as a rail, the sim shrinks vertically to make
  // room — we steal 88px from the sim area for the rail.
  const railH = 88;

  return (
    <div style={{
      width: W, height: H, background: G.bg, color: G.ink,
      fontFamily: sans, position: 'relative', overflow: 'hidden',
      letterSpacing: '-.005em',
    }}>

      {/* ── Top utility bar ───────────────────────────────────────────── */}
      <div style={{
        height: 56, display: 'flex', alignItems: 'center', justifyContent: 'flex-start',
        padding: '0 36px', borderBottom: `1px solid ${G.border}`,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
          <span style={{ fontSize: 14, fontWeight: 600, letterSpacing: '-.015em', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ display: 'inline-flex', gap: 3 }}>
              <span style={{ width: 7, height: 7, borderRadius: 999, background: G.b }} />
              <span style={{ width: 7, height: 7, borderRadius: 999, background: G.r }} />
            </span>
            polarlab
          </span>
          <div style={{ display: 'flex', gap: 26, fontSize: 13.5, color: G.ink3 }}>
            <span style={{ color: G.ink, fontWeight: 500 }}>Playground</span>
            <span>About</span>
            <span>Methods</span>
            <span>Cite</span>
          </div>
        </div>
      </div>

      {/* ── Hero split ───────────────────────────────────────────────── */}
      <div style={{
        height: H - 56 - 120,
        padding: '0 0 0 60px',
        display: 'grid', gridTemplateColumns: '600px 1fr', columnGap: 60,
        alignItems: 'stretch',
      }}>

        {/* LEFT — title, body, KPIs, scenarios, CTA */}
        <div style={{
          display: 'flex', flexDirection: 'column', gap: 22,
          padding: '40px 0 40px',
        }}>
          <h1 style={{
            margin: 0, fontWeight: 500,
            fontSize: 52, lineHeight: 1.02, letterSpacing: '-.028em',
            color: G.ink,
          }}>
            How echoes become walls.
          </h1>

          <p style={{
            margin: 0, fontSize: 15.5, lineHeight: 1.55,
            color: G.ink2, fontWeight: 400,
          }}>
            A live agent-based model of opinion dynamics. Six hundred agents start near the
            centre. Each updates toward neighbours it considers reasonable — and ignores the
            rest. You decide how reasonable.
          </p>

          {/* KPI strip */}
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 0,
            borderTop: `1px solid ${G.border}`,
            borderBottom: `1px solid ${G.border}`,
          }}>
            <KPI2 tokens={G} label="polarization"     value="0.81" trend="↑ +12%"      accent info compact />
            <KPI2 tokens={G} label="cross-talk"       value="3%"   trend="↓ from 41%"        info compact />
            <KPI2 tokens={G} label="largest faction"  value="54%"  trend="B-leaning"         info compact />
            <KPI2 tokens={G} label="bimodality"       value="0.92" trend="sharp split"       info compact last />
          </div>

          {/* Scenarios */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <span style={{
              fontSize: 11, color: G.ink3, letterSpacing: '.14em',
              textTransform: 'uppercase', fontWeight: 500,
            }}>Currently running</span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 22, alignItems: 'baseline' }}>
              <ScenarioLink2 tokens={G} lead="Echo"         tail="chamber" selected />
              <ScenarioLink2 tokens={G} lead="Mixed"        tail="society" />
              <ScenarioLink2 tokens={G} lead="Media-driven" tail="drift" />
              <ScenarioLink2 tokens={G} lead="Extremist"    tail="seed" />
            </div>
          </div>

          {/* CTA pinned to bottom */}
          <div style={{ flex: 1, display: 'flex', alignItems: 'flex-end' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <span style={{
                display: 'inline-flex', alignItems: 'center', gap: 10,
                padding: '11px 18px 11px 20px',
                background: G.ink, color: dark ? G.bg : '#fff',
                fontSize: 14, fontWeight: 500, letterSpacing: '-.005em',
                borderRadius: 999, cursor: 'default',
              }}>
                Open fullscreen
                <span style={{ fontSize: 13, opacity: .9 }}>↗</span>
              </span>
              <span style={{ fontSize: 13.5, color: G.ink3 }}>
                · or tweak right here
              </span>
            </div>
          </div>
        </div>

        {/* RIGHT — sim column */}
        <div style={{
          display: 'flex', flexDirection: 'column',
          background: dark ? G.bg2 : G.surface,
          borderLeft: `1px solid ${G.border}`,
          alignSelf: 'stretch', position: 'relative',
        }}>
          <div style={{ position: 'relative', flex: 1, minHeight: 0 }}>
            <WideSimGrid2 tokens={G} accent={accent} dark={dark} />

            {/* ── Parameters: state machine ─────────────────────────── */}
            {paramsState === 'collapsed' && (
              <ParametersPill tokens={G} dark={dark} mono={mono} accent={accent} />
            )}

            {paramsState === 'expanded' && (
              <FloatingCardSplit2 tokens={G} dark={dark} style={{ left: 20, top: 20, width: 252 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                  <span style={{ fontSize: 12.5, fontWeight: 600, color: G.ink, letterSpacing: '-.005em' }}>Parameters</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontSize: 11, color: G.ink3, fontFamily: mono, ...tnum }}>4 / 12</span>
                    {/* Close affordance — communicates hideability */}
                    <span style={{
                      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                      width: 16, height: 16, borderRadius: 999,
                      color: G.ink3, fontSize: 11, lineHeight: 1, cursor: 'default',
                      border: `1px solid ${G.border}`,
                    }}>×</span>
                  </div>
                </div>
                <ModernSlider2 tokens={G} label="homophily"  value={0.72} display="0.72" info />
                <ModernSlider2 tokens={G} label="tolerance"  value={0.28} display="0.28" info />
                <ModernSlider2 tokens={G} label="persuasion" value={0.12} display="0.12" info />
                <ModernSlider2 tokens={G} label="media bias" value={0.55} display="+0.10" centered info />
                <div style={{
                  marginTop: 10, paddingTop: 10, borderTop: `1px solid ${G.border}`,
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  fontSize: 12, color: G.ink3,
                }}>
                  <span>Show advanced</span>
                  <span style={{ fontFamily: mono }}>+</span>
                </div>
              </FloatingCardSplit2>
            )}

            {/* When rail mode is active, no top-left card at all — the rail
                lives below the sim. We still show the other floating cards. */}

            {/* Inspector — bottom right (always present) */}
            <FloatingCardSplit2 tokens={G} dark={dark} style={{ right: 20, bottom: 20, width: 244 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <span style={{ fontSize: 12.5, fontWeight: 600, color: G.ink }}>
                  Agent <span style={{ fontFamily: mono, color: G.ink2, ...tnum }}>#1287</span>
                </span>
                <span style={{
                  fontSize: 10.5, color: accent ? G.r : G.ink2,
                  background: accent ? G.rSoft : G.bg2,
                  padding: '2px 8px', borderRadius: 999, letterSpacing: '.04em',
                }}>position B</span>
              </div>
              <InspectorRow2 tokens={G} label="opinion"    value="+0.68" mono={mono} />
              <InspectorRow2 tokens={G} label="certainty"  value="0.41"  mono={mono} />
              <InspectorRow2 tokens={G} label="neighbours" value="6"     mono={mono} last />
              <div style={{ marginTop: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 5 }}>
                  <span style={{ fontSize: 11, color: G.ink3 }}>Neighbourhood</span>
                  <span style={{ fontSize: 11, color: G.ink3 }}>
                    diversity{' '}
                    <span style={{ color: G.ink, fontFamily: mono, ...tnum }}>0.17</span>
                  </span>
                </div>
                <NeighbourhoodMap2 tokens={G} accent={accent} dark={dark} agentOp={0.68} />
                <div style={{
                  marginTop: 2, fontSize: 11.5, color: G.ink3,
                  display: 'flex', justifyContent: 'space-between',
                }}>
                  <span>5 alike · 1 outlier</span>
                  <span style={{ color: accent ? G.r : G.ink2 }}>echo-chamber risk ↑</span>
                </div>
              </div>
            </FloatingCardSplit2>

            {/* Sparkline — top right */}
            <FloatingCardSplit2 tokens={G} dark={dark} style={{ right: 20, top: 20, width: 196, padding: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ fontSize: 11, color: G.ink3 }}>Polarization</span>
                <span style={{ fontSize: 11.5, color: G.ink, fontFamily: mono, ...tnum }}>0.81</span>
              </div>
              <svg viewBox="0 0 176 28" width="100%" height="28" style={{ display: 'block', marginTop: 4 }}>
                <line x1="0" y1="14" x2="176" y2="14" stroke={G.border} strokeDasharray="2 3" />
                <path d="M0,22 C18,21 28,18 46,15 S96,4 176,2"
                      fill="none" stroke={accent ? G.r : G.ink} strokeWidth="1.5" />
              </svg>
            </FloatingCardSplit2>

            {/* Legend — bottom left, only when not docked rail (rail shows it inline) */}
            {!isRail && (
              <FloatingCardSplit2 tokens={G} dark={dark} style={{ left: 20, bottom: 20, padding: '8px 14px' }}>
                <div style={{ display: 'flex', gap: 14, alignItems: 'center', fontSize: 12, color: G.ink2 }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 8, height: 8, borderRadius: 999, background: accent ? G.b : G.ink }} /> A
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 8, height: 8, borderRadius: 999, background: G.ink4 }} /> ?
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 8, height: 8, borderRadius: 999, background: accent ? G.r : '#888' }} /> B
                  </span>
                </div>
              </FloatingCardSplit2>
            )}
          </div>

          {/* ── Bottom rail (only in rail mode): parameters live here ── */}
          {isRail && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 0,
              padding: '14px 20px', height: railH, flexShrink: 0,
              borderTop: `1px solid ${G.border}`,
              background: dark ? G.bg : G.bg,
            }}>
              <RailSlider tokens={G} mono={mono} label="homophily"  value={0.72} display="0.72" />
              <div style={{ width: 1, height: 32, background: G.border, margin: '0 18px' }} />
              <RailSlider tokens={G} mono={mono} label="tolerance"  value={0.28} display="0.28" />
              <div style={{ width: 1, height: 32, background: G.border, margin: '0 18px' }} />
              <RailSlider tokens={G} mono={mono} label="persuasion" value={0.12} display="0.12" />
              <div style={{ width: 1, height: 32, background: G.border, margin: '0 18px' }} />
              <RailSlider tokens={G} mono={mono} label="media bias" value={0.55} display="+0.10" centered />
              <div style={{ width: 1, height: 32, background: G.border, margin: '0 18px' }} />
              <span style={{
                fontSize: 12, color: G.ink3, whiteSpace: 'nowrap',
                display: 'flex', alignItems: 'center', gap: 6,
              }}>
                <span style={{ fontFamily: mono, ...tnum }}>+8 more</span>
                <span style={{ color: G.ink2 }}>›</span>
              </span>
            </div>
          )}

          {/* Transport bar — always present */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 12,
            padding: '0 20px', height: 44, flexShrink: 0,
            borderTop: `1px solid ${G.border}`,
            background: dark ? G.bg : G.bg,
          }}>
            <CircleBtn2 tokens={G} icon="▶" filled small />
            <CircleBtn2 tokens={G} icon="⏭" small />
            <CircleBtn2 tokens={G} icon="↺" small />
            <div style={{ width: 1, height: 14, background: G.border, margin: '0 2px' }} />
            <div style={{ display: 'flex', gap: 3 }}>
              {['½','1×','2×','4×'].map((s, i) => (
                <span key={s} style={{
                  fontSize: 10.5, padding: '2px 7px', borderRadius: 999,
                  border: `1px solid ${i === 1 ? G.ink : G.border}`,
                  color: i === 1 ? G.ink : G.ink3,
                  fontFamily: mono, fontWeight: i === 1 ? 500 : 400, ...tnum,
                  background: i === 1 ? (dark ? G.bg2 : '#fff') : 'transparent',
                }}>{s}</span>
              ))}
            </div>
            <div style={{ flex: 1, position: 'relative', height: 3,
              background: dark ? G.bg2 : G.bg2, borderRadius: 999, marginLeft: 4 }}>
              <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: '49%',
                background: G.ink, borderRadius: 999 }} />
              <div style={{ position: 'absolute', left: '49%', top: -4, width: 11, height: 11,
                background: dark ? G.surface : '#fff', border: `1.5px solid ${G.ink}`,
                borderRadius: 999, transform: 'translateX(-50%)' }} />
            </div>
            <span style={{ fontFamily: mono, fontSize: 11.5, color: G.ink2,
              minWidth: 100, textAlign: 'right', ...tnum }}>t = 2,460 / 5,000</span>
          </div>
        </div>
      </div>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <div style={{
        padding: '18px 60px 16px',
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 64,
        borderTop: `1px solid ${G.border}`,
        height: 120,
      }}>
        <Section2 tokens={G} title="How to read" compact>
          <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.55, color: G.ink2 }}>
            Each dot is one agent. Colour shows which side it currently leans toward; saturation,
            how strongly. A flat boundary between colours is a population that has stopped
            listening.
          </p>
        </Section2>

        <Section2 tokens={G} title="How to play" compact>
          <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.55, color: G.ink2 }}>
            Drag any slider; the sim resumes live. Hover a dot to inspect; click to pin. The URL
            captures the full configuration.
          </p>
        </Section2>
      </div>
    </div>
  );
}

// ── Collapsed Parameters pill ─────────────────────────────────────────
// Lives where the full card was; communicates *what* is collapsed by
// listing the four current values inline. Cheap to scan, single line,
// clickable to expand. Roughly 1/4 the footprint of the open card.
function ParametersPill({ tokens, dark, mono, accent }) {
  const G = tokens;
  const chip = (label, val) => (
    <span style={{ display: 'inline-flex', alignItems: 'baseline', gap: 5 }}>
      <span style={{ fontSize: 11, color: G.ink3 }}>{label}</span>
      <span style={{
        fontSize: 11.5, color: G.ink, fontFamily: mono,
        fontFeatureSettings: '"tnum", "ss01"',
      }}>{val}</span>
    </span>
  );
  return (
    <div style={{
      position: 'absolute', left: 20, top: 20,
      display: 'inline-flex', alignItems: 'center', gap: 14,
      padding: '7px 10px 7px 14px',
      background: dark ? 'rgba(31,31,35,.84)' : 'rgba(255,255,255,.88)',
      backdropFilter: 'blur(18px) saturate(140%)',
      WebkitBackdropFilter: 'blur(18px) saturate(140%)',
      border: `1px solid ${G.border}`,
      borderRadius: 999,
      boxShadow: dark
        ? '0 6px 22px rgba(0,0,0,.35)'
        : '0 4px 16px rgba(26,29,35,.05)',
    }}>
      <span style={{
        fontSize: 12, fontWeight: 600, color: G.ink, letterSpacing: '-.005em',
      }}>Parameters</span>
      <span style={{ width: 1, height: 12, background: G.border }} />
      {chip('homophily',  '0.72')}
      {chip('tolerance',  '0.28')}
      {chip('persuasion', '0.12')}
      {chip('media',      '+0.10')}
      <span style={{
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        width: 22, height: 22, borderRadius: 999,
        background: dark ? G.bg2 : G.bg,
        color: G.ink2, fontSize: 11, marginLeft: 2,
      }}>▾</span>
    </div>
  );
}

// ── Rail-sized slider for the docked-bottom variant ───────────────────
function RailSlider({ tokens, mono, label, value, display, centered }) {
  const G = tokens;
  const v = Math.max(0, Math.min(1, value));
  const thumbLeft = `${v * 100}%`;
  const tnum = { fontFeatureSettings: '"tnum", "ss01"' };
  return (
    <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 5 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <span style={{ fontSize: 11.5, color: G.ink2 }}>{label}</span>
        <span style={{ fontSize: 12, color: G.ink, fontFamily: mono, ...tnum }}>{display}</span>
      </div>
      <div style={{ position: 'relative', height: 14, display: 'flex', alignItems: 'center' }}>
        <div style={{ width: '100%', height: 2, background: G.border, borderRadius: 999 }} />
        {centered && (
          <div style={{ position: 'absolute', left: '50%', top: -2, width: 1, height: 6, background: G.ink4 }} />
        )}
        <div style={{
          position: 'absolute', left: 0, top: '50%', height: 2, marginTop: -1,
          width: centered ? `${Math.abs(v - 0.5) * 100}%` : `${v * 100}%`,
          marginLeft: centered ? (v >= 0.5 ? '50%' : `${v * 100}%`) : 0,
          background: G.ink, borderRadius: 999,
        }} />
        <div style={{
          position: 'absolute', left: thumbLeft, top: '50%',
          width: 10, height: 10, marginTop: -5, marginLeft: -5,
          background: '#fff', border: `1.5px solid ${G.ink}`, borderRadius: 999,
        }} />
      </div>
    </div>
  );
}

// ── Local copies of shared sub-components (avoid name clashes) ────────
function KPI2({ tokens, label, value, trend, accent, info, last, compact }) {
  const G = tokens;
  return (
    <div style={{
      padding: compact ? '10px 14px 12px' : '14px 18px 16px',
      borderRight: last ? 'none' : `1px solid ${G.border}`,
      display: 'flex', flexDirection: 'column', gap: 1,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6,
        fontSize: compact ? 10.5 : 11.5, color: G.ink3, letterSpacing: '.02em' }}>
        {label}
        {info && (
          <span style={{
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            width: compact ? 11 : 13, height: compact ? 11 : 13, borderRadius: 999,
            border: `1px solid ${G.ink4}`, color: G.ink3,
            fontSize: compact ? 8 : 9, fontWeight: 500, lineHeight: 1,
            fontStyle: 'italic', cursor: 'default',
          }}>i</span>
        )}
      </div>
      <div style={{
        fontSize: compact ? 22 : 28, fontWeight: 500, letterSpacing: '-.025em',
        color: G.ink, lineHeight: 1.05, marginTop: 2,
        fontFeatureSettings: '"tnum", "ss01"',
      }}>{value}</div>
      <div style={{
        fontSize: compact ? 10.5 : 11.5, color: accent ? G.r : G.ink3, marginTop: 2,
        letterSpacing: '.01em',
      }}>{trend}</div>
    </div>
  );
}

function ScenarioLink2({ tokens, lead, tail, selected }) {
  const G = tokens;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'baseline', gap: 8,
      fontSize: 17, letterSpacing: '-.012em', fontWeight: 500,
      color: G.ink, cursor: 'default',
    }}>
      <span style={selected ? {
        textDecoration: 'underline',
        textDecorationColor: G.r,
        textDecorationThickness: '1.5px',
        textUnderlineOffset: '7px',
      } : {}}>
        <span>{lead} </span>
        <span style={{ color: G.r }}>{tail}</span>
      </span>
      {!selected && (
        <span style={{ fontSize: 13.5, color: G.ink3, fontWeight: 400 }}>→</span>
      )}
    </span>
  );
}

function FloatingCardSplit2({ tokens, dark, style, children }) {
  const G = tokens;
  return (
    <div style={{
      position: 'absolute',
      background: dark ? 'rgba(31,31,35,.84)' : 'rgba(255,255,255,.88)',
      backdropFilter: 'blur(18px) saturate(140%)',
      WebkitBackdropFilter: 'blur(18px) saturate(140%)',
      border: `1px solid ${G.border}`,
      borderRadius: 12,
      padding: 12,
      boxShadow: dark
        ? '0 6px 22px rgba(0,0,0,.35)'
        : '0 6px 22px rgba(26,29,35,.06)',
      ...style,
    }}>{children}</div>
  );
}

function Section2({ tokens, title, compact, children }) {
  const G = tokens;
  return (
    <div>
      <h4 style={{
        margin: '0 0 4px', fontSize: 11, fontWeight: 500,
        letterSpacing: '.14em', textTransform: 'uppercase', color: G.ink3,
      }}>{title}</h4>
      {children}
    </div>
  );
}

function WideSimGrid2({ tokens, accent, dark }) {
  const G = tokens;
  const cols = 40, rows = 22;
  const W = 1280, H = 720;
  const rng = mulberry32(31);
  const cellW = W / cols, cellH = H / rows;
  const dots = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const u = (c / (cols - 1)) - 0.5;
      const v = (r / (rows - 1)) - 0.5;
      const region = u + v * 0.18 + (rng() - 0.5) * 0.22;
      const op = Math.tanh(region * 3.6);
      const x = c * cellW + cellW * 0.5 + (rng() - 0.5) * cellW * 0.3;
      const y = r * cellH + cellH * 0.5 + (rng() - 0.5) * cellH * 0.35;
      dots.push({ x, y, op, id: r * cols + c });
    }
  }
  const hexRGB = (h) => [parseInt(h.slice(1,3),16), parseInt(h.slice(3,5),16), parseInt(h.slice(5,7),16)];
  const [rR,rG,rB] = hexRGB(G.r);
  const [bR,bG,bB] = hexRGB(G.b);
  const tint = (op) => {
    if (!accent) {
      if (dark) { const g = Math.round(110 + Math.abs(op) * 140); return `rgb(${g},${g},${g})`; }
      const g = Math.round(180 - Math.abs(op) * 130);
      return `rgb(${g},${g},${g})`;
    }
    if (op > 0.06) {
      const t = Math.min(1, op);
      return `rgba(${rR},${rG},${rB},${0.32 + t * 0.58})`;
    } else if (op < -0.06) {
      const t = Math.min(1, -op);
      return `rgba(${bR},${bG},${bB},${0.32 + t * 0.58})`;
    }
    return dark ? 'rgba(200,200,200,0.32)' : 'rgba(120,120,120,0.30)';
  };
  const dotR = Math.min(cellW, cellH) * 0.32;
  const hover = dots[11 * cols + 27];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="100%"
         preserveAspectRatio="xMidYMid slice" style={{ display: 'block', position: 'absolute', inset: 0 }}>
      {dots.map((d) => (
        <circle key={d.id} cx={d.x} cy={d.y} r={dotR} fill={tint(d.op)} />
      ))}
      {hover && (
        <g>
          <circle cx={hover.x} cy={hover.y} r={dotR * 2.2} fill="none"
            stroke={G.ink} strokeWidth="1.2" />
        </g>
      )}
    </svg>
  );
}

// Slider, Inspector row, Neighbourhood, Button — re-implementations that
// avoid relying on names from sibling JSX files (each script has its own
// scope after Babel transpilation).
function ModernSlider2({ tokens, label, value, display, centered, info }) {
  const G = tokens;
  const v = Math.max(0, Math.min(1, value));
  const thumbLeft = `${v * 100}%`;
  const tnum = { fontFeatureSettings: '"tnum", "ss01"' };
  const mono = "'Geist Mono', ui-monospace, monospace";
  return (
    <div style={{ marginBottom: 9 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5,
          fontSize: 12, color: G.ink2 }}>
          {label}
          {info && (
            <span style={{
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              width: 11, height: 11, borderRadius: 999,
              border: `1px solid ${G.ink4}`, color: G.ink3,
              fontSize: 8, fontWeight: 500, lineHeight: 1, fontStyle: 'italic',
            }}>i</span>
          )}
        </span>
        <span style={{ fontSize: 12, color: G.ink, fontFamily: mono, ...tnum }}>{display}</span>
      </div>
      <div style={{ position: 'relative', height: 14, display: 'flex', alignItems: 'center' }}>
        <div style={{ width: '100%', height: 2, background: G.border, borderRadius: 999 }} />
        {centered && (
          <div style={{ position: 'absolute', left: '50%', top: -2, width: 1, height: 6, background: G.ink4 }} />
        )}
        <div style={{
          position: 'absolute', left: 0, top: '50%', height: 2, marginTop: -1,
          width: centered ? `${Math.abs(v - 0.5) * 100}%` : `${v * 100}%`,
          marginLeft: centered ? (v >= 0.5 ? '50%' : `${v * 100}%`) : 0,
          background: G.ink, borderRadius: 999,
        }} />
        <div style={{
          position: 'absolute', left: thumbLeft, top: '50%',
          width: 10, height: 10, marginTop: -5, marginLeft: -5,
          background: '#fff', border: `1.5px solid ${G.ink}`, borderRadius: 999,
        }} />
      </div>
    </div>
  );
}

function InspectorRow2({ tokens, label, value, mono, last }) {
  const G = tokens;
  const tnum = { fontFeatureSettings: '"tnum", "ss01"' };
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
      padding: '5px 0', borderBottom: last ? 'none' : `1px solid ${G.border}`,
    }}>
      <span style={{ fontSize: 11.5, color: G.ink3 }}>{label}</span>
      <span style={{ fontSize: 12, color: G.ink, fontFamily: mono, ...tnum }}>{value}</span>
    </div>
  );
}

function NeighbourhoodMap2({ tokens, accent, dark, agentOp }) {
  const G = tokens;
  const W = 220, H = 70;
  const ego = { x: W / 2, y: H - 10, r: 6, op: agentOp };
  const rng = mulberry32(7);
  const neigh = Array.from({ length: 6 }, (_, i) => {
    const ang = (i / 6) * Math.PI - Math.PI / 12;
    const d = 22 + rng() * 28;
    const op = i === 5 ? -0.4 : 0.3 + rng() * 0.5;
    return {
      x: ego.x + Math.cos(ang) * d,
      y: ego.y - Math.sin(ang) * d,
      op,
      r: 4 + rng() * 1.4,
    };
  });
  const tint = (op) => {
    if (!accent) return dark ? '#d4d4d6' : '#888';
    if (op > 0) return G.r;
    if (op < 0) return G.b;
    return G.ink4;
  };
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} style={{ display: 'block' }}>
      {neigh.map((n, i) => (
        <line key={i} x1={ego.x} y1={ego.y} x2={n.x} y2={n.y}
              stroke={G.border} strokeWidth="1" />
      ))}
      {neigh.map((n, i) => (
        <circle key={i} cx={n.x} cy={n.y} r={n.r} fill={tint(n.op)} opacity={0.5 + Math.abs(n.op) * 0.5} />
      ))}
      <circle cx={ego.x} cy={ego.y} r={ego.r + 3} fill="none" stroke={G.ink} strokeWidth="1" />
      <circle cx={ego.x} cy={ego.y} r={ego.r} fill={tint(ego.op)} />
    </svg>
  );
}

function CircleBtn2({ tokens, icon, filled, small }) {
  const G = tokens;
  const sz = small ? 24 : 30;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      width: sz, height: sz, borderRadius: 999,
      background: filled ? G.ink : 'transparent',
      color: filled ? '#fff' : G.ink2,
      border: filled ? 'none' : `1px solid ${G.border}`,
      fontSize: small ? 10 : 12, fontWeight: 500,
    }}>{icon}</span>
  );
}

// Mulberry32 PRNG (deterministic dot layout)
function mulberry32(a) {
  return function() {
    let t = a += 0x6D2B79F5;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

window.WireframeEHeroSplitHideable = WireframeEHeroSplitHideable;
