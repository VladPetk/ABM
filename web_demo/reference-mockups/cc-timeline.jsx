// Calm to Camps — historical timeline + macro sparklines
// TimelineBar: 1980→2025 track with decade labels, event markers, a date
// playhead, and (in intervention mode) the 10 release-year candidates plus a
// chosen release marker. MacroSparklines: the two Iyengar metrics, with an
// optional counterfactual overlay.

function TimelineBar({ width = 1200, year = 2016, releaseYear = null, showReleaseMarkers = false, color = CC.ink }) {
  const H = 92, padL = 14, padR = 14;
  const trackY = 50;
  const x0 = padL, x1 = width - padR;
  const yx = (y) => x0 + ((y - YEAR0) / (YEAR1 - YEAR0)) * (x1 - x0);
  const releaseYears = [1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025];
  const playX = yx(year);

  return (
    <svg viewBox={`0 0 ${width} ${H}`} width="100%" height={H} style={{ display: 'block' }}>
      {/* base track */}
      <line x1={x0} y1={trackY} x2={x1} y2={trackY} stroke={CC.borderS} strokeWidth="1.5" />
      {/* progress fill to playhead */}
      <line x1={x0} y1={trackY} x2={playX} y2={trackY} stroke={CC.ink} strokeWidth="1.5" />

      {/* decade + 5-year ticks */}
      {[1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025].map((y) => {
        const decade = y % 10 === 0;
        return (
          <g key={y}>
            <line x1={yx(y)} y1={trackY} x2={yx(y)} y2={trackY + (decade ? 9 : 5)} stroke={CC.ink4} strokeWidth="1" />
            {decade && (
              <text x={yx(y)} y={trackY + 24} textAnchor="middle"
                    style={{ fontFamily: MONO, fontSize: 11.5, fill: CC.ink3, ...TNUM }}>{y}</text>
            )}
          </g>
        );
      })}

      {/* event markers (above track) */}
      {EVENTS.map((e, i) => {
        const ex = yx(e.year);
        const up = trackY - 14 - (i % 2) * 15;   // stagger to avoid label collisions
        return (
          <g key={e.id}>
            <line x1={ex} y1={trackY} x2={ex} y2={up + 7} stroke={CC.ink4} strokeWidth="1" strokeDasharray="1.5 2" />
            <circle cx={ex} cy={trackY} r="2.6" fill={CC.ink2} />
            <text x={ex} y={up} textAnchor="middle"
                  style={{ fontFamily: SANS, fontSize: 10.5, fill: CC.ink3, fontWeight: 500 }}>{e.short}</text>
          </g>
        );
      })}

      {/* release-year candidates */}
      {showReleaseMarkers && releaseYears.map((y) => {
        const sel = releaseYear === y;
        return (
          <circle key={'rc' + y} cx={yx(y)} cy={trackY} r={sel ? 5 : 3.5}
                  fill={sel ? color : CC.surface} stroke={color} strokeWidth="1.4" />
        );
      })}

      {/* chosen release marker */}
      {releaseYear && (
        <g>
          <line x1={yx(releaseYear)} y1={trackY - 4} x2={yx(releaseYear)} y2={H} stroke={color} strokeWidth="1.4" strokeDasharray="3 3" />
          <text x={yx(releaseYear)} y={H - 3} textAnchor="middle"
                style={{ fontFamily: MONO, fontSize: 10, fill: color, fontWeight: 600 }}>released {releaseYear}</text>
        </g>
      )}

      {/* playhead */}
      <line x1={playX} y1={trackY - 4} x2={playX} y2={trackY + 4} stroke={CC.ink} strokeWidth="2" />
      <circle cx={playX} cy={trackY} r="6.5" fill={CC.surface} stroke={CC.ink} strokeWidth="2" />
    </svg>
  );
}

// Twin Iyengar metric sparklines. counterfactualRelease draws the
// baseline in grey and the bent counterfactual in the intervention colour.
function MacroSparklines({ width = 360, year = 2016, counterfactualRelease = null, color = CC.ink, compact = false }) {
  const base = macroSeries();
  const cf = counterfactualRelease ? macroCounterfactual(counterfactualRelease) : null;
  const padL = 4, padR = 4, chartW = width - padL - padR;
  const rowH = compact ? 37 : 54, gap = compact ? 13 : 16, labelW = 0;
  const H = rowH * 2 + gap + 22;
  const yx = (y) => padL + ((y - YEAR0) / (YEAR1 - YEAR0)) * chartW;
  const playX = yx(year);

  const Row = ({ y0, key1, label, value }) => (
    <g>
      <text x={padL} y={y0 - 6} style={{ fontFamily: SANS, fontSize: 11.5, fill: CC.ink2, fontWeight: 500 }}>{label}</text>
      <text x={width - padR} y={y0 - 6} textAnchor="end"
            style={{ fontFamily: MONO, fontSize: 11.5, fill: cf ? color : CC.ink, ...TNUM }}>{value}</text>
      <line x1={padL} y1={y0 + rowH} x2={width - padR} y2={y0 + rowH} stroke={CC.border} strokeWidth="1" />
      {/* baseline */}
      <path d={seriesPath(base, key1, padL, y0, chartW, rowH)} fill="none"
            stroke={cf ? CC.ink4 : (key1 === 'sep' ? CC.ink2 : CC.r)} strokeWidth={cf ? 1.4 : 1.75}
            strokeDasharray={cf ? '3 3' : 'none'} />
      {/* counterfactual */}
      {cf && <path d={seriesPath(cf, key1, padL, y0, chartW, rowH)} fill="none" stroke={color} strokeWidth="1.9" />}
      {/* playhead */}
      <line x1={playX} y1={y0 - 2} x2={playX} y2={y0 + rowH} stroke={CC.ink4} strokeDasharray="1 3" strokeWidth="1" />
    </g>
  );

  const cur = base.find((p) => Math.round(p.year) === Math.round(year)) || base[base.length - 1];
  const curCf = cf ? (cf.find((p) => Math.round(p.year) === Math.round(year)) || cf[cf.length - 1]) : null;
  const sepVal = (curCf || cur).sep.toFixed(2);
  const affVal = (curCf || cur).aff.toFixed(2);

  return (
    <svg viewBox={`0 0 ${width} ${H}`} width="100%" height={H} style={{ display: 'block' }}>
      <Row y0={18} key1="sep" label="Party separation" value={sepVal} />
      <Row y0={18 + rowH + gap} key1="aff" label="Affective polarization" value={affVal} />
    </svg>
  );
}

window.TimelineBar = TimelineBar;
window.MacroSparklines = MacroSparklines;
