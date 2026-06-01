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
  return <p style={{ fontSize: DS.type.body, lineHeight: 1.68, color: CC.ink2, margin: '20px 0 0', maxWidth: '42em', textWrap: 'pretty' }}>{children}</p>;
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
          Mechanism-driven but hypothetical — each maps to a real engine knob (elite extremity, open-mindedness, media
          power) cranked far past anything we'd calibrate. Useful for seeing how the system <em>can</em> respond; not a
          claim about how it <em>would</em>.
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
