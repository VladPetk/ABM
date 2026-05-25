// Direction E — "Combined" (refined)
// Modern, calm, confident. Single typeface family (Geist) with
// tabular nums for figures. Deep oxblood + deep navy as the two
// political poles — no orange, no cream-cum-Claude palette.
//
// Three vertical zones:
//   ① Top: title + concise explanation + live stats
//   ② Middle: full-bleed wide playground; floating Parameters,
//        Inspector, sparkline, legend; transport bar pinned below.
//   ③ Bottom: "how to read / play / try / refs" — four lean columns.

// Seeded RNG used by the sim grid + neighbourhood map.
function mulberry32(a) {
  return function () {
    let t = (a += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function WireframeE({ accent = true, mode = 'light' }) {
  const W = 1440, H = 1180;
  const dark = mode === 'dark';
  const G = dark ?
  {
    bg: '#18181b', bg2: '#1f1f23', surface: '#1f1f23',
    ink: '#ecebe4', ink2: '#b6b6b0', ink3: '#86878a', ink4: '#54565a',
    border: '#2c2c30', borderS: '#3a3a40',
    r: '#c25c5c', b: '#7993cf', rSoft: '#2b1c1f', bSoft: '#1b2030'
  } :
  {
    bg: '#f3f3f0', bg2: '#ebe8df', surface: '#ffffff',
    ink: '#1a1d23', ink2: '#3d4148', ink3: '#74797f', ink4: '#adb1b5',
    border: '#e0ddd3', borderS: '#cdc9bd',
    r: '#8b2530', b: '#1f3565', rSoft: '#ead7d9', bSoft: '#d4d9e3'
  };

  const sans = "'Geist', system-ui, -apple-system, sans-serif";
  const mono = "'Geist Mono', ui-monospace, monospace";
  const tnum = { fontFeatureSettings: '"tnum", "ss01"' };

  return (
    <div style={{
        width: W, height: H, background: G.bg, color: G.ink,
        fontFamily: sans, position: 'relative', overflow: 'hidden',
        letterSpacing: '-.005em'
      }}>

      {/* ── Top utility bar ───────────────────────────────────────────── */}
      <div style={{
        height: 56, display: 'flex', alignItems: 'center', justifyContent: 'flex-start',
        padding: '0 36px', borderBottom: `1px solid ${G.border}`
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

      {/* ── ZONE ① Header / explanation ──────────────────────────────── */}
      <div style={{ padding: '40px 60px 36px', display: 'grid', gridTemplateColumns: '1fr 380px', gap: 56, alignItems: 'flex-start' }}>
        <div>
          <h1 style={{
            margin: 0, fontFamily: sans, fontWeight: 500,
            fontSize: 60, lineHeight: 1.02, letterSpacing: '-.028em',
            color: G.ink
          }}>
            How echoes become walls.
          </h1>
          <p style={{
            margin: '22px 0 0', maxWidth: 720, fontSize: 16.5, lineHeight: 1.6,
            color: G.ink2, fontWeight: 400
          }}>
            A live agent-based model of opinion dynamics. Six hundred agents start near the centre.
            Each updates toward neighbours it considers reasonable — and ignores the rest. Below,
            you decide how reasonable. Watch a single population split into two.
          </p>
          <div style={{ marginTop: 22, display: 'flex', alignItems: 'center', gap: 18 }}>
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 10,
              padding: '11px 18px 11px 20px',
              background: G.ink, color: dark ? G.bg : '#fff',
              fontSize: 14, fontWeight: 500, letterSpacing: '-.005em',
              borderRadius: 999, cursor: 'default'
            }}>
              Open fullscreen
              <span style={{ fontSize: 13, opacity: .9 }}>↗</span>
            </span>
            <span style={{ fontSize: 13.5, color: G.ink3 }}>
              · or stay here and scroll
            </span>
          </div>
        </div>

        {/* live stats — sans, tabular nums, restrained */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, background: G.border, border: `1px solid ${G.border}`, borderRadius: 14, overflow: 'hidden' }}>
          <Stat tokens={G} label="polarization" value="0.81" trend="↑ +12% this run" accent info />
          <Stat tokens={G} label="cross-talk" value="3%" trend="↓ from 41% start" info />
          <Stat tokens={G} label="largest faction" value="54%" trend="B-leaning" info />
          <Stat tokens={G} label="bimodality" value="0.92" trend="sharp split" info />
        </div>
      </div>

      {/* ── ZONE ② Full-bleed playground ─────────────────────────────── */}
      <div style={{
        position: 'relative',
        background: dark ? G.bg2 : G.surface,
        borderTop: `1px solid ${G.border}`,
        borderBottom: `1px solid ${G.border}`
      }}>
        {/* the stage */}
        <div style={{ position: 'relative', height: 460 }}>
          <ModernSimGrid tokens={G} accent={accent} dark={dark} />

          {/* parameters panel — top left */}
          <FloatingCard tokens={G} dark={dark} style={{ left: 36, top: 28, width: 260 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <span style={{ fontSize: 12.5, fontWeight: 600, color: G.ink, letterSpacing: '-.005em' }}>Parameters</span>
              <span style={{ fontSize: 11, color: G.ink3, fontFamily: mono, ...tnum }}>4 / 12</span>
            </div>
            <ModernSlider tokens={G} label="homophily" value={0.72} display="0.72" info />
            <ModernSlider tokens={G} label="tolerance" value={0.28} display="0.28" info />
            <ModernSlider tokens={G} label="persuasion" value={0.12} display="0.12" info />
            <ModernSlider tokens={G} label="media bias" value={0.55} display="+0.10" centered info />
            <div style={{
              marginTop: 12, paddingTop: 10, borderTop: `1px solid ${G.border}`,
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              fontSize: 12, color: G.ink3
            }}>
              <span>Show advanced</span>
              <span style={{ fontFamily: mono }}>+</span>
            </div>
          </FloatingCard>

          {/* inspector panel — top right */}
          <FloatingCard tokens={G} dark={dark} style={{ right: 36, top: 28, width: 260 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <span style={{ fontSize: 12.5, fontWeight: 600, color: G.ink, letterSpacing: '-.005em' }}>
                Agent <span style={{ fontFamily: mono, color: G.ink2, ...tnum }}>#1287</span>
              </span>
              <span style={{
                fontSize: 10.5, color: accent ? G.r : G.ink2,
                background: accent ? G.rSoft : G.bg2,
                padding: '2px 8px', borderRadius: 999, letterSpacing: '.04em'
              }}>position B</span>
            </div>
            <InspectorRow tokens={G} label="opinion" value="+0.68" mono={mono} />
            <InspectorRow tokens={G} label="certainty" value="0.41" mono={mono} />
            <InspectorRow tokens={G} label="neighbours" value="6" mono={mono} />
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
              <svg viewBox="0 0 220 40" width="100%" height="40" style={{ display: 'block' }}>
                <line x1="0" y1="20" x2="220" y2="20" stroke={G.border} strokeDasharray="2 3" />
                <path d="M0,28 C30,27 50,24 80,20 S150,8 220,5"
                fill="none" stroke={accent ? G.r : G.ink} strokeWidth="1.5" />
              </svg>
            </div>
          </FloatingCard>

          {/* sparkline — bottom left */}
          <FloatingCard tokens={G} dark={dark} style={{ left: 36, bottom: 28, width: 230, padding: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
              <span style={{ fontSize: 11.5, color: G.ink3 }}>Polarization index</span>
              <span style={{ fontSize: 12.5, color: G.ink, fontFamily: mono, ...tnum }}>0.81</span>
            </div>
            <svg viewBox="0 0 196 32" width="100%" height="32" style={{ display: 'block', marginTop: 6 }}>
              <line x1="0" y1="16" x2="196" y2="16" stroke={G.border} strokeDasharray="2 3" />
              <path d="M0,24 C18,23 30,20 50,17 S110,5 196,3" fill="none"
              stroke={accent ? G.r : G.ink} strokeWidth="1.5" />
            </svg>
          </FloatingCard>

          {/* legend — bottom right */}
          <FloatingCard tokens={G} dark={dark} style={{ right: 36, bottom: 28, padding: '10px 16px' }}>
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

        {/* transport bar — slim, flush under the stage, full bleed */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 14,
          padding: '8px 36px',
          borderTop: `1px solid ${G.border}`,
          background: dark ? G.bg : G.bg,
          height: 44
        }}>
          <CircleBtn tokens={G} icon="▶" filled small />
          <CircleBtn tokens={G} icon="⏭" small />
          <CircleBtn tokens={G} icon="↺" small />
          <div style={{ width: 1, height: 14, background: G.border, margin: '0 2px' }} />
          <span style={{ fontSize: 11.5, color: G.ink3 }}>Speed</span>
          <div style={{ display: 'flex', gap: 3 }}>
            {['½', '1×', '2×', '4×'].map((s, i) =>
            <span key={s} style={{
              fontSize: 11, padding: '2px 8px', borderRadius: 999,
              border: `1px solid ${i === 1 ? G.ink : G.border}`,
              color: i === 1 ? G.ink : G.ink3,
              fontFamily: mono, fontWeight: i === 1 ? 500 : 400, ...tnum,
              background: i === 1 ? dark ? G.bg2 : '#fff' : 'transparent'
            }}>{s}</span>
            )}
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

      {/* ── Scenario row — single line, no header, no boxes ──────────── */}
      <div style={{
        padding: '24px 60px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        gap: 36, flexWrap: 'wrap'
      }}>
        <Scenario tokens={G} lead="Echo" tail="chamber" selected />
        <Scenario tokens={G} lead="Mixed" tail="society" />
        <Scenario tokens={G} lead="Media-driven" tail="drift" />
        <Scenario tokens={G} lead="Extremist" tail="seed" />
      </div>

      {/* ── ZONE ③ How to read · How to play ─────────────────────────── */}
      <div style={{
        padding: '12px 60px 28px',
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 64,
        borderTop: `1px solid ${G.border}`
      }}>
        <Section tokens={G} title="How to read">
          <p style={{ margin: 0, fontSize: 15, lineHeight: 1.6, color: G.ink2, maxWidth: 560 }}>
            Each dot is one agent. Its colour shows which side of the issue it currently leans
            toward; its saturation, how strongly. The lattice is only for display — agents
            actually talk through a hidden small-world network<Foot n={3} tokens={G} />.
            A flat boundary between colours is the signature of a population that has
            stopped listening<Foot n={2} tokens={G} />.
          </p>
        </Section>

        <Section tokens={G} title="How to play">
          <p style={{ margin: 0, fontSize: 15, lineHeight: 1.6, color: G.ink2, maxWidth: 560 }}>
            Drag any slider; the sim resumes from the current state. Each parameter has an
            <InfoChip tokens={G} /> icon — open it to read what the parameter
            actually controls and how it is implemented. Hover any dot to inspect; click to pin
            its trajectory. The URL captures the full configuration, so a single link is enough
            to share an exact run.
          </p>
        </Section>
      </div>

      {/* footer */}
      <div style={{
        position: 'absolute', left: 60, right: 60, bottom: 18,
        display: 'flex', justifyContent: 'space-between',
        fontSize: 12, color: G.ink3,
        borderTop: `1px solid ${G.border}`, paddingTop: 14,
        letterSpacing: '.005em'
      }}>
        <span>polarlab</span>
        <span style={{ display: 'flex', gap: 22 }}>
          <span>About</span>
          <span>Methods</span>
          <span>Source ↗</span>
        </span>
      </div>
    </div>);

}

// ─────────────────────────────────────────────────────────────────────
// Subcomponents
// ─────────────────────────────────────────────────────────────────────

function Stat({ tokens, label, value, trend, accent, info }) {
  const G = tokens;
  return (
    <div style={{
      background: G.surface, padding: '14px 16px',
      display: 'flex', flexDirection: 'column', gap: 2
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6,
        fontSize: 11.5, color: G.ink3, letterSpacing: '.02em' }}>
        {label}
        {info &&
        <span style={{
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          width: 13, height: 13, borderRadius: 999,
          border: `1px solid ${G.ink4}`, color: G.ink3,
          fontSize: 9, fontWeight: 500, lineHeight: 1,
          fontStyle: 'italic', cursor: 'default'
        }} title="What does this measure?">i</span>
        }
      </div>
      <div style={{
        fontSize: 28, fontWeight: 500, letterSpacing: '-.025em',
        color: G.ink, lineHeight: 1.05, marginTop: 2,
        fontFeatureSettings: '"tnum", "ss01"'
      }}>
        {value}
      </div>
      <div style={{
        fontSize: 11.5, color: accent ? G.r : G.ink3, marginTop: 2,
        letterSpacing: '.01em'
      }}>{trend}</div>
    </div>);

}

function FloatingCard({ tokens, dark, style, children }) {
  const G = tokens;
  return (
    <div style={{
      position: 'absolute',
      background: dark ? 'rgba(31,31,35,.84)' : 'rgba(255,255,255,.88)',
      backdropFilter: 'blur(18px) saturate(140%)',
      WebkitBackdropFilter: 'blur(18px) saturate(140%)',
      border: `1px solid ${G.border}`,
      borderRadius: 12,
      padding: 14,
      boxShadow: dark ?
      '0 6px 22px rgba(0,0,0,.35)' :
      '0 6px 22px rgba(26,29,35,.06)',
      ...style
    }}>{children}</div>);

}

function ModernSlider({ tokens, label, value, display, centered, info }) {
  const G = tokens;
  const pct = Math.min(1, Math.max(0, value));
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 5 }}>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12.5, color: G.ink2 }}>
          {label}
          {info &&
          <span style={{
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            width: 13, height: 13, borderRadius: 999,
            border: `1px solid ${G.ink4}`, color: G.ink3,
            fontSize: 9, fontWeight: 500, lineHeight: 1,
            fontFamily: "'Geist', sans-serif",
            fontStyle: 'italic',
            cursor: 'default'
          }} title="What does this do?">i</span>
          }
        </span>
        <span style={{ fontSize: 11.5, color: G.ink3,
          fontFamily: "'Geist Mono', monospace",
          fontFeatureSettings: '"tnum"' }}>{display}</span>
      </div>
      <div style={{ position: 'relative', height: 8 }}>
        <div style={{ position: 'absolute', left: 0, right: 0, top: 3, height: 2, background: G.border, borderRadius: 2 }} />
        {centered ?
        <div style={{ position: 'absolute', left: '50%', top: 3, height: 2,
          width: `${Math.abs(pct - 0.5) * 100}%`,
          transform: pct < 0.5 ? 'translateX(-100%)' : 'none',
          background: G.ink, borderRadius: 2 }} /> :

        <div style={{ position: 'absolute', left: 0, top: 3, height: 2,
          width: `${pct * 100}%`, background: G.ink, borderRadius: 2 }} />
        }
        <div style={{ position: 'absolute', left: `${pct * 100}%`, top: -1,
          width: 10, height: 10, background: G.surface,
          border: `1.5px solid ${G.ink}`, borderRadius: 999,
          transform: 'translateX(-50%)' }} />
      </div>
    </div>);

}

function InspectorRow({ tokens, label, value, mono, last }) {
  const G = tokens;
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '6px 0',
      borderBottom: last ? 'none' : `1px solid ${G.border}`,
      fontSize: 12.5
    }}>
      <span style={{ color: G.ink3 }}>{label}</span>
      <span style={{ color: G.ink, fontFamily: mono, fontSize: 12,
        fontFeatureSettings: '"tnum"' }}>{value}</span>
    </div>);

}

function CircleBtn({ tokens, icon, filled, small }) {
  const G = tokens;
  const size = small ? 26 : 32;
  return (
    <div style={{
      width: size, height: size, borderRadius: 999,
      background: filled ? G.ink : 'transparent',
      color: filled ? G.surface : G.ink,
      border: filled ? 'none' : `1px solid ${G.border}`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: small ? 10 : 11
    }}>{icon}</div>);

}

function Section({ tokens, title, children }) {
  const G = tokens;
  return (
    <div>
      <div style={{
        fontSize: 18, fontWeight: 500, color: G.ink,
        letterSpacing: '-.014em', marginBottom: 12
      }}>{title}</div>
      {children}
    </div>);

}

function Scenario({ tokens, lead, tail, selected }) {
  const G = tokens;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'baseline', gap: 10,
      fontSize: 17, letterSpacing: '-.012em', fontWeight: 500,
      color: G.ink, cursor: 'default'
    }}>
      <span style={selected ? {
        textDecoration: 'underline',
        textDecorationColor: G.r,
        textDecorationThickness: '1.5px',
        textUnderlineOffset: '7px'
      } : {}}>
        <span>{lead} </span>
        <span style={{ color: G.r }}>{tail}</span>
      </span>
      {!selected && (
        <span style={{ fontSize: 14, color: G.ink3, fontWeight: 400 }}>→</span>
      )}
    </span>);

}

function ScenarioCard({ tokens, title, body }) {
  // kept for backward-compat; not used in current layout
  const G = tokens;
  return (
    <div style={{
      padding: '18px 20px 20px',
      border: `1px solid ${G.border}`, borderRadius: 12, background: G.surface
    }}>
      <div style={{ fontSize: 17, fontWeight: 500, color: G.ink }}>{title}</div>
      <div style={{ fontSize: 13.5, color: G.ink2, marginTop: 6 }}>{body}</div>
    </div>);

}

function InfoChip({ tokens }) {
  const G = tokens;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      width: 16, height: 16, borderRadius: 999,
      border: `1px solid ${G.ink4}`, color: G.ink3,
      fontSize: 10.5, lineHeight: 1, fontStyle: 'italic',
      fontWeight: 500, margin: '0 4px',
      verticalAlign: 'baseline', position: 'relative', top: 3
    }}>i</span>);

}

// ── Mini local-network map ───────────────────────────────────────────
// The pinned agent + its 6 neighbours, colored by current opinion,
// edges drawn between them. The "are you in a bubble?" view.
function NeighbourhoodMap({ tokens, accent, dark, agentOp = 0.68 }) {
  const G = tokens;
  const W = 236, H = 96;
  const cx = W / 2, cy = H / 2 + 4;

  // 6 neighbours: 5 same-side (red, B-leaning) + 1 outlier (blue, A)
  const N = [
    { x: 24,  y: 18, op:  0.62 },
    { x: 60,  y: 8,  op:  0.55 },
    { x: 96,  y: 22, op:  0.74 },
    { x: 134, y: 14, op:  0.48 },
    { x: 178, y: 26, op: -0.58 },  // ← outlier
    { x: 212, y: 70, op:  0.7  },
  ];
  // light internal edges (small-world cluster feel)
  const ee = [[0,1],[1,2],[2,3],[5,3]];

  const tint = (op) => {
    if (!accent) {
      const g = dark ? 110 + Math.abs(op) * 130 : 180 - Math.abs(op) * 130;
      return `rgb(${Math.round(g)},${Math.round(g)},${Math.round(g)})`;
    }
    const hexRGB = (h) => [parseInt(h.slice(1,3),16), parseInt(h.slice(3,5),16), parseInt(h.slice(5,7),16)];
    if (op > 0.05) {
      const [r,g,b] = hexRGB(G.r); const t = Math.min(1, op);
      return `rgba(${r},${g},${b},${0.4 + t * 0.55})`;
    } else if (op < -0.05) {
      const [r,g,b] = hexRGB(G.b); const t = Math.min(1, -op);
      return `rgba(${r},${g},${b},${0.4 + t * 0.55})`;
    }
    return dark ? 'rgba(200,200,200,0.4)' : 'rgba(120,120,120,0.4)';
  };

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} style={{ display: 'block' }}>
      {/* center→neighbour edges */}
      {N.map((n, i) => (
        <line key={`c${i}`} x1={cx} y1={cy} x2={n.x} y2={n.y}
              stroke={G.border} strokeWidth=".9" />
      ))}
      {/* a few neighbour↔neighbour edges, faint (small-world clumping) */}
      {ee.map(([a,b], i) => (
        <line key={`e${i}`} x1={N[a].x} y1={N[a].y} x2={N[b].x} y2={N[b].y}
              stroke={G.border} strokeWidth=".6" opacity=".55" />
      ))}
      {/* neighbour dots */}
      {N.map((n, i) => (
        <circle key={`n${i}`} cx={n.x} cy={n.y} r="6.5"
                fill={tint(n.op)}
                stroke={dark ? 'rgba(255,255,255,.12)' : 'rgba(0,0,0,.18)'}
                strokeWidth=".6" />
      ))}
      {/* the pinned agent itself: filled + ring */}
      <circle cx={cx} cy={cy} r="11.5" fill="none"
              stroke={G.ink} strokeWidth="1.25" />
      <circle cx={cx} cy={cy} r="6.5" fill={tint(agentOp)}
              stroke={dark ? 'rgba(255,255,255,.18)' : 'rgba(0,0,0,.3)'} strokeWidth=".6" />
    </svg>
  );
}

window.NeighbourhoodMap = NeighbourhoodMap;

function Foot({ n, tokens }) {
  const G = tokens;
  return (
    <sup style={{
      fontSize: 9.5, color: G.ink2, fontWeight: 500,
      marginLeft: 2, padding: '1px 4px',
      borderRadius: 3, background: G.bg2,
      verticalAlign: 'super', lineHeight: 1,
      fontFamily: "'Geist Mono', monospace"
    }}>{n}</sup>);

}

// ── Wide modern sim grid ─────────────────────────────────────────────
function ModernSimGrid({ tokens, accent, dark }) {
  const G = tokens;
  const cols = 60,rows = 22;
  const W = 1320,H = 460;
  const rng = mulberry32(31);
  const cellW = W / cols,cellH = H / rows;
  const dots = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const u = c / (cols - 1) - 0.5;
      const v = r / (rows - 1) - 0.5;
      const region = u + v * 0.18 + (rng() - 0.5) * 0.22;
      const op = Math.tanh(region * 3.6);
      const x = c * cellW + cellW * 0.5 + (rng() - 0.5) * cellW * 0.3;
      const y = r * cellH + cellH * 0.5 + (rng() - 0.5) * cellH * 0.35;
      dots.push({ x, y, op, id: r * cols + c });
    }
  }
  // Parse a hex into [r,g,b]
  const hexRGB = (h) => {
    const x = h.replace('#', '');
    return [parseInt(x.slice(0, 2), 16), parseInt(x.slice(2, 4), 16), parseInt(x.slice(4, 6), 16)];
  };
  const [rR, rG, rB] = hexRGB(G.r);
  const [bR, bG, bB] = hexRGB(G.b);

  const tint = (op) => {
    if (!accent) {
      if (dark) {
        const g = Math.round(110 + Math.abs(op) * 140);
        return `rgb(${g},${g},${g})`;
      }
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
  const hover = dots[10 * cols + 40];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="100%"
    preserveAspectRatio="xMidYMid meet" style={{ display: 'block' }}>
      {dots.map((d) =>
      <circle key={d.id} cx={d.x} cy={d.y} r={dotR} fill={tint(d.op)} />
      )}
      {hover &&
      <g>
          <circle cx={hover.x} cy={hover.y} r={dotR * 2.2} fill="none"
        stroke={dark ? G.ink : G.ink} strokeWidth="1.2" />
          <line x1={hover.x + dotR * 2.2} y1={hover.y - dotR * 1.8}
        x2={hover.x + 80} y2={hover.y - 40}
        stroke={dark ? 'rgba(245,244,240,.5)' : 'rgba(26,29,35,.45)'}
        strokeWidth="1" strokeDasharray="2 3" />
        </g>
      }
    </svg>);

}

window.WireframeE = WireframeE;