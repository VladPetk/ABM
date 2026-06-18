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
// Measured fractions are blessed in docs/results/honesty_budget.json (R-phase
// canonical config, 6 seeds; methods §5.32; scripts/audit/t35_budget_brake.py).
// Two honest slices of each metric's 1980→2025 rise:
//   free_flowing    = the mechanism with every EMPIRICAL/external driver removed
//                     (mobilization frozen at 1980, no events, no media) — the loop's
//                     own dynamics from the 1980 seed.
//   empirical_input = (rise_with − rise_sans)/rise_with — how much the ANES-calibrated
//                     forcing (mobilization timing + dated events + media) ADJUSTS that
//                     free-flowing mechanism (= 1 − free_flowing). This is forcing /
//                     timing, NOT fed positions: the data-fed-POSITION channel is ~0
//                     (fed_positions in the JSON) — the model is told WHEN activists
//                     mobilized, not WHERE the parties ended up. We do NOT claim "0
//                     empirical input": the calibration genuinely moves the result.
// Widths are honest roundings of the blessed fractions (rise-based).
const BUDGET_C = { emergent: '#3f7d54', empirical: CC.d };
const BUDGET = [
  { k: 'Party separation', emergent: 34, empirical: 66,
    note: 'The model supplies the mechanism, the data supplies the timing. Freeze the activist→elite→mass loop and the sorting collapses to its 1980 seed — so it’s the loop, not fed positions, that produces the sorting (earlier versions replayed the ANES centroids outright). But left to itself the loop only makes ~34% of the rise; the other ~66% is the loop amplified by an ANES-calibrated mobilization schedule. Calibrated forcing, not fed answers — but real empirical input.' },
  { k: 'Affective polarization', emergent: 83, empirical: 17,
    note: 'Mostly the model’s own animus dynamics (83%); empirical input — dated media/events — adjusts only ~17%. Independent of the positional loop.' },
  { k: 'Identity alignment', emergent: 36, empirical: 64,
    note: 'Identity tracks the emergent party positions, so the loop carries it (was ~2% — it used to follow the same data-fed party series). Like separation, ~64% of the rise rides the empirically-calibrated forcing.' },
];

function BudgetBar({ row }) {
  const seg = (w, c, title) => w > 0
    ? <div title={title} style={{ width: `${w}%`, background: c, height: '100%' }} /> : null;
  return (
    <div style={{ padding: '16px 0', borderBottom: `1px solid ${CC.border}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 }}>
        <span style={{ fontFamily: SANS, fontSize: DS.type.small, fontWeight: 600, color: CC.ink }}>{row.k}</span>
        <span style={{ fontFamily: SANS, fontSize: DS.type.small, color: CC.ink3 }}>
          <strong style={{ color: CC.ink }}>{row.emergent}% free-flowing</strong>
          <span style={{ color: CC.ink4 }}> · {row.empirical}% empirical</span>
        </span>
      </div>
      <div style={{ display: 'flex', height: 10, borderRadius: DS.rad.pill, overflow: 'hidden', background: CC.bg2 }}>
        {seg(row.emergent, BUDGET_C.emergent, `${row.emergent}% free-flowing`)}
        {seg(row.empirical, BUDGET_C.empirical, `${row.empirical}% empirical input`)}
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
      {dot(BUDGET_C.emergent, 'Free-flowing — the loop’s own dynamics')}
      {dot(BUDGET_C.empirical, 'Empirical input — ANES-calibrated forcing (timing, not positions)')}
    </div>
  );
}

// four-cut holdout — transcribed from docs/results/e5_holdout.md (endogenous
// config; 1/3 substantive cuts pass; bands pre-registered before the fit).
// emergence-recovery E5.1. The FED config scored 3/3 — but it passed the
// temporal cut TRIVIALLY by feeding the party trajectory; with sorting now
// emergent, the cut is a real out-of-sample test the model does not pass.
const HOLDOUT = [
  { cut: 'Temporal', q: 'Fit on ≤2000 only, then predict 2010 / 2020 / 2025', v: 'FAIL',
    why: 'The late-2010s acceleration isn’t predictable from the early decades alone — it rides an exogenously-calibrated mobilization schedule. (The old data-fed version passed this only by replaying the answer.)' },
  { cut: 'Instrument', q: 'Shipped model vs a held-out survey (GSS) it was never fit to', v: 'FAIL',
    why: 'Partisan-sorting slope lands inside the GSS band, but the issue-to-issue correlation grows ~1.6× too fast (the compass axes over-align) — so the cut fails on balance.' },
  { cut: 'Statistic', q: 'Fit separation / affect / spread, then predict issue constraint', v: 'PASS',
    why: 'Issue constraint is predicted from the other three statistics across all six decades.' },
];

const HOLDOUT_C = { PASS: '#3f7d54', MIXED: '#c47a2c', FAIL: '#b04a3a' };

function HoldoutScorecard() {
  return (
    <div style={{ marginTop: 18, border: `1px solid ${CC.border}`, borderRadius: DS.rad.inset, overflow: 'hidden' }}>
      <div style={{ padding: '11px 16px', background: CC.bg, borderBottom: `1px solid ${CC.border}`,
        display: 'flex', alignItems: 'baseline', gap: 10 }}>
        <span style={{ fontFamily: SANS, fontSize: 11, fontWeight: 700, letterSpacing: '.06em', color: CC.ink }}>1 OF 3 CUTS PASS</span>
        <span style={{ fontSize: DS.type.micro, color: CC.ink3 }}>bands written down before the fit — a failed band is a finding, not a retune</span>
      </div>
      {HOLDOUT.map((h, i) => (
        <div key={h.cut} style={{ padding: '13px 16px',
          borderTop: i ? `1px solid ${CC.border}` : 'none', background: CC.surface }}>
          <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
            <span style={{ width: 86, flexShrink: 0, fontFamily: SANS, fontSize: DS.type.small, fontWeight: 600, color: CC.ink }}>{h.cut}</span>
            <span style={{ flex: 1, fontSize: DS.type.small, lineHeight: 1.5, color: CC.ink2 }}>{h.q}</span>
            <span style={{ flexShrink: 0, fontFamily: SANS, fontSize: 11, fontWeight: 700, letterSpacing: '.06em',
              color: HOLDOUT_C[h.v] }}>{h.v}</span>
          </div>
          <p style={{ margin: '6px 0 0 100px', fontSize: DS.type.micro, lineHeight: 1.5, color: CC.ink3, maxWidth: '38em' }}>{h.why}</p>
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
        numbers we fed in? We measure it, rather than assert it. The model does <em>not</em> feed in where the parties
        went — positional sorting <strong style={{ color: CC.ink }}>emerges</strong> from a feedback loop: each party’s
        activists pull its elite outward, the elite cue pulls the rank-and-file, and the cycle ratchets. We split each
        arc two ways. Run the loop with every external driver stripped out and you get the
        <strong style={{ color: CC.ink }}> free-flowing</strong> mechanism — the model’s own dynamics. Switch the real
        ANES-calibrated forcing back on (when activists mobilized, the dated shocks, media reach) and the gap it adds is
        the <strong style={{ color: CC.ink }}>empirical input</strong> — measured as how much that forcing moves the
        result. Crucially, that input is <em>timing and intensity</em>, never the party positions themselves (the
        old “feed the answer” channel is ~0).
      </Prose>
      <div style={{ marginTop: 24 }}>
        <BudgetLegend />
        {BUDGET.map((row) => <BudgetBar key={row.k} row={row} />)}
      </div>
      <Prose>
        So we won’t claim it’s “wholly emergent.” The honest read: <strong style={{ color: CC.ink }}>the model supplies
        the mechanism, the data supplies the timing.</strong> Freeze the loop and party separation collapses to its 1980
        seed — so the sorting is the loop’s doing, not fed positions (earlier versions replayed the ANES centroids
        outright; that channel is now ~0). But left entirely to itself the loop only makes about a third of the rise;
        the rest is the loop <em>amplified</em> by an ANES-calibrated mobilization schedule — so ~66% of separation and
        ~64% of identity alignment is empirical input. That’s calibrated forcing, not fed answers, but it’s real, and we’d
        rather show it than round it to zero. The <strong style={{ color: CC.ink }}>emotional</strong> arc is the
        exception: 83% is the model’s own animus dynamics, with empirical input adjusting only ~17%.
      </Prose>

      <H2>Why only a third? — the saturation ratchet</H2>
      <Prose>
        Is that ~34% a weakness we should engineer away? We checked, and the answer is no — it’s telling us something
        real. Ask the cleanest possible version of the question: take the actual 1980 electorate, freeze where everyone
        stands on the issues, and just <em>re-label</em> who’s a Democrat and who’s a Republican to pull the two camps as
        far apart as the 1980 public will allow. That best-case re-sorting reaches separation <strong style={{ color: CC.ink }}>0.66</strong>
        — but 2025 is <strong style={{ color: CC.ink }}>1.11</strong>. So roughly <strong style={{ color: CC.ink }}>60% of the
        rise sits above the ceiling of anything you can do by re-arranging the 1980 world</strong> — close to the
        ~66% the calibrated forcing carries. <strong style={{ color: CC.ink }}>1980 was genuinely calm:</strong> reaching the
        modern split required real, slow change — elites repositioning, a generation turning over — and the timing of that
        change is set by history, not by the starting conditions.
      </Prose>
      <Prose>
        Put plainly: <strong style={{ color: CC.ink }}>the model supplies the mechanism; history supplies the timing.</strong>
        About 34% of the 1980→2025 rise was already latent in the 1980 electorate and emerges from the loop on its own; the
        rest required 45 years of real change whose timing no model can author from initial conditions. (And the model’s own
        spontaneous loop already recovers most of that latent 0.66 — there’s no hidden reservoir of “missing” emergence to
        unlock.) The one channel that <em>does</em> run away on its own is the emotional one — animus has no anchor pulling it
        back, so it self-amplifies; issue positions are sticky and have to be moved. That 83%-vs-34% gap isn’t a bug; it’s the
        model faithfully reproducing how the two actually behaved.
      </Prose>

      <H2>Does it hold up out of sample — the holdout</H2>
      <Prose>
        A fit that only reproduces what it was shown proves nothing. So the calibration is checked against data
        deliberately held out before fitting — with the pass/fail bands written down first, so the test couldn't be
        moved to fit the result. Now that the sorting <em>emerges</em> rather than being replayed, this is a tougher,
        more honest test — and the model only partly passes it. We show the result straight.
      </Prose>
      <HoldoutScorecard />
      <Prose>
        The honest read: <strong style={{ color: CC.ink }}>the model explains the mechanism but not the timing.</strong>
        The statistic cut passes outright. But the temporal cut now <em>fails</em> — the late-2010s explosion in
        separation can’t be predicted from the early decades; it depends on an exogenous “when did activists mobilize”
        schedule that’s calibrated to the whole period. (The earlier data-fed version passed this cut only because it was
        handed the answer.) And the model sorts the two compass axes together a little faster than a held-out survey says
        it should. These are real limitations — the price of making the sorting genuinely emergent instead of replaying
        it — and we’d rather show them than hide behind a test the old version passed for the wrong reason.
      </Prose>

      <H2>Interventions — what's real, what isn't</H2>
      <Prose>
        The interventions are split into two clearly-marked tiers. The line between them is the most important thing on
        that screen.
      </Prose>
      <div style={{ marginTop: 18 }}>
        <MethodRow k="Realistic">
          Calibrated to published field experiments — Bail (2018) on cross-party exposure, Allcott et&nbsp;al. (2020) on
          quitting social media. The honest finding: most barely move the needle, and some backfire. All seven are
          <em>live counterfactual runs</em> of the full engine, not illustrative estimates.
        </MethodRow>
        <MethodRow k="Beyond realism — the Sandbox">
          Mechanism-driven but hypothetical — five dials, each mapping to a real engine cause (party leaders’ extremism,
          identity stacking, shared daily life, within-party conformity, and echo-chamber ties) cranked far past anything
          we'd calibrate. Useful for seeing how the system <em>can</em> respond; not a claim about how it <em>would</em>.
        </MethodRow>
      </div>

      <H2>Limits</H2>
      <Prose>
        A simulation calibrated to a handful of experiments is a tool for intuition, not prediction. Agent positions are
        synthetic; the "beyond realism" effects are deliberately un-calibrated. Read the modeled effects as
        <em>directional</em> — which way a lever pushes, and roughly how hard — not as forecasts.
      </Prose>
    </PageShell>
  );
}

Object.assign(window, { AboutPage, MethodsPage });
