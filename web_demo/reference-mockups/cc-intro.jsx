// Calm to Camps — intro / landing artboard
// The framing moment before you press play. Editorial left column,
// a calm 1980 compass on the right (the "before" picture).

function IntroScreen() {
  const W = 1440, H = 900;
  // the compass is "already playing" — a slow loop from 1980→2025
  const [yr, setYr] = React.useState(1980);
  React.useEffect(() => {
    let raf, start = null;
    const period = 70;
    const loop = (ts) => {
      if (start == null) start = ts;
      const t = ((ts - start) / 1000) % period;
      setYr(YEAR0 + (YEAR1 - YEAR0) * (t / period));
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);
  return (
    <div style={{ width: W, height: H, background: CC.bg, color: CC.ink, fontFamily: SANS, position: 'relative', overflow: 'hidden', letterSpacing: '-.005em' }} data-screen-label="Intro">
      {/* header */}
      <div style={{ height: 60, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 40px', borderBottom: `1px solid ${CC.border}` }}>
        <Logo />
        <div style={{ display: 'flex', gap: 26, fontSize: 13.5, color: CC.ink3 }}>
          <span style={{ color: CC.ink, fontWeight: 500 }}>The story</span>
          <span>Characters</span>
          <span>Interventions</span>
          <span>Methods</span>
          <span>About</span>
        </div>
      </div>

      {/* body split */}
      <div style={{ display: 'grid', gridTemplateColumns: '620px 1fr', height: H - 60 }}>
        {/* left — framing */}
        <div style={{ padding: '64px 56px 48px', display: 'flex', flexDirection: 'column' }}>
          <Eyebrow color={CC.ink3}>An interactive history of American polarization · 1980–2025</Eyebrow>
          <h1 style={{ margin: '22px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: 76, lineHeight: 0.98, letterSpacing: '-.025em' }}>
            Calm to Camps
          </h1>
          <p style={{ margin: '20px 0 0', fontFamily: SERIF, fontStyle: 'italic', fontSize: 21, lineHeight: 1.4, color: CC.ink2, maxWidth: 480 }}>
            How a country that mostly agreed to disagree sorted itself into two camps that can barely speak.
          </p>
          <p style={{ margin: '26px 0 0', fontSize: 15.5, lineHeight: 1.6, color: CC.ink2, maxWidth: 470 }}>
            Watch 240 Americans drift across the political compass over forty-five years. Follow four of them by name. See the events that pushed them — and try the interventions that were supposed to bring them back together.
          </p>

          {/* character preview */}
          <div style={{ marginTop: 34 }}>
            <Eyebrow>You'll follow</Eyebrow>
            <div style={{ display: 'flex', gap: 10, marginTop: 12, flexWrap: 'wrap' }}>
              {[['linda', 'Suburban swing voter'], ['james', 'Stable left, cooling'], ['maria', 'Independent → left'], ['bob', 'Tea Party → MAGA']].map(([id, desc]) => (
                <div key={id} style={{ display: 'flex', alignItems: 'center', gap: 9, padding: '8px 13px', background: CC.surface, border: `1px solid ${CC.border}`, borderRadius: 10 }}>
                  <PartySwatch party={CHARACTERS[id].party === undefined ? 'I' : 'I'} size={9} />
                  <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.15 }}>
                    <span style={{ fontSize: 13.5, fontWeight: 600 }}>{CHARACTERS[id].name}</span>
                    <span style={{ fontSize: 11.5, color: CC.ink3 }}>{desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* CTA */}
          <div style={{ marginTop: 'auto', display: 'flex', alignItems: 'center', gap: 18 }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 11, padding: '13px 22px 13px 24px', background: CC.ink, color: '#fff', fontSize: 15, fontWeight: 500, borderRadius: 999, cursor: 'default' }}>
              Press play — watch 45 years
              <span style={{ display: 'inline-flex', width: 18, height: 18, borderRadius: 999, background: 'rgba(255,255,255,.18)', alignItems: 'center', justifyContent: 'center', fontSize: 9 }}>▶</span>
            </span>
            <span style={{ fontSize: 13, color: CC.ink3, fontFamily: MONO, ...TNUM }}>45 years · 240 lives · 1 compass</span>
          </div>
        </div>

        {/* right — calm 1980 compass */}
        <div style={{ position: 'relative', borderLeft: `1px solid ${CC.border}`, background: CC.surface, display: 'flex', flexDirection: 'column', padding: '40px 48px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <span style={{ fontFamily: SERIF, fontStyle: 'italic', fontSize: 19, color: CC.ink2 }}>The United States, {Math.floor(yr)}</span>
            <span style={{ fontSize: 12.5, color: CC.ink3, display: 'inline-flex', alignItems: 'center', gap: 7 }}>
              <span style={{ width: 7, height: 7, borderRadius: 999, background: '#3f7d54' }} /> playing · 1980 → 2025
            </span>
          </div>
          <div style={{ flex: 1, position: 'relative', marginTop: 12 }}>
            <Compass year={yr} spotlight={true} />
          </div>
          {/* legend */}
          <div style={{ display: 'flex', gap: 20, alignItems: 'center', fontSize: 13, color: CC.ink2, justifyContent: 'center' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 7 }}><PartySwatch party="D" /> Democrat</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 7 }}><PartySwatch party="I" /> Independent</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 7 }}><PartySwatch party="R" /> Republican</span>
          </div>
        </div>
      </div>
    </div>
  );
}

window.IntroScreen = IntroScreen;
