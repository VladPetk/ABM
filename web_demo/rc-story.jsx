// Story chapter data (STORY_BEATS) — the tick-anchored chapters of the U.S.
// story. This file is now DATA-ONLY: the chapters are rendered by WatchRail in
// cc-unified.jsx (and their markers reused on the 3-D page). The old standalone
// ConceptStory renderer was retired in the copy rewrite — it was mounted nowhere
// and had become a second, drifting source of the same chapter copy.
// Single society-level voice (named characters/personas were retired in v1).

const _sepAt = (t) => centroids(posAt(D.runs.baseline, t), D.runs.baseline.party[Math.round(t)]).gap;
const _alignAt = (t) => macroAt(D.runs.baseline, t, 'identity_alignment');
// Chapters re-anchored to the engine's evidence-graded mechanisms (Step 5):
// elite drift lives at Gingrich/1994 (HIGH), not Citizens United (now a
// non-causal MARKER); social media is the contested suspect (LOW); identity
// sorting (Mason) is named as the master mechanism; the affect pivot stays at
// 2016 (status threat, CONTESTED). Copy is truthful to
// docs/polarization_causal_model.md — no "social media caused it", no "CU drove
// it", and identity alignment is framed as co-rising with animus, not its cause.
// The story chapters are the EXTERNAL forces that drove the US ABOVE where the
// bare engine stalls (see the prologue). Each is graded to the literature
// (docs/polarization_causal_model.md): elite drift + cable are well-evidenced;
// the activist ratchet is a mechanism; 2016 status-threat and social-media-as-
// cause are CONTESTED and worded as such; there is no single cause. No
// orientation beat (the prologue covers it); mega-identity dropped (a co-rising
// consequence, ~0.36 emergent, not an independent driver); Citizens United
// dropped (best-identified studies: null).
const STORY_BEATS = [
  {
    tick: 42, title: 'The leaders break first', short: 'Elite drift', layer: 'position',
    lead: 'The split starts at the top — with the politicians, not the public.',
    body: 'For more than a decade after 1980 the parties barely move. Then the elites pull apart — Newt Gingrich’s 1994 takeover the sharpest inflection — and the Republican side moves right faster than Democrats move left. This asymmetric elite drift is the best-evidenced first cause. Note what it isn’t: voters don’t so much radicalize as sort — they keep their party and bring their positions into line behind its leaders. It’s the outward shove the engine, left to itself, never produced.',
    metric: (t) => `party separation at ${_sepAt(t).toFixed(2)} — elites lead`,
    data: { label: 'Party separation', valueAt: _sepAt, fmt: (v) => v.toFixed(2), note: 'elites lead', color: 'd' },
  },
  {
    tick: 48, title: 'A media you never leave', short: 'Cable', layer: 'position',
    lead: 'For the first time, you can build a news diet that never disagrees with you.',
    body: 'Talk radio is already loud, the Fairness Doctrine was repealed in 1987, and Fox News launches in 1996. Of all the media stories, partisan cable carries the strongest causal evidence — but it works as an amplifier on people already sorting, deepening the divide rather than starting it. Through the 2000s the sort grinds on quietly: party, ideology, religion and region slowly stack into the same identity.',
    metric: (t) => `out-party warmth still near ${warmthDegAt(t)}°`,
    data: { label: 'Out-party warmth', valueAt: (t) => warmthDegAt(t), fmt: (v) => `${Math.round(v)}°`, note: 'still warm' },
  },
  {
    tick: 84, title: 'The feed everyone blames', short: 'The feed', layer: 'position',
    lead: 'Social media reaches almost everyone — and gets the blame for everything after.',
    body: 'It’s the famous suspect the data won’t convict. Affective polarization rose fastest among the oldest, least-online Americans — the opposite of what a social-media story predicts — and the big deactivation experiments came back near zero. Here, as in the evidence, the feed is at most a weak, contested accelerant — not the cause.',
    metric: (t) => `party separation at ${_sepAt(t).toFixed(2)} — contested driver`,
    data: { label: 'Party separation', valueAt: _sepAt, fmt: (v) => v.toFixed(2), note: 'contested', color: 'd' },
  },
  {
    tick: 90, title: 'The base takes the wheel', short: 'The base', layer: 'position',
    lead: 'The activists, not the donors, drag each party toward its edge.',
    body: 'Primary challenges and a newly-organized base pull the parties outward — the Tea Party hardens the right first. It works as a ratchet: the most intense activists decide who survives a primary, so officials answer to the edges and the parties keep drifting apart. The middle keeps thinning.',
    metric: (t) => `party separation at ${_sepAt(t).toFixed(2)} — edges harden`,
    data: { label: 'Party separation', valueAt: _sepAt, fmt: (v) => v.toFixed(2), note: 'edges harden', color: 'd' },
  },
  {
    tick: 108, title: 'It stops being about policy', short: 'Animus', layer: 'position',
    lead: 'Dislike, not distance, takes over — and the middle stops feeling safe to stand in.',
    body: 'Americans still haven’t moved far apart on the issues — but now they dislike each other, and that matters more than the issues do. What lit the 2016 fuse is genuinely contested: Mutz reads it as status threat — high-status groups feeling displaced — while Morgan, re-analyzing the same data, finds economic interests mattered at least as much. Either way, the feeling curdles.',
    metric: (t) => `out-party warmth down to ${warmthDegAt(t)}° — coldest yet`,
    data: { label: 'Out-party warmth', valueAt: (t) => warmthDegAt(t), fmt: (v) => `${Math.round(v)}°`, note: 'coldest yet' },
  },
  {
    tick: 120, title: 'Two Americas', short: 'Two Americas', layer: 'position',
    lead: 'By the pandemic, the two camps no longer share a map — or a set of facts.',
    body: 'COVID and January 6th harden the sort into two separate masses. Out-party warmth has fallen from the high-50s to the low-30s — down by more than a third. Forty years earlier they were one crowd; now they can barely speak.',
    metric: (t) => `out-party warmth bottoms near ${warmthDegAt(t)}°`,
    data: { label: 'Out-party warmth', valueAt: (t) => warmthDegAt(t), fmt: (v) => `${Math.round(v)}°`, note: 'two camps' },
  },
];

window.STORY_BEATS = STORY_BEATS;
