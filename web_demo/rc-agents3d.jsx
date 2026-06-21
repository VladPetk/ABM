// Calm to Camps — "For the brave" 3D agent view.
// A full-bleed, borderless scatter of every one of the 250 simulated agents as
// individual points — NOT the density clouds the rest of the site shows. The
// floor plane is the familiar political compass (x = economic, depth = cultural)
// and the vertical axis is ANIMUS (out-party coldness, = −affect), so the crowd
// both spreads into two camps AND rises as it cools — the "scissors" as one
// motion. No chapters, no annotations: just a slowly auto-rotating scene you can
// orbit + zoom, driven by the same timeline as everywhere else.
//
// All three axes are real engine data: pos (econ/cultural) and the per-agent
// affect series (runs.baseline.affect = [tick][agent]). Nothing here is mocked.
//
// Hand-rolled canvas-2D projection (250 pts → no three.js / no dependency, true
// to the build-free demo). RAF drives the spin; a synchronous draw on every
// tick/resize means a static first frame exists even where RAF is paused
// (headless preview), so the projection itself stays verifiable.

const A3 = {
  CAM: 4.2,          // camera distance along +Z (world units)
  HEIGHT: 1.05,      // world displacement for animus = 1 (each camp lifts this far)
  SPIN: 0.16,        // auto-rotation rad/s
  PITCH0: 0.46,      // initial down-tilt (look onto the plane)
  YAW0: -0.62,
  BG: [249, 248, 244],
};

// per-agent animus at a fractional tick — interpolated straight from the engine
// affect series. animus = max(0, −warmth); warm agents sit on the floor.
function animusAt(run, f) {
  const t0 = Math.max(0, Math.min(LAST, Math.floor(f)));
  const t1 = Math.min(LAST, t0 + 1);
  const a = f - t0;
  const A = run.affect[t0], B = run.affect[t1];
  const out = new Float32Array(A.length);
  for (let i = 0; i < A.length; i++) {
    const v = A[i] + (B[i] - A[i]) * a;
    out[i] = v < 0 ? -v : 0;          // coldness magnitude
  }
  return out;
}

const _mixc = (c, d, t) => [c[0] + (d[0] - c[0]) * t, c[1] + (d[1] - c[1]) * t, c[2] + (d[2] - c[2]) * t];
const _rgbStr = (c, a) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;
const _clmp = (lo, hi, v) => v < lo ? lo : v > hi ? hi : v;

function Scatter3D({ tick, run, zoomApi }) {
  const ref = React.useRef(null);
  const wrapRef = React.useRef(null);
  const [sz, setSz] = React.useState({ w: 900, h: 640 });

  const yawRef = React.useRef(A3.YAW0);
  const pitchRef = React.useRef(A3.PITCH0);
  const zoomRef = React.useRef(1.3);
  const tickRef = React.useRef(tick);
  tickRef.current = tick;
  const szRef = React.useRef(sz);
  szRef.current = sz;
  const dragRef = React.useRef(null);     // {x,y,moved} while orbiting
  const drawRef = React.useRef(() => {});

  // ── the draw — reads everything from refs so the RAF loop and the static
  // tick/resize effect share one implementation. ───────────────────────────
  const draw = React.useCallback(() => {
    const cv = ref.current; if (!cv) return;
    const { w: W, h: H } = szRef.current;
    if (W < 40 || H < 40) return;
    const ctx = cv.getContext('2d');
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    if (cv.width !== Math.round(W * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);

    const safe = Number.isFinite(tickRef.current) ? _clmp(0, LAST, tickRef.current) : 0;
    const Smin = Math.min(W, H);
    const cx = W / 2, cy = H / 2 + H * 0.03;
    const yaw = yawRef.current, pitch = pitchRef.current, zoom = zoomRef.current;
    const cosY = Math.cos(yaw), sinY = Math.sin(yaw), cosP = Math.cos(pitch), sinP = Math.sin(pitch);
    const F = Smin * 1.32 * zoom;
    // world (X,Y,Z) → screen [sx, sy, depth, scale]
    const project = (X, Y, Z) => {
      const X1 = X * cosY + Z * sinY, Z1 = -X * sinY + Z * cosY;
      const Y2 = Y * cosP - Z1 * sinP, Z2 = Y * sinP + Z1 * cosP;
      const depth = A3.CAM - Z2;
      const s = F / Math.max(0.25, depth);
      return [cx + X1 * s, cy - Y2 * s, depth, s];
    };

    const HT = A3.HEIGHT;
    const ink = [26, 29, 35];

    // a projected line with the compass's fade-at-the-ends treatment
    const fadeSeg = (p, q, rgb, wid, edge, peak) => {
      const g = ctx.createLinearGradient(p[0], p[1], q[0], q[1]);
      g.addColorStop(0, _rgbStr(rgb, 0));
      g.addColorStop(edge, _rgbStr(rgb, peak));
      g.addColorStop(1 - edge, _rgbStr(rgb, peak));
      g.addColorStop(1, _rgbStr(rgb, 0));
      ctx.strokeStyle = g; ctx.lineWidth = wid; ctx.beginPath();
      ctx.moveTo(p[0], p[1]); ctx.lineTo(q[0], q[1]); ctx.stroke();
    };
    const border = [193, 188, 176];

    // ── the common-ground plane: the compass at animus 0, run through the middle ──
    const c00 = project(-1, 0, -1), c10 = project(1, 0, -1), c11 = project(1, 0, 1), c01 = project(-1, 0, 1);
    ctx.beginPath();
    ctx.moveTo(c00[0], c00[1]); ctx.lineTo(c10[0], c10[1]); ctx.lineTo(c11[0], c11[1]); ctx.lineTo(c01[0], c01[1]); ctx.closePath();
    ctx.fillStyle = _rgbStr(ink, 0.025); ctx.fill();
    [[c00, c10], [c10, c11], [c11, c01], [c01, c00]].forEach(([p, q]) => fadeSeg(p, q, border, 1, 0.06, 0.55));
    // centre cross — econ (X) and cultural (Z) axes across the plane
    fadeSeg(project(-1.12, 0, 0), project(1.12, 0, 0), border, 1.3, 0.05, 0.85);
    fadeSeg(project(0, 0, -1.12), project(0, 0, 1.12), border, 1.3, 0.05, 0.85);
    // faint interior grid lines for plane reference
    [-0.5, 0.5].forEach((u) => {
      fadeSeg(project(u, 0, -0.9), project(u, 0, 0.9), border, 0.8, 0.12, 0.30);
      fadeSeg(project(-0.9, 0, u), project(0.9, 0, u), border, 0.8, 0.12, 0.30);
    });
    // ── vertical animus axis: bidirectional through the plane (up = Dem cooling,
    // down = Rep cooling) — the gap between the camps IS their mutual animus ──
    fadeSeg(project(0, -HT - 0.12, 0), project(0, HT + 0.12, 0), border, 1.3, 0.04, 0.62);
    for (let k = 1; k <= 3; k++) {
      [HT * (k / 3), -HT * (k / 3)].forEach((yy) => {
        const a = project(0, yy, 0), b = project(0.05, yy, 0.05);
        ctx.strokeStyle = _rgbStr(border, 0.5); ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
      });
    }

    // ── agents — each lifts off the common ground by its own animus, signed by
    // party: Democrats up, Republicans down, Independents stay on the plane ──
    const pos = posAt(run, safe);
    const party = run.party[Math.round(safe)];
    const an = animusAt(run, safe);
    const PCOL = [RGB_NAVY, RGB_OX, RGB_GREY];
    const PSGN = [1, -1, 0];
    const n = pos.length;
    const items = new Array(n);
    for (let i = 0; i < n; i++) {
      const p = party[i];
      const sgn = PSGN[p] || 0;
      const ex = pos[i][0], cu = pos[i][1], a = an[i];
      const pr = project(ex, sgn * a * HT, cu);
      const gr = project(ex, 0, cu);               // footprint on the common ground
      items[i] = { sx: pr[0], sy: pr[1], gx: gr[0], gy: gr[1], depth: pr[2], scale: pr[3], col: PCOL[p] || RGB_GREY, lift: sgn !== 0 && a > 0.02 };
    }
    items.sort((u, v) => v.depth - u.depth);        // painter's: far → near

    // stems + footprints first (under the points)
    for (const it of items) {
      const nd = _clmp(0, 1, (it.depth - (A3.CAM - 1.7)) / 3.4);   // 0 near … 1 far
      // a faint stem back to the plane — shows how far each side has withdrawn
      if (it.lift) {
        ctx.strokeStyle = _rgbStr(it.col, 0.07 * (1 - 0.5 * nd));
        ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(it.gx, it.gy); ctx.lineTo(it.sx, it.sy); ctx.stroke();
      }
      // footprint on the plane (the agent's bare compass position)
      ctx.fillStyle = _rgbStr(ink, 0.045 * (1 - 0.4 * nd));
      ctx.beginPath(); ctx.ellipse(it.gx, it.gy, 2.6 * it.scale / 260, 1.3 * it.scale / 260, 0, 0, 6.283); ctx.fill();
    }
    // the points
    for (const it of items) {
      const nd = _clmp(0, 1, (it.depth - (A3.CAM - 1.7)) / 3.4);
      const r = _clmp(1.4, 7, 2.7 * it.scale / 260);
      const col = _mixc(it.col, A3.BG, nd * 0.5);                  // depth fog
      ctx.fillStyle = _rgbStr(col, 0.92 - nd * 0.42);
      ctx.beginPath(); ctx.arc(it.sx, it.sy, r, 0, 6.283); ctx.fill();
      // tiny near-side highlight so close points read as round, not flat
      if (nd < 0.45) {
        ctx.fillStyle = _rgbStr([255, 255, 255], 0.16 * (1 - nd / 0.45));
        ctx.beginPath(); ctx.arc(it.sx - r * 0.3, it.sy - r * 0.3, r * 0.42, 0, 6.283); ctx.fill();
      }
    }

    // ── billboard labels (upright, ride the rotating axes) ──
    const label = (p, text, dx, dy, col) => {
      ctx.font = `italic ${Math.max(11, Math.min(13.5, Smin * 0.02))}px Newsreader, Georgia, serif`;
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.lineJoin = 'round'; ctx.strokeStyle = 'rgba(249,248,244,.92)'; ctx.lineWidth = 3.4;
      ctx.strokeText(text, p[0] + dx, p[1] + dy);
      ctx.fillStyle = col || '#74797f'; ctx.fillText(text, p[0] + dx, p[1] + dy);
    };
    label(project(1.2, 0, 0), 'economic →', 0, 12);
    label(project(0, 0, 1.2), 'cultural →', 0, 12);
    label(project(0, HT + 0.12, 0), 'Democrats cool ↑', 0, -12, CC.d);
    label(project(0, -HT - 0.12, 0), 'Republicans cool ↓', 0, 16, CC.r);
  }, []);
  drawRef.current = draw;

  // measure the wrap (full-bleed)
  React.useEffect(() => {
    const el = wrapRef.current; if (!el) return;
    const measure = () => {
      const r = el.getBoundingClientRect();
      const w = Math.round(r.width), h = Math.round(r.height);
      setSz((p) => Math.abs(p.w - w) > 2 || Math.abs(p.h - h) > 2 ? { w, h } : p);
    };
    measure();
    const ro = new ResizeObserver(measure); ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // static draw on every tick / resize → a deterministic frame even where RAF
  // is paused (so the projection is verifiable headlessly).
  React.useEffect(() => { draw(); }, [draw, tick, sz]);

  // continuous auto-rotation (RAF) — paused while orbiting by hand.
  React.useEffect(() => {
    let raf, prev = null;
    const loop = (ts) => {
      if (prev == null) prev = ts;
      const dt = Math.min(0.05, (ts - prev) / 1000); prev = ts;
      if (!dragRef.current) yawRef.current += A3.SPIN * dt;
      drawRef.current();
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  // orbit (drag) + zoom (wheel) — the only direct interaction besides time.
  React.useEffect(() => {
    const el = wrapRef.current; if (!el) return;
    const onDown = (e) => {
      dragRef.current = { x: e.clientX, y: e.clientY };
      const move = (ev) => {
        const d = dragRef.current; if (!d) return;
        yawRef.current += (ev.clientX - d.x) * 0.008;
        pitchRef.current = _clmp(0.12, 1.24, pitchRef.current - (ev.clientY - d.y) * 0.006);
        d.x = ev.clientX; d.y = ev.clientY;
        drawRef.current();
      };
      const up = () => {
        dragRef.current = null;
        window.removeEventListener('pointermove', move);
        window.removeEventListener('pointerup', up);
      };
      window.addEventListener('pointermove', move);
      window.addEventListener('pointerup', up);
    };
    const onWheel = (e) => {
      e.preventDefault(); e.stopPropagation();
      zoomRef.current = _clmp(0.5, 2.8, zoomRef.current * (1 - e.deltaY * 0.0012));
      drawRef.current();
    };
    el.addEventListener('pointerdown', onDown);
    el.addEventListener('wheel', onWheel, { passive: false });
    return () => { el.removeEventListener('pointerdown', onDown); el.removeEventListener('wheel', onWheel); };
  }, []);

  // expose zoom to the page (the +/- buttons live at page level so they sit at
  // the viewport corner, not inside the off-screen-bleeding square).
  React.useEffect(() => {
    if (!zoomApi) return;
    zoomApi.current = (f) => { zoomRef.current = _clmp(0.5, 2.8, zoomRef.current * f); drawRef.current(); };
    return () => { if (zoomApi) zoomApi.current = null; };
  }, [zoomApi]);

  return (
    <div ref={wrapRef} style={{ position: 'absolute', inset: 0, overflow: 'hidden', cursor: 'grab', touchAction: 'none' }}>
      <canvas ref={ref} style={{ width: '100%', height: '100%', display: 'block' }} />
    </div>
  );
}

// ── the page: right-anchored scene · left prose · shared timeline — the same
// frame as the story page, minus the chapters ──────────────────────────────
function Agents3DPage() {
  const ph = useTick({ start: 0, autoplay: true, base: 2.25 });
  const { tick, setTick, playing, toggle, speed, setSpeed } = ph;
  const run = D.runs.baseline;
  const zoomApi = React.useRef(null);
  const zoom = (f) => { if (zoomApi.current) zoomApi.current(f); };
  const year = Math.floor(tickToYear(tick));
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const monthLabel = `${months[Math.min(11, Math.floor((tickToYear(tick) - year) * 12))]} ${year}`;
  const Dot = ({ c }) => <span style={{ width: 8, height: 8, borderRadius: 999, background: c, display: 'inline-block', flexShrink: 0 }} />;
  const LX = 'clamp(64px, 14vw, 248px)';
  // the same chapter markers as the U.S. story (not the raw historical events)
  const BEATS = window.STORY_BEATS || [];
  let beatI = 0; for (let i = 0; i < BEATS.length; i++) if (tick + 1e-6 >= BEATS[i].tick) beatI = i;

  return (
    <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', position: 'relative', background: CC.bg }}>
      <div style={{ flex: 1, minHeight: 0, position: 'relative', overflow: 'hidden', background: CC.bg }}>
        {/* the scene — a square anchored right that bleeds off the edges, exactly
            like the compass on the story page */}
        <div style={{ position: 'absolute', top: '-6%', bottom: '-6%', right: '8%', aspectRatio: '1' }}>
          <Scatter3D tick={tick} run={run} zoomApi={zoomApi} />
        </div>

        {/* paper scrim — keeps the prose legible, feathers out before the cloud */}
        <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, width: '56%', background: `linear-gradient(90deg, ${CC.bg} 0%, ${CC.bg} 88%, rgba(249,248,244,0) 100%)`, pointerEvents: 'none', zIndex: 1 }} />

        {/* floating narrative — left column, same position as the story rail */}
        <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, width: 'min(54%, 820px)', display: 'flex', flexDirection: 'column', minHeight: 0, zIndex: 3, pointerEvents: 'none' }}>
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, justifyContent: 'safe center', overflow: 'auto' }}>
            <div style={{ flexShrink: 0, padding: `clamp(28px,4.5vh,52px) 44px clamp(28px,4.5vh,52px) ${LX}` }}>
              <Eyebrow>Under the hood · for the brave</Eyebrow>
              <h2 style={{ margin: '14px 0 18px', fontFamily: SERIF, fontWeight: 600, fontSize: 46, lineHeight: 1.04, letterSpacing: '-.022em', maxWidth: 460 }}>
                Every agent, in three dimensions.
              </h2>
              <p style={{ margin: 0, fontFamily: SERIF, fontStyle: 'italic', fontSize: DS.type.subhead, lineHeight: 1.42, color: CC.ink, maxWidth: 440 }}>
                No clouds, no chapters — just the 250 people the model actually moves, one dot each.
              </p>
              <p style={{ margin: '16px 0 0', ...PROSE, color: CC.ink2, maxWidth: 460 }}>
                The flat plane is the political compass you already know — left–right is the economy, front–back is culture. Then each person lifts off it as they sour on the other side: <strong>Democrats rise, Republicans sink</strong>, so the vertical gap between blue and red <em>is</em> their mutual animus. Independents stay in the common middle.
              </p>
              <p style={{ margin: '14px 0 0', ...PROSE, color: CC.ink2, maxWidth: 460 }}>
                Press play and watch the two camps fly apart.
              </p>
              <p style={{ margin: '18px 0 0', display: 'flex', alignItems: 'center', gap: 16, fontSize: DS.type.small, color: CC.ink3, flexWrap: 'wrap' }}>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}><Dot c={CC.d} /> Democrat</span>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}><Dot c={CC.r} /> Republican</span>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}><Dot c={CC.i} /> Independent</span>
              </p>
              <Caption style={{ marginTop: 14 }}>Drag to orbit · scroll to zoom · all three axes are engine output.</Caption>
            </div>
          </div>
        </div>

        {/* zoom — viewport corner, above the timeline bar */}
        <div style={{ position: 'absolute', right: 'clamp(28px, 4vw, 56px)', bottom: 18, display: 'flex', flexDirection: 'column', gap: 6, zIndex: 4 }}>
          {[['+', 1.18], ['−', 1 / 1.18]].map(([g, f]) => (
            <button key={g} onClick={() => zoom(f)} aria-label={g === '+' ? 'Zoom in' : 'Zoom out'} style={{
              width: 32, height: 32, borderRadius: 999, border: `1px solid ${CC.border}`, background: 'rgba(255,255,255,.86)',
              color: CC.ink2, cursor: 'pointer', fontSize: 16, lineHeight: 1, fontFamily: SANS, boxShadow: '0 1px 4px rgba(26,29,35,.08)'
            }}>{g}</button>
          ))}
        </div>
      </div>

      {/* bottom bar — the same timeline language as the rest of the site */}
      <div style={{ height: 96, flexShrink: 0, background: CC.bg, position: 'relative', display: 'flex', alignItems: 'center', gap: 'clamp(18px, 3vw, 40px)', padding: '0 clamp(28px, 4vw, 56px)' }}>
        <div style={{ position: 'absolute', top: 0, left: 'clamp(28px, 4vw, 56px)', right: 'clamp(28px, 4vw, 56px)', height: 1, background: CC.border }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
          <button onClick={toggle} aria-label={playing ? 'Pause' : 'Play'} style={{
            width: 36, height: 36, borderRadius: 999, background: CC.ink, color: '#fff', border: 'none', cursor: 'pointer',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, flexShrink: 0
          }}>{playing ? '❚❚' : '▶'}</button>
          <button onClick={() => setTick(0)} aria-label="Restart" style={{
            width: 28, height: 28, borderRadius: 999, border: `1px solid ${CC.borderS}`, color: CC.ink2, background: 'transparent', cursor: 'pointer', fontSize: 13, flexShrink: 0
          }}>↺</button>
          <span style={{ width: 1, height: 20, background: CC.border, margin: '0 2px' }} />
          <SpeedControl speed={speed} setSpeed={setSpeed} />
          <div style={{ marginLeft: 6, display: 'flex', flexDirection: 'column', lineHeight: 1.15 }}>
            <MonoVal size={DS.type.small} color={CC.ink}>{monthLabel}</MonoVal>
            <span style={{ fontSize: DS.type.micro, color: CC.ink4 }}>tick {Math.round(tick)}/{LAST}</span>
          </div>
        </div>
        <div style={{ flex: 1, minWidth: 0, position: 'relative' }}>
          {BEATS.map((b, k) => {
            const on = k === beatI;
            const left = `calc(14px + ${b.tick / LAST} * (100% - 28px))`;
            return (
              <React.Fragment key={k}>
                {on &&
                  <span style={{ position: 'absolute', zIndex: 5, left, top: 54, transform: 'translateX(-50%)', whiteSpace: 'nowrap', fontFamily: SANS, fontSize: 10, fontWeight: 600, color: CC.ink, background: 'rgba(249,248,244,.9)', padding: '0 3px' }}>{b.short}</span>}
                <button title={b.title} onClick={() => setTick(b.tick)} style={{
                  position: 'absolute', zIndex: 4, left, top: 38, transform: 'translate(-50%,-50%) rotate(45deg)',
                  width: on ? 13 : 10, height: on ? 13 : 10, background: b.tick <= tick ? CC.ink : CC.surface,
                  border: `2px solid ${b.tick <= tick ? CC.ink : CC.ink3}`, cursor: 'pointer', padding: 0, borderRadius: 2,
                }} />
              </React.Fragment>
            );
          })}
          <ProtoTimeline tick={tick} setTick={setTick} color={CC.ink} altLabels events={false} />
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { Scatter3D, Agents3DPage });
