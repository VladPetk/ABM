// Direction E — "Hero left, sim right" variant
// Two-column layout where the sim is a confident square hero-image
// on the right, and the left column carries the title, intro, KPIs,
// scenarios, and the fullscreen CTA. Footer stays the same.

function WireframeEHeroSplit({ accent = true, mode = 'light' }) {
  const W = 1440, H = 810; // 16:9
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

      {/* ── Hero split: text-left, sim full-height-right ─────────────── */}
      <div style={{
        height: H - 56 - 120, // header above, footer below
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
            <KPI tokens={G} label="polarization"     value="0.81" trend="↑ +12%"      accent info compact />
            <KPI tokens={G} label="cross-talk"       value="3%"   trend="↓ from 41%"         info compact />
            <KPI tokens={G} label="largest faction"  value="54%"  trend="B-leaning"          info compact />
            <KPI tokens={G} label="bimodality"       value="0.92" trend="sharp split"        info compact last />
          </div>

          {/* Scenarios */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <span style={{
              fontSize: 11, color: G.ink3, letterSpacing: '.14em',
              textTransform: 'uppercase', fontWeight: 500,
            }}>Currently running</span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 22, alignItems: 'baseline' }}>
              <ScenarioLink tokens={G} lead="Echo"         tail="chamber" selected />
              <ScenarioLink tokens={G} lead="Mixed"        tail="society" />
              <ScenarioLink tokens={G} lead="Media-driven" tail="drift" />
              <ScenarioLink tokens={G} lead="Extremist"    tail="seed" />
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

        {/* RIGHT — sim, fills the full hero height & bleeds to right edge */}
        <div style={{
          display: 'flex', flexDirection: 'column',
          background: dark ? G.bg2 : G.surface,
          borderLeft: `1px solid ${G.border}`,
          alignSelf: 'stretch', position: 'relative',
        }}>
          <div style={{ position: 'relative', flex: 1, minHeight: 0 }}>
            <WideSimGrid tokens={G} accent={accent} dark={dark} />

            {/* Parameters — top left */}
            <FloatingCardSplit tokens={G} dark={dark} style={{ left: 20, top: 20, width: 244 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <span style={{ fontSize: 12.5, fontWeight: 600, color: G.ink, letterSpacing: '-.005em' }}>Parameters</span>
                <span style={{ fontSize: 11, color: G.ink3, fontFamily: mono, ...tnum }}>4 / 12</span>
              </div>
              <ModernSlider tokens={G} label="homophily"  value={0.72} display="0.72" info />
              <ModernSlider tokens={G} label="tolerance"  value={0.28} display="0.28" info />
              <ModernSlider tokens={G} label="persuasion" value={0.12} display="0.12" info />
              <ModernSlider tokens={G} label="media bias" value={0.55} display="+0.10" centered info />
              <div style={{
                marginTop: 10, paddingTop: 10, borderTop: `1px solid ${G.border}`,
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                fontSize: 12, color: G.ink3,
              }}>
                <span>Show advanced</span>
                <span style={{ fontFamily: mono }}>+</span>
              </div>
            </FloatingCardSplit>

            {/* Inspector — bottom right */}
            <FloatingCardSplit tokens={G} dark={dark} style={{ right: 20, bottom: 20, width: 244 }}>
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
              <InspectorRow tokens={G} label="opinion"    value="+0.68" mono={mono} />
              <InspectorRow tokens={G} label="certainty"  value="0.41"  mono={mono} />
              <InspectorRow tokens={G} label="neighbours" value="6"     mono={mono} last />
              <div style={{ marginTop: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 5 }}>
                  <span style={{ fontSize: 11, color: G.ink3 }}>Neighbourhood</span>
                  <span style={{ fontSize: 11, color: G.ink3 }}>
                    diversity{' '}
                    <span style={{ color: G.ink, fontFamily: mono, ...tnum }}>0.17</span>
                  </span>
                </div>
                <NeighbourhoodMap tokens={G} accent={accent} dark={dark} agentOp={0.68} />
                <div style={{
                  marginTop: 2, fontSize: 11.5, color: G.ink3,
                  display: 'flex', justifyContent: 'space-between',
                }}>
                  <span>5 alike · 1 outlier</span>
                  <span style={{ color: accent ? G.r : G.ink2 }}>echo-chamber risk ↑</span>
                </div>
              </div>
            </FloatingCardSplit>

            {/* Sparkline — top right */}
            <FloatingCardSplit tokens={G} dark={dark} style={{ right: 20, top: 20, width: 196, padding: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ fontSize: 11, color: G.ink3 }}>Polarization</span>
                <span style={{ fontSize: 11.5, color: G.ink, fontFamily: mono, ...tnum }}>0.81</span>
              </div>
              <svg viewBox="0 0 176 28" width="100%" height="28" style={{ display: 'block', marginTop: 4 }}>
                <line x1="0" y1="14" x2="176" y2="14" stroke={G.border} strokeDasharray="2 3" />
                <path d="M0,22 C18,21 28,18 46,15 S96,4 176,2"
                      fill="none" stroke={accent ? G.r : G.ink} strokeWidth="1.5" />
              </svg>
            </FloatingCardSplit>

            {/* Legend — bottom left */}
            <FloatingCardSplit tokens={G} dark={dark} style={{ left: 20, bottom: 20, padding: '8px 14px' }}>
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
            </FloatingCardSplit>
          </div>

          {/* Transport bar inside the right column, above the footer */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 12,
            padding: '0 20px', height: 44, flexShrink: 0,
            borderTop: `1px solid ${G.border}`,
            background: dark ? G.bg : G.bg,
          }}>
            <CircleBtn tokens={G} icon="▶" filled small />
            <CircleBtn tokens={G} icon="⏭" small />
            <CircleBtn tokens={G} icon="↺" small />
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

      {/* ── Footer: compact 2-col + thin meta line ───────────────────── */}
      <div style={{
        padding: '18px 60px 16px',
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 64,
        borderTop: `1px solid ${G.border}`,
        height: 120, // matches the height reserved above
      }}>
        <Section tokens={G} title="How to read" compact>
          <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.55, color: G.ink2 }}>
            Each dot is one agent. Colour shows which side it currently leans toward; saturation,
            how strongly. A flat boundary between colours is a population that has stopped
            listening<Foot n={2} tokens={G} />.
          </p>
        </Section>

        <Section tokens={G} title="How to play" compact>
          <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.55, color: G.ink2 }}>
            Drag any slider; the sim resumes live. Each parameter has an
            <InfoChip tokens={G} /> icon for what it actually controls. Hover a dot to inspect;
            click to pin. The URL captures the full configuration.
          </p>
        </Section>
      </div>
    </div>
  );
}

// ── KPI cell (no card chrome; sits inside a hairline-bordered strip) ──
function KPI({ tokens, label, value, trend, accent, info, last, compact }) {
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

// ── Scenario as a magazine-style nav link (FT underline for active) ───
function ScenarioLink({ tokens, lead, tail, selected }) {
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

// ── Floating card scoped to this artboard (smaller padding default) ───
function FloatingCardSplit({ tokens, dark, style, children }) {
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

// ── Wide 16:9 dot field that fills its container ──────────────────────
function WideSimGrid({ tokens, accent, dark }) {
  const G = tokens;
  const cols = 40, rows = 22;
  const W = 1280, H = 720; // 16:9 viewBox
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

window.WireframeEHeroSplit = WireframeEHeroSplit;
