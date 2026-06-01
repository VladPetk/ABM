// Calm to Camps — visual-language system (addresses fix-list section F).
// One source of truth for the type scale, radii, spacing, and the small
// chip/caption family — so every view draws from the same set instead of
// choosing values per element. Builds on CC tokens from cc-shared.jsx.

const DS = {
  // F1 — six-step type ladder. Use ONLY these.
  type: { display: 40, title: 28, subhead: 20, body: 15, small: 13, micro: 11.5 },
  // F4 — three radii + one spacing step
  rad:  { inset: 10, card: 14, pill: 999 },
  sp:   { xs: 8, sm: 14, md: 22, lg: 30 },
};

// F2 — STATUS TAG: the one component for outcome / state labels.
// Sans (not mono — F3), small caps. Tone drives colour; only the charged
// "backfire" tone is allowed to borrow oxblood (F5).
function Tag({ children, tone = 'neutral', solid = false, style }) {
  const map = {
    neutral: CC.ink3, strong: CC.ink, soft: CC.ink4, backfire: CC.r,
  };
  const col = map[tone] || CC.ink3;
  return (
    <span style={{
      fontFamily: SANS, fontSize: 10, fontWeight: 600, letterSpacing: '.08em', textTransform: 'uppercase',
      color: solid ? '#fff' : col, background: solid ? col : 'transparent',
      padding: solid ? '3px 9px' : 0, borderRadius: DS.rad.pill, whiteSpace: 'nowrap',
      display: 'inline-flex', alignItems: 'center', gap: 6, ...style,
    }}>{children}</span>
  );
}

// F2/F5 — CAPTION: plain metadata ("calibrated", "beyond realism").
// Never a pill, never a party colour — just quiet ink.
function Caption({ children, style }) {
  return (
    <span style={{ fontFamily: SANS, fontSize: DS.type.micro, color: CC.ink3, fontStyle: 'italic', ...style }}>{children}</span>
  );
}

// F3 — MONO is for live numeric data only. One helper keeps that honest.
function MonoVal({ children, size = DS.type.small, color = CC.ink, weight = 500, style }) {
  return (
    <span style={{ fontFamily: MONO, fontSize: size, fontWeight: weight, color, ...TNUM, ...style }}>{children}</span>
  );
}

Object.assign(window, { DS, Tag, Caption, MonoVal });
