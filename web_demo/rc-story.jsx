// Concept 2 — Story dispatch in the polished simulation-page frame:
// header · dimmed field · wide dispatch rail · bottom chapter-timeline strip.
// v1: single society voice (personal voice marked as a v2 slot).

const _sepAt = (t) => centroids(posAt(D.runs.baseline, t), D.runs.baseline.party[Math.round(t)]).gap;
const _alignAt = (t) => macroAt(D.runs.baseline, t, 'identity_alignment');
// Chapters re-anchored to the engine's evidence-graded mechanisms (Step 5):
// elite drift lives at Gingrich/1994 (HIGH), not Citizens United (now a
// non-causal MARKER); social media is the contested suspect (LOW); identity
// sorting (Mason) is named as the master mechanism; the affect pivot stays at
// 2016 (status threat, CONTESTED). Copy is truthful to
// docs/polarization_causal_model.md — no "social media caused it", no "CU drove
// it", and identity alignment is framed as co-rising with animus, not its cause.
const STORY_BEATS = [
  {
    tick: 0, title: 'What you’re looking at', short: 'Orientation', layer: 'position', orient: true, landmarks: true,
    lead: 'Every point on this map is one American.',
    body: 'Left to right is the economy: who should hold the money and the power. Top to bottom is culture: how fast the country should change. In 1980 — the parties only just beginning to sort along the old racial and regional lines — almost everyone still piles into a single warm cluster near the middle.',
  },
  {
    tick: 42, title: 'The parties pull apart at the top', short: 'Elite drift', layer: 'position',
    lead: 'The split starts with the politicians, not the public.',
    body: 'Newt Gingrich’s 1994 takeover hardens Congress into two disciplined teams — and the Republican side moves right faster than Democrats move left. Voters haven’t budged yet; their leaders have. This asymmetric elite drift is the best-evidenced first cause.',
    metric: (t) => `party separation at ${_sepAt(t).toFixed(2)} — elites lead`,
    data: { label: 'Party separation', valueAt: _sepAt, fmt: (v) => v.toFixed(2), note: 'elites lead', color: 'd' },
  },
  {
    tick: 48, title: 'Cable picks a side', short: 'Cable', layer: 'position',
    lead: 'For the first time, you can build a news diet that never disagrees with you.',
    body: 'Fox News launches; talk radio is already loud. Nobody’s opinions move overnight — the country just quietly learns to sort itself by what it watches. Of all the media stories, this one carries the strongest causal evidence.',
    metric: (t) => `out-party warmth still near ${warmthDegAt(t)}°`,
    data: { label: 'Out-party warmth', valueAt: (t) => warmthDegAt(t), fmt: (v) => `${Math.round(v)}°`, note: 'still warm' },
  },
  {
    tick: 60, title: 'Sorting into mega-identities', short: 'Sorting', layer: 'position',
    lead: 'Party, ideology, religion and region begin to stack into a single identity.',
    body: 'This is the quiet master mechanism. People mostly keep their party and move their positions to match it — Democrat and Republican come to mean two whole ways of life. As those identities align, the warmth between the camps drains away. The model’s alignment score climbs from about 0.21 to 0.36 over the run — a 1.7× rise that tracks the animus without, on its own, causing it.',
    metric: (t) => `identity alignment ${_alignAt(t).toFixed(2)} and rising`,
    data: { label: 'Identity alignment', valueAt: _alignAt, fmt: (v) => v.toFixed(2), note: 'stacking rises', color: 'd' },
  },
  {
    tick: 84, title: 'The feed everyone blames', short: 'The feed', layer: 'position',
    lead: 'Social media reaches almost everyone — and gets the blame for everything after.',
    body: 'It’s the famous suspect the data won’t convict: polarization rose fastest among the oldest, least-online Americans, and the big deactivation experiments came back near zero. In this model social media is only a small, contested accelerant — not the cause.',
    metric: (t) => `party separation at ${_sepAt(t).toFixed(2)} — contested driver`,
    data: { label: 'Party separation', valueAt: _sepAt, fmt: (v) => v.toFixed(2), note: 'contested', color: 'd' },
  },
  {
    tick: 90, title: 'The base hardens', short: 'The base', layer: 'position',
    lead: 'The activists, not the donors, drag each party toward its edge.',
    body: 'Primary challenges and a newly-organized base pull the parties outward — the Tea Party hardens the right first. Citizens United lands the same year and gets the credit, but the best-identified studies find no clear polarization effect; here it is only an era marker. The middle keeps thinning.',
    metric: (t) => `party separation at ${_sepAt(t).toFixed(2)} — edges harden`,
    data: { label: 'Party separation', valueAt: _sepAt, fmt: (v) => v.toFixed(2), note: 'edges harden', color: 'd' },
  },
  {
    tick: 108, title: 'It stops being about policy', short: 'Animus', layer: 'affect',
    lead: 'A status-threat shock lands, and the middle stops feeling safe to stand in.',
    body: 'Americans still haven’t moved far apart on the issues — but now they dislike each other, and that matters more than the issues do. The trigger is a contested one: Mutz reads 2016 as status threat; Morgan argues economics mattered too. Either way, the feeling curdles.',
    metric: (t) => `out-party warmth down to ${warmthDegAt(t)}° — coldest yet`,
    data: { label: 'Out-party warmth', valueAt: (t) => warmthDegAt(t), fmt: (v) => `${Math.round(v)}°`, note: 'coldest yet' },
  },
  {
    tick: 120, title: 'Two Americas', short: 'Two Americas', layer: 'affect',
    lead: 'By the pandemic, the two camps no longer share a map — or a set of facts.',
    body: 'COVID and January 6th harden the sort into two separate masses. Out-party warmth has fallen from the high-40s to the mid-20s and is near its floor — there isn’t much colder left to go. Forty years earlier they were one crowd; now they can barely speak.',
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

          <div style={{ marginTop: 16, padding: '11px 14px', border: `1px dashed ${CC.borderS}`, borderRadius: 10 }}>
            <span style={{ fontSize: 11.5, lineHeight: 1.45, color: CC.ink3 }}>
              <strong style={{ color: CC.ink2, fontWeight: 600 }}>v2 slot:</strong> a personal voice (one named American living through this beat) drops in here, in italic — once the character system is properly designed.
            </span>
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
