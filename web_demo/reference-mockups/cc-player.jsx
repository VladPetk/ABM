// Calm to Camps — main player, two layout variations.
// A: character panel right, sparklines floating on the compass, timeline full-width footer.
// B: character panel left, compass right, sparklines docked into a bottom dashboard.

function InterventionPicker({ active = null }) {
  const label = active ? INTERVENTIONS.find((i) => i.id === active).name : 'No intervention (baseline)';
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 9, padding: '7px 13px', border: `1px solid ${CC.borderS}`, borderRadius: 999, background: CC.surface, fontSize: 13.5, color: CC.ink, cursor: 'default' }}>
      <Eyebrow style={{ fontSize: 9.5, color: CC.ink3 }}>Intervention</Eyebrow>
      <span style={{ fontWeight: 500 }}>{label}</span>
      <span style={{ color: CC.ink3, fontSize: 11 }}>▾</span>
    </span>
  );
}

function PlayerHeader({ active = null }) {
  return (
    <div style={{ height: 56, flexShrink: 0, display: 'flex', alignItems: 'center', gap: 18, padding: '0 22px', borderBottom: `1px solid ${CC.border}`, background: CC.bg }}>
      <Logo />
      <span style={{ width: 1, height: 18, background: CC.border }} />
      <span style={{ fontFamily: SERIF, fontStyle: 'italic', fontSize: 16, color: CC.ink2, whiteSpace: 'nowrap' }}>Calm to Camps</span>
      <span style={{ flex: 1 }} />
      <InterventionPicker active={active} />
      <span style={{ fontSize: 13, color: CC.ink2, display: 'inline-flex', alignItems: 'center', gap: 7, padding: '6px 13px', border: `1px solid ${CC.border}`, borderRadius: 999 }}>About this model <InfoDot /></span>
    </div>
  );
}

function monthYear(year) {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const frac = year - Math.floor(year);
  return `${months[Math.min(11, Math.floor(frac * 12))]} ${Math.floor(year)}`;
}

function Transport({ year, tick = 108, total = 135 }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      <span style={{ display: 'inline-flex', width: 32, height: 32, borderRadius: 999, background: CC.ink, color: '#fff', alignItems: 'center', justifyContent: 'center', fontSize: 12 }}>▶</span>
      <span style={{ display: 'inline-flex', width: 28, height: 28, borderRadius: 999, border: `1px solid ${CC.border}`, color: CC.ink2, alignItems: 'center', justifyContent: 'center', fontSize: 11 }}>↺</span>
      <div style={{ display: 'flex', gap: 3 }}>
        {['½', '1×', '2×', '4×'].map((s, i) => (
          <span key={s} style={{ fontSize: 11, padding: '3px 8px', borderRadius: 999, border: `1px solid ${i === 1 ? CC.ink : CC.border}`, color: i === 1 ? CC.ink : CC.ink3, fontFamily: MONO, fontWeight: i === 1 ? 500 : 400, background: i === 1 ? CC.surface : 'transparent', ...TNUM }}>{s}</span>
        ))}
      </div>
    </div>
  );
}

function CompassLegend({ style }) {
  return (
    <FloatCard style={{ padding: '9px 15px', ...style }}>
      <div style={{ display: 'flex', gap: 16, alignItems: 'center', fontSize: 12.5, color: CC.ink2 }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 7 }}><PartySwatch party="D" /> Democrat</span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 7 }}><PartySwatch party="I" /> Independent</span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 7 }}><PartySwatch party="R" /> Republican</span>
      </div>
    </FloatCard>
  );
}

function PlayerScreen({ layout = 'A', year = 2016, character = 'linda' }) {
  const W = 1440, H = 900;
  const SIDEBAR = 420;
  const footerH = 158;

  return (
    <div style={{ width: W, height: H, background: CC.bg, color: CC.ink, fontFamily: SANS, display: 'flex', flexDirection: 'column', overflow: 'hidden', letterSpacing: '-.005em' }} data-screen-label="Player">
      <PlayerHeader />
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: `1fr ${SIDEBAR}px`, minHeight: 0 }}>
        {/* clean, unobstructed compass */}
        <div style={{ position: 'relative', background: CC.surface, height: '100%' }}>
          <div style={{ position: 'absolute', inset: 0, padding: '20px 28px 16px' }}>
            <Compass year={year} spotlight={true} />
          </div>
          <CompassLegend style={{ left: 22, bottom: 18 }} />
        </div>
        {/* character sidebar (right) */}
        <div style={{ padding: '18px 30px 24px', borderLeft: `1px solid ${CC.border}`, background: CC.bg, overflow: 'hidden' }}>
          <CharacterPanel year={year} character={character} />
        </div>
      </div>
      {/* single full-width footer: transport · timeline · inline sparklines */}
      <div style={{ height: footerH, flexShrink: 0, borderTop: `1px solid ${CC.border}`, background: CC.bg, display: 'flex', alignItems: 'center', gap: 28, padding: '0 32px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flexShrink: 0 }}>
          <Transport year={year} />
          <span style={{ fontFamily: MONO, fontSize: 12.5, color: CC.ink, ...TNUM }}>{monthYear(year)} <span style={{ color: CC.ink4 }}>· tick 108 / 135</span></span>
        </div>
        <div style={{ width: 1, height: 96, background: CC.border }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <Eyebrow style={{ color: CC.ink3 }}>1980 → 2025</Eyebrow>
          <div style={{ marginTop: 4 }}><TimelineBar width={780} year={year} /></div>
        </div>
        <div style={{ width: 1, height: 96, background: CC.border }} />
        <div style={{ width: 300, flexShrink: 0 }}>
          <Eyebrow style={{ color: CC.ink3 }}>Where the country is</Eyebrow>
          <div style={{ marginTop: 2 }}><MacroSparklines width={300} year={year} compact /></div>
        </div>
      </div>
    </div>
  );
}

window.PlayerScreen = PlayerScreen;
window.PlayerHeader = PlayerHeader;
window.Transport = Transport;
window.monthYear = monthYear;
window.InterventionPicker = InterventionPicker;
window.CompassLegend = CompassLegend;
