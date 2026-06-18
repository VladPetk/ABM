// Concept 2 — Story dispatch in the polished simulation-page frame:
// header · dimmed field · wide dispatch rail · bottom chapter-timeline strip.
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
    body: 'COVID and January 6th harden the sort into two separate masses. Out-party warmth has fallen from the high-50s to the mid-30s — down by more than a third. Forty years earlier they were one crowd; now they can barely speak.',
    metric: (t) => `out-party warmth bottoms near ${warmthDegAt(t)}°`,
    data: { label: 'Out-party warmth', valueAt: (t) => warmthDegAt(t), fmt: (v) => `${Math.round(v)}°`, note: 'two camps' },
  },
];

function ConceptStory() {
  const [bi, setBi] = React.useState(0);
  const beat = STORY_BEATS[bi];
  const year = Math.floor(tickToYear(beat.tick));

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: CC.bg, minHeight: 0 }}>
      {/* header */}
      <div style={{ height: 54, flexShrink: 0, display: 'flex', alignItems: 'center', gap: 14, padding: '0 22px', borderBottom: `1px solid ${CC.border}`, background: CC.bg }}>
        <Eyebrow>Watch · the guided story</Eyebrow>
        <span style={{ fontSize: 13, color: CC.ink3 }}>auto-pauses at the moments that matter</span>
        <span style={{ flex: 1 }} />
        <span style={{ fontSize: 12.5, color: CC.ink2, display: 'inline-flex', alignItems: 'center', gap: 7, padding: '6px 13px', border: `1px solid ${CC.border}`, borderRadius: 999 }}>About this model <InfoDot /></span>
      </div>

      {/* body: dimmed field | dispatch rail */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 460px', minHeight: 0 }}>
        <div style={{ position: 'relative', background: CC.surface, minWidth: 0, minHeight: 0 }}>
          <Field run={D.runs.baseline} tick={beat.tick} layer="position" view="density" showGap dim={0.26} />
          <div style={{ position: 'absolute', left: 24, top: 20, display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: CC.ink3, background: 'rgba(255,255,255,.85)', padding: '5px 12px', borderRadius: 999, border: `1px solid ${CC.border}` }}>
            <span style={{ width: 7, height: 7, borderRadius: 999, background: '#c47a2c' }} /> paused at a story beat · {year}
          </div>
        </div>

        <div style={{ borderLeft: `1px solid ${CC.border}`, background: CC.bg, padding: '26px 30px', display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <Eyebrow>Chapter {bi + 1} of {STORY_BEATS.length}</Eyebrow>
            <span style={{ fontFamily: MONO, fontSize: 13, color: CC.ink3, ...TNUM }}>{year}</span>
          </div>
          <h2 style={{ margin: '10px 0 20px', fontFamily: SERIF, fontWeight: 600, fontSize: 33, lineHeight: 1.03, letterSpacing: '-.015em' }}>{beat.title}</h2>

          <p style={{ margin: 0, fontFamily: SERIF, fontStyle: 'italic', fontSize: 20, lineHeight: 1.42, color: CC.ink }}>{beat.lead}</p>
          <p style={{ margin: '16px 0 0', fontSize: 15, lineHeight: 1.6, color: CC.ink2 }}>{beat.body}</p>

          <div style={{ marginTop: 20, padding: '12px 15px', background: CC.surface, border: `1px solid ${CC.border}`, borderRadius: 10, display: 'flex', alignItems: 'center', gap: 11 }}>
            <span style={{ fontFamily: MONO, fontSize: 10, letterSpacing: '.1em', textTransform: 'uppercase', color: CC.ink4 }}>data</span>
            <span style={{ fontFamily: MONO, fontSize: 13.5, color: CC.ink, ...TNUM }}>{beat.metric(beat.tick)}</span>
          </div>

          <div style={{ marginTop: 'auto', paddingTop: 24, display: 'flex', gap: 10 }}>
            <button onClick={() => setBi((i) => Math.max(0, i - 1))} disabled={bi === 0} style={{
              padding: '12px 16px', borderRadius: 999, border: `1px solid ${CC.border}`, background: CC.surface,
              color: bi === 0 ? CC.ink4 : CC.ink2, cursor: bi === 0 ? 'default' : 'pointer', fontFamily: SANS, fontSize: 13.5,
            }}>← Back</button>
            <button onClick={() => setBi((i) => Math.min(STORY_BEATS.length - 1, i + 1))} style={{
              flex: 1, padding: '12px 16px', borderRadius: 999, border: 'none', background: CC.ink, color: '#fff',
              cursor: 'pointer', fontFamily: SANS, fontSize: 14, fontWeight: 500,
            }}>{bi === STORY_BEATS.length - 1 ? 'Finish the story' : 'Continue →'}</button>
          </div>
        </div>
      </div>

      {/* bottom strip: chapter timeline */}
      <div style={{ minHeight: 100, flexShrink: 0, borderTop: `1px solid ${CC.border}`, background: CC.bg, display: 'flex', alignItems: 'center', gap: 22, padding: '14px 30px' }}>
        <div style={{ flexShrink: 0 }}>
          <Eyebrow style={{ color: CC.ink3 }}>The story</Eyebrow>
          <div style={{ fontFamily: MONO, fontSize: 13, color: CC.ink, marginTop: 4, ...TNUM }}>1980 → 2025</div>
        </div>
        <div style={{ width: 1, height: 56, background: CC.border }} />
        <div style={{ flex: 1, minWidth: 0, position: 'relative', height: 50, display: 'flex', alignItems: 'center' }}>
          <div style={{ position: 'absolute', left: 0, right: 0, height: 3, borderRadius: 999, background: CC.border }} />
          <div style={{ position: 'absolute', left: 0, width: `${(beat.tick / LAST) * 100}%`, height: 3, borderRadius: 999, background: CC.ink }} />
          {/* faint event ticks for context */}
          {TL_EVENTS.filter((e) => e.fn).map((e) => (
            <span key={e.tick} style={{ position: 'absolute', left: `${(e.tick / LAST) * 100}%`, top: 19, width: 1, height: 12, background: CC.ink4, transform: 'translateX(-50%)' }} />
          ))}
          {STORY_BEATS.map((b, k) => {
            const on = k === bi, past = b.tick <= beat.tick;
            return (
              <button key={k} onClick={() => setBi(k)} title={b.title} style={{
                position: 'absolute', left: `${(b.tick / LAST) * 100}%`, transform: 'translateX(-50%)', top: 2,
                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5, background: 'none', border: 'none', cursor: 'pointer', padding: 0,
              }}>
                <span style={{ width: on ? 15 : 12, height: on ? 15 : 12, borderRadius: 999, background: past ? CC.ink : CC.surface, border: `2px solid ${past ? CC.ink : CC.ink4}` }} />
                <span style={{ fontFamily: SANS, fontSize: 11, color: on ? CC.ink : CC.ink3, whiteSpace: 'nowrap', fontWeight: on ? 600 : 400 }}>{b.title}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

window.ConceptStory = ConceptStory;
window.STORY_BEATS = STORY_BEATS;
