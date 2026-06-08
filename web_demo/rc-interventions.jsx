// Calm to Camps — interventions, Step 4: driven by the engine, not hardcoded.
//
// SINGLE SOURCE OF TRUTH. Every bucket and Δ on this screen is computed LIVE
// from the shipped seed-0 data: D.interventions (metadata + provenance) and
// D.counterfactuals (the 56 real per-tick runs). There is NO hardcoded number
// table anywhere here. phase10_results.md is the validation oracle — the live
// numbers reproduce it. (Single representative seed; the 9-seed means in the
// doc differ only within noise.)
//
// STAGED REVEAL (the payoff): picking an intervention no longer dumps the
// answer. The user PREDICTS (helps / no effect / backfires); only then does the
// compass MORPH from the real 2025 baseline to the counterfactual endpoint
// (cf.endpos) and a branching GHOST-LINE split from the chosen release year
// play out. The "wait, that backfires?" moment is the whole product.
//
// BRIGHT LINE: the 7 engine-measured interventions and the illustrative
// "Sandbox" (what-if scenarios + free tinkering) are STRUCTURALLY separate —
// different surfaces, never one list. The sandbox changes the *model*, not a
// policy, and is badged as not-a-finding.

// ── the 7 engine interventions (order + lay copy; numbers come from data) ────
const IV_ORDER = [
  'X1_show_other_side', 'X2_fix_algorithm', 'X3_quit_cable_news',
  'X4_bipartisan_dialogue', 'X5_ranked_choice_voting',
  'X6_shared_institutions', 'X7_perception_correction',
];

// Lay take per intervention (COPY, not numbers — the honest one-line lesson).
const IV_TAKE = {
  X1_show_other_side: 'Sustained cross-party exposure activated identity threat and cascaded into a worse split — the classic Bail backfire, played out at population scale.',
  X2_fix_algorithm: 'Muting the recommender moved nothing — faithful to the Meta-2020 deactivation null.',
  X3_quit_cable_news: 'At a realistic share who actually quit, the population-level effect washes out to nothing.',
  X4_bipartisan_dialogue: 'Dialogue helps the people in the room, but at realistic reach it does not move the country.',
  X5_ranked_choice_voting: 'Structural electoral reform bends the split — but only in some decades. It bites hardest where the elite drift it suppresses is itself large.',
  X6_shared_institutions: 'Ordinary shared life — neighbourhoods, workplaces, institutions — is the one lever that reliably warms feelings toward the other side.',
  X7_perception_correction: 'Correcting the perception gap works for the treated — but in a sorted network the corrected view rarely meets the other side, so it never propagates.',
};

// Extra caveats the audit requires be shown in-UI (§3.4 #6, §5.2).
const IV_CAVEAT = {
  X1_show_other_side: 'The backfire magnitude here is this model’s extrapolation to a sustained 20-year policy — roughly 3× Bail’s ~0.1 SD field effect, and exposure can flip helpful when anonymous or structured. Read the direction, not the number.',
  X5_ranked_choice_voting: 'Theoretical: direct RCV field studies (Donovan & Bowler 2023; Maine) find ~null effects. The engine reports the Drutman mechanism’s prediction, not a measured RCV impact.',
};

const RELEASE_YEARS = ['1985', '1990', '1995', '2000', '2005', '2010', '2015', '2020'];
const DEFAULT_RELEASE = '2000';
const HORIZON = 30; // phase10 measurement window (clipped to available length)

const IVMETA = D.interventions;
const CF = D.counterfactuals;
const BASE_MACRO = D.runs.baseline.macro;
const BASE_POS_LAST = D.runs.baseline.pos[LAST];
const BASE_PARTY_LAST = D.runs.baseline.party[LAST];

// ── bucket math — exactly phase10's rule (helpful = -Δsep / +Δaff) ───────────
// |Δ|<0.05 null · 0.05–0.15 helpful = partial · ≥0.15 helpful = real ·
// >0.05 in the unhelpful direction = backfire.
function bucketSep(d) {
  if (Math.abs(d) < 0.05) return 'null';
  if (d > 0) return 'backfire';
  return d <= -0.15 ? 'real' : 'partial';
}
function bucketAff(d) {
  if (Math.abs(d) < 0.05) return 'null';
  if (d < 0) return 'backfire';
  return d >= 0.15 ? 'real' : 'partial';
}
// Which axis is this intervention's headline (from its DECLARED, stable bucket)?
function headlineMetric(id) {
  const b = IVMETA[id].effect_buckets;
  return b.affect && b.affect !== 'null' ? 'aff' : 'sep';
}

// Δ at the (clipped) horizon for one (intervention, release year), vs baseline.
function deltasAt(id, year) {
  const cf = CF[id][year];
  const rt = cf.release_tick;
  const k = Math.min(HORIZON, cf.sep.length - 1); // clip — 2020 release only has 15 ticks
  const bt = rt + k;
  return {
    cf, releaseTick: rt,
    dSep: cf.sep[k] - BASE_MACRO[bt].sep,
    dAff: cf.aff[k] - BASE_MACRO[bt].aff, // out-party warmth Δ: positive = warmer = helpful
  };
}
// Headline bucket for an intervention at a release year (drives the live tag).
function bucketAt(id, year) {
  const { dSep, dAff } = deltasAt(id, year);
  return headlineMetric(id) === 'aff' ? bucketAff(dAff) : bucketSep(dSep);
}
// Signed "improvement" on the headline axis (positive = good), for tracks/sparkline.
function improvementAt(id, year) {
  const { dSep, dAff } = deltasAt(id, year);
  return headlineMetric(id) === 'aff' ? dAff : -dSep;
}

// provenance: theoretical when the [T] tags outweigh the field tags (L:M+L:D).
function provenanceOf(id) {
  const t = IVMETA[id].provenance_tags || {};
  const field = (t['L:M'] || 0) + (t['L:D'] || 0);
  const theo = t['T'] || 0;
  return theo > field
    ? { kind: 'theoretical', label: 'Theoretical', note: 'Mechanism-only — not yet supported by field evidence.' }
    : { kind: 'field', label: 'Field-tested', note: 'Anchored to field experiments.' };
}
// Does the effect flip bucket across the eight release decades? (X5 does.)
function decadeVaries(id) {
  const set = new Set(RELEASE_YEARS.map((y) => bucketAt(id, y)));
  return set.size > 1;
}

// ── sandbox (illustrative ONLY — never engine-measured) ──────────────────────
// Walled off on its own surface. These map to real engine knobs cranked past
// anything we'd calibrate; the field response is a cosmetic spread, not a run.
const SB_SCENARIOS = [
  { id: 'W1', name: 'Ban a media channel', spread: -0.16, take: 'Zero an outlet’s weight in every diet. The field visibly re-merges — but this is fantasy policy.' },
  { id: 'W2', name: 'Make elites super-extreme', spread: 0.31, take: 'Crank elite drift 3×→8×. The two camps fly apart — the model responds dramatically.' },
  { id: 'W3', name: 'Wipe everyone’s priors', spread: -0.40, take: 'Reset every agent toward the origin. Watch sorting collapse — then re-emerge, or not.' },
  { id: 'W4', name: 'Echo-chamber world', spread: 0.36, take: 'Drop open-mindedness, raise clustering. Maximal sorting — the worst case, made visible.' },
];
const SB_SLIDERS = [
  { key: 'elite', name: 'Elite extremity', stops: ['realistic', '2×', '5×', '8×'], def: 0 },
  { key: 'open', name: 'Open-mindedness', stops: ['closed', 'low', 'realistic', 'open'], def: 2 },
  { key: 'media', name: 'Media power', stops: ['off', 'realistic', 'high', 'max'], def: 1 },
];

// outcome → tone in the shared Tag system. Only "backfire" borrows oxblood.
const OUTCOME = {
  null:     { label: 'no effect',   tone: 'soft' },
  partial:  { label: 'partial',     tone: 'neutral' },
  real:     { label: 'real effect', tone: 'strong' },
  backfire: { label: 'backfire',    tone: 'backfire' },
};
// the three bets the user can place
const GUESS = {
  help:     { label: 'It helps',     sub: 'pulls them back together' },
  none:     { label: 'No effect',    sub: 'barely moves the needle' },
  backfire: { label: 'It backfires', sub: 'makes the split worse' },
};
const bucketToBet = (b) => b === 'backfire' ? 'backfire' : b === 'null' ? 'none' : 'help';
// metric-aware verb for the verdict line
const VERB = {
  sep: { help: 'pulls the two camps back together', none: 'leaves the split essentially unchanged', backfire: 'drives the two camps further apart' },
  aff: { help: 'warms feelings toward the other side', none: 'leaves feelings essentially unchanged', backfire: 'chills feelings toward the other side' },
};

const _clampN = (lo, hi, v) => Math.max(lo, Math.min(hi, v));
const _mark = (v) => (_clampN(-0.6, 1, v) - (-0.6)) / 1.6 * 100;
const _bucketCol = (b) => b === 'backfire' ? CC.r : b === 'null' ? CC.ink4 : '#3f7d54';

// sandbox effect from the four what-if presets / the three sliders (cosmetic)
function sandboxFromScenario(sc) {
  return { name: sc.name, take: sc.take, mult: _clampN(0.45, 1.62, 1 + sc.spread), spread: sc.spread, custom: false };
}
function sandboxFromTinker(v) {
  const spread = v.elite * 0.13 + (2 - v.open) * 0.1 + (v.media - 1) * 0.1;
  return {
    name: 'Custom scenario', mult: _clampN(0.5, 1.62, 1 + spread), spread, custom: true,
    take: Math.abs(spread) < 0.04 ? 'At these settings the field sits at its calibrated baseline.'
      : spread > 0 ? 'Cranking these knobs pushes the camps further apart.' : 'Dialing these down pulls the camps back toward the centre.',
  };
}

// ── sandbox: the 5-knob pre-rendered grid (build_sandbox_data.py) ─────────────
// Each knob has 5 detents; the values MUST match GRID in build_sandbox_data.py.
// Data-driven (scripts/sandbox_knob_screen.py): each owns a distinct axis.
// All five are CAUSES you set; the readouts below (separation, animus, spread,
// mega-identity) are OUTCOMES you watch. Order MUST match KNOB_ORDER in
// scripts/build_sandbox_data.py — the cell key is the detent indices joined.
const SANDBOX_KNOBS = [
  { key: 'identity',  name: 'Mega-identity',          stops: ['off', '½×', '1×', '2×', '3×'],          owns: 'how much race, religion & lifestyle line up with party' },
  { key: 'elite',     name: 'Elite extremism',        stops: ['0×', '1.5×', '3×', '5×', '8×'],         owns: 'how far apart the party leaders pull' },
  { key: 'openness',  name: 'Open-mindedness',        stops: ['closed', 'low', 'mid', 'high', 'open'], owns: 'how widely people will hear the other side' },
  { key: 'contact',   name: 'Contact & mixing',       stops: ['none', 'some', 'lots', 'high', 'max'],  owns: 'how much the two sides mix in daily life' },
  { key: 'diversity', name: 'Within-party diversity', stops: ['lockstep', 'low', 'mid', 'high', 'free'], owns: 'free-thinking individuals vs marching in lockstep' },
];
const SANDBOX_CENTER = [2, 2, 1, 0, 1];   // the shipped arc (center cell of the grid)
// Presets = named knob-vectors (indices into each knob's stops, in KNOB_ORDER).
// Each preset emulates a recognizable scenario; `note` says WHAT it models.
const SANDBOX_PRESETS = [
  { name: 'The shipped arc', vec: [2, 2, 1, 0, 1],
    note: 'What actually happened — the calibrated 1980→2025 baseline. The center of the grid.' },
  { name: 'Great Sorting', vec: [4, 4, 0, 0, 0],
    note: 'Identity stacked, elites maxed, minds closed, no mixing, lockstep ranks — the two camps slam into opposite corners.' },
  { name: 'Depolarized', vec: [0, 0, 4, 4, 2],
    note: 'Open minds and real mixing, with identity and elite divergence dialed away — the camps merge into one warmer cloud.' },
  { name: 'Mega-identity', vec: [4, 2, 1, 0, 1],
    note: 'Race, religion and lifestyle all line up with party — Mason’s mega-identity end-state (the diagonal collapse).' },
  { name: 'The Great Mixing', vec: [2, 2, 1, 4, 1],
    note: 'The real arc, but the two sides mix everywhere — they warm to each other even while still disagreeing on the issues.' },
  { name: 'Free Thinkers', vec: [2, 2, 1, 0, 4],
    note: 'The real arc, but everyone thinks for themselves — the party clouds blur and the hard edges soften.' },
];

// ── shared state ─────────────────────────────────────────────────────────────
function useInterventions() {
  const [activeId, setActiveId] = React.useState(null);       // full engine id, or null
  const [releaseYear, setReleaseYear] = React.useState(DEFAULT_RELEASE);
  const [revealed, setRevealed] = React.useState(() => new Set());
  const [guesses, setGuesses] = React.useState({});
  // sandbox is a SEPARATE surface — the 5-knob pre-rendered alternate-history grid
  const [sbMode, setSbMode] = React.useState(false);          // sandbox surface open?
  const [sbKnobs, setSbKnobs] = React.useState(SANDBOX_CENTER); // 5 detent indices

  const active = activeId ? IVMETA[activeId] : null;
  const predicting = !!active && !revealed.has(activeId);
  const showResult = !!active && revealed.has(activeId);

  // live engine effect for the active intervention at the chosen release year
  let eff = null;
  if (active) {
    const { dSep, dAff, releaseTick, cf } = deltasAt(activeId, releaseYear);
    const metric = headlineMetric(activeId);
    const bucket = metric === 'aff' ? bucketAff(dAff) : bucketSep(dSep);
    eff = {
      id: activeId, name: IVMETA[activeId].label, bucket, metric, dSep, dAff,
      releaseTick, endpos: cf.endpos, cf, take: IV_TAKE[activeId],
      caveat: IV_CAVEAT[activeId] || null, prov: provenanceOf(activeId),
      varies: decadeVaries(activeId), improvement: improvementAt(activeId, releaseYear),
    };
  }
  const o = eff ? OUTCOME[eff.bucket] : null;

  // ── compass morph: real per-agent baseline-2025 → counterfactual endpoint ──
  // (positions only; coloured by baseline party, which cf.endpos omits.)
  const animRef = React.useRef(0); // 0 = baseline 2025, 1 = counterfactual 2025
  const [, force] = React.useState(0);
  const morphTarget = showResult && eff ? 1 : 0;
  React.useEffect(() => {
    let raf; const from = animRef.current, to = morphTarget, t0 = performance.now();
    const dur = Math.abs(to - from) < 0.001 ? 0 : 780;
    const step = (now) => {
      const k = dur ? Math.min(1, (now - t0) / dur) : 1;
      const e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      animRef.current = from + (to - from) * e; force((x) => x + 1);
      if (k < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [morphTarget, activeId, releaseYear]);
  const m = animRef.current;

  // the transform handed to <Field>: the engine-result path morphs the 2025
  // cloud to the counterfactual endpoint. The sandbox no longer uses a cosmetic
  // transform — it plays a REAL pre-rendered run (useIvPlayback / loadSandbox).
  const transform = React.useCallback((ps) => {
    if (eff && eff.endpos && m > 0.0001) {
      const ep = eff.endpos;
      return ps.map((p, i) => {
        const e = ep[i] || p;
        return [p[0] + (e[0] - p[0]) * m, p[1] + (e[1] - p[1]) * m];
      });
    }
    return ps;
  }, [eff, m]);

  const baseGap = centroids(BASE_POS_LAST, BASE_PARTY_LAST).gap;
  const nowGap = centroids(transform(BASE_POS_LAST.map((p) => [p[0], p[1]])), BASE_PARTY_LAST).gap;

  const guess = activeId ? guesses[activeId] : null;
  const correct = guess && eff ? bucketToBet(eff.bucket) === guess : null;

  // Reset to the canonical fixed decade on each pick. For interventions whose
  // result is steady across decades the selector is hidden, so this is the one
  // release they run; the decade-dependent ones (X5/X6) re-expose the picker.
  const pick = (id) => { setSbMode(false); setActiveId(id); setReleaseYear(DEFAULT_RELEASE); };
  const submitGuess = (g) => {
    if (!activeId) return;
    setGuesses((p) => ({ ...p, [activeId]: g }));
    setRevealed((p) => { const n = new Set(p); n.add(activeId); return n; });
  };
  const openSandbox = () => { setActiveId(null); setSbMode(true); };
  const closeSandbox = () => { setSbMode(false); };
  // return to the intervention picker from a specific lever OR the sandbox
  const back = () => { setSbMode(false); setActiveId(null); };
  // sandbox knob controls
  const setSbKnob = (i, idx) => setSbKnobs((p) => { const n = p.slice(); n[i] = idx; return n; });
  const applyPreset = (vec) => setSbKnobs(vec.slice());
  const sbKey = sbKnobs.join('');

  const revealedCount = revealed.size;

  return {
    activeId, active, eff, o, releaseYear, setReleaseYear, transform, baseGap, nowGap,
    predicting, showResult, guess, correct,
    sbMode, sbKnobs, sbKey, isSandbox: sbMode,
    pick, submitGuess, openSandbox, closeSandbox, setSbKnob, applyPreset, back,
    revealed, revealedCount, total: IV_ORDER.length,
  };
}

// ── LEFT TRAY — the seven engine interventions + a walled sandbox entry ───────
function IvRow({ id, year, active, revealed, onClick }) {
  const meta = IVMETA[id];
  const bucket = bucketAt(id, year);
  const o = OUTCOME[bucket];
  return (
    <button onClick={onClick} style={{
      textAlign: 'left', width: '100%', padding: '10px 12px', cursor: 'pointer', fontFamily: SANS,
      background: active ? CC.surface : 'transparent', borderRadius: DS.rad.inset,
      border: `1px solid ${active ? CC.borderS : 'transparent'}`,
      boxShadow: active ? '0 1px 3px rgba(26,29,35,.05)' : 'none',
      display: 'flex', alignItems: 'center', gap: 11,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: DS.rad.pill, flexShrink: 0, background: active ? CC.ink : CC.ink4, opacity: active ? 1 : 0.45 }} />
      <span style={{ flex: 1, fontSize: DS.type.small + 1, fontWeight: active ? 600 : 450, color: active ? CC.ink : CC.ink2 }}>{meta.label}</span>
      {revealed
        ? <Tag tone={o.tone}>{o.label}</Tag>
        : <span style={{ fontFamily: MONO, fontSize: 12, color: CC.ink4, opacity: 0.8 }}>?</span>}
    </button>
  );
}

function IvTray({ iv }) {
  return (
    <div style={{ height: '100%', overflow: 'auto', padding: `${DS.sp.md}px 18px`, display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '0 4px' }}>
        <Eyebrow>Interventions</Eyebrow>
        <h3 style={{ margin: '8px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: DS.type.subhead, letterSpacing: '-.01em' }}>What could we do about it?</h3>
        <p style={{ margin: '7px 0 0', fontSize: DS.type.micro, lineHeight: 1.45, color: CC.ink3 }}>
          Seven things people have actually tried. Pick one and call it before you run it. <MonoVal size={DS.type.micro} color={CC.ink3}>{iv.revealedCount}/{iv.total}</MonoVal> run so far.
        </p>
      </div>

      <div style={{ marginTop: DS.sp.md, paddingTop: 18, borderTop: `1px solid ${CC.border}` }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 9, padding: '0 4px' }}>
          <Eyebrow style={{ color: CC.ink2 }}>Field-tested levers</Eyebrow>
        </div>
        <p style={{ margin: '7px 4px 10px', fontSize: DS.type.micro, lineHeight: 1.45, color: CC.ink3 }}>
          Each runs the real simulation. The honest answer: most do little, one backfires, and the win isn’t the one you’d guess.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {IV_ORDER.map((id) => (
            <IvRow key={id} id={id} year={iv.releaseYear}
              active={!iv.isSandbox && iv.activeId === id}
              revealed={iv.revealed.has(id)} onClick={() => iv.pick(id)} />
          ))}
        </div>
      </div>

      {/* ── the bright line: sandbox is a separate, clearly-walled surface ── */}
      <div style={{ marginTop: DS.sp.md, paddingTop: 18, borderTop: `1px dashed ${CC.borderS}` }}>
        <button onClick={iv.isSandbox ? iv.closeSandbox : iv.openSandbox} style={{
          width: '100%', textAlign: 'left', cursor: 'pointer', fontFamily: SANS,
          background: iv.isSandbox ? CC.bg2 : 'transparent', border: `1px solid ${iv.isSandbox ? CC.borderS : CC.border}`,
          borderRadius: DS.rad.inset, padding: '11px 12px', display: 'flex', alignItems: 'center', gap: 10,
        }}>
          <span style={{ fontSize: 13 }}>{'⚠︎'}</span>
          <span style={{ flex: 1 }}>
            <span style={{ display: 'block', fontSize: DS.type.small, fontWeight: 600, color: CC.ink }}>Sandbox</span>
            <span style={{ display: 'block', fontSize: DS.type.micro, color: CC.ink3, marginTop: 1 }}>Not real interventions — changes the model, not a policy.</span>
          </span>
          <span style={{ fontFamily: MONO, fontSize: 13, color: CC.ink3 }}>{iv.isSandbox ? '×' : '+'}</span>
        </button>
      </div>
    </div>
  );
}

// ── release-year selector (the teachable "when did we try it?" control) ──────
function ReleaseSelector({ year, onPick }) {
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
        <Eyebrow style={{ color: CC.ink3 }}>If we’d done it in…</Eyebrow>
        <Caption>try a different decade</Caption>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 8 }}>
        {RELEASE_YEARS.map((y) => {
          const on = y === year;
          return (
            <button key={y} onClick={() => onPick(y)} style={{
              fontFamily: MONO, fontSize: 12, fontWeight: on ? 600 : 400, cursor: 'pointer',
              color: on ? '#fff' : CC.ink2, background: on ? CC.ink : CC.surface,
              border: `1px solid ${on ? CC.ink : CC.border}`, borderRadius: DS.rad.pill, padding: '4px 9px', ...TNUM,
            }}>{y}</button>
          );
        })}
      </div>
    </div>
  );
}

// ── the branching ghost-line: real counterfactual trajectory vs baseline ─────
function GhostChart({ eff, revealed, width = 392, height = 132 }) {
  const padL = 8, padR = 10, padT = 12, padB = 18;
  const plotW = width - padL - padR, plotH = height - padT - padB;
  const metric = eff.metric;
  const bVal = (m) => metric === 'aff' ? -m.aff : m.sep;   // -aff so "up = more polarized"
  const cVal = (k) => metric === 'aff' ? -eff.cf.aff[k] : eff.cf.sep[k];

  // domain over baseline + the cf branch
  let lo = Infinity, hi = -Infinity;
  for (const m of BASE_MACRO) { const v = bVal(m); if (v < lo) lo = v; if (v > hi) hi = v; }
  for (let k = 0; k < eff.cf.sep.length; k++) { const v = cVal(k); if (v < lo) lo = v; if (v > hi) hi = v; }
  const pad = (hi - lo) * 0.1 || 0.05; lo -= pad; hi += pad;

  const X = (t) => padL + (t / LAST) * plotW;
  const Y = (v) => padT + plotH - ((v - lo) / (hi - lo || 1)) * plotH;
  const toPath = (pts) => pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');

  const basePts = BASE_MACRO.map((m, t) => [X(t), Y(bVal(m))]);
  const rt = eff.releaseTick;
  const cfPts = [];
  for (let k = 0; k < eff.cf.sep.length; k++) cfPts.push([X(rt + k), Y(cVal(k))]);

  const col = _bucketCol(eff.bucket);
  const relYear = Math.round(1980 + rt / 3);
  const axisLabel = metric === 'aff' ? 'Affective polarization (colder → up)' : 'Party separation (wider → up)';

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={height} preserveAspectRatio="xMidYMid meet" style={{ display: 'block' }}>
        {/* release marker */}
        <line x1={X(rt)} y1={padT - 2} x2={X(rt)} y2={padT + plotH} stroke={CC.ink4} strokeWidth="1" strokeDasharray="1 3" />
        <text x={X(rt) + 3} y={padT + 7} style={{ fontFamily: MONO, fontSize: 9, fill: CC.ink4, ...TNUM }}>{relYear}</text>
        {/* baseline (what actually happened) */}
        <path d={toPath(basePts)} fill="none" stroke={CC.ink3} strokeWidth="1.8" strokeLinejoin="round" strokeLinecap="round" />
        {/* counterfactual branch — only once revealed */}
        {revealed && <path d={toPath(cfPts)} fill="none" stroke={col} strokeWidth="2.4" strokeLinejoin="round" strokeLinecap="round" strokeDasharray={eff.bucket === 'null' ? '4 3' : 'none'} />}
        <text x={padL} y={height - 5} style={{ fontFamily: SANS, fontSize: 9.5, fill: CC.ink4 }}>1980</text>
        <text x={width - padR} y={height - 5} textAnchor="end" style={{ fontFamily: SANS, fontSize: 9.5, fill: CC.ink4 }}>2025</text>
      </svg>
      <div style={{ display: 'flex', gap: 16, marginTop: 4, fontSize: DS.type.micro, color: CC.ink3 }}>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}><span style={{ width: 16, height: 0, borderTop: `1.8px solid ${CC.ink3}` }} /> what happened</span>
        {revealed && <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}><span style={{ width: 16, height: 0, borderTop: `2.4px ${eff.bucket === 'null' ? 'dashed' : 'solid'} ${col}` }} /> if we’d intervened</span>}
      </div>
      <Caption style={{ display: 'block', marginTop: 5 }}>{axisLabel}. Single representative run (seed 0).</Caption>
    </div>
  );
}

// ── the "effect by decade enacted" sparkline (X5's decade-dependence, §3.4) ──
function DecadeSparkline({ id, year, onPick, width = 392, height = 64 }) {
  const padL = 4, padR = 4, padT = 8, padB = 16;
  const plotW = width - padL - padR, plotH = height - padT - padB;
  const pts = RELEASE_YEARS.map((y) => ({ y, imp: improvementAt(id, y), bucket: bucketAt(id, y) }));
  let lo = 0, hi = 0;
  for (const p of pts) { if (p.imp < lo) lo = p.imp; if (p.imp > hi) hi = p.imp; }
  const span = Math.max(0.12, hi - lo); lo -= span * 0.15; hi += span * 0.15;
  const X = (i) => padL + (i / (RELEASE_YEARS.length - 1)) * plotW;
  const Y = (v) => padT + plotH - ((v - lo) / (hi - lo || 1)) * plotH;
  const zeroY = Y(0);
  return (
    <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={height} preserveAspectRatio="xMidYMid meet" style={{ display: 'block' }}>
      <line x1={padL} y1={zeroY} x2={width - padR} y2={zeroY} stroke={CC.border} strokeWidth="1" strokeDasharray="2 3" />
      <text x={width - padR} y={zeroY - 3} textAnchor="end" style={{ fontFamily: SANS, fontSize: 8.5, fill: CC.ink4 }}>no effect</text>
      {pts.map((p, i) => {
        const on = p.y === year;
        const col = _bucketCol(p.bucket);
        return (
          <g key={p.y} style={{ cursor: 'pointer' }} onClick={() => onPick(p.y)}>
            <line x1={X(i)} y1={zeroY} x2={X(i)} y2={Y(p.imp)} stroke={col} strokeWidth={on ? 2.4 : 1.4} opacity={on ? 1 : 0.55} />
            <circle cx={X(i)} cy={Y(p.imp)} r={on ? 4 : 2.6} fill={col} opacity={on ? 1 : 0.6} stroke={on ? '#fff' : 'none'} strokeWidth="1.5" />
            <text x={X(i)} y={height - 4} textAnchor="middle" style={{ fontFamily: MONO, fontSize: 8, fontWeight: on ? 600 : 400, fill: on ? CC.ink : CC.ink4, ...TNUM }}>{p.y.slice(2)}</text>
          </g>
        );
      })}
    </svg>
  );
}

// big tappable bet button used in the predict gate
function BetButton({ g, onClick }) {
  const [hov, setHov] = React.useState(false);
  return (
    <button onClick={onClick} onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)} style={{
      textAlign: 'left', width: '100%', padding: '13px 15px', cursor: 'pointer', fontFamily: SANS,
      background: hov ? CC.surface : CC.bg, borderRadius: DS.rad.inset,
      border: `1px solid ${hov ? CC.ink : CC.borderS}`,
      boxShadow: hov ? '0 2px 8px rgba(26,29,35,.08)' : 'none',
      display: 'flex', alignItems: 'center', gap: 13, transition: 'border-color .12s, box-shadow .12s, background .12s',
    }}>
      <span style={{
        width: 26, height: 26, flexShrink: 0, borderRadius: DS.rad.pill, border: `1.5px solid ${hov ? CC.ink : CC.ink4}`,
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, color: hov ? CC.ink : CC.ink3,
      }}>{g.key === 'help' ? '↓' : g.key === 'backfire' ? '↑' : '→'}</span>
      <span style={{ flex: 1 }}>
        <span style={{ display: 'block', fontSize: DS.type.body, fontWeight: 600, color: CC.ink }}>{g.label}</span>
        <span style={{ display: 'block', fontSize: DS.type.micro, color: CC.ink3, marginTop: 1 }}>{g.sub}</span>
      </span>
    </button>
  );
}

function DeltaStat({ label, v, helpfulSign, max = 0.4 }) {
  // helpfulSign: -1 means negative is good (sep); +1 means positive is good (aff)
  const good = v != null && v * helpfulSign > 0.005 && Math.abs(v) >= 0.05;
  const bad = v != null && v * helpfulSign < -0.005 && Math.abs(v) >= 0.05;
  const col = v == null ? CC.ink4 : bad ? CC.r : good ? '#3f7d54' : CC.ink3;
  const arrow = v == null ? '' : v > 0.005 ? '↑' : v < -0.005 ? '↓' : '→';
  const txt = v == null ? '—' : (v > 0 ? '+' : '') + (+v).toFixed(3);
  const mag = v == null ? 0 : _clampN(0, 1, Math.abs(v) / max);
  return (
    <div style={{ flex: 1, minWidth: 0 }}>
      <div style={{ fontSize: DS.type.micro, color: CC.ink3 }}>{label}</div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginTop: 5 }}>
        <span style={{ fontFamily: SERIF, fontWeight: 600, fontSize: 26, letterSpacing: '-.01em', lineHeight: 1, color: col }}>{txt}</span>
        <span style={{ fontFamily: SANS, fontSize: 13, color: col }}>{arrow}</span>
      </div>
      <div style={{ marginTop: 9, height: 3, borderRadius: DS.rad.pill, background: CC.bg2, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${mag * 100}%`, background: col, borderRadius: DS.rad.pill, transition: 'width .15s linear' }} />
      </div>
    </div>
  );
}

function ProvBadge({ prov }) {
  const theo = prov.kind === 'theoretical';
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6, fontFamily: SANS, fontSize: 10, fontWeight: 600,
      letterSpacing: '.05em', textTransform: 'uppercase', color: theo ? '#8a6d1f' : CC.ink2,
      background: theo ? 'rgba(196,122,44,.1)' : CC.bg2, border: `1px solid ${theo ? 'rgba(196,122,44,.35)' : CC.border}`,
      borderRadius: DS.rad.pill, padding: '3px 9px',
    }}>
      <span style={{ width: 6, height: 6, borderRadius: DS.rad.pill, background: theo ? '#c47a2c' : '#3f7d54' }} />
      {prov.label}
    </span>
  );
}

// ── RIGHT RAIL ────────────────────────────────────────────────────────────────
function IvRail({ iv }) {
  const { eff, o, baseGap, nowGap, active, predicting, showResult, guess, correct, isSandbox, sbEff } = iv;

  // ── SANDBOX surface — visually walled off, never a finding ──
  if (isSandbox) {
    return (
      <div style={{ background: 'transparent', display: 'flex', flexDirection: 'column', minHeight: 0, height: '100%' }}>
        <div style={{ flex: 1, overflow: 'auto', padding: `${DS.sp.lg - 6}px ${DS.sp.lg - 2}px` }}>
          <div style={{ padding: '10px 13px', borderRadius: DS.rad.inset, background: 'rgba(196,122,44,.08)', border: '1px dashed rgba(196,122,44,.4)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 13 }}>{'⚠︎'}</span>
              <span style={{ fontFamily: SANS, fontSize: DS.type.small, fontWeight: 700, color: '#8a6d1f', letterSpacing: '.04em', textTransform: 'uppercase' }}>Sandbox — not a finding</span>
            </div>
            <p style={{ margin: '7px 0 0', fontSize: DS.type.micro, lineHeight: 1.5, color: CC.ink2 }}>
              These scenarios crank the model’s own knobs past anything we’d calibrate. The field response is <strong>illustrative</strong> — it changes the model, not a real-world policy, and owes the X1–X7 re-bless gate before it could be called measured.
            </p>
          </div>

          <Eyebrow style={{ marginTop: 22, display: 'block' }}>What-if scenarios</Eyebrow>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5, marginTop: 10 }}>
            {SB_SCENARIOS.map((s) => {
              const on = iv.sbId === s.id;
              return (
                <button key={s.id} onClick={() => iv.pickScenario(s.id)} style={{
                  textAlign: 'left', width: '100%', padding: '9px 12px', cursor: 'pointer', fontFamily: SANS,
                  background: on ? CC.surface : 'transparent', borderRadius: DS.rad.inset,
                  border: `1px solid ${on ? CC.borderS : 'transparent'}`,
                  fontSize: DS.type.small, fontWeight: on ? 600 : 450, color: on ? CC.ink : CC.ink2,
                }}>{s.name}</button>
              );
            })}
          </div>

          <Eyebrow style={{ marginTop: 22, display: 'block' }}>Or tinker freely</Eyebrow>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 15, marginTop: 12 }}>
            {SB_SLIDERS.map((s) => <Detent key={s.key} s={s} value={iv.tv[s.key]} onChange={(k) => iv.setKnob(s.key, k)} />)}
          </div>

          {sbEff && (
            <div style={{ marginTop: 22, paddingTop: 18, borderTop: `1px solid ${CC.border}` }}>
              <h3 style={{ margin: 0, fontFamily: SERIF, fontWeight: 600, fontSize: DS.type.subhead }}>{sbEff.name}</h3>
              <p style={{ margin: '8px 0 0', fontSize: DS.type.body, lineHeight: 1.55, color: CC.ink }}>{sbEff.take}</p>
              <Caption style={{ display: 'block', marginTop: 10 }}>Illustrative spread — not an engine measurement.</Caption>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ── empty state ──
  if (!active) {
    return (
      <div style={{ background: 'transparent', display: 'flex', flexDirection: 'column', minHeight: 0, height: '100%' }}>
        <div style={{ flex: 1, overflow: 'auto', padding: `${DS.sp.lg - 6}px ${DS.sp.lg - 2}px` }}>
          <Eyebrow>The experiment</Eyebrow>
          <h2 style={{ margin: '12px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: DS.type.title, lineHeight: 1.08, letterSpacing: '-.015em' }}>Could anything have stopped it?</h2>
          <p style={{ margin: '16px 0 0', ...PROSE, color: CC.ink2 }}>Researchers have tried — exposure programs, media diets, voting reform, contact. Most do less than you’d think. One backfires. The one that works isn’t the obvious one.</p>
          <p style={{ margin: '14px 0 0', ...PROSE, color: CC.ink2 }}>Pick an intervention on the left, <strong>call what it does before you run it</strong>, then watch the model answer — and try changing <em>when</em> it was tried.</p>
          <div style={{ marginTop: 22, padding: '13px 15px', background: CC.surface, border: `1px solid ${CC.border}`, borderRadius: DS.rad.inset }}>
            <Caption>Your hunches get scored. The interesting ones are where you’re wrong.</Caption>
          </div>
        </div>
      </div>
    );
  }

  // ── predict gate ──
  if (predicting) {
    return (
      <div style={{ background: 'transparent', display: 'flex', flexDirection: 'column', minHeight: 0, height: '100%' }}>
        <div style={{ flex: 1, overflow: 'auto', padding: `${DS.sp.lg - 6}px ${DS.sp.lg - 2}px` }}>
          <Eyebrow>Your call · before the run</Eyebrow>
          <h2 style={{ margin: '12px 0 16px', fontFamily: SERIF, fontWeight: 600, fontSize: DS.type.title, lineHeight: 1.05, letterSpacing: '-.015em' }}>{active.label}</h2>
          <div style={{ marginBottom: 18, padding: '12px 14px', background: CC.surface, border: `1px solid ${CC.border}`, borderRadius: DS.rad.inset }}>
            <ReleaseSelector year={iv.releaseYear} onPick={iv.setReleaseYear} />
          </div>
          <p style={{ margin: '0 0 16px', fontSize: DS.type.body, lineHeight: 1.55, color: CC.ink2 }}>If we’d actually done this in {iv.releaseYear}, what happens by 2025?</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
            <BetButton g={{ ...GUESS.help, key: 'help' }} onClick={() => iv.submitGuess('help')} />
            <BetButton g={{ ...GUESS.none, key: 'none' }} onClick={() => iv.submitGuess('none')} />
            <BetButton g={{ ...GUESS.backfire, key: 'backfire' }} onClick={() => iv.submitGuess('backfire')} />
          </div>
          <p style={{ margin: '16px 0 0', fontSize: DS.type.micro, lineHeight: 1.5, color: CC.ink4 }}>The field is frozen at today until you commit. Pick one to run the model.</p>
        </div>
      </div>
    );
  }

  // ── revealed result ──
  const metric = eff.metric;
  const helpfulSign = metric === 'aff' ? 1 : -1;
  const actualVerb = VERB[metric][bucketToBet(eff.bucket)];
  const guessLabel = guess ? GUESS[guess].label.toLowerCase() : '';
  return (
    <div style={{ background: 'transparent', display: 'flex', flexDirection: 'column', minHeight: 0, height: '100%' }}>
      <div style={{ flex: 1, overflow: 'auto', padding: `${DS.sp.lg - 6}px ${DS.sp.lg - 2}px` }}>
        {guess != null && (
          <div style={{
            marginBottom: 18, padding: '12px 14px', borderRadius: DS.rad.inset,
            background: correct ? 'rgba(63,125,84,.08)' : (eff.bucket === 'backfire' ? CC.rSoft : CC.bg2),
            border: `1px solid ${correct ? 'rgba(63,125,84,.3)' : (eff.bucket === 'backfire' ? CC.rLine : CC.borderS)}`,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 14, color: correct ? '#3f7d54' : CC.r, fontWeight: 700 }}>{correct ? '✓' : '✗'}</span>
              <span style={{ fontFamily: SANS, fontSize: DS.type.small, fontWeight: 600, color: correct ? '#2f6a42' : CC.ink }}>
                {correct ? 'You called it.' : 'Not what most expect.'}
              </span>
            </div>
            <p style={{ margin: '6px 0 0', fontSize: DS.type.small, lineHeight: 1.5, color: CC.ink2 }}>
              You bet <strong>{guessLabel}</strong>. The model says it {actualVerb}.
            </p>
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <Eyebrow>Modeled effect · released {iv.releaseYear}</Eyebrow>
          {o && <Tag tone={o.tone}>{o.label}</Tag>}
        </div>
        <h2 style={{ margin: '12px 0 0', fontFamily: SERIF, fontWeight: 600, fontSize: DS.type.title, lineHeight: 1.05, letterSpacing: '-.015em' }}>{eff.name}</h2>
        <div style={{ marginTop: 10 }}><ProvBadge prov={eff.prov} /></div>

        <p style={{ margin: '16px 0 0', ...PROSE, color: CC.ink }}>{eff.take}</p>
        {eff.caveat && (
          <p style={{ margin: '10px 0 0', padding: '9px 11px', fontSize: DS.type.small, lineHeight: 1.5, color: CC.ink2, background: CC.bg2, borderRadius: DS.rad.inset, borderLeft: `2px solid ${CC.ink4}` }}>{eff.caveat}</p>
        )}

        {/* release-year control stays available so the user can explore "when" */}
        <div style={{ marginTop: 18, padding: '12px 14px', background: CC.surface, border: `1px solid ${CC.border}`, borderRadius: DS.rad.inset }}>
          <ReleaseSelector year={iv.releaseYear} onPick={iv.setReleaseYear} />
        </div>

        <div style={{ height: 1, background: CC.border, margin: '20px 0' }} />

        {/* the real counterfactual trajectory */}
        <Eyebrow style={{ color: CC.ink3 }}>The two futures</Eyebrow>
        <div style={{ marginTop: 12 }}><GhostChart eff={eff} revealed /></div>

        {/* decade-dependence — the lesson that it depends WHEN you act */}
        <div style={{ marginTop: 18 }}>
          <Eyebrow style={{ color: CC.ink3 }}>Effect by decade enacted</Eyebrow>
          <div style={{ marginTop: 8 }}><DecadeSparkline id={eff.id} year={iv.releaseYear} onPick={iv.setReleaseYear} /></div>
          <p style={{ margin: '4px 0 0', fontSize: DS.type.micro, lineHeight: 1.5, color: CC.ink3 }}>
            {eff.varies
              ? (eff.id === 'X5_ranked_choice_voting'
                ? 'Structural reform helps — but only in some windows. Tap a decade to see it flip.'
                : 'The effect depends on when it’s enacted. Tap a decade to compare.')
              : 'Steady across decades — the result barely depends on when it’s tried.'}
          </p>
        </div>

        <div style={{ height: 1, background: CC.border, margin: '20px 0' }} />

        <Eyebrow style={{ color: CC.ink3 }}>Where the country lands</Eyebrow>
        <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 7 }}>
              <span style={{ fontSize: DS.type.small, color: CC.ink2 }}>Party gap at 2025</span>
              <span style={{ display: 'inline-flex', alignItems: 'baseline', gap: 7 }}>
                <MonoVal size={DS.type.small} color={CC.ink4}>{baseGap.toFixed(2)}</MonoVal>
                <span style={{ color: CC.ink4, fontSize: 12 }}>→</span>
                <MonoVal size={DS.type.body} color={nowGap > baseGap + 0.01 ? CC.r : nowGap < baseGap - 0.01 ? '#3f7d54' : CC.ink} weight={600}>{nowGap.toFixed(2)}</MonoVal>
              </span>
            </div>
            <div style={{ height: 8, borderRadius: DS.rad.pill, background: CC.bg2, overflow: 'hidden', position: 'relative' }}>
              <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: `${_clampN(0, 1, baseGap / 2) * 100}%`, background: CC.ink4, opacity: 0.5 }} />
              <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: `${_clampN(0, 1, nowGap / 2) * 100}%`, background: nowGap > baseGap + 0.01 ? CC.r : '#3f7d54', borderRadius: DS.rad.pill, transition: 'width .15s linear' }} />
            </div>
          </div>

          <div style={{ display: 'flex', gap: 22, alignItems: 'stretch' }}>
            <DeltaStat label="Δ party gap" v={eff.dSep} helpfulSign={-1} />
            <div style={{ width: 1, background: CC.border, flexShrink: 0 }} />
            <DeltaStat label="Δ out-party warmth" v={eff.dAff} helpfulSign={1} />
          </div>
          <p style={{ margin: 0, fontSize: DS.type.micro, lineHeight: 1.5, color: CC.ink3 }}>
            Helpful = a <span style={{ color: '#3f7d54' }}>smaller party gap</span> or <span style={{ color: '#3f7d54' }}>warmer feelings</span> toward the other side. Δ vs. no intervention, ~10 years out. Single representative run.
          </p>
        </div>
      </div>
    </div>
  );
}

// Detent knob — the site's timeline grammar in miniature: a hairline track,
// quiet ticks at the stops, ink up to a hollow playhead ring at the active
// detent. The mono readout (top-right) carries the exact value, so the track
// stays wordless. Click anywhere or DRAG the head — pointer x snaps to the
// nearest detent (the ProtoTimeline scrub pattern). Arrow keys step it too.
function Detent({ s, value, onChange }) {
  const n = s.stops.length - 1;
  const ref = React.useRef(null);
  const cx = (k) => `calc(6px + ${(k / n) * 100}% - ${(k / n) * 12}px)`; // centre of stop k
  const pickAt = (clientX) => {
    const r = ref.current.getBoundingClientRect();
    const frac = (clientX - r.left - 6) / Math.max(1, r.width - 12);
    onChange(Math.round(Math.max(0, Math.min(1, frac)) * n));
  };
  const onDown = (e) => {
    e.preventDefault();
    if (ref.current) ref.current.focus();
    pickAt(e.clientX);
    const mv = (ev) => pickAt(ev.clientX);
    const up = () => { window.removeEventListener('pointermove', mv); window.removeEventListener('pointerup', up); };
    window.addEventListener('pointermove', mv);
    window.addEventListener('pointerup', up);
  };
  const onKey = (e) => {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') { e.preventDefault(); onChange(Math.max(0, value - 1)); }
    if (e.key === 'ArrowRight' || e.key === 'ArrowUp') { e.preventDefault(); onChange(Math.min(n, value + 1)); }
  };
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <span style={{ fontSize: DS.type.small, fontWeight: 500, color: CC.ink }}>{s.name}</span>
        <MonoVal size={DS.type.micro} color={CC.ink} weight={600}>{s.stops[value]}</MonoVal>
      </div>
      <div ref={ref} onPointerDown={onDown} onKeyDown={onKey} tabIndex={0} role="slider"
        aria-label={s.name} aria-valuemin={0} aria-valuemax={n} aria-valuenow={value} aria-valuetext={s.stops[value]}
        style={{ position: 'relative', height: 22, marginTop: 4, cursor: 'pointer', touchAction: 'none', outline: 'none' }}>
        <div style={{ position: 'absolute', left: 6, right: 6, top: 10, height: 1.5, background: CC.borderS, pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', left: 6, top: 10, width: `calc(${(value / n) * 100}% - ${(value / n) * 12}px)`, height: 1.5, background: CC.ink, pointerEvents: 'none', transition: 'width .12s ease' }} />
        {s.stops.map((_, k) => (k === value ? null :
          <span key={'t' + k} style={{ position: 'absolute', left: cx(k), top: 7, width: 1, height: 8, background: CC.ink4, transform: 'translateX(-50%)', pointerEvents: 'none' }} />
        ))}
        <span style={{ position: 'absolute', left: cx(value), top: 10.75, transform: 'translate(-50%,-50%)', width: 11, height: 11, boxSizing: 'border-box', borderRadius: DS.rad.pill, background: CC.bg, border: `2px solid ${CC.ink}`, pointerEvents: 'none', transition: 'left .12s ease' }} />
      </div>
    </div>
  );
}

// ── BOTTOM — hope vs. what happened (metric-aware) ───────────────────────────
function IvBottom({ iv }) {
  const { eff, predicting, showResult, isSandbox } = iv;

  if (isSandbox) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, width: '100%' }}>
        <span style={{ fontSize: 13 }}>{'⚠︎'}</span>
        <div>
          <Eyebrow style={{ color: '#8a6d1f' }}>Sandbox · illustrative</Eyebrow>
          <div style={{ marginTop: 5, fontSize: DS.type.micro, color: CC.ink3 }}>Not an engine measurement — these knobs change the model, not a policy.</div>
        </div>
      </div>
    );
  }

  if (!showResult) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 26, width: '100%' }}>
        <div style={{ flexShrink: 0 }}>
          <Eyebrow style={{ color: CC.ink3 }}>Hope vs. what happened</Eyebrow>
          <div style={{ marginTop: 6, fontSize: DS.type.micro, color: CC.ink3 }}>
            {predicting ? 'Place your bet on the right to run the model.' : 'Pick an intervention to begin.'}
          </div>
        </div>
        <div style={{ width: 1, height: 54, background: CC.border, flexShrink: 0 }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: DS.type.micro, color: CC.ink4, fontFamily: SANS, marginBottom: 7 }}>
            <span>← worse</span><span>better →</span>
          </div>
          <div style={{ position: 'relative', height: 34 }}>
            <div style={{ position: 'absolute', top: 14, left: 0, right: 0, height: 4, borderRadius: DS.rad.pill, background: CC.border }} />
            <div style={{ position: 'absolute', top: 8, left: `${_mark(0)}%`, transform: 'translateX(-50%)', width: 2, height: 16, background: CC.ink4 }} />
            <span style={{ position: 'absolute', top: -4, left: `${_mark(0)}%`, transform: 'translateX(-50%)', fontSize: 10, color: CC.ink4, fontFamily: MONO }}>today</span>
            {predicting && (
              <div style={{ position: 'absolute', top: 8, left: `${_mark(0.5)}%`, transform: 'translateX(-50%)', width: 15, height: 15, borderRadius: DS.rad.pill, border: `2px dashed ${CC.ink3}`, background: 'rgba(255,255,255,.7)' }} title="where people hope it lands" />
            )}
          </div>
        </div>
      </div>
    );
  }

  const hope = 0.5;                 // the naive hope is always "it helps"
  const actual = _clampN(-0.6, 1, eff.improvement * 2.4); // headline improvement, scaled to the track
  const worse = actual < -0.01;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 26, width: '100%' }}>
      <div style={{ flexShrink: 0 }}>
        <Eyebrow style={{ color: CC.ink3 }}>Hope vs. what happened</Eyebrow>
        <div style={{ marginTop: 6, display: 'flex', gap: 16, fontSize: DS.type.micro, color: CC.ink3 }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}><span style={{ width: 10, height: 10, borderRadius: DS.rad.pill, border: `2px dashed ${CC.ink3}` }} /> the hope</span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}><span style={{ width: 10, height: 10, borderRadius: DS.rad.pill, background: worse ? CC.r : '#3f7d54' }} /> what happened</span>
        </div>
      </div>
      <div style={{ width: 1, height: 54, background: CC.border, flexShrink: 0 }} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: DS.type.micro, color: CC.ink3, fontFamily: SANS, marginBottom: 7 }}>
          <span>← worse</span><span>better →</span>
        </div>
        <div style={{ position: 'relative', height: 34 }}>
          <div style={{ position: 'absolute', top: 14, left: 0, right: 0, height: 4, borderRadius: DS.rad.pill, background: `linear-gradient(90deg, ${CC.r}, ${CC.i}, #3f7d54)`, opacity: 0.4 }} />
          <div style={{ position: 'absolute', top: 8, left: `${_mark(0)}%`, transform: 'translateX(-50%)', width: 2, height: 16, background: CC.ink4 }} />
          <span style={{ position: 'absolute', top: -4, left: `${_mark(0)}%`, transform: 'translateX(-50%)', fontSize: 10, color: CC.ink4, fontFamily: MONO }}>today</span>
          <div style={{ position: 'absolute', top: 8, left: `${_mark(hope)}%`, transform: 'translateX(-50%)', width: 15, height: 15, borderRadius: DS.rad.pill, border: `2px dashed ${CC.ink3}`, background: 'rgba(255,255,255,.7)', transition: 'left .3s ease' }} />
          <div style={{ position: 'absolute', top: 8, left: `${_mark(actual)}%`, transform: 'translateX(-50%)', width: 15, height: 15, borderRadius: DS.rad.pill, background: worse ? CC.r : '#3f7d54', border: '2px solid #fff', boxShadow: '0 1px 5px rgba(26,29,35,.25)', transition: 'left .3s ease' }} />
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { useInterventions, IvTray, IvRail, IvBottom,
  // exported for the alternate interventions layouts (rc-iv-layouts.jsx)
  IV_ORDER, IVMETA, OUTCOME, bucketAt, RELEASE_YEARS,
  BetButton, DeltaStat, ProvBadge, ReleaseSelector, DecadeSparkline,
  GUESS, VERB, bucketToBet, improvementAt, _bucketCol, _clampN,
  SANDBOX_KNOBS, SANDBOX_PRESETS, SANDBOX_CENTER });
