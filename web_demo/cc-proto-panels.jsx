// Calm to Camps — prototype panels: timeline, sparklines.

// ── timeline ───────────────────────────────────────────────────────────
// curated labels for the crowded event timeline — others render as bare ticks
const LABELLED = {
  gingrich_1994: 'Gingrich',
  fairness_doctrine_1987: 'Fairness Doctrine',
  fox_news_1996: 'Fox News',
  social_media_ramp_start_2008: 'Obama · social media',
  tea_party_2009: 'Tea Party',
  maga_2015: 'MAGA',
  trump_2016_and_status_threat: 'Trump',
  covid_jan6_2020: 'COVID · Jan 6',
};

// Short names for the non-causal era markers (hairline glyph). These are NOT in
// LABELLED — they ride a faint dashed tick to read as "present, but not a cause."
// (The renderer used to hardcode "Citizens United" here, which mislabeled
// Obergefell; keyed by event label now so each reads correctly.)
const MARKER_NAME = {
  decade_2010_and_citizens_united: 'Citizens United',
  obergefell_2015: 'Obergefell',
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
  social_media_ramp_start_2008: 'Often blamed, rarely convicted: polarization rose fastest among the least-online, and deactivation studies came back near zero.',
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

function ProtoTimeline({ tick, setTick, width = 820, releaseTick = null, showReleases = false, color = CC.ink, altLabels = false, events = true }) {
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

  // Watch-mode label placement: pack every text label (causal landmarks +
  // era markers) into stacked lanes so none overlap, however crowded the
  // 2008–2020 stretch gets. Glyphs stay on the track; only the text + its
  // connector line move into a lane. Innermost lanes fill first, alternating
  // below/above, so labels only stack outward where they'd actually collide.
  const labelLayout = React.useMemo(() => {
    if (!altLabels || !events) return null;
    const textW = (s, fs) => s.length * fs * 0.54 + 6; // rough width + breathing room
    const items = [];
    D.events.filter((e) => LABELLED[e.label]).forEach((e) =>
      items.push({ key: e.label, ex: tx(e.tick), text: LABELLED[e.label], italic: false, fs: 10, w: textW(LABELLED[e.label], 10) }));
    // MARKER / hairline events (Citizens United, Obergefell) are dropped entirely —
    // no label and no tick (see the minor-events filter below).
    items.sort((a, b) => a.ex - b.ex);
    const lanes = [
      { side: 'below', row: 0 }, { side: 'above', row: 0 },
      { side: 'below', row: 1 }, { side: 'above', row: 1 },
      { side: 'below', row: 2 }, { side: 'above', row: 2 },
    ].map((l) => ({ ...l, right: -Infinity }));
    const GAP = 7;
    for (const it of items) {
      const left = it.ex - it.w / 2;
      const lane = lanes.find((l) => left >= l.right + GAP) || lanes[lanes.length - 1];
      it.side = lane.side; it.row = lane.row;
      lane.right = it.ex + it.w / 2;
    }
    return items;
  }, [w, altLabels]);

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
      {/* minor events: unlabeled ticks. Decade boundaries stay hidden — including
          the Citizens United MARKER, dropped from the story entirely (best-
          identified studies find no polarization effect; it was useless). Only
          graded non-boundary events show. */}
      {events && D.events.filter((e) => e.kind !== 'decade_boundary' && !LABELLED[e.label] && !(gradeOf(e) && gradeOf(e).glyph === 'hairline')).map((e) => {
        const g = gradeOf(e);
        const on = hovEvt && hovEvt.label === e.label;
        const ex = tx(e.tick);
        if (g && g.glyph === 'hairline') {
          return (
            <g key={e.label}>
              <line x1={ex} y1={trackY - 7} x2={ex} y2={trackY + 7} stroke={on ? CC.ink2 : CC.ink4} strokeWidth="1" strokeDasharray="1.5 2.5" />
              {!altLabels &&
              <text x={ex} y={trackY - 11} textAnchor="middle" style={{ fontFamily: SANS, fontSize: 8.5, fontStyle: 'italic', fill: on ? CC.ink2 : CC.ink4 }}>{MARKER_NAME[e.label] || e.label}</text>}
            </g>
          );
        }
        const faint = g && g.glyph === 'faint';
        return <circle key={e.label} cx={ex} cy={trackY} r={on ? 3.4 : faint ? 1.8 : 2.2} fill={on ? CC.ink2 : CC.ink4} opacity={faint && !on ? 0.6 : 1} />;
      })}
      {/* major events: short labels. altLabels => alternate below/above the line (C8) */}
      {events && D.events.filter((e) => LABELLED[e.label]).map((e, i) => {
        const ex = tx(e.tick);
        const on = hovEvt && hovEvt.label === e.label;
        if (altLabels) {
          // text + connector come from the collision-free layout pass below;
          // here we only place the on-track grade marker.
          return <GradeMarker key={e.label} ex={ex} y={trackY} on={on} g={gradeOf(e)} />;
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
      {/* altLabels: every text label drawn from the packed, collision-free
          layout — innermost lane first, stacking outward only where needed. */}
      {altLabels && labelLayout && labelLayout.map((it) => {
        const on = hovEvt && hovEvt.label === it.key;
        const ty = it.side === 'below' ? trackY + 19 + it.row * 13 : trackY - 12 - it.row * 13;
        const ly = it.side === 'below' ? ty - 9 : ty + 3;
        return (
          <g key={'lbl-' + it.key}>
            <line x1={it.ex} y1={trackY} x2={it.ex} y2={ly} stroke={on ? CC.ink2 : CC.ink4} strokeWidth="1" strokeDasharray="1.5 2" />
            <text x={it.ex} y={ty} textAnchor="middle" dominantBaseline={it.side === 'below' ? 'hanging' : 'auto'}
              style={{ fontFamily: SANS, fontSize: it.fs, fontStyle: it.italic ? 'italic' : 'normal',
                fill: on ? CC.ink : (it.italic ? CC.ink4 : CC.ink2), fontWeight: it.italic ? 400 : (on ? 600 : 500) }}>{it.text}</text>
          </g>
        );
      })}
      {/* generous transparent hit-areas for any event carrying a tooltip
          (evidence_note from the engine, or a fallback hook) */}
      {events && D.events.filter((e) => hasTip(e)).map((e) => (
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
function ProtoSparklines({ tick, run, cfRun = null, color = CC.ink, rowH = 56, gap = 34 }) {
  // full-width: measure the container so the viewBox is 1:1 with pixels (no
  // letterboxing) — the charts fill the narrative column like BeatMetric.
  const ref = React.useRef(null);
  const [w, setW] = React.useState(420);
  React.useEffect(() => {
    const el = ref.current; if (!el) return;
    const u = () => setW(Math.max(240, el.clientWidth));
    u(); const ro = new ResizeObserver(u); ro.observe(el); return () => ro.disconnect();
  }, []);
  const padL = 4, padR = 4, chartW = w - padL - padR;
  const labelH = 20, H = rowH * 2 + gap + labelH;
  const playX = padL + (tick / LAST) * chartW;

  const yOf = (m, v) => { const [lo, hi] = m.domain, span = (hi - lo) || 1; return rowH - ((v - lo) / span) * (rowH - 9); };
  const ptsOf = (r, m) => r.macro.map((mm, i) => [padL + (i / LAST) * chartW, yOf(m, m.transform(mm[m.key]))]);
  const toPath = (pts) => pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');

  // minimal sparkline (matches BeatMetric): faint dashed full trajectory,
  // solid accent up to the playhead, hollow dot on the page colour.
  const Row = ({ y0, m, accent }) => {
    const valNow = m.transform(macroAt(cfRun || run, tick, m.key));
    const pts = ptsOf(run, m);
    const dotY = yOf(m, valNow);
    const past = pts.filter((p) => p[0] <= playX + 0.01);
    const pastPath = [...past.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`), `L${playX.toFixed(1)},${dotY.toFixed(1)}`].join(' ');
    return (
      <g transform={`translate(0,${y0})`}>
        <text x={padL} y={-7} style={{ fontFamily: SANS, fontSize: 11.5, fill: CC.ink2, fontWeight: 500 }}>{m.label}</text>
        <text x={w - padR} y={-7} textAnchor="end" style={{ fontFamily: MONO, fontSize: 13, fontWeight: 600, fill: cfRun ? color : CC.ink, ...TNUM }}>{valNow.toFixed(2)}</text>
        <path d={toPath(pts)} fill="none" stroke={CC.borderS} strokeWidth="1.1" strokeDasharray="2 3" opacity="0.8" />
        {cfRun ?
          <path d={toPath(ptsOf(cfRun, m))} fill="none" stroke={color} strokeWidth="1.9" strokeLinejoin="round" strokeLinecap="round" /> :
          <path d={pastPath} fill="none" stroke={accent} strokeWidth="1.9" strokeLinejoin="round" strokeLinecap="round" />}
        <circle cx={playX} cy={dotY} r="3.4" fill={CC.bg} stroke={cfRun ? color : accent} strokeWidth="2" />
      </g>
    );
  };

  return (
    <div ref={ref}>
      <svg viewBox={`0 0 ${w} ${H}`} width="100%" height={H} preserveAspectRatio="xMidYMid meet" style={{ display: 'block' }}>
        <Row y0={labelH} m={METRICS.sep} accent={CC.d} />
        <Row y0={labelH + rowH + gap} m={METRICS.aff} accent={CC.r} />
      </svg>
    </div>
  );
}

Object.assign(window, { ProtoTimeline, ProtoSparklines });
