// Calm to Camps — Redesign concept helpers.
// Builds on the real engine (window.CC_DATA, posAt, macroAt, tickToYear, LAST,
// partyColor, CC tokens). Adds: in-browser party-blended KDE that bleeds past
// the square compass grid, the affect "ash" ramp, the centroid "gap" motif, a
// reusable edge-to-edge <Field> canvas, and a labelled two-tier timeline.

// ── colour math ───────────────────────────────────────────────────────────
function _lerp(a, b, t) {return a + (b - a) * t;}
function _mix(c0, c1, t) {return [_lerp(c0[0], c1[0], t), _lerp(c0[1], c1[1], t), _lerp(c0[2], c1[2], t)];}
const _clamp01 = (v) => v < 0 ? 0 : v > 1 ? 1 : v;
const _smooth = (v) => {v = _clamp01(v);return v * v * (3 - 2 * v);};
const _rgb = (c, a) => `rgba(${Math.round(c[0])},${Math.round(c[1])},${Math.round(c[2])},${a})`;

const RGB_NAVY = [31, 53, 101];
const RGB_OX = [139, 37, 48];
const RGB_GREY = [150, 150, 153];
const RGB_WARM = [221, 206, 170];
const RGB_ASH = [32, 35, 41];

function partisanColor(p) {
  if (p <= 0) return _mix(RGB_GREY, RGB_NAVY, _clamp01(-p));
  return _mix(RGB_GREY, RGB_OX, _clamp01(p));
}
function ashColor(t) {return _mix(RGB_WARM, RGB_ASH, _clamp01(t));}

// Affect tint — a party field that KEEPS its hue but deepens as it cools.
// lc∈[0,1] is local out-party coldness: warm crowds read as a pale, calm
// party tint; cold crowds read as the deep, saturated party colour. This
// replaces the single warm→ash ramp (which threw party identity away), so the
// two camps stay legible *and* you can watch them cool. — affect rebuild §3.5
const RGB_INKDEEP = [22, 24, 30];
function coolParty(base, lc) {
  const pale = _mix(base, RGB_WARM, 0.5);          // low animus — calm, warm-tinted
  const deep = _mix(base, RGB_INKDEEP, 0.32);      // high animus — deep, near-ash
  return _mix(pale, deep, _clamp01(lc));
}
// Straight-alpha "source-over": paint src (rgb at alpha sa) on top of dst.
function _over(dst, src, sa) {
  const da = dst[3];
  const oa = sa + da * (1 - sa);
  if (oa < 1e-6) return [0, 0, 0, 0];
  const k = da * (1 - sa);
  return [
    (src[0] * sa + dst[0] * k) / oa,
    (src[1] * sa + dst[1] * k) / oa,
    (src[2] * sa + dst[2] * k) / oa,
    oa,
  ];
}

// ── engine-derived entities on the compass (audit §3.9, contract §entities) ──
// Everything here is the simulation's OWN data — never eyeballed. Three classes:
//   • 'party'   — live Dem/Rep centroids (ride the sim, always on)
//   • 'faction' — engine emergent factions, drawn at their real sub_centroid
//                 and TIME-GATED: nothing appears before its emergence year
//   • 'media'   — calibrated outlet positions (AllSides/Ad Fontes), gated so
//                 nothing predates its launch (Fox phases in at 1996)
// The old hand-placed politicians (Sanders/AOC/Manchin/Romney/Cruz) and the
// fake constant-offset "MAGA wing" were retired — decision C, Step 3.
const _clampN = (lo, hi, v) => v < lo ? lo : v > hi ? hi : v;

// Outlets that didn't exist for the whole run get an on-air tick. Others
// (pre-1980 papers / Local TV) are treated as always-present anchors.
const OUTLET_ON_AIR = { 'Fox News': 48 /* 1996 */, 'MSNBC': 48 /* 1996 */ };
const _leanOf = (x) => (x < -0.12 ? 'd' : x > 0.12 ? 'r' : 'i');

// Build the entity list for a given tick. `mode`:
//   'fixed' — outlets + emergent factions (the always-on reference set)
//   'all'   — also the live party-centroid labels (Explore "Show parties")
function engineEntities(tick, pos, party, mode = 'fixed') {
  const t = tick + 0.5; // half-tick grace so an entity shows on its emergence beat
  const out = [];
  for (const o of D.entities.outlets) {
    const onAir = OUTLET_ON_AIR[o.name] || 0;
    if (t < onAir) continue;
    out.push({ name: o.name, x: o.pos[0], y: o.pos[1], cls: 'media',
      lean: _leanOf(o.pos[0]), side: o.pos[0] < 0 ? 'l' : 'r' });
  }
  for (const f of D.entities.factions_emergent) {
    if (t < f.emergence_tick) continue;           // time-gate — never anachronistic
    const [x, y] = f.sub_centroid;
    out.push({ name: f.name.replace(/_/g, ' '), x, y, cls: 'faction',
      lean: _leanOf(x), side: x < 0 ? 'l' : 'r' });
  }
  if (mode === 'all') {
    const { D0, R0 } = centroids(pos, party);
    out.push({ name: 'Democratic Party', x: D0[0], y: D0[1], cls: 'party', lean: 'd', side: 'l' });
    out.push({ name: 'Republican Party', x: R0[0], y: R0[1], cls: 'party', lean: 'r', side: 'r' });
  }
  return out;
}

const _AFF = D.runs.baseline.macro.map((m) => -m.aff);
const _AFF_LO = Math.min(..._AFF),_AFF_HI = Math.max(..._AFF);
// normalized 0..1 coldness — drives the field's *relative* cooling intensity
function coldnessAt(tick) {
  const v = -macroAt(D.runs.baseline, tick, 'aff');
  return _clamp01((v - _AFF_LO) / (_AFF_HI - _AFF_LO || 1));
}
// Out-party warmth in ANES-style degrees, on the ABSOLUTE 0–100 thermometer —
// the contract mapping deg = (1 + aff)*50 + 12 (coldness = −aff), NOT the
// normalized ramp. Runs ~57° (1980) → ~33° (2025), matching the literature's
// high-50s→low-30s out-party collapse, and shares a scale with the in-party
// ANES overlay so the two can be drawn as one honest "scissors".
function outPartyDeg(tick) {return (1 + macroAt(D.runs.baseline, tick, 'aff')) * 50 + 12;}
// In-party warmth (degrees) — EXTERNAL ANES overlay, NOT engine (contract §2).
function inPartyDeg(tick) {return macroAt(D.runs.baseline, tick, 'aff_in_empirical');}
function warmthDegAt(tick) {return Math.round(outPartyDeg(tick));}

// ── per-agent affect / animus ───────────────────────────────────────────────
// Coldness per agent in [0,1] (0 = warm, 1 = cold ash). The engine doesn't yet
// carry a per-agent affect series for the whole crowd, so we synthesise a
// deterministic one: extremists run hotter, the middle stays warmer, every
// agent has a stable personal temperament + a slow individual drift. The macro
// trend (coldnessAt) still sets the overall level so the field cools over time —
// it just no longer cools *uniformly*. When the engine grows a real field
// (run.affect = [tick][agent]), we read that instead. — mock per Vlad
function _hash01(n) {const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;return x - Math.floor(x);}
function agentColdness(run, tick, pos, party) {
  const n = pos.length;
  const out = new Float32Array(n);
  // forward-compat: real per-agent affect series once the engine provides one
  const real = run.affect || null;
  if (real) {
    const t0 = Math.max(0, Math.min(LAST, Math.floor(tick))),t1 = Math.min(LAST, t0 + 1),a = tick - t0;
    for (let i = 0; i < n; i++) {
      const v = real[t0][i] + (real[t1][i] - real[t0][i]) * a;
      out[i] = _clamp01(-v); // engine warmth is negative; coldness is its magnitude
    }
    return out;
  }
  const g = coldnessAt(tick);
  for (let a = 0; a < n; a++) {
    const ext = _clamp01(Math.hypot(pos[a][0], pos[a][1]) / 1.05); // distance from centre
    const h = _hash01(a + 1); // stable temperament 0..1
    const partyGain = party[a] === 2 ? 0.55 : 1; // independents carry less animus
    const drift = 0.1 * Math.sin(tick * 0.045 + h * 6.2832); // slow personal wobble
    const c = g * (0.3 + 1.05 * ext) * partyGain + (h - 0.5) * 0.36 + drift;
    out[a] = _clamp01(c);
  }
  return out;
}

// ── density (in-browser KDE over an arbitrary world bbox) ────────────────────
function computeDensity(pos, party, box, affect = null) {
  const { x0, x1, y0, y1, Gx, Gy, bw } = box;
  const dD = new Float32Array(Gx * Gy),dR = new Float32Array(Gx * Gy),dI = new Float32Array(Gx * Gy);
  // dA = density-weighted sum of per-agent coldness; dA[k]/total = local mean
  // affect. dAD/dAR split it by party so each camp can be tinted by ITS OWN
  // animus (the asymmetry the single ash ramp erased). — affect rebuild §3.5
  const dA = affect ? new Float32Array(Gx * Gy) : null;
  const dAD = affect ? new Float32Array(Gx * Gy) : null;
  const dAR = affect ? new Float32Array(Gx * Gy) : null;
  const inv = 1 / (2 * bw * bw);
  const cwx = (x1 - x0) / (Gx - 1),cwy = (y1 - y0) / (Gy - 1);
  const radx = Math.ceil(bw * 3 / cwx),rady = Math.ceil(bw * 3 / cwy);
  for (let a = 0; a < pos.length; a++) {
    const wx = pos[a][0],wy = pos[a][1];
    const ci = Math.round((wx - x0) / cwx),cj = Math.round((wy - y0) / cwy);
    const g = party[a] === 0 ? dD : party[a] === 1 ? dR : dI;
    const av = dA ? affect[a] : 0;
    for (let j = Math.max(0, cj - rady); j <= Math.min(Gy - 1, cj + rady); j++) {
      const yy = y0 + j * cwy;
      for (let i = Math.max(0, ci - radx); i <= Math.min(Gx - 1, ci + radx); i++) {
        const xx = x0 + i * cwx;
        const dx = xx - wx,dy = yy - wy;
        const w = Math.exp(-(dx * dx + dy * dy) * inv);
        const k = j * Gx + i;
        g[k] += w;
        if (dA) {
          dA[k] += w * av;
          if (party[a] === 0) dAD[k] += w * av;else
          if (party[a] === 1) dAR[k] += w * av;
        }
      }
    }
  }
  let max = 0,maxD = 0,maxR = 0;
  for (let k = 0; k < Gx * Gy; k++) {
    const t = dD[k] + dR[k] + dI[k];if (t > max) max = t;
    if (dD[k] > maxD) maxD = dD[k];if (dR[k] > maxR) maxR = dR[k];
  }
  return { dD, dR, dI, dA, dAD, dAR, max, maxD, maxR, Gx, Gy };
}

function _isx(lev, va, vb) {const d = vb - va;return d === 0 ? 0.5 : (lev - va) / d;}
function marchingSquares(grid, Gx, Gy, level) {
  const segs = [];
  for (let j = 0; j < Gy - 1; j++) {
    for (let i = 0; i < Gx - 1; i++) {
      const va = grid[j * Gx + i],vb = grid[j * Gx + i + 1],vc = grid[(j + 1) * Gx + i + 1],vd = grid[(j + 1) * Gx + i];
      let id = 0;if (va > level) id |= 1;if (vb > level) id |= 2;if (vc > level) id |= 4;if (vd > level) id |= 8;
      if (id === 0 || id === 15) continue;
      const AB = [i + _isx(level, va, vb), j],BC = [i + 1, j + _isx(level, vb, vc)];
      const CD = [i + _isx(level, vd, vc), j + 1],DA = [i, j + _isx(level, va, vd)];
      const P = (p, q) => segs.push([p[0], p[1], q[0], q[1]]);
      switch (id) {
        case 1:case 14:P(DA, AB);break;
        case 2:case 13:P(AB, BC);break;
        case 3:case 12:P(DA, BC);break;
        case 4:case 11:P(BC, CD);break;
        case 5:P(DA, AB);P(BC, CD);break;
        case 6:case 9:P(AB, CD);break;
        case 7:case 8:P(DA, CD);break;
        case 10:P(AB, BC);P(CD, DA);break;
      }
    }
  }
  return segs;
}

function centroids(pos, party) {
  let dx = 0,dy = 0,dn = 0,rx = 0,ry = 0,rn = 0;
  for (let i = 0; i < pos.length; i++) {
    if (party[i] === 0) {dx += pos[i][0];dy += pos[i][1];dn++;} else
    if (party[i] === 1) {rx += pos[i][0];ry += pos[i][1];rn++;}
  }
  const D0 = dn ? [dx / dn, dy / dn] : [0, 0];
  const R0 = rn ? [rx / rn, ry / rn] : [0, 0];
  return { D0, R0, gap: Math.hypot(R0[0] - D0[0], R0[1] - D0[1]) };
}

// ── the shared field canvas (edge-to-edge; square grid; field bleeds past it) ─
function Field({ run, tick, layer = 'position', view = 'density', showGap = true, dim = 0, transform = null, landmarks = false, reveal = null, morphT = null, chrome = true, compact = false, quadrants = true }) {
  // `reveal` (array of layer names) stages the first Watch chapter element by
  // element. null = draw everything, exactly as before.
  // `morphT` crossfades the two representations of the SAME positions on one
  // canvas: 0 = individual dots (the intro), 1 = density clouds (the story).
  // null = no morph; `view` alone decides ('dots' or 'density').
  const show = (k) => !reveal || reveal.indexOf(k) !== -1;
  const ref = React.useRef(null);
  const wrapRef = React.useRef(null);
  const [sz, setSz] = React.useState({ w: 800, h: 600 });
  React.useEffect(() => {
    const el = wrapRef.current;if (!el) return;
    const measure = () => {
      const r = el.getBoundingClientRect();
      const w = Math.round(r.width),h = Math.round(r.height);
      setSz((p) => Math.abs(p.w - w) > 2 || Math.abs(p.h - h) > 2 ? { w, h } : p);
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  React.useEffect(() => {
    const cv = ref.current;if (!cv) return;
    const safeTick = Number.isFinite(tick) ? Math.max(0, Math.min(LAST, tick)) : 0;
    const ctx = cv.getContext('2d');
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const W = sz.w,H = sz.h;
    if (W < 40 || H < 40) return;
    if (cv.width !== W * dpr) {cv.width = W * dpr;cv.height = H * dpr;}
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);

    // centered square grid (this is "the viz" the eye reads)
    const m = Math.min(W, H) * 0.11;
    const S = Math.min(W, H) - 2 * m;
    const sx = (W - S) / 2,sy = (H - S) / 2;
    const mx = (x) => sx + (x + 1) / 2 * S;
    const my = (y) => sy + S - (y + 1) / 2 * S;
    // `compact` shrinks all chrome (labels + markers) for the mobile story's
    // small compass, where the default sizes read as oversized.
    const _ck = compact ? 0.78 : 1, _mk = compact ? 0.74 : 1;
    const fq = _ck * Math.max(11, Math.min(15.5, S * 0.03)),fa = _ck * Math.max(10, Math.min(13.5, S * 0.026));
    // world coords of the full canvas rect (the field bleeds across all of it)
    const x0 = (0 - sx) / S * 2 - 1,x1 = (W - sx) / S * 2 - 1;
    const y0 = (sy + S - H) / S * 2 - 1,y1 = (sy + S - 0) / S * 2 - 1;

    let pos = posAt(run, safeTick);
    // T-VIZ: cohort-replacement crossfade — NO glide across the splice.
    // A replacement_event [te, a] means the old occupant's last frame is
    // pos[te] and the NEW occupant first appears at pos[te+1] (the big jump is
    // te->te+1, verified). posAt() would interpolate straight across that
    // splice, drawing the dot gliding across the whole compass. Instead we HOLD
    // the old occupant at pos[te] (so neither the KDE nor the base dot streaks)
    // and fade the new occupant in at pos[te+1] below — death-fade / birth-fade.
    const tFloor = Math.floor(safeTick);
    const splitFrac = safeTick - tFloor;            // 0..1 within the splice
    const replacing = (splitFrac > 0 && tFloor < LAST && run.replacement_events)
      ? run.replacement_events.filter(([t]) => t === tFloor).map(([, a]) => a)
      : [];
    const replSet = replacing.length ? new Set(replacing) : null;
    let posIn = null;                                // new occupants' positions
    if (replSet) {
      posIn = posAt(run, tFloor + 1);                // == pos[te+1] cloud
      for (const a of replacing) pos[a] = run.pos[tFloor][a];  // hold old, no glide
    }
    if (transform) { pos = transform(pos); if (posIn) posIn = transform(posIn); }
    const party = run.party[Math.round(safeTick)];
    // representation crossfade: density alpha vs dot alpha (see prop docs above)
    const denA = morphT == null ? (view === 'dots' ? 0 : 1) : Math.max(0, Math.min(1, morphT));
    const dotA = morphT == null ? (view === 'dots' ? 1 : 0) : 1 - denA;
    const cold = coldnessAt(safeTick);
    // per-agent coldness drives the affect view so the camps cool at different rates
    const affArr = layer === 'affect' ? agentColdness(run, safeTick, pos, party) : null;

    // supporting grid recedes & fades; primary axes extend past the square & fade
    const fadeLine = (x1, y1, x2, y2, rgb, wid, inset) => {
      const g = ctx.createLinearGradient(x1, y1, x2, y2);
      g.addColorStop(0, `rgba(${rgb},0)`);g.addColorStop(inset, `rgba(${rgb},1)`);
      g.addColorStop(1 - inset, `rgba(${rgb},1)`);g.addColorStop(1, `rgba(${rgb},0)`);
      ctx.strokeStyle = g;ctx.lineWidth = wid;ctx.beginPath();ctx.moveTo(x1, y1);ctx.lineTo(x2, y2);ctx.stroke();
    };
    const BORD = '224,221,211',BORDS = '193,188,176';
    if (show('axes')) {
      [-0.5, 0.5].forEach((g) => {
        fadeLine(mx(g), my(-0.84), mx(g), my(0.84), BORD, 1, 0.14);
        fadeLine(mx(-0.84), my(g), mx(0.84), my(g), BORD, 1, 0.14);
      });
      fadeLine(mx(0), my(-1.14), mx(0), my(1.14), BORDS, 1.4, 0.07);
      fadeLine(mx(-1.14), my(0), mx(1.14), my(0), BORDS, 1.4, 0.07);
    }

    // KDE over the full canvas bbox
    const cell = 2 / 57; // world units per cell (matches old square resolution)
    const Gx = Math.min(150, Math.max(20, Math.round((x1 - x0) / cell) + 1));
    const Gy = Math.min(150, Math.max(20, Math.round((y1 - y0) / cell) + 1));
    const den = computeDensity(pos, party, { x0, x1, y0, y1, Gx, Gy, bw: 0.135 }, affArr);

    if (show('blobs') && denA > 0.01) {
    const off = document.createElement('canvas');off.width = Gx;off.height = Gy;
    const octx = off.getContext('2d');const img = octx.createImageData(Gx, Gy);
    // TWO overlapping party-coloured fields — Dem (navy) and Rep (oxblood) each
    // keep their own hue, composited source-over so the two camps stay legible
    // and the overlap zone reads as the (honest) contested middle, instead of
    // the old single blended KDE that melted both lumps into one grey smear.
    // Independents wash in as a faint neutral underlay. In affect mode the same
    // two fields DEEPEN with each camp's own out-party coldness (§3.5/§3.6).
    for (let j = 0; j < Gy; j++) {
      for (let i = 0; i < Gx; i++) {
        const idx = j * Gx + i;
        const nD = den.dD[idx] / (den.maxD || 1);
        const nR = den.dR[idx] / (den.maxR || 1);
        const nI = den.dI[idx] / (den.max || 1);
        let colD, colR;
        if (layer === 'affect') {
          const lcD = den.dD[idx] > 1e-6 ? _clamp01(den.dAD[idx] / den.dD[idx]) : cold;
          const lcR = den.dR[idx] > 1e-6 ? _clamp01(den.dAR[idx] / den.dR[idx]) : cold;
          colD = coolParty(RGB_NAVY, lcD);colR = coolParty(RGB_OX, lcR);
        } else {
          colD = RGB_NAVY;colR = RGB_OX;
        }
        const aI = _smooth(Math.pow(_clamp01(nI), 0.7)) * 0.30;
        const aD = _smooth(Math.pow(_clamp01(nD), 0.72)) * 0.80;
        const aR = _smooth(Math.pow(_clamp01(nR), 0.72)) * 0.80;
        // paper → independents → rep → dem (source-over, straight alpha)
        let px4 = [0, 0, 0, 0];
        px4 = _over(px4, RGB_GREY, aI);
        px4 = _over(px4, colR, aR);
        px4 = _over(px4, colD, aD);
        const py = Gy - 1 - j;
        const o = (py * Gx + i) * 4;
        img.data[o] = px4[0];img.data[o + 1] = px4[1];img.data[o + 2] = px4[2];img.data[o + 3] = px4[3] * 255;
      }
    }
    octx.putImageData(img, 0, 0);
    ctx.imageSmoothingEnabled = true;ctx.imageSmoothingQuality = 'high';
    ctx.globalAlpha = denA;
    ctx.drawImage(off, 0, 0, W, H);
    ctx.globalAlpha = 1;

    // Light contour edges — just TWO levels per camp, so the filled heatmap
    // leads and the lines only give the lumps a soft edge (the old four-level
    // pass read as busy noise — §3.6).
    if (denA > 0.45) {
      ctx.globalAlpha = denA;
      const gpx = (gi) => gi / (Gx - 1) * W;
      const gpy = (gj) => (1 - gj / (Gy - 1)) * H;
      const drawC = (grid, gmax, colorFn) => {
        [0.22, 0.52].forEach((f, li) => {
          const lev = f * gmax;
          const segs = marchingSquares(grid, Gx, Gy, lev);
          ctx.beginPath();
          for (let s = 0; s < segs.length; s++) {const g = segs[s];ctx.moveTo(gpx(g[0]), gpy(g[1]));ctx.lineTo(gpx(g[2]), gpy(g[3]));}
          ctx.strokeStyle = colorFn(li, lev);ctx.lineWidth = 1 + li * 0.4;ctx.lineJoin = 'round';ctx.lineCap = 'round';ctx.stroke();
        });
      };
      if (layer === 'affect') {
        drawC(den.dD, den.maxD, (li) => `rgba(20,22,28,${0.16 + li * 0.12})`);
        drawC(den.dR, den.maxR, (li) => `rgba(20,22,28,${0.16 + li * 0.12})`);
      } else {
        drawC(den.dD, den.maxD, (li) => `rgba(31,53,101,${0.28 + li * 0.16})`);
        drawC(den.dR, den.maxR, (li) => `rgba(139,37,48,${0.28 + li * 0.16})`);
      }
      ctx.globalAlpha = 1;
    }
    }

    // individual agents — one dot per simulated American, coloured by party.
    // Drawn over any (fading) density so the morph reads as dots gathering
    // into clouds. Same positions, different representation (ADR-001: the
    // compass is where state is SHOWN; influence flows along ties).
    if (dotA > 0.01) {
      const r = Math.max(2.2, Math.min(3.4, S * 0.0055));
      const baseA = dotA * 0.9;
      // T-VIZ: at a replacement splice the OLD occupant (held at pos[te] above)
      // fades out by its own party colour; the NEW occupant fades in at pos[te+1].
      const oldParty = replSet ? run.party[tFloor] : null;
      const dotCol = (p) => p === 0 ? CC.d : p === 1 ? CC.r : _rgb(RGB_GREY, 1);
      for (let i = 0; i < pos.length; i++) {
        const isRepl = replSet && replSet.has(i);
        ctx.globalAlpha = isRepl ? baseA * (1 - splitFrac) : baseA;
        ctx.fillStyle = dotCol(isRepl ? oldParty[i] : party[i]);
        ctx.beginPath();ctx.arc(mx(pos[i][0]), my(pos[i][1]), r, 0, 6.283);ctx.fill();
      }
      if (replSet) {
        const newParty = run.party[Math.min(LAST, tFloor + 1)];
        ctx.globalAlpha = baseA * splitFrac;
        for (const a of replacing) {
          ctx.fillStyle = dotCol(newParty[a]);
          ctx.beginPath();ctx.arc(mx(posIn[a][0]), my(posIn[a][1]), r, 0, 6.283);ctx.fill();
        }
      }
      ctx.globalAlpha = 1;
    }

    // centroids + connector. In POSITION it's the literal party-gap tether; in
    // AFFECT it doubles as the "felt-distance" tether — same two camps, but the
    // line thickens/darkens as out-party warmth falls, so the cooling reads on
    // the map too (the gap value itself reads in the bar/scissors). — §3.5
    if (show('rings') && showGap && (layer === 'position' || layer === 'affect')) {
      const { D0, R0 } = centroids(pos, party);
      if (layer === 'affect') {
        const c = coldnessAt(safeTick);
        ctx.strokeStyle = _rgb(_mix([122, 126, 132], RGB_INKDEEP, c), 0.5 + 0.45 * c);
        ctx.lineWidth = 1.4 + 3.2 * c;ctx.setLineDash([]);
      } else {
        ctx.strokeStyle = CC.ink2;ctx.lineWidth = 1.6;ctx.setLineDash([2, 5]);
      }
      ctx.beginPath();ctx.moveTo(mx(D0[0]), my(D0[1]));ctx.lineTo(mx(R0[0]), my(R0[1]));ctx.stroke();
      ctx.setLineDash([]);
      const _cr = 5.5 * _mk;
      [[D0, CC.d], [R0, CC.r]].forEach(([c, col]) => {
        ctx.fillStyle = col;ctx.beginPath();ctx.arc(mx(c[0]), my(c[1]), _cr, 0, 6.283);ctx.fill();
        ctx.strokeStyle = '#fff';ctx.lineWidth = 2 * _mk;ctx.beginPath();ctx.arc(mx(c[0]), my(c[1]), _cr, 0, 6.283);ctx.stroke();
      });
    }

    // quadrant + axis labels on the square (chrome=false drops them, e.g. the
    // mobile story's collapsed compass strip, where they'd just be clutter)
    if (show('labels') && chrome) {
    ctx.textBaseline = 'middle';
    if (quadrants) {
    ctx.fillStyle = CC.ink4;ctx.font = `italic ${fq}px Newsreader, Georgia, serif`;
    ctx.textAlign = 'left';ctx.fillText('populist', mx(-0.95), my(0.9));
    ctx.textAlign = 'right';ctx.fillText('traditional right', mx(0.95), my(0.9));
    ctx.textAlign = 'left';ctx.fillText('progressive left', mx(-0.95), my(-0.9));
    ctx.textAlign = 'right';ctx.fillText('libertarian', mx(0.95), my(-0.9));
    }
    ctx.fillStyle = CC.ink3;ctx.font = `500 ${fa}px Geist, system-ui, sans-serif`;
    ctx.textAlign = 'center';ctx.textBaseline = 'alphabetic';
    ctx.fillText('traditional', (mx(-1) + mx(1)) / 2, my(1) - fa * 1.1);
    ctx.textBaseline = 'hanging';
    ctx.fillText('progressive', (mx(-1) + mx(1)) / 2, my(-1) + fa * 1.1);
    ctx.textBaseline = 'bottom';ctx.fillStyle = CC.ink3;
    ctx.textAlign = 'left';ctx.fillText('← redistributive', mx(-0.98), my(0) - 7);
    ctx.textAlign = 'right';ctx.fillText('laissez-faire →', mx(0.98), my(0) - 7);
    }

    if (dim > 0) {ctx.fillStyle = `rgba(243,243,240,${dim})`;ctx.fillRect(0, 0, W, H);}

    // engine-derived entities — drawn last so they read over the field. All
    // positions come from D.entities (outlets, emergent factions) or the live
    // centroids (parties); nothing is eyeballed and nothing predates its year.
    // landmarks: 'fixed' = outlets + emerged factions · 'all' = + party labels.
    if (show('entities') && landmarks && layer === 'position') {
      const list = engineEntities(safeTick, pos, party, landmarks === 'fixed' ? 'fixed' : 'all');
      const efs = _ck * Math.max(11, Math.min(13.5, S * 0.024));
      const sq = 3.3 * _mk, dia = 3.6 * _mk;
      list.forEach((L) => {
        const px = mx(L.x),py = my(L.y);
        const col = L.lean === 'd' ? CC.d : L.lean === 'r' ? CC.r : CC.ink2;
        if (L.cls === 'media') {
          // outlet — hollow square (the attractors that pull agents)
          ctx.fillStyle = '#fff';ctx.strokeStyle = col;ctx.lineWidth = 1.6;
          ctx.beginPath();ctx.rect(px - sq, py - sq, sq * 2, sq * 2);ctx.fill();ctx.stroke();
        } else if (L.cls === 'party') {
          // party centroid — ring with a filled core
          ctx.fillStyle = '#fff';ctx.beginPath();ctx.arc(px, py, 7 * _mk, 0, 6.283);ctx.fill();
          ctx.strokeStyle = col;ctx.lineWidth = 2.4;ctx.beginPath();ctx.arc(px, py, 6.4 * _mk, 0, 6.283);ctx.stroke();
          ctx.fillStyle = col;ctx.beginPath();ctx.arc(px, py, 2.4 * _mk, 0, 6.283);ctx.fill();
        } else {
          // emergent faction — diamond, so it reads distinctly from parties
          ctx.save();ctx.translate(px, py);ctx.rotate(Math.PI / 4);
          ctx.fillStyle = col;ctx.fillRect(-dia, -dia, dia * 2, dia * 2);
          ctx.strokeStyle = '#fff';ctx.lineWidth = 1.5;ctx.strokeRect(-dia, -dia, dia * 2, dia * 2);
          ctx.restore();
        }
        const right = L.side ? L.side === 'r' : L.x >= 0;
        const isParty = L.cls === 'party';
        ctx.font = `${L.cls === 'media' ? 'italic ' : ''}${isParty ? 700 : 600} ${isParty ? efs + 0.5 : efs}px Geist, system-ui, sans-serif`;
        ctx.textAlign = right ? 'left' : 'right';
        ctx.textBaseline = 'middle';
        const lx = px + (right ? (isParty ? 11 : 9) : (isParty ? -11 : -9)) * _mk;
        ctx.lineJoin = 'round';ctx.strokeStyle = 'rgba(243,243,240,.94)';ctx.lineWidth = 3.6;
        ctx.strokeText(L.name, lx, py);
        ctx.fillStyle = isParty ? col : (L.cls === 'media' ? CC.ink2 : CC.ink);
        ctx.fillText(L.name, lx, py);
      });
    }
  }, [run, tick, layer, view, showGap, dim, sz, transform, landmarks, reveal, morphT, chrome, compact]);

  return (
    <div ref={wrapRef} style={{ position: 'absolute', inset: 0, overflow: 'hidden' }}>
      <canvas ref={ref} style={{ width: '100%', height: '100%', display: 'block' }} />
    </div>);

}

// ── small UI ──────────────────────────────────────────────────────────────────
function Segmented({ value, onChange, options, accent = CC.ink, compact = false }) {
  return (
    <div style={{ display: 'inline-flex', gap: 3, padding: compact ? 2 : 3, background: 'transparent', borderRadius: 999, border: `1px solid ${CC.ink}` }}>
      {options.map(([v, l]) => {
        const on = value === v;
        return (
          <button key={v} onClick={() => onChange(v)} style={{
            fontSize: compact ? 11.5 : 12.5, padding: compact ? '4px 11px' : '5px 13px', borderRadius: 999, cursor: 'pointer', fontFamily: SANS,
            border: `1px solid ${on ? CC.ink : 'transparent'}`, background: 'transparent', color: on ? accent : CC.ink3,
            fontWeight: on ? 600 : 500, whiteSpace: 'nowrap'
          }}>{l}</button>);

      })}
    </div>);

}

// curated timeline events: functional shocks (labelled) vs context (hairline)
const TL_EVENTS = [
{ tick: 21, fn: true, major: true, short: 'Fairness Doctrine', full: 'Fairness Doctrine repealed (1987)' },
{ tick: 30, fn: false, full: '1990' },
{ tick: 48, fn: true, major: true, short: 'Fox News', full: 'Fox News launched (1996)' },
{ tick: 60, fn: false, full: '2000' },
{ tick: 84, fn: true, major: true, short: 'Social media', full: 'Social media adoption + Obama (2008)' },
{ tick: 87, fn: true, short: 'Tea Party', full: 'Tea Party emergence (2009)' },
{ tick: 90, fn: true, short: 'Citizens United', full: 'Citizens United (2010) — era marker, not a cause' },
{ tick: 96, fn: true, short: 'Social media peak', full: 'Social media adoption peak (2012)' },
{ tick: 105, fn: true, short: 'MAGA', full: 'MAGA emergence (2015)' },
{ tick: 108, fn: true, major: true, short: 'Trump', full: 'Trump + status-threat spike (2016)' },
{ tick: 114, fn: true, short: 'DSA', full: 'DSA emergence (2018)' },
{ tick: 120, fn: true, major: true, short: 'COVID', full: 'COVID + Jan 6 (2020)' },
{ tick: 123, fn: false, full: 'Affect revert (2021)' }];


function YearScrubber({ tick, setTick, playing, toggle, color = CC.ink }) {
  const trackRef = React.useRef(null);
  const [hover, setHover] = React.useState(null);
  const drag = (clientX) => {
    const r = trackRef.current.getBoundingClientRect();
    setTick(Math.max(0, Math.min(LAST, (clientX - r.left) / r.width * LAST)));
  };
  const onDown = (e) => {
    drag(e.clientX);
    const mv = (ev) => drag(ev.clientX);
    const up = () => {window.removeEventListener('mousemove', mv);window.removeEventListener('mouseup', up);};
    window.addEventListener('mousemove', mv);window.addEventListener('mouseup', up);
  };
  const pct = tick / LAST * 100;
  const year = Math.floor(tickToYear(tick));
  // the most recent event at or before the playhead — always legible, never collides
  let last = null;
  for (const e of TL_EVENTS) if (e.tick <= tick + 0.5) last = e;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
      <button onClick={toggle} style={{
        width: 38, height: 38, flexShrink: 0, borderRadius: 999, background: CC.ink, color: '#fff', border: 'none',
        cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 12
      }}>{playing ? '❚❚' : '▶'}</button>
      <div style={{ width: 150, flexShrink: 0, display: 'flex', flexDirection: 'column', lineHeight: 1.1 }}>
        <span style={{ fontFamily: MONO, fontSize: 22, fontWeight: 500, color: CC.ink, ...TNUM }}>{year}</span>
        <span style={{ fontSize: 11, color: CC.ink3, marginTop: 3, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {last ? <><span style={{ color: last.fn ? CC.ink3 : CC.ink4 }}>{last.fn ? '●' : '○'}</span> {last.short || last.full}</> : 'before the record'}
        </span>
      </div>
      <div style={{ flex: 1, position: 'relative' }}>
        {hover &&
        <span style={{ position: 'absolute', left: `${hover.tick / LAST * 100}%`, transform: 'translateX(-50%)', bottom: 26, whiteSpace: 'nowrap', fontSize: 11, color: '#fff', background: CC.ink, padding: '4px 9px', borderRadius: 6, zIndex: 5, fontFamily: SANS, pointerEvents: 'none' }}>{hover.full}</span>
        }
        <div ref={trackRef} onMouseDown={onDown} style={{ height: 26, position: 'relative', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
          <div style={{ position: 'absolute', left: 0, right: 0, height: 4, borderRadius: 999, background: CC.border }} />
          <div style={{ position: 'absolute', left: 0, width: `${pct}%`, height: 4, borderRadius: 999, background: color }} />
          {TL_EVENTS.map((e) => {
            const x = e.tick / LAST * 100;
            return (
              <span key={`${e.tick}-${e.full}`}
              onMouseEnter={() => setHover(e)} onMouseLeave={() => setHover(null)}
              style={{ position: 'absolute', left: `${x}%`, top: e.fn ? 1 : 7, width: e.fn ? 2 : 1, height: e.fn ? 24 : 12, background: e.fn ? CC.ink3 : CC.ink4, transform: 'translateX(-50%)', cursor: 'pointer' }} />);

          })}
          <div style={{ position: 'absolute', left: `${pct}%`, width: 16, height: 16, borderRadius: 999, background: '#fff', border: `3px solid ${color}`, transform: 'translateX(-50%)', boxShadow: '0 2px 6px rgba(26,29,35,.18)' }} />
        </div>
      </div>
    </div>);

}

// a "grown" horizontal meter (party gap / out-party warmth) — replaces the canvas pill
function MeterBar({ label, value, fill, max, color = CC.ink, suffix = '' }) {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 6 }}>
        <Eyebrow style={{ color: CC.ink3 }}>{label}</Eyebrow>
        <span style={{ fontFamily: MONO, fontSize: 15, fontWeight: 600, color: CC.ink, ...TNUM }}>{value}{suffix}</span>
      </div>
      <div style={{ height: 8, borderRadius: 999, background: CC.bg2, overflow: 'hidden' }}>
        <div style={{ width: `${_clamp01(fill / max) * 100}%`, height: '100%', borderRadius: 999, background: color, transition: 'width .12s linear' }} />
      </div>
    </div>);

}

function useTick({ autoplay = false, start = 42, base = 4.5 } = {}) {
  const [tick, setTick] = React.useState(start);
  const [playing, setPlaying] = React.useState(autoplay);
  const [speed, setSpeed] = React.useState(1);
  const ref = React.useRef(tick);ref.current = tick;
  React.useEffect(() => {
    if (!playing) return;
    let raf,prev = null;
    const loop = (ts) => {
      if (prev == null) prev = ts;
      const dt = (ts - prev) / 1000;prev = ts;
      let nt = ref.current + dt * base * speed;
      if (nt >= LAST) {setTick(LAST);setPlaying(false);return;}
      setTick(nt);raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [playing, base, speed]);
  const toggle = () => {if (ref.current >= LAST) setTick(0);setPlaying((p) => !p);};
  return { tick, setTick, playing, setPlaying, toggle, speed, setSpeed };
}

// proto-style transport: play / restart / speed (mirrors the simulation page)
function SpeedControl({ speed, setSpeed }) {
  return (
    <div style={{ display: 'flex', gap: 3 }}>
      {[[0.5, '½'], [1, '1×'], [2, '2×'], [4, '4×']].map(([v, l]) => {
        const on = speed === v;
        return (
          <button key={v} onClick={() => setSpeed(v)} style={{
            fontSize: 11, padding: '3px 8px', borderRadius: 999, fontFamily: MONO, cursor: 'pointer',
            border: `1px solid ${on ? CC.ink : CC.border}`, color: on ? CC.ink : CC.ink3,
            fontWeight: on ? 500 : 400, background: on ? CC.surface : 'transparent', ...TNUM
          }}>{l}</button>);

      })}
    </div>);

}
function Transport({ playing, toggle, setTick, speed, setSpeed }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      <button onClick={toggle} aria-label={playing ? 'Pause' : 'Play'} style={{
        width: 34, height: 34, borderRadius: 999, background: CC.ink, color: '#fff', border: 'none',
        cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 12
      }}>{playing ? '❚❚' : '▶'}</button>
      <button onClick={() => setTick(0)} aria-label="Restart" style={{
        width: 28, height: 28, borderRadius: 999, border: `1px solid ${CC.border}`, color: CC.ink2,
        cursor: 'pointer', background: 'transparent', fontSize: 12
      }}>↺</button>
      <SpeedControl speed={speed} setSpeed={setSpeed} />
    </div>);

}

// ── the ANES "scissors" — the primary affect treatment (§3.5) ───────────────
// Two feeling-thermometer lines over 1980→2025, both in degrees on the same
// 0–100 scale: a flat-ish IN-party line and a plunging OUT-party line. The
// out-party line is engine-measured (macro.aff); the in-party line is an
// EXTERNAL ANES overlay (macro.aff_in_empirical) and is labelled as such — the
// honesty bright line the contract is explicit about. A layperson reads "the
// lines pull apart" instantly; this replaces the unreadable ash blob as the
// authoritative way to feel affective polarization.
function ScissorsChart({ tick, width = 392, height = 168 }) {
  const padL = 34, padR = 14, padT = 14, padB = 26;
  const plotW = width - padL - padR, plotH = height - padT - padB;
  const LO = 15, HI = 80; // degrees window
  const X = (t) => padL + (t / LAST) * plotW;
  const Y = (deg) => padT + plotH - ((deg - LO) / (HI - LO)) * plotH;
  const N = 90;
  const outPts = [], inPts = [];
  for (let i = 0; i <= N; i++) {
    const t = (i / N) * LAST;
    outPts.push([X(t), Y(outPartyDeg(t))]);
    inPts.push([X(t), Y(inPartyDeg(t))]);
  }
  const toPath = (pts) => pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');
  // the widening wedge between the two lines = the "scissors" opening
  const band = toPath(inPts) + ' L' +
    [...outPts].reverse().map((p) => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' L') + ' Z';
  const px = X(tick);
  const outNow = outPartyDeg(tick), inNow = inPartyDeg(tick);
  const grid = [20, 40, 60, 80];
  return (
    <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={height} preserveAspectRatio="xMidYMid meet" style={{ display: 'block' }}>
      {grid.map((d) => (
        <g key={d}>
          <line x1={padL} y1={Y(d)} x2={width - padR} y2={Y(d)} stroke={CC.border} strokeWidth="1" strokeDasharray="2 4" opacity="0.7" />
          <text x={padL - 6} y={Y(d) + 3} textAnchor="end" style={{ fontFamily: MONO, fontSize: 9.5, fill: CC.ink4, ...TNUM }}>{d}°</text>
        </g>
      ))}
      <path d={band} fill="rgba(139,37,48,0.07)" stroke="none" />
      <path d={toPath(inPts)} fill="none" stroke={CC.d} strokeWidth="2" strokeDasharray="4 3" strokeLinejoin="round" strokeLinecap="round" />
      <path d={toPath(outPts)} fill="none" stroke={CC.r} strokeWidth="2.4" strokeLinejoin="round" strokeLinecap="round" />
      <line x1={px} y1={padT - 2} x2={px} y2={padT + plotH} stroke={CC.ink4} strokeWidth="1" strokeDasharray="1 3" />
      <circle cx={px} cy={Y(inNow)} r="3.4" fill={CC.surface} stroke={CC.d} strokeWidth="2" />
      <circle cx={px} cy={Y(outNow)} r="3.4" fill={CC.surface} stroke={CC.r} strokeWidth="2" />
    </svg>
  );
}

// the legend/readout that frames the scissors and carries the provenance label
function ScissorsLegend({ tick }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 7, fontFamily: SANS }}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 10 }}>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: DS.type.small, color: CC.ink2 }}>
          <span style={{ width: 16, height: 0, borderTop: `2.4px solid ${CC.r}` }} /> Toward the <strong>other</strong> party
        </span>
        <MonoVal size={DS.type.small} color={CC.r}>{Math.round(outPartyDeg(tick))}°</MonoVal>
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 10 }}>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: DS.type.small, color: CC.ink2 }}>
          <span style={{ width: 16, height: 0, borderTop: `2px dashed ${CC.d}` }} /> Toward <strong>their own</strong> party
        </span>
        <MonoVal size={DS.type.small} color={CC.d}>{Math.round(inPartyDeg(tick))}°</MonoVal>
      </div>
      <p style={{ margin: '3px 0 0', fontSize: DS.type.micro, lineHeight: 1.45, color: CC.ink4 }}>
        Out-party warmth is engine-measured. The in-party line is an <strong>external ANES reference</strong> (Iyengar et al.), drawn for the honest scissors — not a simulation output.
      </p>
    </div>
  );
}

// ── small-multiples strip — calm→camps proof that needs no animation (§3.6) ──
// Four frozen years side-by-side: a viewer sees one lump become two at a glance.
function SmallMultiples({ years = [[0, 1980], [48, 1996], [90, 2010], [135, 2025]] }) {
  return (
    <div style={{ display: 'flex', gap: 8 }}>
      {years.map(([t, yr]) => (
        <div key={t} style={{ flex: 1, minWidth: 0 }}>
          <div style={{ position: 'relative', width: '100%', aspectRatio: '1', borderRadius: DS.rad.inset, overflow: 'hidden', border: `1px solid ${CC.border}`, background: CC.surface }}>
            <Field run={D.runs.baseline} tick={t} layer="position" view="density" showGap={false} />
          </div>
          <div style={{ marginTop: 5, textAlign: 'center', fontFamily: MONO, fontSize: 10.5, color: CC.ink3, ...TNUM }}>{yr}</div>
        </div>
      ))}
    </div>
  );
}

Object.assign(window, {
  partisanColor, ashColor, coolParty, coldnessAt, warmthDegAt, outPartyDeg, inPartyDeg,
  agentColdness, computeDensity, centroids, marchingSquares, engineEntities,
  Field, ScissorsChart, ScissorsLegend, SmallMultiples,
  Segmented, YearScrubber, MeterBar, Transport, SpeedControl, useTick, TL_EVENTS, _rgb, RGB_NAVY, RGB_OX, RGB_WARM, RGB_ASH
});
