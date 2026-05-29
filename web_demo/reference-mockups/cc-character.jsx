// Calm to Camps — character panel
// Tab strip + bio + issues + live out-party affect + mini ego-network +
// the narrative beat for the current year. Bios/beats in Newsreader for an
// editorial, documentary feel. Linda is fully authored; the other three
// carry enough to populate the panel.

const CHARACTERS = {
  linda: {
    name: 'Linda', birth: 1953, city: 'suburban Ohio', job: 'school district administrator',
    issues: ['Education', 'Healthcare', 'Taxes'],
    bio: 'A school administrator and mother of two. In the mid-80s she votes Democrat without much thought — it is what her family has always done. Over forty years, quietly, that changes.',
    affect: (yf) => -(0.10 + 0.62 * Math.pow(yf, 1.3)),   // warmth toward out-party
    outParty: (year) => (lindaAt(year).party === 'R' ? 'Democrats' : 'Republicans'),
    beats: [
      { year: 1985, text: 'In 1985 Linda is 32, married, raising two kids. She votes Democrat, like her parents did, and rarely thinks about politics between elections.' },
      { year: 1996, text: "By '96 the dinner-table arguments have an edge they didn't used to. Cable news is on in the kitchen now, most evenings." },
      { year: 2001, text: 'After 9/11 she finds herself trusting a different set of voices. Her registration still says Democrat, but it no longer fits.' },
      { year: 2016, text: 'Linda votes Republican for the first time. The people she talks to most have, almost all, made the same move.' },
      { year: 2023, text: 'Now in her seventies, she watches both MSNBC and Fox — and is sure only one of them is lying.' },
    ],
  },
  james: {
    name: 'James', birth: 1958, city: 'Portland, Oregon', job: 'union electrician',
    issues: ['Labor', 'Climate', 'Healthcare'],
    bio: "A stable left-leaner his whole life. His positions barely move — but his warmth toward the other side collapses after 2008. The same man, a colder feeling.",
    affect: (yf) => -(0.08 + 0.72 * Math.pow(yf, 1.6)),
    outParty: () => 'Republicans',
    beats: [
      { year: 1985, text: 'James is a young electrician, reliably Democratic, with Republican friends he argues with and still invites to barbecues.' },
      { year: 2008, text: 'His views haven\u2019t shifted much. But the barbecues have thinned out, and the arguments stopped being friendly.' },
      { year: 2020, text: 'Same ballot he\u2019d always cast. A warmth toward the other side that is simply gone.' },
    ],
  },
  maria: {
    name: 'Maria', birth: 1971, city: 'Phoenix, Arizona', job: 'community organizer',
    issues: ['Housing', 'Immigration', 'Wages'],
    bio: 'Independent through the 90s, leaning Democratic in the 2000s, pulled into the post-2016 left by housing and wages. A leftward emergence story.',
    affect: (yf) => -(0.05 + 0.55 * Math.pow(yf, 1.5)),
    outParty: () => 'Republicans',
    beats: [
      { year: 1996, text: 'Maria registers Independent and means it \u2014 she splits her ticket and distrusts both parties.' },
      { year: 2016, text: 'The aftermath pulls her left. For the first time she feels she has a side.' },
    ],
  },
  bob: {
    name: 'Bob', birth: 1955, city: 'rural Pennsylvania', job: 'small-business owner',
    issues: ['Taxes', 'Guns', 'Immigration'],
    bio: 'A mainstream Republican in 1985. Tea Party by 2009, drawn into the MAGA coalition by 2015, settled in that faction by 2025. The factional-emergence story from the right.',
    affect: (yf) => -(0.12 + 0.68 * Math.pow(yf, 1.4)),
    outParty: () => 'Democrats',
    beats: [
      { year: 1985, text: 'Bob is a Chamber-of-Commerce Republican: low taxes, strong defense, nothing dramatic.' },
      { year: 2009, text: 'The Tea Party gives a name to a frustration he\u2019d felt for years.' },
      { year: 2016, text: 'By now the movement has a candidate, and Bob is all the way in.' },
    ],
  },
};

function currentBeat(char, year) {
  const b = CHARACTERS[char].beats;
  let chosen = b[0];
  for (const beat of b) if (year >= beat.year) chosen = beat;
  return chosen;
}

// Tie strength is shown by PROXIMITY (closer = stronger) and node size,
// not edge thickness. Same-party ties strengthen over time; cross-party ties
// weaken and drift outward — so the hub visibly homogenises and tightens.
function MiniEgoNetwork({ year }) {
  const VB = 260, H = 150, cx = VB / 2, cy = H / 2;
  const linda = lindaAt(year);
  const yf = yearToFrac(year);
  const rng = ccRng(99);
  const matchFrac = 0.45 + 0.5 * yf;
  const pc = (p) => (p === 'D' ? CC.d : p === 'R' ? CC.r : CC.i);
  const N = 9;
  const nodes = [];
  for (let i = 0; i < N; i++) {
    const ang = (i / N) * Math.PI * 2 + 0.45;
    const matches = rng() < matchFrac;
    const party = matches ? linda.party : (rng() < 0.4 ? 'I' : (linda.party === 'D' ? 'R' : 'D'));
    const base = 0.30 + rng() * 0.45;
    const strength = matches
      ? Math.min(0.98, base + 0.45 * yf)
      : Math.max(0.10, base - 0.55 * yf);
    nodes.push({ ang, party, strength });
  }
  const near = 42, farX = 118, farY = 62;
  const placed = nodes.map((nd) => {
    const rx = farX - (farX - near) * nd.strength;
    const ry = farY - (farY - near) * nd.strength;
    return {
      x: cx + Math.cos(nd.ang) * rx,
      y: cy + Math.sin(nd.ang) * ry,
      party: nd.party, strength: nd.strength,
      r: 4.5 + nd.strength * 3.5,
    };
  });
  return (
    <svg viewBox={`0 0 ${VB} ${H}`} width="100%" height="110" preserveAspectRatio="xMidYMid meet" style={{ display: 'block' }}>
      {/* faint proximity guide rings */}
      {[0.65, 0.3].map((s, i) => (
        <ellipse key={'r' + i} cx={cx} cy={cy} rx={farX - (farX - near) * s} ry={farY - (farY - near) * s}
                 fill="none" stroke={CC.border} strokeWidth="1" strokeDasharray="2 4" />
      ))}
      {placed.map((p, i) => (
        <line key={'l' + i} x1={cx} y1={cy} x2={p.x} y2={p.y}
              stroke={CC.ink3} strokeWidth="1" opacity={0.16 + 0.24 * p.strength} />
      ))}
      {placed.map((p, i) => (
        <circle key={'c' + i} cx={p.x} cy={p.y} r={p.r} fill={pc(p.party)} opacity="0.92" />
      ))}
      <circle cx={cx} cy={cy} r="10" fill="none" stroke="#fff" strokeWidth="3" />
      <circle cx={cx} cy={cy} r="8.5" fill={pc(linda.party)} />
      <circle cx={cx} cy={cy} r="10" fill="none" stroke={CC.ink} strokeWidth="1.2" />
    </svg>
  );
}

function CharacterPanel({ year = 2016, character = 'linda', compact = false }) {
  const ch = CHARACTERS[character];
  const yf = yearToFrac(year);
  const age = Math.round(year) - ch.birth;
  const live = character === 'linda' ? lindaAt(year) : { party: character === 'bob' ? 'R' : 'D' };
  const party = live.party === 'R' ? 'Republican' : live.party === 'D' ? 'Democrat' : 'Independent';
  const affect = ch.affect(yf).toFixed(2);
  const beat = currentBeat(character, Math.round(year));
  const tabs = ['linda', 'james', 'maria', 'bob'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', fontFamily: SANS, color: CC.ink }}>
      {/* tab strip */}
      <div style={{ display: 'flex', gap: 4, padding: '0 0 14px', borderBottom: `1px solid ${CC.border}` }}>
        {tabs.map((t) => {
          const on = t === character;
          return (
            <span key={t} style={{
              fontSize: 12.5, fontWeight: on ? 600 : 400,
              color: on ? CC.ink : CC.ink3, padding: '5px 11px', borderRadius: 999,
              background: on ? CC.bg2 : 'transparent', cursor: 'default', textTransform: 'capitalize',
              border: `1px solid ${on ? CC.borderS : 'transparent'}`,
            }}>{CHARACTERS[t].name}</span>
          );
        })}
      </div>

      {/* identity */}
      <div style={{ padding: '14px 0 12px', borderBottom: `1px solid ${CC.border}` }}>
        <h3 style={{ margin: 0, fontFamily: SERIF, fontWeight: 600, fontSize: 26, lineHeight: 1.05, letterSpacing: '-.01em' }}>{ch.name}</h3>
        <div style={{ fontSize: 12.5, color: CC.ink3, fontFamily: MONO, marginTop: 4, ...TNUM }}>age {age} · {Math.round(year)} · {ch.city}</div>
        <div style={{ fontSize: 13, color: CC.ink2, marginTop: 2 }}>{ch.job}</div>
        <p style={{ margin: '11px 0 0', fontFamily: SERIF, fontSize: 15, lineHeight: 1.48, color: CC.ink2, textWrap: 'pretty' }}>{ch.bio}</p>
      </div>

      {/* party + affect */}
      <div style={{ padding: '12px 0', borderBottom: `1px solid ${CC.border}`, display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 13, color: CC.ink3 }}>Votes</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 13.5, fontWeight: 500 }}>
            <PartySwatch party={live.party} /> {party}
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 13, color: CC.ink3, display: 'inline-flex', gap: 6, alignItems: 'center' }}>
            Warmth toward {ch.outParty(Math.round(year))} <InfoDot />
          </span>
          <span style={{ fontSize: 14, fontWeight: 600, fontFamily: MONO, color: CC.r, ...TNUM }}>{affect}</span>
        </div>
        {/* affect bar (centered at 0) */}
        <div style={{ position: 'relative', height: 5, background: CC.bg2, borderRadius: 999 }}>
          <div style={{ position: 'absolute', left: '50%', top: -2, bottom: -2, width: 1, background: CC.ink4 }} />
          <div style={{ position: 'absolute', right: '50%', top: 0, bottom: 0, width: `${Math.abs(affect) * 50}%`, background: CC.r, borderRadius: 999 }} />
        </div>
      </div>

      {/* issues */}
      <div style={{ padding: '12px 0', borderBottom: `1px solid ${CC.border}` }}>
        <Eyebrow>Issues she cares about</Eyebrow>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7, marginTop: 9 }}>
          {ch.issues.map((iss) => (
            <span key={iss} style={{
              fontSize: 12.5, color: CC.ink2, padding: '4px 11px', borderRadius: 999,
              border: `1px solid ${CC.border}`, background: CC.surface,
            }}>{iss}</span>
          ))}
        </div>
      </div>

      {/* ego network */}
      <div style={{ padding: '12px 0', borderBottom: `1px solid ${CC.border}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
          <Eyebrow>Her network</Eyebrow>
          <span style={{ fontSize: 11.5, color: CC.ink3 }}>closer = stronger tie</span>
        </div>
        <div style={{ marginTop: 6 }}><MiniEgoNetwork year={year} /></div>
      </div>

      {/* narrative beat */}
      <div style={{ padding: '13px 0 0', flex: 1 }}>
        <Eyebrow style={{ color: CC.ink4 }}>{beat.year}</Eyebrow>
        <p style={{ margin: '7px 0 0', fontFamily: SERIF, fontSize: 15.5, lineHeight: 1.46, color: CC.ink, textWrap: 'pretty' }}>{beat.text}</p>
      </div>
    </div>
  );
}

window.CharacterPanel = CharacterPanel;
window.CHARACTERS = CHARACTERS;
window.MiniEgoNetwork = MiniEgoNetwork;
