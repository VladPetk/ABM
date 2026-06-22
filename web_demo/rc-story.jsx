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
    tick: 0, title: 'The same engine, now with the history switched on.', short: 'Setup', layer: 'position', orient: true,
    lead: 'Nothing about the forces changes here — only what’s driving them.',
    body: 'These are the same forces you watched stall short a moment ago, already tuned to the United States: their strengths were fit to decades of ANES survey data — where Americans actually stood, and how cold they’d grown toward the other side. What the prologue switched off, and this switches back on, is the history: the real drivers fed in on top of the mechanism — the spread of partisan media across the period, and the dated events that shaped it, from Fox News to the Tea Party to 2016 to COVID and January 6th. That’s what carries the engine the rest of the way, onto the actual 1980→2025 arc. From here you’re watching a reconstruction of the United States, and we’ll stop at the moments that moved it.',
  },
  {
    tick: 42, title: 'The leaders break first', short: 'Elite drift', layer: 'position',
    lead: 'The split begins at the top — the politicians before the public.',
    body: (<>For more than a decade after 1980, the parties hardly move. Then the elites start to pull apart, the sharpest turn coming with Newt Gingrich’s 1994 takeover. And the Republican side moved right faster than the Democrats moved left. Among everything in this story, the <em>direction</em> and <em>timing</em> of this elite drift carry the strongest evidence as a real cause of accelerated polarization. Note that the voters don’t so much radicalize as <strong>sort</strong>: they don’t necessarily move more toward the edges of the compass, rather they cluster more around their parties.</>),
    metric: (t) => `party separation at ${_sepAt(t).toFixed(2)} — elites lead`,
    data: { label: 'Party separation', valueAt: _sepAt, fmt: (v) => v.toFixed(2), note: 'elites lead', color: 'd' },
  },
  {
    tick: 48, title: 'Media that says yes', short: 'Cable', layer: 'position',
    lead: 'By the mid-’90s, you can build a whole news diet that never disagrees with you.',
    body: (<>In 1996 Fox News, one of the first clearly partisan channels, launches. Of all the types of media in this story, partisan cable carries the strongest causal evidence. Studies show it exerts a real pull on the viewers. But note <em>how</em> it works: rather than tugging in a new direction, it amplifies the tendencies of a public that is already sorting itself. Through the 2000s the sorting carries on steadily, with party, ideology, religion and region all slowly stacking into a single identity (which researchers inventively dubbed the <em>mega-identity</em>).</>),
    metric: (t) => `out-party warmth still near ${warmthDegAt(t)}°`,
    data: { label: 'Out-party warmth', valueAt: (t) => warmthDegAt(t), fmt: (v) => `${Math.round(v)}°`, note: 'still warm' },
  },
  {
    tick: 84, title: 'The feed everyone blames', short: 'The feed', layer: 'position',
    lead: 'With great reach comes great responsibility. Some think.',
    body: 'Blaming social media for societal ill is as old as social media itself. But what does the data actually say? Affective polarization rose fastest among the oldest, least-online Americans. Quite the opposite of what a social-media story would predict. To top that off, big experimental studies find no significant results. Could the feed still matter in ways those studies don’t catch? Perhaps. But here, as in the evidence, it looks like a weak and contested accelerant at most, and nowhere near the cause.',
    metric: (t) => `party separation at ${_sepAt(t).toFixed(2)} — contested driver`,
    data: { label: 'Party separation', valueAt: _sepAt, fmt: (v) => v.toFixed(2), note: 'contested', color: 'd' },
  },
  {
    tick: 90, title: 'Activists take the reins', short: 'Activists', layer: 'position',
    lead: 'It’s the activists that drag each party toward its edge.',
    body: 'Primary challenges from an increasingly organized, ideological base pull the parties outward. The mechanism runs like a ratchet: the most intense activists are the ones who decide who survives a primary, so officials end up answering to the edges, and the two parties keep drifting apart. The middle, all the while, keeps thinning out.',
    metric: (t) => `party separation at ${_sepAt(t).toFixed(2)} — edges harden`,
    data: { label: 'Party separation', valueAt: _sepAt, fmt: (v) => v.toFixed(2), note: 'edges harden', color: 'd' },
  },
  {
    tick: 108, title: 'It stops being about policy', short: 'Animus', layer: 'position',
    lead: 'Dislike, more than distance, moves to the front.',
    body: 'Americans really did pull apart on the issues. But that’s only half the picture. Over the same stretch they came to dislike the other side more — arguably more than the drift itself warrants — and by now those feelings matter at least as much as the issues do. What lit the 2016 fuse is genuinely contested: some read it as a status threat, with high-status groups feeling displaced, while others argue the economics counted for at least as much. That argument isn’t settled. The drift, and the dislike, are.',
    metric: (t) => `out-party warmth down to ${warmthDegAt(t)}° — coldest yet`,
    data: { label: 'Out-party warmth', valueAt: (t) => warmthDegAt(t), fmt: (v) => `${Math.round(v)}°`, note: 'coldest yet' },
  },
  {
    tick: 120, title: 'Two Americas', short: 'Two Americas', layer: 'position',
    lead: 'By the pandemic, the two camps hardly touch on the map anymore.',
    body: 'COVID and January 6th finish the sort, with the electorate now cleanly split into two separate masses. Out-party warmth has dropped from the high-50s to the low-30s, down by more than a third. Forty years before, this was a single warm(ish) crowd; by 2020 the middle has been almost entirely hollowed out. Does it have to stay that way? That’s the open question — and it’s why the controls come next.',
    metric: (t) => `out-party warmth near its floor, ~33° by 2025`,
    data: { label: 'Out-party warmth', valueAt: (t) => warmthDegAt(t), fmt: (v) => `${Math.round(v)}°`, note: 'two camps' },
  },
];

window.STORY_BEATS = STORY_BEATS;
