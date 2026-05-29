// Calm to Camps — the political compass (hero visual)
// 2D ideology plane rendered as SVG. x = economic, y = cultural (flipped to
// match the literature: traditional/authoritarian top, progressive/libertarian
// bottom). Dots coloured by party. Linda is spotlighted with her ego edges.
//
// Counterfactual mode renders TWO clouds instead of straight trails:
//   · ghost (hollow, faint) = where each life WOULD be without the intervention
//   · solid                 = where they are WITH it (pulled back toward centre)
// The growing gap between the clouds is the story. `damp` (0..1) ramps the
// divergence so it can animate as time passes.

function Compass({ year = 2016, seed = 7, spotlight = true, mode = 'normal', damp = 0.42 }) {
  const VB = 600,C = 300,HALF = 238;
  const mx = (x) => C + x * HALF;
  const my = (y) => C - y * HALF;

  const agents = genAgents(year, seed);
  const linda = lindaAt(year);
  const net = lindaNetwork(year);
  const isCF = mode === 'counterfactual';

  const partyColor = (p) => p === 'D' ? CC.d : p === 'R' ? CC.r : CC.i;
  // counterfactual: pull a point back toward the centre
  const cf = (p) => ({ x: p.x * (1 - damp * 0.6), y: p.y * (1 - damp * 0.6) });

  const dotBase = 4.5;
  const crowdOpacity = spotlight ? 0.42 : 0.85;

  const axLabel = { fontFamily: SANS, fontSize: 13, fill: CC.ink3, fontWeight: 500, letterSpacing: '.02em' };
  const quad = { fontFamily: SERIF, fontStyle: 'italic', fontSize: 14.5, fill: CC.ink4 };

  return (
    <svg viewBox={`0 0 ${VB} ${VB}`} width="100%" height="100%"
    preserveAspectRatio="xMidYMid meet" style={{ display: 'block', height: "723px" }}>
      {/* faint gridlines */}
      {[-0.5, 0.5].map((g) =>
      <g key={g}>
          <line x1={mx(g)} y1={my(-1)} x2={mx(g)} y2={my(1)} stroke={CC.border} strokeWidth="1" />
          <line x1={mx(-1)} y1={my(g)} x2={mx(1)} y2={my(g)} stroke={CC.border} strokeWidth="1" />
        </g>
      )}
      {/* main axes */}
      <line x1={mx(0)} y1={my(-1)} x2={mx(0)} y2={my(1)} stroke={CC.borderS} strokeWidth="1.25" />
      <line x1={mx(-1)} y1={my(0)} x2={mx(1)} y2={my(0)} stroke={CC.borderS} strokeWidth="1.25" />

      {/* quadrant labels (flipped: traditional top, progressive bottom) */}
      <text x={mx(-0.92)} y={my(0.9)} style={quad} textAnchor="start">populist</text>
      <text x={mx(0.92)} y={my(0.9)} style={quad} textAnchor="end">traditional right</text>
      <text x={mx(-0.92)} y={my(-0.86)} style={quad} textAnchor="start">progressive left</text>
      <text x={mx(0.92)} y={my(-0.86)} style={quad} textAnchor="end">libertarian</text>

      {/* axis end labels */}
      <text x={mx(-1)} y={C + 23} style={axLabel} textAnchor="start">← economic left</text>
      <text x={mx(1)} y={C + 23} style={axLabel} textAnchor="end">economic right →</text>
      <text x={C} y={my(1) - 10} style={axLabel} textAnchor="middle">traditional</text>
      <text x={C} y={my(-1) + 20} style={axLabel} textAnchor="middle">progressive</text>

      {/* ── COUNTERFACTUAL: ghost (without) + solid (with) ─────────────── */}
      {isCF && agents.map((a) =>
      <circle key={'g' + a.id} cx={mx(a.x)} cy={my(a.y)} r={dotBase - 0.3}
      fill="none" stroke={partyColor(a.party)} strokeWidth="1" opacity="0.22" />
      )}
      {isCF && agents.map((a) => {
        const t = cf(a);
        return (
          <circle key={'s' + a.id} cx={mx(t.x)} cy={my(t.y)} r={dotBase}
          fill={partyColor(a.party)} opacity={spotlight ? 0.5 : 0.82} />);

      })}

      {/* ── NORMAL: single cloud ──────────────────────────────────────── */}
      {!isCF && agents.map((a) =>
      <circle key={a.id} cx={mx(a.x)} cy={my(a.y)} r={dotBase}
      fill={partyColor(a.party)} opacity={crowdOpacity} />
      )}

      {/* Linda's ego edges (uniform, faint — strength is shown elsewhere) */}
      {spotlight && net.map((nd) => {
        const base = { x: linda.x + nd.dx, y: linda.y + nd.dy };
        const p = isCF ? cf(base) : base;
        const l = isCF ? cf(linda) : linda;
        return (
          <line key={'e' + nd.i} x1={mx(l.x)} y1={my(l.y)} x2={mx(p.x)} y2={my(p.y)}
          stroke={CC.ink2} strokeWidth="1" opacity="0.32" />);

      })}
      {/* Linda's neighbour dots */}
      {spotlight && net.map((nd) => {
        const base = { x: linda.x + nd.dx, y: linda.y + nd.dy };
        const p = isCF ? cf(base) : base;
        return (
          <circle key={'n' + nd.i} cx={mx(p.x)} cy={my(p.y)} r={dotBase + 0.8}
          fill={partyColor(nd.party)} opacity="0.92" />);

      })}

      {/* Linda — ghost (actual) + solid (counterfactual) when CF */}
      {spotlight && isCF && damp > 0.02 &&
      <g>
          <line x1={mx(linda.x)} y1={my(linda.y)} x2={mx(cf(linda).x)} y2={my(cf(linda).y)}
        stroke={CC.ink3} strokeWidth="1.4" opacity="0.55" strokeDasharray="3 3" />
          <circle cx={mx(linda.x)} cy={my(linda.y)} r={9} fill="none" stroke={CC.ink3} strokeWidth="1.6" strokeDasharray="2.5 2.5" opacity="0.7" />
        </g>
      }
      {spotlight && (() => {
        const l = isCF ? cf(linda) : linda;
        return (
          <g>
            <circle cx={mx(l.x)} cy={my(l.y)} r={11} fill="none" stroke="#fff" strokeWidth="3.5" />
            <circle cx={mx(l.x)} cy={my(l.y)} r={9} fill={partyColor(linda.party)} />
            <circle cx={mx(l.x)} cy={my(l.y)} r={11} fill="none" stroke={CC.ink} strokeWidth="1.4" />
            <text x={mx(l.x)} y={my(l.y) - 18} textAnchor="middle"
            style={{ fontFamily: SANS, fontSize: 13, fontWeight: 600, fill: CC.ink }}>Linda</text>
          </g>);

      })()}
    </svg>);

}

// Loops `year` from `from`→`to` over `period` seconds for the "already playing"
// intro compass.
function AnimatedCompass({ from = 1980, to = 2025, period = 70, ...rest }) {
  const [year, setYear] = React.useState(from);
  React.useEffect(() => {
    let raf,start = null;
    const loop = (ts) => {
      if (start == null) start = ts;
      const t = (ts - start) / 1000 % period;
      setYear(from + (to - from) * (t / period));
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [from, to, period]);
  return <Compass year={year} {...rest} />;
}

window.Compass = Compass;
window.AnimatedCompass = AnimatedCompass;