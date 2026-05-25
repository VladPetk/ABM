/* CompassCanvas — editorial-restraint compass renderer.

   Stretches edge-to-edge inside the stage. The dot field is the chart.
   Restraint over polish: no density grids, no quadrant tints, no centroid
   marker. Just a hairline frame, a subtle crosshair, deep-palette dots
   whose alpha rises with opinion intensity, simple party labels, and
   bold corner labels that double as the axes.
*/

class CompassCanvas {
  constructor(canvasEl) {
    this.canvas = canvasEl;
    this.ctx = canvasEl.getContext('2d');
    this.dpr = window.devicePixelRatio || 1;

    this.prev = null;
    this.target = null;
    this.snap = null;
    this.lastSnapTime = 0;
    this.smoothedInterval = 0;
    this.transitionDur = 100;

    this.viz = { group_colors: {}, group_names: {} };
    this.hoverIdx = -1;
    this.pinnedIdx = -1;
    this.darkMode = false;
    this._dirty = true;
    this._rgbCache = {};     // group_id -> "r,g,b" string (cached per snapshot)

    this._resize();
    window.addEventListener('resize', () => { this._resize(); this.draw(); });

    this._loop = this._loop.bind(this);
    this._looping = false;
    this.draw();
  }

  setDarkMode(dark) { this.darkMode = !!dark; this._rgbCache = {}; this.draw(); }
  setViz(viz)       { this.viz = viz || {}; this._rgbCache = {}; this.draw(); }
  setHover(idx)     { if (idx !== this.hoverIdx) { this.hoverIdx = idx; this.draw(); } }
  setPinned(idx)    { if (idx !== this.pinnedIdx) { this.pinnedIdx = idx; this.draw(); } }

  setSnapshot(snap) {
    const now = performance.now();
    if (this.lastSnapTime) {
      const interval = now - this.lastSnapTime;
      // Exponential moving average to smooth WebSocket arrival jitter.
      this.smoothedInterval = this.smoothedInterval
        ? this.smoothedInterval * 0.7 + interval * 0.3
        : interval;
      // Tween longer than the snapshot interval so the next snapshot
      // arrives mid-tween — guarantees continuous motion (no freeze gap).
      this.transitionDur = Math.max(60, Math.min(380, this.smoothedInterval * 1.3));
    }
    this.lastSnapTime = now;
    this.transitionStart = now;
    this.prev = this._currentFrame() || snap.agents.map(a => a.slice());
    this.target = snap.agents.map(a => a.slice());
    if (this.prev.length !== this.target.length) {
      if (this.prev.length < this.target.length) {
        while (this.prev.length < this.target.length) this.prev.push(this.target[this.prev.length].slice());
      } else {
        this.prev = this.prev.slice(0, this.target.length);
      }
    }
    this.snap = snap;
    this.draw();
    this._kickLoop();
  }

  _kickLoop() {
    if (this._looping) return;
    this._looping = true;
    requestAnimationFrame(this._loop);
  }

  _loop() {
    const now = performance.now();
    const inTween = this.lastSnapTime && (now - this.transitionStart) < this.transitionDur;
    if (inTween) {
      this.draw();
      requestAnimationFrame(this._loop);
    } else {
      this.draw();         // one last frame to settle
      this._looping = false;
    }
  }

  _currentFrame() {
    if (!this.prev || !this.target) return null;
    const now = performance.now();
    const t = Math.min(1, (now - this.transitionStart) / this.transitionDur);
    const ease = 1 - Math.pow(1 - t, 3);
    const out = new Array(this.target.length);
    for (let i = 0; i < this.target.length; i++) {
      const p = this.prev[i] || this.target[i];
      const tg = this.target[i];
      out[i] = [
        p[0] + (tg[0] - p[0]) * ease,
        p[1] + (tg[1] - p[1]) * ease,
        tg[2],
      ];
    }
    return out;
  }

  _resize() {
    const r = this.canvas.getBoundingClientRect();
    this.cssW = r.width; this.cssH = r.height;
    this.canvas.width  = Math.max(1, Math.floor(r.width  * this.dpr));
    this.canvas.height = Math.max(1, Math.floor(r.height * this.dpr));
    this.ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
  }

  // Compass plot area — fills the canvas with margins for edge labels.
  _bounds() {
    const m = { top: 22, right: 32, bottom: 24, left: 32 };
    return {
      x0: m.left, x1: this.cssW - m.right,
      y0: this.cssH - m.bottom, y1: m.top,
      m,
    };
  }

  // (worldX, worldY) ∈ [-1, 1]² → canvas pixels.
  // We *stretch* x to fill the stage width — this is a "political landscape"
  // wider than tall, which reads as a field rather than a tiny square.
  _world(x, y) {
    const b = this._bounds();
    const sx = b.x0 + ((x + 1) / 2) * (b.x1 - b.x0);
    const sy = b.y1 + ((1 - y) / 2) * (b.y0 - b.y1);
    return [sx, sy];
  }

  pickAgent(px, py, pickRadius = 14) {
    if (!this.target) return -1;
    const frame = this._currentFrame() || this.target;
    let bestI = -1, bestD = pickRadius * pickRadius;
    for (let i = 0; i < frame.length; i++) {
      const [x, y] = frame[i];
      const [sx, sy] = this._world(x, y);
      const dx = sx - px, dy = sy - py;
      const d = dx*dx + dy*dy;
      if (d < bestD) { bestD = d; bestI = i; }
    }
    return bestI;
  }

  draw() {
    const ctx = this.ctx;
    const W = this.cssW, H = this.cssH;
    ctx.clearRect(0, 0, W, H);

    const T = this.darkMode ? {
      bg:       '#1f1f23',
      frame:    'rgba(245,244,240,0.10)',
      axis:     'rgba(245,244,240,0.06)',
      axisInk:  '#ecebe4',
      ghost:    'rgba(245,244,240,0.34)',
      label:    'rgba(245,244,240,0.85)',
      sub:      'rgba(245,244,240,0.40)',
      chipBg:   'rgba(31,31,35,0.94)',
      chipBor:  '#3a3a40',
      chipInk:  '#ecebe4',
      dotInk:   '#ecebe4',
    } : {
      bg:       '#ffffff',
      frame:    'rgba(26,29,35,0.10)',
      axis:     'rgba(26,29,35,0.06)',
      axisInk:  '#1a1d23',
      ghost:    'rgba(26,29,35,0.32)',
      label:    'rgba(26,29,35,0.86)',
      sub:      'rgba(26,29,35,0.42)',
      chipBg:   'rgba(255,255,255,0.96)',
      chipBor:  '#cdc9bd',
      chipInk:  '#1a1d23',
      dotInk:   '#1a1d23',
    };

    ctx.fillStyle = T.bg;
    ctx.fillRect(0, 0, W, H);

    const b = this._bounds();
    const [cx, cy] = this._world(0, 0);

    // Hairline frame around the plot area — no other chrome
    ctx.strokeStyle = T.frame;
    ctx.lineWidth = 1;
    ctx.strokeRect(b.x0 + 0.5, b.y1 + 0.5, b.x1 - b.x0 - 1, b.y0 - b.y1 - 1);

    // Subtle crosshair through origin
    ctx.strokeStyle = T.axis;
    ctx.beginPath();
    ctx.moveTo(b.x0, cy); ctx.lineTo(b.x1, cy);
    ctx.moveTo(cx, b.y1); ctx.lineTo(cx, b.y0);
    ctx.stroke();

    // === Dots ============================================================
    const frame = this._currentFrame();
    const colors = this.viz.group_colors || {};
    const fallback = this.darkMode ? '#7993cf' : '#1f3565';

    if (frame) {
      // Cache hex→"rgb(r,g,b)" once per render; per-dot we only set
      // globalAlpha. Saves 600 string parses per frame at 60fps.
      const rgbStr = (hex) => {
        if (this._rgbCache[hex]) return this._rgbCache[hex];
        const h = hex.replace('#', '');
        return this._rgbCache[hex] = `rgb(${parseInt(h.slice(0,2),16)},${parseInt(h.slice(2,4),16)},${parseInt(h.slice(4,6),16)})`;
      };
      for (let i = 0; i < frame.length; i++) {
        const [x, y, g] = frame[i];
        const [sx, sy] = this._world(x, y);
        // Intensity = chebyshev distance from origin in [0, 1]
        const mag = Math.min(1, Math.max(Math.abs(x), Math.abs(y)));
        ctx.globalAlpha = 0.30 + 0.62 * mag;
        ctx.fillStyle = rgbStr(colors[g] || fallback);
        ctx.beginPath();
        ctx.arc(sx, sy, 5.5, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
    }

    // === Media-shock marker (transient) =================================
    if (this.snap?.event) {
      const e = this.snap.event;
      const [sx, sy] = this._world(e.target[0], e.target[1]);
      const op = Math.max(0, 1 - e.age / 30);
      ctx.strokeStyle = `rgba(214,154,67,${op * 0.7})`;
      ctx.lineWidth = 1.2;
      for (const r of [12, 22, 32]) {
        ctx.beginPath(); ctx.arc(sx, sy, r, 0, Math.PI * 2); ctx.stroke();
      }
      ctx.fillStyle = `rgba(214,154,67,${op})`;
      ctx.font = '500 10.5px "Geist", system-ui, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(`media shock · t = ${e.tick}`, sx, sy + 44);
    }

    // === Media outlets — small named squares, drawn UNDER party stars ===
    const outlets = this.viz.outlets || [];
    for (const o of outlets) {
      const [sx, sy] = this._world(o.position[0], o.position[1]);
      // soft outlined square (distinguishes from circular party discs)
      ctx.fillStyle = o.color || T.label;
      ctx.fillRect(sx - 4, sy - 4, 8, 8);
      ctx.strokeStyle = T.bg;
      ctx.lineWidth = 1.5;
      ctx.strokeRect(sx - 4, sy - 4, 8, 8);
      // outlet name
      ctx.fillStyle = T.label;
      ctx.font = '500 10px "Geist", system-ui, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillText(o.name, sx, sy + 8);
      ctx.textBaseline = 'alphabetic';
    }

    // === Party markers — small disc + label below =======================
    const parties = this.snap?.parties || {};
    const names   = this.viz.group_names || {};
    for (const [gid, [px, py]] of Object.entries(parties)) {
      const [sx, sy] = this._world(px, py);
      const color = colors[gid] || fallback;
      // halo
      ctx.fillStyle = this._hexA(color, 0.14);
      ctx.beginPath(); ctx.arc(sx, sy, 13, 0, Math.PI * 2); ctx.fill();
      // disc + white outline
      ctx.fillStyle = color;
      ctx.beginPath(); ctx.arc(sx, sy, 6, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = T.bg;
      ctx.lineWidth = 2;
      ctx.stroke();
      // text label below
      ctx.fillStyle = T.label;
      ctx.font = '500 11.5px "Geist", system-ui, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillText(names[gid] || `Party ${gid}`, sx, sy + 12);
      ctx.textBaseline = 'alphabetic';
    }

    // === Hover / pinned annotation ======================================
    const pickIdx = this.pinnedIdx >= 0 ? this.pinnedIdx
                                        : (this.hoverIdx >= 0 ? this.hoverIdx : -1);
    if (frame && pickIdx >= 0 && pickIdx < frame.length) {
      const [x, y, g] = frame[pickIdx];
      const [sx, sy] = this._world(x, y);
      const color = colors[g] || fallback;
      // ring
      ctx.strokeStyle = T.axisInk;
      ctx.lineWidth = 1.4;
      ctx.beginPath(); ctx.arc(sx, sy, 10, 0, Math.PI * 2); ctx.stroke();
      // leader + chip
      const right = sx < W - 220;
      const lx = sx + (right ? 18 : -18);
      const ly = sy - 22;
      ctx.strokeStyle = T.ghost;
      ctx.setLineDash([2, 3]);
      ctx.beginPath();
      ctx.moveTo(sx + (right ? 11 : -11), sy);
      ctx.lineTo(lx, ly + 12);
      ctx.stroke();
      ctx.setLineDash([]);
      const partyLabel = names[g] || `group ${g}`;
      this._chip(ctx, lx, ly, `Agent #${pickIdx} · ${partyLabel}`, color, T, right ? 'left' : 'right');
    }

    // === Bold corner / edge labels ======================================
    ctx.fillStyle = T.label;
    ctx.font = '600 11px "Geist", system-ui, sans-serif';
    ctx.textBaseline = 'middle';

    // Real-issue compass: economic stance (x) × cultural stance (y).
    ctx.textAlign = 'center';
    ctx.fillText('↑ CULTURAL CONSERVATIVE', cx, b.y1 - 11);
    ctx.fillText('↓ CULTURAL LIBERAL',     cx, b.y0 + 13);
    ctx.textAlign = 'left';
    ctx.fillText('← REDISTRIBUTIVE', b.x0 + 4, b.y1 - 11);
    ctx.textAlign = 'right';
    ctx.fillText('FREE-MARKET →', b.x1 - 4, b.y1 - 11);
    ctx.textBaseline = 'alphabetic';
  }

  _chip(ctx, x, y, text, color, T, align) {
    ctx.font = '500 10.5px "Geist", system-ui, sans-serif';
    const metrics = ctx.measureText(text);
    const padX = 8;
    const w = metrics.width + padX * 2 + 8;
    const h = 18;
    let bx;
    if (align === 'center')      bx = x - w / 2;
    else if (align === 'right')  bx = x - w;
    else                         bx = x;
    const by = y - h / 2;
    ctx.fillStyle = T.chipBg;
    ctx.strokeStyle = T.chipBor;
    ctx.lineWidth = 1;
    this._roundRect(ctx, bx, by, w, h, 4);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = color;
    ctx.beginPath(); ctx.arc(bx + padX, y, 2.6, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = T.chipInk;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, bx + padX + 8, y);
    ctx.textBaseline = 'alphabetic';
  }

  _roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }

  _hexA(hex, a) {
    const h = hex.replace('#', '');
    return `rgba(${parseInt(h.slice(0,2),16)},${parseInt(h.slice(2,4),16)},${parseInt(h.slice(4,6),16)},${a})`;
  }
}

window.CompassCanvas = CompassCanvas;
