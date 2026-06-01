// Calm to Camps — prototype panels: character sidebar, ego-mini, timeline, sparklines.

// proximity-based ego mini-graph from the real network snapshot.
// (tie strength is faked from cross/same-party for now — a real weight field
//  is coming in the data; closer = stronger.)
function ProtoEgoMini({ tick, run, idx }) {
  const VB = 260, H = 116, cx = VB / 2, cy = H / 2;
  const edges = egoEdges(run, tick, idx);
  const myParty = partyAt(run, tick, idx);
  const pc = (p) => partyColor(p);
  const near = 40, farX = 116, farY = 46;
  const placed = edges.slice(0, 12).map((e, i) => {
    const other = e[0] === idx ? e[1] : e[0];
    const cross = e[2] === 1;
    const otherParty = run.party[Math.round(tick)][other];
    const strength = cross ? 0.28 : 0.85;             // placeholder until weight ships
    const ang = (i / Math.max(1, Math.min(12, edges.length))) * Math.PI * 2 + 0.5;
    const rx = farX - (farX - near) * strength, ry = farY - (farY - near * 0.5) * strength;
    return { x: cx + Math.cos(ang) * rx, y: cy + Math.sin(ang) * ry, party: otherParty, strength };
  });
  return (
    <svg viewBox={`0 0 ${VB} ${H}`} width="100%" height="106" preserveAspectRatio="xMidYMid meet" style={{ display: 'block' }}>
      {[0.62, 0.3].map((s, i) => (
        <ellipse key={i} cx={cx} cy={cy} rx={farX - (farX - near) * s} ry={farY - (farY - near * 0.5) * s}
                 fill="none" stroke={CC.border} strokeWidth="1" strokeDasharray="2 4" />
      ))}
      {placed.map((p, i) => (
        <line key={'l' + i} x1={cx} y1={cy} x2={p.x} y2={p.y} stroke={CC.ink3} strokeWidth="1" opacity={0.14 + 0.26 * p.strength} />
      ))}
      {placed.map((p, i) => (
        <circle key={'c' + i} cx={p.x} cy={p.y} r={4 + p.strength * 3.5} fill={pc(p.party)} opacity="0.92" />
      ))}
      <circle cx={cx} cy={cy} r="10" fill="none" stroke="#fff" strokeWidth="3" />
      <circle cx={cx} cy={cy} r="8.5" fill={pc(myParty)} />
      <circle cx={cx} cy={cy} r="10" fill="none" stroke={CC.ink} strokeWidth="1.2" />
    </svg>
  );
}

function currentBeat(charKey, tick) {
  const beats = D.chars[charKey].beats;
  let chosen = beats[0];
  for (const b of beats) if (tick >= b.tick) chosen = b;
  return chosen;
}

function ProtoCharacter({ tick, run, charKey, tabs, onTab }) {
  const ch = D.chars[charKey];
  const idx = ch.agent_index;
  const year = Math.round(tickToYear(tick));
  const party = partyAt(run, tick, idx);
  const affect = affectAt(run, tick, idx);
  const faction = factionAt(run, tick, idx);
  const beat = currentBeat(charKey, tick);
  const warmthName = party === 1 ? 'Democrats' : 'Republicans';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', fontFamily: SANS, color: CC.ink }}>
      <div style={{ display: 'flex', gap: 4, paddingBottom: 13, borderBottom: `1px solid ${CC.border}` }}>
        {tabs.map((t) => {
          const on = t === charKey;
          return (
            <button key={t} onClick={() => onTab(t)} style={{
              fontSize: 12.5, fontWeight: on ? 600 : 400, color: on ? CC.ink : CC.ink3,
              padding: '5px 12px', borderRadius: 999, background: on ? CC.bg2 : 'transparent',
              border: `1px solid ${on ? CC.borderS : 'transparent'}`, cursor: 'pointer', fontFamily: SANS,
            }}>{D.chars[t].name}</button>
          );
        })}
      </div>

      <div style={{ padding: '14px 0 12px', borderBottom: `1px solid ${CC.border}` }}>
        <h3 style={{ margin: 0, fontFamily: SERIF, fontWeight: 600, fontSize: 26, lineHeight: 1.05, letterSpacing: '-.01em' }}>{ch.name}</h3>
        <div style={{ fontSize: 12.5, color: CC.ink3, fontFamily: MONO, marginTop: 4, ...TNUM }}>{ch.city} · {year}{faction ? ` · ${faction}` : ''}</div>
        <div style={{ fontSize: 13, color: CC.ink2, marginTop: 2 }}>{ch.job}</div>
        <p style={{ margin: '11px 0 0', fontFamily: SERIF, fontSize: 15, lineHeight: 1.48, color: CC.ink2, textWrap: 'pretty' }}>{ch.bio}</p>
      </div>

      <div style={{ padding: '12px 0', borderBottom: `1px solid ${CC.border}`, display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 13, color: CC.ink3 }}>Votes</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 13.5, fontWeight: 500 }}>
            <PartySwatch party={PARTY_CH[party]} /> {partyName(party)}
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 13, color: CC.ink3, display: 'inline-flex', gap: 6, alignItems: 'center' }}>Warmth toward {warmthName} <InfoDot /></span>
          <span style={{ fontSize: 14, fontWeight: 600, fontFamily: MONO, color: affect < 0 ? CC.r : CC.d, ...TNUM }}>{affect != null ? affect.toFixed(2) : '—'}</span>
        </div>
        <div style={{ position: 'relative', height: 5, background: CC.bg2, borderRadius: 999 }}>
          <div style={{ position: 'absolute', left: '50%', top: -2, bottom: -2, width: 1, background: CC.ink4 }} />
          <div style={{ position: 'absolute', right: '50%', top: 0, bottom: 0, width: `${Math.min(50, Math.abs(affect || 0) * 50)}%`, background: CC.r, borderRadius: 999 }} />
        </div>
      </div>

      <div style={{ padding: '12px 0', borderBottom: `1px solid ${CC.border}` }}>
        <Eyebrow>Issues she cares about</Eyebrow>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7, marginTop: 9 }}>
          {ch.issues.map((iss) => (
            <span key={iss} style={{ fontSize: 12.5, color: CC.ink2, padding: '4px 11px', borderRadius: 999, border: `1px solid ${CC.border}`, background: CC.surface }}>{iss}</span>
          ))}
        </div>
      </div>

      <div style={{ padding: '12px 0', borderBottom: `1px solid ${CC.border}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
          <Eyebrow>Her network</Eyebrow>
          <span style={{ fontSize: 11.5, color: CC.ink3 }}>closer = stronger tie</span>
        </div>
        <div style={{ marginTop: 6 }}><ProtoEgoMini tick={tick} run={run} idx={idx} /></div>
      </div>

      <div style={{ padding: '13px 0 0', flex: 1, minHeight: 0 }}>
        <Eyebrow style={{ color: CC.ink4 }}>{Math.round(tickToYear(beat.tick))}</Eyebrow>
        <p style={{ margin: '7px 0 0', fontFamily: SERIF, fontSize: 15.5, lineHeight: 1.46, color: CC.ink, textWrap: 'pretty' }}>{beat.prose}</p>
      </div>
    </div>
  );
}

// ── timeline ───────────────────────────────────────────────────────────
// curated labels for the crowded event timeline — others render as bare ticks
const LABELLED = {
  gingrich_1994: 'Gingrich',
  fairness_doctrine_1987: 'Fairness Doctrine',
  fox_news_1996: 'Fox News',
  social_media_ramp_start_and_obama_2008: 'Obama · social media',
  tea_party_2009: 'Tea Party',
  maga_2015: 'MAGA',
  trump_2016_and_status_threat: 'Trump',
  covid_jan6_2020: 'COVID · Jan 6',
};

// one-sentence "why this moment mattered to polarization" — surfaced on hover so
// scrubbing the timeline becomes discovering, not just replaying. Keyed to the
// engine's event labels; not a history lesson, just the mechanism. Reconciled to
// the Step-1 evidence re-grade: elite drift now lives at Gingrich (not CU, which
// is a non-causal marker here), and social media is framed as contested. These
// are a fallback — the tooltip prefers the engine's own evidence_note. (Step 5)
const EVENT_HOOKS = {
  gingrich_1994: 'Party elites pull apart at the top — the Republican side moves right fastest. The best-evidenced first cause.',
  fairness_doctrine_1987: 'Broadcasters were no longer required to air opposing views.',
  fox_news_1996: 'For the first time, a major TV network built for a single audience — the strongest causal media evidence.',
  social_media_ramp_start_and_obama_2008: 'Often blamed, rarely convicted: polarization rose fastest among the least-online, and deactivation studies came back near zero.',
  tea_party_2009: 'A newly-organized base starts pulling Republican elites toward the edge.',
  decade_2010_and_citizens_united: 'Citizens United lands here, but the best-identified studies find no clear polarization effect — an era marker, not a cause.',
  social_media_ramp_end_2012: 'Personalized feeds are now near-universal — a small, contested accelerant at most.',
  maga_2015: 'A new faction hardens at the edge of the right; the center keeps thinning.',
  trump_2016_and_status_threat: 'A status-threat shock (Mutz) — contested in magnitude (Morgan), but the animosity spikes harder than the issues.',
  covid_jan6_2020: 'Crisis and remote life deepen the sort; the camps stop sharing a common reality.',
};

// Evidence-grade styling for timeline markers (Step 5, Q5). Drives both the
// marker glyph and the chip in the hover tooltip, straight from
// D.events[].evidence: HIGH solid · CONTESTED amber-hollow · LOW faint ·
// MARKER hairline. MED reads as a muted solid; faction/OTHER events get no chip.
const GRADE_STYLE = {
  HIGH:      { label: 'Well-evidenced',          chip: '#2f6b43', glyph: 'solid' },
  MED:       { label: 'Moderate evidence',       chip: CC.ink2,   glyph: 'solid' },
  CONTESTED: { label: 'Contested',               chip: '#b8791f', glyph: 'hollow' },
  LOW:       { label: 'Weak / contested',        chip: '#b8791f', glyph: 'faint' },
  MARKER:    { label: 'Era marker — not causal', chip: CC.ink4,   glyph: 'hairline' },
};
const gradeOf = (e) => (e && GRADE_STYLE[e.evidence]) || null;
const tipOf = (e) => (e && e.evidence_note) || (e && EVENT_HOOKS[e.label]) || null;
const hasTip = (e) => !!tipOf(e);

function TimelineTip({ evt, x, above }) {
  if (!evt) return null;
  const tip = tipOf(evt);
  if (!tip) return null;
  const g = gradeOf(evt);
  return (
    <div style={{
      position: 'absolute', left: x, bottom: above, transform: 'translateX(-50%)',
      width: 248, maxWidth: '60vw', pointerEvents: 'none', zIndex: 20,
      background: CC.ink, color: '#fff', borderRadius: 8, padding: '9px 12px',
      boxShadow: '0 6px 22px rgba(26,29,35,.22)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 4, flexWrap: 'wrap' }}>
        <span style={{ fontFamily: SANS, fontSize: 11, fontWeight: 600, letterSpacing: '.02em' }}>{evt.description}</span>
        {g && <span style={{ fontFamily: SANS, fontSize: 8.5, fontWeight: 700, letterSpacing: '.04em', textTransform: 'uppercase', color: '#fff', background: g.chip, borderRadius: 4, padding: '1px 5px', whiteSpace: 'nowrap' }}>{g.label}</span>}
      </div>
      <div style={{ fontFamily: SANS, fontSize: 11.5, lineHeight: 1.4, color: 'rgba(255,255,255,.82)' }}>{tip}</div>
      <span style={{ position: 'absolute', left: '50%', bottom: -5, transform: 'translateX(-50%) rotate(45deg)', width: 10, height: 10, background: CC.ink }} />
    </div>
  );
}

// a timeline marker whose glyph reads the evidence grade (Step 5):
//   solid  — HIGH/MED (well-evidenced)    hollow — CONTESTED (amber ring)
//   faint  — LOW (weak/contested)         default solid for ungraded factions
function GradeMarker({ ex, y, on, g }) {
  const glyph = g ? g.glyph : 'solid';
  if (glyph === 'hollow') {
    return <circle cx={ex} cy={y} r={on ? 4 : 3} fill={CC.surface} stroke={on ? '#b8791f' : '#c79248'} strokeWidth={1.7} />;
  }
  if (glyph === 'faint') {
    return <circle cx={ex} cy={y} r={on ? 3.4 : 2.4} fill={on ? CC.ink2 : CC.ink4} opacity={on ? 1 : 0.6} />;
  }
  return <circle cx={ex} cy={y} r={on ? 3.8 : 2.8} fill={on ? CC.ink : CC.ink2} />;
}

function ProtoTimeline({ tick, setTick, width = 820, releaseTick = null, showReleases = false, color = CC.ink, altLabels = false }) {
  const H = altLabels ? 104 : 92, padL = 14, padR = 14, trackY = altLabels ? 38 : 50;
  const decades = [1980, 1990, 2000, 2010, 2020];
  const releaseTicksArr = Object.keys(D.meta.release_years).map(Number);
  const [hovEvt, setHovEvt] = React.useState(null);

  // measure the rendered width so the viewBox is 1:1 with pixels (no circle stretch)
  const ref = React.useRef(null);
  const [w, setW] = React.useState(width);
  React.useEffect(() => {
    const el = ref.current; if (!el) return;
    const update = () => setW(Math.max(320, el.clientWidth || width));
    update();
    const ro = new ResizeObserver(update); ro.observe(el);
    return () => ro.disconnect();
  }, [width]);

  const x0 = padL, x1 = w - padR;
  const tx = (t) => x0 + (t / LAST) * (x1 - x0);
  const playX = tx(tick);
  const scrub = (clientX) => {
    const r = ref.current.getBoundingClientRect();
    const frac = (clientX - r.left) / r.width;
    setTick(Math.max(0, Math.min(LAST, frac * LAST)));
  };
  const onDown = (e) => { scrub(e.clientX); const mv = (ev) => scrub(ev.clientX); const up = () => { window.removeEventListener('pointermove', mv); window.removeEventListener('pointerup', up); }; window.addEventListener('pointermove', mv); window.addEventListener('pointerup', up); };

  const tipX = hovEvt ? tx(hovEvt.tick) : 0;
  const tipBottom = (H - trackY) + 16;
  return (
    <div style={{ position: 'relative' }} onMouseLeave={() => setHovEvt(null)}>
    <TimelineTip evt={hovEvt} x={tipX} above={tipBottom} />
    <svg ref={ref} viewBox={`0 0 ${w} ${H}`} width="100%" height={H} preserveAspectRatio="xMidYMid meet"
         onPointerDown={onDown} style={{ display: 'block', cursor: 'pointer', touchAction: 'none' }}>
      <line x1={x0} y1={trackY} x2={x1} y2={trackY} stroke={CC.borderS} strokeWidth="1.5" />
      <line x1={x0} y1={trackY} x2={playX} y2={trackY} stroke={CC.ink} strokeWidth="1.5" />
      {decades.map((y) => (
        <g key={y}>
          {altLabels ? (
            <React.Fragment>
              <line x1={tx(yearToTick(y))} y1={H - 16} x2={tx(yearToTick(y))} y2={H - 12} stroke={CC.ink4} strokeWidth="1" />
              <text x={tx(yearToTick(y))} y={H - 3} textAnchor="middle" style={{ fontFamily: MONO, fontSize: 10.5, fill: CC.ink4, ...TNUM }}>{y}</text>
            </React.Fragment>
          ) : (
            <React.Fragment>
              <line x1={tx(yearToTick(y))} y1={trackY} x2={tx(yearToTick(y))} y2={trackY + 9} stroke={CC.ink4} strokeWidth="1" />
              <text x={tx(yearToTick(y))} y={trackY + 24} textAnchor="middle" style={{ fontFamily: MONO, fontSize: 11.5, fill: CC.ink3, ...TNUM }}>{y}</text>
            </React.Fragment>
          )}
        </g>
      ))}
      {/* minor events: unlabeled ticks. Plain decade boundaries stay hidden, but
          the MARKER-graded Citizens United still shows — as a faint hairline, so
          the demotion (present, but non-causal) reads honestly. (Step 5) */}
      {D.events.filter((e) => (e.kind !== 'decade_boundary' || e.evidence === 'MARKER') && !LABELLED[e.label]).map((e) => {
        const g = gradeOf(e);
        const on = hovEvt && hovEvt.label === e.label;
        const ex = tx(e.tick);
        if (g && g.glyph === 'hairline') {
          return (
            <g key={e.label}>
              <line x1={ex} y1={trackY - 7} x2={ex} y2={trackY + 7} stroke={on ? CC.ink2 : CC.ink4} strokeWidth="1" strokeDasharray="1.5 2.5" />
              <text x={ex} y={trackY - 11} textAnchor="middle" style={{ fontFamily: SANS, fontSize: 8.5, fontStyle: 'italic', fill: on ? CC.ink2 : CC.ink4 }}>Citizens United</text>
            </g>
          );
        }
        const faint = g && g.glyph === 'faint';
        return <circle key={e.label} cx={ex} cy={trackY} r={on ? 3.4 : faint ? 1.8 : 2.2} fill={on ? CC.ink2 : CC.ink4} opacity={faint && !on ? 0.6 : 1} />;
      })}
      {/* major events: short labels. altLabels => alternate below/above the line (C8) */}
      {D.events.filter((e) => LABELLED[e.label]).map((e, i) => {
        const ex = tx(e.tick);
        const on = hovEvt && hovEvt.label === e.label;
        if (altLabels) {
          const below = i % 2 === 0;                 // bottom-top-bottom
          const ty = below ? trackY + 20 : trackY - 13;
          const ly = below ? trackY + 11 : trackY - 11;
          return (
            <g key={e.label}>
              <line x1={ex} y1={trackY} x2={ex} y2={ly} stroke={on ? CC.ink2 : CC.ink4} strokeWidth="1" strokeDasharray="1.5 2" />
              <GradeMarker ex={ex} y={trackY} on={on} g={gradeOf(e)} />
              <text x={ex} y={ty} textAnchor="middle" dominantBaseline={below ? 'hanging' : 'auto'} style={{ fontFamily: SANS, fontSize: 10, fill: on ? CC.ink : CC.ink2, fontWeight: on ? 600 : 500 }}>{LABELLED[e.label]}</text>
            </g>
          );
        }
        const up = trackY - 13 - (i % 2) * 16;
        return (
          <g key={e.label}>
            <line x1={ex} y1={trackY} x2={ex} y2={up + 6} stroke={on ? CC.ink2 : CC.ink4} strokeWidth="1" strokeDasharray="1.5 2" />
            <GradeMarker ex={ex} y={trackY} on={on} g={gradeOf(e)} />
            <text x={ex} y={up} textAnchor="middle" style={{ fontFamily: SANS, fontSize: 10, fill: on ? CC.ink : CC.ink3, fontWeight: on ? 600 : 500 }}>{LABELLED[e.label]}</text>
          </g>
        );
      })}
      {/* generous transparent hit-areas for any event carrying a tooltip
          (evidence_note from the engine, or a fallback hook) */}
      {D.events.filter((e) => hasTip(e)).map((e) => (
        <rect key={'hit-' + e.label} x={tx(e.tick) - 13} y={0} width={26} height={H}
          fill="transparent" style={{ cursor: 'help' }}
          onMouseEnter={() => setHovEvt(e)} onMouseMove={() => setHovEvt(e)}
          onPointerDown={(ev) => { ev.stopPropagation(); setTick(e.tick); }} />
      ))}
      {showReleases && releaseTicksArr.map((rt) => {
        const sel = releaseTick === rt;
        return <circle key={rt} cx={tx(rt)} cy={trackY} r={sel ? 5 : 3.5} fill={sel ? color : CC.surface} stroke={color} strokeWidth="1.4" />;
      })}
      {releaseTick != null && (
        <g>
          <line x1={tx(releaseTick)} y1={trackY - 4} x2={tx(releaseTick)} y2={H} stroke={color} strokeWidth="1.4" strokeDasharray="3 3" />
          <text x={tx(releaseTick)} y={H - 3} textAnchor="middle" style={{ fontFamily: MONO, fontSize: 10, fill: color, fontWeight: 600 }}>released {D.meta.release_years[releaseTick]}</text>
        </g>
      )}
      <line x1={playX} y1={trackY - 5} x2={playX} y2={trackY + 5} stroke={CC.ink} strokeWidth="2" />
      <circle cx={playX} cy={trackY} r="6.5" fill={CC.surface} stroke={CC.ink} strokeWidth="2" />
    </svg>
    </div>
  );
}

// ── sparklines (real macro) ───────────────────────────────────────────────
function ProtoSparklines({ tick, run, cfRun = null, color = CC.ink, width = 300, rowH = 30, gap = 30 }) {
  const padL = 4, padR = 4, chartW = width - padL - padR;
  const labelH = 20, H = rowH * 2 + gap + labelH;
  const tx = (t) => padL + (t / LAST) * chartW;
  const playX = tx(tick);
  const rawUid = React.useId();
  const uid = rawUid.replace(/[^a-zA-Z0-9]/g, '');

  const yOf = (m, v) => { const [lo, hi] = m.domain, span = (hi - lo) || 1; return rowH - ((v - lo) / span) * (rowH - 9); };
  const linePts = (r, m) => r.macro.map((mm, i) => [padL + (i / LAST) * chartW, yOf(m, m.transform(mm[m.key]))]);
  const toPath = (pts) => pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');

  const Row = ({ y0, m, accent, gid }) => {
    const valNow = m.transform(macroAt(cfRun || run, tick, m.key));
    const pts = linePts(run, m);
    const area = `${toPath(pts)} L${pts[pts.length - 1][0].toFixed(1)},${rowH} L${pts[0][0].toFixed(1)},${rowH} Z`;
    const dotY = yOf(m, valNow);
    return (
      <g transform={`translate(0,${y0})`}>
        <text x={padL} y={-7} style={{ fontFamily: SANS, fontSize: 11.5, fill: CC.ink2, fontWeight: 500 }}>{m.label}</text>
        <text x={width - padR} y={-7} textAnchor="end" style={{ fontFamily: MONO, fontSize: 13, fontWeight: 600, fill: cfRun ? color : CC.ink, ...TNUM }}>{valNow.toFixed(2)}</text>
        <line x1={padL} y1={9} x2={width - padR} y2={9} stroke={CC.border} strokeWidth="1" strokeDasharray="2 4" opacity="0.55" />
        <line x1={padL} y1={rowH} x2={width - padR} y2={rowH} stroke={CC.border} strokeWidth="1" />
        {!cfRun && <path d={area} fill={`url(#${gid})`} stroke="none" />}
        <path d={toPath(linePts(run, m))} fill="none" stroke={cfRun ? CC.ink4 : accent} strokeWidth={cfRun ? 1.3 : 2} strokeDasharray={cfRun ? '3 3' : 'none'} strokeLinejoin="round" strokeLinecap="round" />
        {cfRun && <path d={toPath(linePts(cfRun, m))} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />}
        <line x1={playX} y1={-2} x2={playX} y2={rowH} stroke={CC.ink4} strokeDasharray="1 3" strokeWidth="1" />
        {!cfRun && <circle cx={playX} cy={dotY} r="3.4" fill={CC.surface} stroke={accent} strokeWidth="2" />}
      </g>
    );
  };

  return (
    <svg viewBox={`0 0 ${width} ${H}`} width="100%" height={H} preserveAspectRatio="xMidYMid meet" style={{ display: 'block' }}>
      <defs>
        <linearGradient id={`${uid}-sep`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="rgba(31,53,101,0.18)" />
          <stop offset="1" stopColor="rgba(31,53,101,0)" />
        </linearGradient>
        <linearGradient id={`${uid}-aff`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="rgba(139,37,48,0.16)" />
          <stop offset="1" stopColor="rgba(139,37,48,0)" />
        </linearGradient>
      </defs>
      <Row y0={labelH} m={METRICS.sep} accent={CC.d} gid={`${uid}-sep`} />
      <Row y0={labelH + rowH + gap} m={METRICS.aff} accent={CC.r} gid={`${uid}-aff`} />
    </svg>
  );
}

Object.assign(window, { ProtoCharacter, ProtoEgoMini, ProtoTimeline, ProtoSparklines, currentBeat });
