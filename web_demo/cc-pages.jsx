// Calm to Camps — static content pages: About + Methods.
// Content is grounded in the real model (250-agent sim, 1980–2025, the
// compass axes, the calibration sources) — no invented numbers. The Methods page
// is "under the hood", structured loosely on the ODD protocol for agent-based
// models (Grimm et al. 2020): overview → entities/state → design concepts →
// details (initialization, input data, submodels), diluted to plain language,
// with a sticky section nav. Sparklines read live from D.runs.baseline.

function PageShell({ eyebrow, title, lead, children }) {
  const isMobile = useIsMobile();
  return (
    <div style={{ flex: 1, minHeight: 0, overflow: 'auto', background: CC.bg }}>
      <div style={{ maxWidth: 760, margin: '0 auto', padding: isMobile ? '40px 20px 96px' : '72px 40px 120px' }}>
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
      eyebrow="About"
      title="The Divide"
      lead="How politics pulled apart: drifting away on the issues, and disliking the other side more than the drift calls for.">
      <Prose>
        <strong style={{ color: CC.ink, fontWeight: 600 }}>The Divide</strong> is an interactive model of political
        polarization — how a public splits into hostile camps. It's a simulation built primarily as an educational tool:
        you can learn about both how polarization (and its simulation) work in general and about American political
        polarization specifically. The story in this demo follows a simulated public — 250 people — as they drift across
        a political compass, pausing at moments to explain a force or note a salient event. The aim is to make a slow,
        abstract process visible and intuitive, both by showing and by letting you pull the levers yourself.
      </Prose>

      <H2>What this is (and isn't)</H2>
      <Prose>
        This isn't an argument with a thesis. It's a model. A handful of forces (albeit carefully constructed), run
        together, produce something that looks like the polarization a country lived through. It won't tell you who's
        right, or where the real harm lies. It just moves dots on a map, trying to stay honest about how it does that.
      </Prose>

      <H2>Who this is for</H2>
      <Prose>
        This demo is for anyone really — curious non-specialists, academics looking for inspiration, people who just
        wandered in and stayed for the slick design. It's for anyone who wants to understand the forces behind
        polarization, see them in action and contextualize them — someone who wants to understand but doesn't quite feel
        like perusing a literature review. And, not least, it is for myself, which brings us to…
      </Prose>

      <H2>What's the point</H2>
      <Prose>
        I built this project for a couple of reasons. Firstly, I was always fond (if intermittently) of studying politics
        computationally. Once upon a time, when I was flirting with doing a PhD, I considered an ABM study to examine
        real-time links between polarization and media consumption. So I suppose it's both satisfying an old intellectual
        itch and just reminiscing on the younger days. Secondly, I do like to dabble in design a bit, and this was no lame
        excuse. I got to play with layouts, colors (or absence thereof), fonts, flows, and so on. A creative itch, this
        time. Thirdly, it's always great to teach people something. I may not miss my short stint in academia, but I do
        fondly remember the times when I managed to explain something challenging to a student — it felt rewarding every
        time without fail. And I hope that this demo, too, will succeed in teaching someone at least something. So in a
        word: it's fun, and might even be useful.
      </Prose>

      <H2>A disclaimer</H2>
      <Prose>
        To close, a word of honesty. This is a model, not a measurement. The realistic interventions are calibrated to
        published field experiments; the "beyond realism" ones are thought experiments driven by the mechanism, turned up
        past anything I'd ever calibrate. The aim was never to predict. It's to build some intuition for which kinds of
        levers actually move a polarized system, and which ones don't. The <a style={{ color: CC.d, textDecoration: 'none', borderBottom: `1px solid ${CC.dSoft}` }} href="#methods" data-goto="methods">Methods</a> page sets out exactly what's under the hood.
      </Prose>
    </PageShell>
  );
}

// ── small shared rows ────────────────────────────────────────────────────────
function MethodRow({ k, children }) {
  const isMobile = useIsMobile();
  return (
    <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', gap: isMobile ? 5 : 18, padding: '16px 0', borderBottom: `1px solid ${CC.border}`, alignItems: isMobile ? 'stretch' : 'baseline' }}>
      <div style={{ width: isMobile ? 'auto' : 132, flexShrink: 0, fontFamily: SANS, fontSize: DS.type.small, fontWeight: 600, color: CC.ink }}>{k}</div>
      <div style={{ flex: 1, fontSize: DS.type.body, lineHeight: 1.6, color: CC.ink2, textWrap: 'pretty' }}>{children}</div>
    </div>
  );
}

// ── live sparkline of a baseline macro series, 1980→2025 ─────────────────────
// Reads D.runs.baseline.macro directly (no invented numbers). `deg` maps the
// out-party affect series to thermometer degrees, matching warmthDegAt:
// (1 + aff) * 50 + 12 — so the affect spark reads 57° → 33° like the rest of the site.
function MSpark({ title, metricKey, deg = false, color = CC.ink }) {
  const width = 320, height = 80;
  const padL = 6, padR = 8, padT = 24, padB = 16;
  const plotW = width - padL - padR, plotH = height - padT - padB;
  const m = D.runs.baseline.macro;
  const xf = deg ? (v) => (1 + v) * 50 + 12 : (v) => v;
  const ys = m.map((x) => xf(x[metricKey]));
  let lo = Infinity, hi = -Infinity;
  for (const v of ys) { if (v < lo) lo = v; if (v > hi) hi = v; }
  const padv = (hi - lo) * 0.14 || 0.05; lo -= padv; hi += padv;
  const N = ys.length - 1;
  const X = (t) => padL + (t / N) * plotW;
  const Y = (v) => padT + plotH - ((v - lo) / (hi - lo || 1)) * plotH;
  const path = ys.map((v, t) => `${t ? 'L' : 'M'}${X(t).toFixed(1)},${Y(v).toFixed(1)}`).join(' ');
  const fmt = (v) => deg ? `${Math.round(v)}°` : v.toFixed(2);
  return (
    <div style={{ flex: 1, minWidth: 230 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 10 }}>
        <span style={{ fontFamily: SANS, fontSize: DS.type.small, fontWeight: 600, color: CC.ink }}>{title}</span>
        <span style={{ fontFamily: MONO, fontSize: DS.type.micro, color: CC.ink3, ...TNUM }}>{fmt(ys[0])} → {fmt(ys[N])}</span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={height} preserveAspectRatio="xMidYMid meet" style={{ display: 'block', marginTop: 4 }}>
        <path d={path} fill="none" stroke={color} strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round" />
        <circle cx={X(N)} cy={Y(ys[N])} r="3.5" fill={color} stroke="#fff" strokeWidth="1.4" />
        <text x={padL} y={height - 3} style={{ fontFamily: SANS, fontSize: 9, fill: CC.ink4 }}>1980</text>
        <text x={width - padR} y={height - 3} textAnchor="end" style={{ fontFamily: SANS, fontSize: 9, fill: CC.ink4 }}>2025</text>
      </svg>
    </div>
  );
}

// ── provenance tag chips (L/N/E) ─────────────────────────────────────────────
const FTAG = {
  L: { label: 'L · literature', c: '#3f7d54' },
  N: { label: 'N · design', c: CC.ink3 },
  E: { label: 'E · extrapolated', c: '#c47a2c' },
};
function TagChip({ tag, label }) {
  const t = FTAG[tag] || { label: label || tag, c: CC.ink3 };
  return <span style={{ fontFamily: MONO, fontSize: 9.5, fontWeight: 600, letterSpacing: '.03em', color: t.c, border: `1px solid ${t.c}`, borderRadius: 4, padding: '1px 6px', whiteSpace: 'nowrap' }}>{label || t.label}</span>;
}

// ── the forces (the lever-y submodels, mapped to engine rules) ───────────────
const FORCES_M = [
  { name: 'Bounded confidence', rule: 'BoundedConfidenceInfluence', tag: 'L',
    what: 'People drift toward the average of the neighbors close enough to still take seriously — inside a confidence radius. Anyone too far away is tuned out.',
    how: 'Each tick an agent moves a fraction of the way toward the mean position of its network neighbors within radius r, weighted by a graded logistic (not a hard cutoff). Influence travels along ties, not raw distance. Left alone it builds agreement, not camps — classic Hegselmann–Krause is the complete-graph special case.',
    cite: 'Hegselmann & Krause 2002; Deffuant et al. 2000' },
  { name: 'Backfire', rule: 'BacklashRepulsion', tag: 'L',
    what: 'The same contact can shove people apart once they have already turned cold on the other side.',
    how: 'Every cross-party encounter is gated on warmth: stay above a threshold and contact is benign; drop below it and the same brush pushes the agent away instead of together. Affect-gated, so it only fires where animus is already high.',
    cite: 'Bail et al. 2018 (contested — did not replicate in Guess & Coppock 2020)' },
  { name: 'Homophily', rule: 'TieRewiring', tag: 'L',
    what: 'Your social circle slowly closes around your own side.',
    how: 'Each tick a few ties rewire: a cross-party link that chafes is dropped and a same-side one added, biased by similarity. Involuntary ties — work, family, the block you live on — never break, so a thin layer of cross-cutting links always survives.',
    cite: 'McPherson, Smith-Lovin & Cook 2001' },
  { name: 'Party pull', rule: 'PartyPull', tag: 'L',
    what: 'Each side feels a steady tug toward its own pole — an elite cue from above.',
    how: 'Partisans drift a small step toward their party’s centroid each tick; Independents feel none. The party positions are not fed in — they emerge from the activist→elite→mass loop (below), so this pull chases a target the engine itself produces.',
    cite: 'Levendusky 2009 (elite cues / partisan sorting)' },
  { name: 'Partisan media', rule: 'MediaConsumption', tag: 'L', forcing: true,
    what: 'A few heavy consumers tune into their own side and get hauled toward the edges.',
    how: 'Agents drift toward the positions of the outlets in their media diet (selective exposure), scaled by how heavily they consume. The mechanism is universal; the US media-penetration curve that switches it on over time is a country-specific forcing, not emergent.',
    cite: 'Levendusky 2013; Martin & Yurukoglu 2017; Allcott et al. 2020' },
  { name: 'Affect — the result', rule: 'AffectiveUpdate', tag: 'L',
    what: 'Not a push, but the feeling the other forces breed — and the second axis polarization is measured on.',
    how: 'Out-party warmth updates each tick from contact (the more of the other side around you, the faster you sour) with a negativity bias. No position moves. Unlike issue stances it has no anchor pulling it back, so it self-amplifies.',
    cite: 'Iyengar, Sood & Lelkes 2012; Iyengar et al. 2019' },
];

function ForceCard({ f }) {
  return (
    <div style={{ padding: '17px 0', borderBottom: `1px solid ${CC.border}` }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 9, flexWrap: 'wrap' }}>
        <span style={{ fontFamily: SANS, fontSize: DS.type.body, fontWeight: 600, color: CC.ink }}>{f.name}</span>
        <TagChip tag={f.tag} />
        {f.forcing && <TagChip label="+ forcing" />}
        <span style={{ fontFamily: MONO, fontSize: DS.type.micro, color: CC.ink4 }}>{f.rule}</span>
      </div>
      <p style={{ margin: '8px 0 0', fontSize: DS.type.body, lineHeight: 1.6, color: CC.ink2, maxWidth: '42em' }}>{f.what}</p>
      <p style={{ margin: '7px 0 0', fontSize: DS.type.small, lineHeight: 1.62, color: CC.ink3, maxWidth: '42em' }}>
        <strong style={{ color: CC.ink2, fontWeight: 600 }}>How it’s computed. </strong>{f.how}
      </p>
      <div style={{ margin: '9px 0 0', display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 12, flexWrap: 'wrap' }}>
        <span style={{ fontSize: DS.type.micro, color: CC.ink4, fontStyle: 'italic' }}>{f.cite}</span>
        <a style={{ color: CC.d, textDecoration: 'none', borderBottom: `1px solid ${CC.dSoft}`, fontFamily: SANS, fontSize: DS.type.micro, whiteSpace: 'nowrap', cursor: 'pointer' }} href="#forces" data-goto="forces">watch it move →</a>
      </div>
    </div>
  );
}

// ── the rest of the machinery (submodels the tour doesn't surface) ───────────
const MACHINERY = [
  { name: 'Activist → elite → mass loop', tag: 'N', rule: 'activist_elite',
    body: 'The endogenous source of party sorting. A party’s activists pull its elite outward, the elite cue pulls the rank-and-file, and the party’s own sorting feeds its next round of mobilization — a spiral. This is why the party positions emerge instead of being read in from data.' },
  { name: '7-issue substrate + emergent constraint', tag: 'N', rule: 'ConstraintOp',
    body: 'Under the hood each agent holds seven correlated issue positions, not two. How tightly those issues bundle into a single left–right axis (“constraint”) emerges from influence rather than being imposed; the 2-axis compass you see is a readout of that richer state.' },
  { name: 'Identity alignment', tag: 'L', rule: 'identity_alignment',
    body: 'Party, religion and region stacking into one mega-identity (after Mason 2018). It is measured, and it co-rises with animus — a consequence of sorting, not an independent cause of it.' },
  { name: 'Cohort replacement', tag: 'L', rule: 'cohort_replacement',
    body: 'Generational turnover: each tick a sliver of the oldest agents is retired and replaced by younger ones drawn from the current climate, so the population slowly refreshes over the 45 years.' },
  { name: 'Threat dynamics', tag: 'E', rule: 'threat_dynamics',
    body: 'Status-threat episodes amplify out-party animus for the threatened subset — the channel behind the 2016 affect spike (Mutz 2018; contested, so graded E).' },
  { name: 'Friedkin–Johnsen anchoring', tag: 'N', rule: 'FJ anchor + stubbornness',
    body: 'Every ideology-moving step is damped by (1 − stubbornness), and each agent feels a small pull back toward its fixed starting anchor. A stubborn majority barely moves; it keeps the system from collapsing to a single point.' },
  { name: 'Gaussian noise', tag: 'N', rule: 'GaussianNoise',
    body: 'Small per-tick random jitter on positions — keeps the dynamics from being knife-edge deterministic.' },
  { name: 'Dated shocks', tag: 'L', rule: 'shocks', label: 'forcing',
    body: 'The historical events, fed in as graded handlers: Fairness-Doctrine repeal (’87), Fox News (’96), the Tea Party (’09), 2016, COVID / Jan 6 (’20). Each carries an evidence grade (HIGH → MARKER); Citizens United, for instance, is a non-causal marker, not a cause.' },
];

function MachRow({ m }) {
  return (
    <div style={{ padding: '13px 0', borderBottom: `1px solid ${CC.border}` }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 9, flexWrap: 'wrap' }}>
        <span style={{ fontFamily: SANS, fontSize: DS.type.small, fontWeight: 600, color: CC.ink }}>{m.name}</span>
        {m.label ? <TagChip label={'+ ' + m.label} /> : <TagChip tag={m.tag} />}
        <span style={{ fontFamily: MONO, fontSize: DS.type.micro, color: CC.ink4 }}>{m.rule}</span>
      </div>
      <p style={{ margin: '5px 0 0', fontSize: DS.type.small, lineHeight: 1.58, color: CC.ink3, maxWidth: '42em' }}>{m.body}</p>
    </div>
  );
}

// ── honesty budget ───────────────────────────────────────────────────────────
// Measured fractions blessed in docs/results/honesty_budget.json (R-phase
// canonical, 6 seeds; methods §5.32). free_flowing = mechanism with every external
// forcing stripped out; empirical_input = how much the ANES-calibrated forcing
// (timing/intensity, NOT fed positions — that channel is ~0) moves the result.
const BUDGET_C = { emergent: '#3f7d54', empirical: CC.d };
const BUDGET = [
  { k: 'Party separation', emergent: 34, empirical: 66,
    note: 'Freeze the activist→elite→mass loop and the sorting collapses to its 1980 seed — so it’s the loop, not fed positions, that produces the sorting (earlier versions replayed the ANES centroids outright). But left to itself the loop only makes ~34% of the rise; the other ~66% is the loop amplified by an ANES-calibrated mobilization schedule. Calibrated forcing, not fed answers — but real empirical input.' },
  { k: 'Affective polarization', emergent: 83, empirical: 17,
    note: 'Mostly the engine’s own animus dynamics (83%); empirical input — dated media/events — adjusts only ~17%. Independent of the positional loop.' },
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

// ── compact sources list ─────────────────────────────────────────────────────
const SOURCES = [
  ['Data', 'ANES Time Series Cumulative File, 1986–2024 (the 2-D compass) · Iyengar, Lelkes, Levendusky, Malhotra & Westwood 2019 (the out-party thermometer trend)'],
  ['Mechanisms', 'Hegselmann & Krause 2002; Deffuant et al. 2000 (bounded confidence) · Bail et al. 2018; Guess & Coppock 2020 (backfire, contested) · McPherson, Smith-Lovin & Cook 2001 (homophily) · Friedkin & Johnsen 1990 (anchoring) · Iyengar, Sood & Lelkes 2012 (affect) · Mason 2018 (identity)'],
  ['Forcings & events', 'Levendusky 2009/2013; Martin & Yurukoglu 2017; Allcott et al. 2020 (media) · McCarty, Poole & Rosenthal 2006 (elite divergence) · Mutz 2018 (status threat) · Pettigrew & Tropp 2006 (contact)'],
  ['Method', 'Grimm et al. 2020, the ODD protocol for describing agent-based models'],
];

// ── Methods page: ODD-structured, sticky section nav + scroll-spy ─────────────
const METHODS_SECTIONS = [
  { id: 'overview', label: 'Overview' },
  { id: 'agents', label: 'The agents' },
  { id: 'compass', label: 'The compass, from ANES' },
  { id: 'clock', label: 'The clock' },
  { id: 'measure', label: 'What we measure' },
  { id: 'forces', label: 'The forces' },
  { id: 'machinery', label: 'The rest of the machinery' },
  { id: 'forcing', label: 'Force vs forcing' },
  { id: 'seeing', label: 'What you’re seeing' },
  { id: 'runs', label: 'Stochasticity & runs' },
  { id: 'budget', label: 'Engine vs history' },
  { id: 'interventions', label: 'Interventions' },
  { id: 'limits', label: 'Limits & scope' },
  { id: 'sources', label: 'Sources' },
];

function MSection({ id, title, first, children }) {
  return (
    <section id={'m-' + id} style={{ scrollMarginTop: 20, marginTop: first ? 36 : 50, paddingTop: first ? 0 : 26, borderTop: first ? 'none' : `1px solid ${CC.border}` }}>
      <h2 style={{ fontFamily: SERIF, fontWeight: 600, fontSize: DS.type.title, letterSpacing: '-.015em', margin: 0 }}>{title}</h2>
      {children}
    </section>
  );
}

function MethodsTOC({ active, onGo }) {
  return (
    <nav style={{ position: 'sticky', top: 20, flexShrink: 0, width: 188, alignSelf: 'flex-start', display: 'flex', flexDirection: 'column', gap: 1 }}>
      <div style={{ fontFamily: MONO, fontSize: 10, letterSpacing: '.08em', textTransform: 'uppercase', color: CC.ink4, margin: '2px 0 10px 11px' }}>On this page</div>
      {METHODS_SECTIONS.map((s) => {
        const on = active === s.id;
        return (
          <button key={s.id} onClick={() => onGo(s.id)} style={{
            textAlign: 'left', background: 'none', border: 'none', cursor: 'pointer',
            padding: '5px 0 5px 11px', borderLeft: `2px solid ${on ? CC.ink : CC.border}`,
            fontFamily: SANS, fontSize: DS.type.small, fontWeight: on ? 600 : 400, color: on ? CC.ink : CC.ink3,
            transition: 'color .15s, border-color .15s',
          }}>{s.label}</button>
        );
      })}
    </nav>
  );
}

function MethodsPage() {
  const scrollRef = React.useRef(null);
  const [active, setActive] = React.useState('overview');
  const isMobile = useIsMobile();

  React.useEffect(() => {
    const root = scrollRef.current; if (!root) return;
    const obs = new IntersectionObserver((entries) => {
      const vis = entries.filter((e) => e.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
      if (vis[0]) setActive(vis[0].target.id.replace('m-', ''));
    }, { root, rootMargin: '0px 0px -68% 0px', threshold: 0 });
    METHODS_SECTIONS.forEach((s) => { const el = root.querySelector('#m-' + s.id); if (el) obs.observe(el); });
    return () => obs.disconnect();
  }, []);

  const go = (id) => {
    const root = scrollRef.current; const el = root && root.querySelector('#m-' + id);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const lnk = { color: CC.d, textDecoration: 'none', borderBottom: `1px solid ${CC.dSoft}`, cursor: 'pointer' };
  const ink = (t) => <strong style={{ color: CC.ink, fontWeight: 600 }}>{t}</strong>;

  return (
    <div ref={scrollRef} style={{ flex: 1, minHeight: 0, overflow: 'auto', background: CC.bg }}>
      <div style={{ maxWidth: 1000, margin: '0 auto', padding: isMobile ? '40px 20px 110px' : '60px 40px 140px', display: 'flex', gap: 46, alignItems: 'flex-start' }}>
        {!isMobile && <MethodsTOC active={active} onGo={go} />}

        <div style={{ flex: 1, minWidth: 0, maxWidth: 720 }}>
          <Eyebrow>Methods · under the hood</Eyebrow>
          <h1 style={{ fontFamily: SERIF, fontWeight: 600, fontSize: DS.type.display, lineHeight: 1.02, letterSpacing: '-.022em', margin: '16px 0 0' }}>What this actually is</h1>
          <p style={{ fontFamily: SERIF, fontStyle: 'italic', fontSize: 21, lineHeight: 1.45, color: CC.ink2, margin: '18px 0 0', maxWidth: '36em', textWrap: 'pretty' }}>
            A small society of simulated people, the forces that move them, the survey data that anchors them — and an honest account of how much of the result is the engine versus history.
          </p>

          <MSection id="overview" title="Overview" first>
            <Prose>
              The Divide is an <strong>agent-based model</strong> of US political polarization across a stylised
              1980→2025 window. It is a <strong>teaching artefact, not a forecast</strong>: every calibration choice is
              anchored to a published finding, and results are illustrative within that citation envelope.
            </Prose>
            <Prose>
              It is built and read as three separable layers, kept strictly apart. {ink('Mechanisms')} are universal,
              science-faithful rules (the forces) that would work in any country. {ink('Forcings')} are country-specific
              inputs — US events, media reach, mobilization timing — fed in only as something that perturbs a mechanism,
              never as the answer itself. {ink('Calibration')} is knob-tuning that scales the mechanisms to fit the US
              trajectory within the envelope. The honesty budget (below) reports, per metric, how much rides each layer.
            </Prose>
            <Prose>
              The description below loosely follows the <a style={lnk} href="https://www.jasss.org/23/2/7.html" target="_blank" rel="noopener noreferrer">ODD
              protocol</a> for documenting agent-based models — entities and state, then design concepts, then the details
              — diluted to plain language.
            </Prose>
          </MSection>

          <MSection id="agents" title="The agents">
            <Prose>
              The crowd is {ink('250 simulated agents')}. Each is <em>two things at once</em>: a point on a political
              compass, <em>and</em> a node in a weighted social network. The defining choice is that the network is the
              primary substrate of influence — a rule asks “who am I tied to,” not “who is near me on the map.” The
              compass holds and displays state; influence flows along the ties.
            </Prose>
            <Prose>Each agent carries:</Prose>
            <div style={{ marginTop: 6 }}>
              <MethodRow k="Issue position">Seven correlated issue stances, summarised onto the two compass axes (economic, cultural).</MethodRow>
              <MethodRow k="Party">Democrat, Republican, or Independent.</MethodRow>
              <MethodRow k="Identity">An identity-strength weight plus cross-cutting identities (race, religion, lifestyle).</MethodRow>
              <MethodRow k="Affect">Evolving warmth toward the out-party — the emotional axis.</MethodRow>
              <MethodRow k="Media diet">Weights over partisan outlets.</MethodRow>
              <MethodRow k="Anchor & stubbornness">A fixed starting position and a “how hard to move” weight (Friedkin–Johnsen). Most agents barely move; a thin tail drifts freely.</MethodRow>
            </div>
          </MSection>

          <MSection id="compass" title="The compass, from ANES">
            <Prose>
              The two axes aren’t invented — they’re built from the {ink('ANES Time Series Cumulative File, 1986–2024')},
              the long-running American National Election Studies survey. Seven items define the space:
              the <strong>economic</strong> axis from liberal–conservative self-placement, government jobs/income, and
              services-vs-spending; the <strong>cultural</strong> axis from abortion, aid to Black Americans, adjusting
              moral views, and traditional values.
            </Prose>
            <Prose>
              Each item is recoded so higher means more conservative, rescaled to [−1, 1] on its theoretical endpoints,
              then averaged into an axis score. Listwise-dropping anyone who skipped a core item takes 44,308 respondents
              down to 22,761. A <strong>kernel-density estimate</strong> (KDE, Scott’s-rule bandwidth) turns that cloud of
              respondents into the smooth density the demo draws — the same estimator used for the live field.
            </Prose>
            <Prose>
              The calibration target is the per-year {ink('overlap between the two parties’ densities')}: it falls from
              0.60 (1986) to 0.20 (2020) — the camps pulling apart, with a slight recovery to 0.25 by 2024. The engine’s
              own pointclouds are matched to the ANES ones, decade by decade, by Wasserstein (optimal-transport) distance.
              One honest caveat: the listwise drop biases toward the politically engaged, so read the densities as the
              population of <em>opinionated</em> voters, not the whole electorate.
            </Prose>
          </MSection>

          <MSection id="clock" title="The clock">
            <Prose>
              Time advances at {ink('three ticks per year')} (one tick ≈ four months); ticks 0…135 run 1980 → end 2025.
              The time axis is pinned to the ANES out-party feeling thermometer, which fell from ~48° (1978) to ~20°
              (2020) — that drop sets the scale of the affect axis. The timeline is <strong>schematic, not literal</strong>:
              it reproduces the shape and ordering of the era, not a month-by-month record.
            </Prose>
          </MSection>

          <MSection id="measure" title="What we measure">
            <Prose>
              Polarization isn’t one number. The engine reports two, side by side, because they tell different stories —
              one crept up, the other dropped sharply. (Both lines are read live from the shipped baseline.)
            </Prose>
            <div style={{ marginTop: 22, display: 'flex', gap: 30, flexWrap: 'wrap' }}>
              <MSpark title="Party separation — positional" metricKey="sep" color={CC.ink} />
              <MSpark title="Out-party warmth — emotional" metricKey="aff" deg color={CC.d} />
            </div>
            <div style={{ marginTop: 16 }}>
              <MethodRow k="Party separation">{ink('Positional.')} How far apart the two party centroids sit on the compass.</MethodRow>
              <MethodRow k="Affective polarization">{ink('Emotional.')} Mean warmth toward the out-party, in thermometer degrees.</MethodRow>
            </div>
          </MSection>

          <MSection id="forces" title="The forces">
            <Prose>
              A handful of mechanisms move the agents each tick. Every one is drawn from the polarization research and
              faithful in form to a published finding; the engine sums their effects and applies them together (each
              ideology-moving step damped by the agent’s stubbornness). Each is tagged for provenance —
              {' '}<TagChip tag="L" />{' '}literature-supported,{' '}<TagChip tag="N" />{' '}a design choice,{' '}<TagChip tag="E" />{' '}
              extrapolated beyond direct evidence — and you can watch any of them alone in
              {' '}<a style={lnk} href="#forces" data-goto="forces">the Forces tour</a>.
            </Prose>
            <div style={{ marginTop: 18 }}>
              {FORCES_M.map((f) => <ForceCard key={f.name} f={f} />)}
            </div>
          </MSection>

          <MSection id="machinery" title="The rest of the machinery">
            <Prose>
              Those are the forces you can isolate in the tour. The full engine layers on more, all running together —
              the parts that make the sorting <em>emerge</em> and the population <em>change</em> over 45 years:
            </Prose>
            <div style={{ marginTop: 16 }}>
              {MACHINERY.map((m) => <MachRow key={m.name} m={m} />)}
            </div>
          </MSection>

          <MSection id="forcing" title="Force vs forcing">
            <Prose>
              Two kinds of input, kept strictly apart. A {ink('force')} is a universal mechanism — it would work in any
              country. A {ink('forcing')} is a country-specific input, fed in only as something that <em>perturbs</em> a
              mechanism: the US media-penetration curve, the dated events, the timing of who mobilized when. A forcing
              never writes an outcome directly — it nudges a force, and the force produces the result. The whole-engine
              view (“the engine, on its own”) runs the forces with the forcings switched off — and it stalls well short
              of the real arc. That gap is what the forcings carry.
            </Prose>
          </MSection>

          <MSection id="seeing" title="What you’re seeing">
            <Prose>
              The map isn’t 250 dots by default — it’s a {ink('kernel-density field')} (the same KDE used for the ANES
              build), so you read where the mass <em>is</em>, not individual points. Navy is Democratic, oxblood
              Republican, gray where they overlap — the vanishing middle. The 3-D view is where the raw individual agents
              are shown, one dot each.
            </Prose>
            <Prose>
              The headline picture is a {ink('“scissors”')}: warmth toward your own side holds steady while warmth toward
              the other side collapses — two lines pulling apart. One honest flag: the flat in-party line in that chart is
              an <strong>external ANES reference, not an engine output</strong>, and is labelled as such wherever it
              appears.
            </Prose>
          </MSection>

          <MSection id="runs" title="Stochasticity & runs">
            <Prose>
              The engine is stochastic — random tie formation, the noise term, cohort draws — so no single run is
              definitive. The baseline you watch isn’t one lucky seed: it’s the model’s {ink('ensemble center')}. Eight
              independent seeds are pooled and a reproducible cross-seed subsample of 250 agents is drawn from them (we call
              it Method-B), validated to sit at the center of the seed-to-seed spread while preserving the model’s true
              within-party dispersion. The published figures — the honesty budget, the intervention buckets — are likewise
              multi-seed means (6 and 9 seeds).
            </Prose>
            <Prose>
              The one deliberate exception is the intervention deltas: each lever’s effect is differenced against a
              single seed’s own run, not the pooled baseline, so the measured buckets stay exactly as blessed rather than
              drifting against an averaged control. Runs are reproducible — the same seeds always produce the same result.
            </Prose>
          </MSection>

          <MSection id="budget" title="Engine vs history — the honesty budget">
            <Prose>
              How much of the 1980→2025 arc does the engine genuinely produce, versus numbers fed in? We measure this
              rather than assert it. Split each arc two ways: run the loop with every external forcing stripped out (the
              {' '}{ink('free-flowing')} mechanism — the engine’s own dynamics), then switch the ANES-calibrated forcing
              back on and measure how much it moves the result (the {ink('empirical input')}). Crucially that input is
              <em> timing and intensity</em>, never the party positions themselves — the old “feed the answer” channel is ~0.
            </Prose>
            <div style={{ marginTop: 24 }}>
              <BudgetLegend />
              {BUDGET.map((row) => <BudgetBar key={row.k} row={row} />)}
            </div>
            <Prose>
              The honest read: {ink('the engine supplies the mechanism, history supplies the timing.')} Left to itself the
              loop makes only about a third of the positional rise — but that isn’t a flaw to engineer away. Even a
              best-case re-sort of the actual 1980 electorate (freeze everyone’s issues, just re-label who’s a Democrat and
              who’s a Republican to pull the camps as far apart as that public allows) reaches separation ~0.66, while 2025
              is 1.11 — so roughly {ink('60% of the rise sits above anything you could reach by rearranging the 1980 world')},
              close to the ~66% the calibrated forcing carries. 1980 was genuinely calm, and closing that gap took 45 years
              of real change whose timing no model can author from initial conditions. The emotional arc is the exception —
              83% is the engine’s own animus dynamics, because warmth has no anchor pulling it back and self-amplifies.
            </Prose>
          </MSection>

          <MSection id="interventions" title="Interventions — real vs Sandbox">
            <Prose>
              The interventions split into two clearly-marked tiers. The line between them is the most important thing on
              that screen.
            </Prose>
            <div style={{ marginTop: 18 }}>
              <MethodRow k="Realistic">
                Calibrated to published field experiments — Bail (2018) on cross-party exposure, Allcott et&nbsp;al. (2020)
                on quitting social media. The honest finding: most barely move the needle, and one can backfire. All seven
                are <em>live counterfactual runs</em> of the full engine, not illustrative estimates.
              </MethodRow>
              <MethodRow k="Beyond realism — the Sandbox">
                Mechanism-driven but hypothetical — five dials, each mapping to a real engine cause (party leaders’
                extremism, identity stacking, shared daily life, within-party conformity, echo-chamber ties) cranked far
                past anything we'd calibrate. Useful for seeing how the system <em>can</em> respond; not a claim about how
                it <em>would</em>.
              </MethodRow>
            </div>
          </MSection>

          <MSection id="limits" title="Limits & scope">
            <Prose>
              A simulation calibrated to a handful of experiments is a tool for intuition, not prediction. It models a
              {' '}<strong>two-party, single-country</strong> system; agent positions are synthetic; the timing of the
              late-period sorting is calibrated to the period, not predicted from it; and the “beyond realism” effects are
              deliberately un-calibrated. Read the modeled effects as <em>directional</em> — which way a lever pushes, and
              roughly how hard — not as forecasts.
            </Prose>
          </MSection>

          <MSection id="sources" title="Sources">
            <Prose>
              The key anchors are below; full citations and the per-mechanism calibration live in the project’s
              <em> methods</em> and <em>literature</em> documentation.
            </Prose>
            <div style={{ marginTop: 14 }}>
              {SOURCES.map(([k, v]) => (
                <div key={k} style={{ display: 'flex', gap: 18, padding: '12px 0', borderBottom: `1px solid ${CC.border}`, alignItems: 'baseline' }}>
                  <div style={{ width: 132, flexShrink: 0, fontFamily: SANS, fontSize: DS.type.small, fontWeight: 600, color: CC.ink }}>{k}</div>
                  <div style={{ flex: 1, fontSize: DS.type.small, lineHeight: 1.6, color: CC.ink3 }}>{v}</div>
                </div>
              ))}
            </div>
          </MSection>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { AboutPage, MethodsPage });
