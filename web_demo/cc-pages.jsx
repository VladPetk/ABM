// Calm to Camps — static content pages (fix-list E1): About + Methods.
// Reachable from the site-level nav. Content is grounded in the real model
// (250-agent polarlab sim, 1980–2025, the compass axes, the calibration
// sources) — no invented numbers.

function PageShell({ eyebrow, title, lead, children }) {
  return (
    <div style={{ flex: 1, minHeight: 0, overflow: 'auto', background: CC.bg }}>
      <div style={{ maxWidth: 760, margin: '0 auto', padding: '72px 40px 120px' }}>
        <Eyebrow>{eyebrow}</Eyebrow>
        <h1 style={{ fontFamily: SERIF, fontWeight: 600, fontSize: DS.type.display, lineHeight: 1.02, letterSpacing: '-.022em', margin: '18px 0 0' }}>{title}</h1>
        {lead && <p style={{ fontFamily: SERIF, fontStyle: 'italic', fontSize: 21, lineHeight: 1.45, color: CC.ink2, margin: '20px 0 0', maxWidth: '40em', textWrap: 'pretty' }}>{lead}</p>}
        <div style={{ marginTop: 8 }}>{children}</div>
      </div>
    </div>
  );
}

function Prose({ children }) {
  return <p style={{ ...PROSE, lineHeight: 1.68, color: CC.ink2, margin: '20px 0 0', maxWidth: '42em', textWrap: 'pretty' }}>{children}</p>;
}
function H2({ children }) {
  return <h2 style={{ fontFamily: SERIF, fontWeight: 600, fontSize: DS.type.title, letterSpacing: '-.015em', margin: '52px 0 0', paddingTop: 28, borderTop: `1px solid ${CC.border}` }}>{children}</h2>;
}

function AboutPage() {
  return (
    <PageShell
      eyebrow="About · polarlab"
      title="Calm to Camps"
      lead="How a country that mostly agreed to disagree sorted itself into two camps that can barely speak.">
      <Prose>
        <strong style={{ color: CC.ink, fontWeight: 600 }}>Calm to Camps</strong> is an interactive history of American
        political polarization from 1980 to 2025. It follows a simulated public — 250 Americans — as they drift across
        a political compass, and pauses at the moments that moved the country: cable news, the social-media feed, a
        status-threat shock. The aim is to make a slow, abstract process visible, then hand you the controls and let you
        ask the obvious question — <em>could anything have pulled them back together?</em>
      </Prose>

      <H2>The claim, in one breath</H2>
      <Prose>
        Americans haven't actually moved that far apart on the issues. What changed is how they <em>feel</em> about each
        other. Positional distance crept up; affective warmth toward the other side collapsed. Distance and animus are
        different axes, and the second one is where the damage is — that distinction is the spine of the whole piece.
      </Prose>

      <H2>Who this is for</H2>
      <Prose>
        It's built for the curious non-specialist: someone who has felt the country harden and wants to understand the
        mechanism without a literature review. Everything quantitative is explained in plain language as you go, and the
        honest answer to "what fixes this?" — <em>most things barely work</em> — is delivered plainly rather than sold.
      </Prose>

      <H2>A word on honesty</H2>
      <Prose>
        This is a model, not a measurement. The realistic interventions are calibrated to published field experiments;
        the "beyond realism" ones are mechanism-driven thought experiments, cranked past anything we'd calibrate, and are
        labelled as such everywhere they appear. The point isn't to predict — it's to build intuition for which kinds of
        levers move a polarized system, and which don't. The <a style={{ color: CC.d, textDecoration: 'none', borderBottom: `1px solid ${CC.dSoft}` }} href="#methods" data-goto="methods">Methods</a> page lays out exactly what's real and what's illustrative.
      </Prose>
    </PageShell>
  );
}

function MethodRow({ k, children }) {
  return (
    <div style={{ display: 'flex', gap: 18, padding: '16px 0', borderBottom: `1px solid ${CC.border}`, alignItems: 'baseline' }}>
      <div style={{ width: 132, flexShrink: 0, fontFamily: SANS, fontSize: DS.type.small, fontWeight: 600, color: CC.ink }}>{k}</div>
      <div style={{ flex: 1, fontSize: DS.type.body, lineHeight: 1.6, color: CC.ink2, textWrap: 'pretty' }}>{children}</div>
    </div>
  );
}

// ── honesty budget ───────────────────────────────────────────────────────────
// Measured fractions are blessed in docs/results/honesty_budget.json (re-measured
// on the fitted shipped config at MHV S5 T5.2, 6 seeds; methods §5.28). Each
// metric's 1980→2025 rise is decomposed by freeze experiments into: emergent
// (rules alone, every external driver frozen at 1980), empirical-input (what the
// data-fed ANES series adds back), and hand-drawn residual (scripted bumps +
// dated events). Display widths are honest roundings that sum to 100; the raw
// measured values (which may slightly over/undershoot from seed noise) live in
// the JSON. "grounded" = emergent + empirical-input = the dark-matter-floor
// quantity (floor ≥0.60 per metric; all clear).
const BUDGET_C = { emergent: '#3f7d54', input: CC.d, residual: '#c47a2c' };
const BUDGET = [
  { k: 'Party separation', emergent: 0, input: 100, residual: 0, grounded: 100,
    note: 'Tracks the empirical ANES party-centroid trajectory almost entirely — the model follows where the survey data says the parties went; it doesn’t invent the sorting.' },
  { k: 'Affective polarization', emergent: 85, input: 0, residual: 15, grounded: 85,
    note: 'The one arc the model’s own dynamics drive: 87% of the collapse in out-party warmth is emergent, produced by the animus rules themselves.' },
  { k: 'Identity alignment', emergent: 2, input: 95, residual: 3, grounded: 97,
    note: 'Also carried by the empirical party trajectory rather than self-organised — alignment follows the same data-fed series.' },
];

function BudgetBar({ row }) {
  const seg = (w, c, title) => w > 0
    ? <div title={title} style={{ width: `${w}%`, background: c, height: '100%' }} /> : null;
  return (
    <div style={{ padding: '16px 0', borderBottom: `1px solid ${CC.border}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 }}>
        <span style={{ fontFamily: SANS, fontSize: DS.type.small, fontWeight: 600, color: CC.ink }}>{row.k}</span>
        <span style={{ fontFamily: SANS, fontSize: DS.type.small, color: CC.ink3 }}>
          <strong style={{ color: CC.ink }}>{row.grounded}% grounded</strong>
          <span style={{ color: CC.ink4 }}> · {row.residual}% hand-drawn</span>
        </span>
      </div>
      <div style={{ display: 'flex', height: 10, borderRadius: DS.rad.pill, overflow: 'hidden', background: CC.bg2 }}>
        {seg(row.emergent, BUDGET_C.emergent, `${row.emergent}% emergent`)}
        {seg(row.input, BUDGET_C.input, `${row.input}% empirical input`)}
        {seg(row.residual, BUDGET_C.residual, `${row.residual}% hand-drawn`)}
      </div>
      <p style={{ margin: '8px 0 0', fontSize: DS.type.micro, lineHeight: 1.5, color: CC.ink3, maxWidth: '40em' }}>{row.note}</p>
    </div>
  );
}

function BudgetLegend() {
  const dot = (c, label) => (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
      <span style={{ width: 9, height: 9, borderRadius: 2, background: c }} />
      <span style={{ fontFamily: SANS, fontSize: DS.type.micro, color: CC.ink2 }}>{label}</span>
    </span>
  );
  return (
    <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', marginBottom: 4 }}>
      {dot(BUDGET_C.emergent, 'Emergent — the agents’ own dynamics')}
      {dot(BUDGET_C.input, 'Empirical input — data-fed ANES series')}
      {dot(BUDGET_C.residual, 'Hand-drawn — scripted bumps + events')}
    </div>
  );
}

// four-cut holdout — transcribed from docs/results/s4_holdout.md (3/3 PASS;
// bands pre-registered before the fit). MHV S4 T4.4.
const HOLDOUT = [
  { cut: 'Temporal', q: 'Fit on ≤2012 only, then predict 2010 / 2020 / 2025', v: 'PASS' },
  { cut: 'Instrument', q: 'Shipped model vs a held-out survey (GSS) it was never fit to', v: 'PASS' },
  { cut: 'Statistic', q: 'Fit separation / affect / spread, then predict issue constraint', v: 'PASS' },
];

function HoldoutScorecard() {
  return (
    <div style={{ marginTop: 18, border: `1px solid ${CC.border}`, borderRadius: DS.rad.inset, overflow: 'hidden' }}>
      {HOLDOUT.map((h, i) => (
        <div key={h.cut} style={{ display: 'flex', gap: 14, alignItems: 'center', padding: '13px 16px',
          borderTop: i ? `1px solid ${CC.border}` : 'none', background: CC.surface }}>
          <span style={{ width: 86, flexShrink: 0, fontFamily: SANS, fontSize: DS.type.small, fontWeight: 600, color: CC.ink }}>{h.cut}</span>
          <span style={{ flex: 1, fontSize: DS.type.small, lineHeight: 1.5, color: CC.ink2 }}>{h.q}</span>
          <span style={{ flexShrink: 0, fontFamily: SANS, fontSize: 11, fontWeight: 700, letterSpacing: '.06em',
            color: '#3f7d54' }}>{h.v}</span>
        </div>
      ))}
    </div>
  );
}

function MethodsPage() {
  return (
    <PageShell
      eyebrow="Methods · how the model works"
      title="What you're looking at"
      lead="An agent-based simulation, two measures of polarization, and a clear line between what's calibrated and what's a thought experiment.">

      <H2>The simulation</H2>
      <Prose>
        The crowd is <strong style={{ color: CC.ink, fontWeight: 600 }}>250 simulated agents</strong>, each with an
        evolving position on a two-axis political compass, stepped across 45 years (1980→2025) at three ticks per year.
        Agents update their views through a media diet and a social network, both of which shift as real-world shocks
        land. The field you see is a smoothed density of where those agents sit — one centrist lump in 1980, two camps
        by 2025, grey where they blend (the vanishing middle).
      </Prose>

      <div style={{ marginTop: 30 }}>
        <Eyebrow>The compass axes</Eyebrow>
        <div style={{ marginTop: 10 }}>
          <MethodRow k="Horizontal — Economic">Redistributive on the left, laissez-faire on the right.</MethodRow>
          <MethodRow k="Vertical — Cultural">Progressive at the bottom, traditional at the top.</MethodRow>
        </div>
      </div>

      <H2>The two measures</H2>
      <Prose>
        Polarization isn't one number. We track two, side by side, because they tell different stories:
      </Prose>
      <div style={{ marginTop: 18 }}>
        <MethodRow k="Party separation"><strong style={{ color: CC.ink }}>Positional.</strong> How far apart the two party centroids sit on the compass. Are they far apart?</MethodRow>
        <MethodRow k="Affective polarization"><strong style={{ color: CC.ink }}>Emotional.</strong> Mean warmth toward the out-party. Do they dislike each other? This is the one that fell off a cliff.</MethodRow>
      </div>

      <H2>How much of this is the model — the honesty budget</H2>
      <Prose>
        A fair question for any simulation: how much of the 1980→2025 arc is the model genuinely producing, versus
        numbers we drew by hand? We measure it, rather than assert it. For each metric we re-run the 45 years with every
        external driver frozen at its 1980 value, then switch only the real data series back on. What survives the full
        freeze is <strong style={{ color: CC.ink }}>emergent</strong> — the agents' own dynamics. What the data adds back
        is <strong style={{ color: CC.ink }}>empirical input</strong> — the model tracking real ANES survey trajectories.
        The remainder is <strong style={{ color: CC.ink }}>hand-drawn</strong>: a few scripted bumps and the dated-event
        handlers. We keep that last slice small on purpose.
      </Prose>
      <div style={{ marginTop: 24 }}>
        <BudgetLegend />
        {BUDGET.map((row) => <BudgetBar key={row.k} row={row} />)}
      </div>
      <Prose>
        The split is revealing, and we'd rather show it than bury it. <strong style={{ color: CC.ink }}>Party
        separation</strong> and <strong style={{ color: CC.ink }}>identity alignment</strong> are carried almost entirely
        by the empirical party-position data — the model tracks where ANES says the parties went, it does not invent the
        sorting. The <strong style={{ color: CC.ink }}>emotional</strong> arc is the exception: 87% of the collapse in
        out-party warmth is emergent, produced by the animus dynamics themselves. Across all three, the hand-drawn residual
        runs between 0% and 15% — comfortably inside the budget we committed to before measuring.
      </Prose>

      <H2>Does it hold up out of sample — the holdout</H2>
      <Prose>
        A fit that only reproduces what it was shown proves nothing. So the calibration was checked four ways, against
        data deliberately held out before fitting — with the pass/fail bands written down first, so the test couldn't be
        moved to fit the result.
      </Prose>
      <HoldoutScorecard />
      <Prose>
        All three substantive cuts pass. The instrument cut is the strongest: the model, calibrated only on ANES, lands
        the trend in a <em>different</em> survey (the GSS) it never saw — survey-to-survey validation, not a circle drawn
        around its own output.
      </Prose>

      <H2>Interventions — what's real, what isn't</H2>
      <Prose>
        The interventions are split into two clearly-marked tiers. The line between them is the most important thing on
        that screen.
      </Prose>
      <div style={{ marginTop: 18 }}>
        <MethodRow k="Realistic">
          Calibrated to published field experiments — Bail (2018) on cross-party exposure, Allcott et&nbsp;al. (2020) on
          quitting social media, Levy (2021) on news diets. The honest finding: most barely move the needle, and some
          backfire. One intervention, the perception-gap correction, is a <em>live counterfactual run</em> of the full
          engine rather than an illustrative estimate.
        </MethodRow>
        <MethodRow k="Beyond realism">
          Mechanism-driven but hypothetical — each maps to a real engine cause (mega-identity, elite extremism,
          open-mindedness, contact &amp; mixing, within-party diversity) cranked far past anything we'd calibrate. Useful
          for seeing how the system <em>can</em> respond; not a claim about how it <em>would</em>.
        </MethodRow>
      </div>

      <H2>Limits</H2>
      <Prose>
        A simulation calibrated to a handful of experiments is a tool for intuition, not prediction. Agent positions are
        synthetic; the four named characters are illustrative composites; the "beyond realism" effects are deliberately
        un-calibrated. Read the modeled effects as <em>directional</em> — which way a lever pushes, and roughly how hard —
        not as forecasts.
      </Prose>
    </PageShell>
  );
}

Object.assign(window, { AboutPage, MethodsPage });
