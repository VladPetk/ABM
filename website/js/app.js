/* polarlab — hero-split + collapsible-params orchestration. */

(function () {
  // ── State ─────────────────────────────────────────────────────────
  const state = {
    scenarios: [],
    currentKey: null,
    detail: null,
    paramValues: {},
    fps: 20,
    playing: false,
    pinnedAgentId: null,
    lastSnapshot: null,
    inspectorAgent: null,
    polHistory: [],
    maxHistory: 240,
    paramsOpen: false,           // collapsed by default
  };

  const $ = (sel) => document.querySelector(sel);
  const dom = {
    canvas:        $('#sim-canvas'),
    paramsPill:    $('#params-pill'),
    paramsPillChips: $('#params-pill-chips'),
    paramsCard:    $('#params-card'),
    paramsClose:   $('#params-close'),
    paramsList:    $('#params-list'),
    paramsCount:   $('#params-count'),
    scenarioRow:   $('#scenario-row'),
    heroStats:     $('#hero-stats'),
    tickCounter:   $('#tick-counter'),
    scrubberFill:  $('#scrubber-fill'),
    scrubberThumb: $('#scrubber-thumb'),
    btnPlay:       $('#btn-play'),
    btnStep:       $('#btn-step'),
    btnReset:      $('#btn-reset'),
    speedPills:    $('#speed-pills'),
    inspectorId:   $('#inspector-id'),
    inspectorParty:$('#inspector-party'),
    inspectorRows: $('#inspector-rows'),
    inspectorMap:  $('#inspector-map'),
    inspectorDiv:  $('#inspector-diversity'),
    inspectorAlike:$('#inspector-alike'),
    inspectorRisk: $('#inspector-risk'),
    inspectorDiet: $('#inspector-diet'),
    dietBar:       $('#diet-bar'),
    dietPresets:   $('#diet-presets'),
    dietTopOutlet: $('#diet-top-outlet'),
    legendCard:    $('#legend-card'),
    sparkline:     $('#sparkline'),
    sparkValue:    $('#sparkline-value'),
    connStatus:    $('#conn-status'),
    infoPop:       $('#info-pop'),
    infoPopTitle:  $('#info-pop-title'),
    infoPopBody:   $('#info-pop-body'),
    modeToggle:    $('#mode-toggle'),
    openFs:        $('#open-fullscreen'),
    exitFs:        $('#exit-fullscreen'),
    fsKpis:        $('#fs-kpis'),
    fsScenarioPill:$('#fs-scenario-pill'),
  };

  const compass = new CompassCanvas(dom.canvas);
  compass.setDarkMode(document.body.classList.contains('dark'));
  // Expose for ad-hoc debugging from the console (and screenshot tooling).
  window.__compass__ = compass;
  window.__state__ = state;

  // ── WebSocket ─────────────────────────────────────────────────────
  const wsScheme = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const sim = new SimClient(`${wsScheme}//${location.host}/api/ws`);

  sim.on('open',  () => setConn('connected'));
  sim.on('close', () => setConn('connecting…'));

  sim.on('scenarios', (msg) => {
    state.scenarios = msg.items;
    state.currentKey = msg.default;
    renderScenarioList();
    renderFsScenarioPill();
  });

  sim.on('loaded', (msg) => {
    state.currentKey = msg.key;
    state.detail = msg.detail;
    state.viz = msg.viz || {};
    state.paramValues = Object.assign({}, msg.detail.defaults);
    state.polHistory = [];
    renderParams();
    renderParamsPill();
    renderLegend(msg.viz);
    compass.setViz(msg.viz);
    if (dom.scenarioRow.children.length) updateScenarioSelected();
    renderFsScenarioPill();
  });

  sim.on('tick', (msg) => {
    state.lastSnapshot = msg;
    compass.setSnapshot(msg);
    updateMetrics(msg);
    dom.tickCounter.textContent = `t = ${msg.t.toLocaleString()}`;
    const pct = Math.min(1, msg.t / 5000);
    dom.scrubberFill.style.width = (pct * 100) + '%';
    dom.scrubberThumb.style.left = (pct * 100) + '%';
    state.polHistory.push(msg.metrics.polarization || 0);
    if (state.polHistory.length > state.maxHistory) state.polHistory.shift();
    drawSparkline();
  });

  sim.on('inspect', (msg) => {
    state.inspectorAgent = msg.agent;
    state.pinnedAgentId = msg.agent ? msg.agent.id : null;
    compass.setPinned(state.pinnedAgentId === null ? -1 : state.pinnedAgentId);
    renderInspector();
  });

  sim.connect();
  window.__sim__ = sim;

  // ── Scenarios (vertical-friendly stack in left column) ────────────
  function renderScenarioList() {
    dom.scenarioRow.innerHTML = '';
    for (const s of state.scenarios) {
      const el = document.createElement('div');
      el.className = 'scenario';
      el.dataset.key = s.key;
      el.innerHTML =
        `<span class="lead-tail"><span class="lead">${s.lead}</span><span class="tail">${s.tail}</span></span>` +
        `<span class="arrow">→</span>` +
        `<span class="tagline">${s.tagline || ''}</span>`;
      el.addEventListener('click', () => {
        sim.load(s.key);
        sim.play();
        state.playing = true;
        syncPlayBtn();
      });
      dom.scenarioRow.appendChild(el);
    }
    updateScenarioSelected();
  }

  function updateScenarioSelected() {
    for (const el of dom.scenarioRow.children) {
      el.classList.toggle('selected', el.dataset.key === state.currentKey);
    }
  }

  // ── Parameters: pill (collapsed) ↔ card (expanded) ───────────────
  function setParamsOpen(open) {
    state.paramsOpen = !!open;
    dom.paramsPill.hidden = state.paramsOpen;
    dom.paramsCard.hidden = !state.paramsOpen;
  }
  dom.paramsPill.addEventListener('click', () => setParamsOpen(true));
  dom.paramsClose.addEventListener('click', (ev) => { ev.stopPropagation(); setParamsOpen(false); });

  function renderParamsPill() {
    const params = state.detail?.params || [];
    const first4 = params.slice(0, 4);
    dom.paramsPillChips.innerHTML = first4.map(p => {
      const v = state.paramValues[p.name];
      return `<span class="params-pill-chip">
        <span class="lbl">${p.label}</span>
        <span class="val">${formatValue(v, p.step)}</span>
      </span>`;
    }).join('');
  }

  function renderParams() {
    dom.paramsList.innerHTML = '';
    const params = state.detail.params || [];
    dom.paramsCount.textContent = `${params.length} / 12`;
    for (const p of params) {
      const wrap = document.createElement('div');
      wrap.className = 'slider';
      const value = state.paramValues[p.name];
      wrap.innerHTML = `
        <div class="slider-head">
          <span class="slider-label">
            ${p.label}
            <button class="info-chip" data-info-text="${escapeAttr(p.info)}" data-info-title="${p.label}">i</button>
          </span>
          <span class="slider-value">${formatValue(value, p.step)}</span>
        </div>
        <div class="slider-track">
          <div class="slider-rail"></div>
          <div class="slider-fill"></div>
          <div class="slider-thumb"></div>
          <input type="range" min="${p.min}" max="${p.max}" step="${p.step}" value="${value}" />
        </div>
      `;
      const input = wrap.querySelector('input');
      const fill = wrap.querySelector('.slider-fill');
      const thumb = wrap.querySelector('.slider-thumb');
      const valueLabel = wrap.querySelector('.slider-value');
      const sync = (v) => {
        const pct = (v - p.min) / (p.max - p.min);
        fill.style.width = (pct * 100) + '%';
        thumb.style.left = (pct * 100) + '%';
        valueLabel.textContent = formatValue(v, p.step);
      };
      sync(value);
      input.addEventListener('input', (ev) => {
        const v = Number(ev.target.value);
        state.paramValues[p.name] = v;
        sync(v);
        sim.setParam(p.name, v);
        renderParamsPill();        // keep the chips fresh
      });
      dom.paramsList.appendChild(wrap);
    }
    dom.paramsList.querySelectorAll('.info-chip').forEach(btn => {
      btn.addEventListener('click', (ev) => {
        ev.stopPropagation();
        showInfo(btn, btn.dataset.infoTitle, btn.dataset.infoText);
      });
    });
  }

  function formatValue(v, step) {
    if (v == null || isNaN(v)) return '—';
    if (step >= 1)     return Number(v).toFixed(0);
    if (step >= 0.01)  return Number(v).toFixed(2);
    if (step >= 0.001) return Number(v).toFixed(3);
    return Number(v).toFixed(4);
  }
  function escapeAttr(s) { return (s || '').replace(/"/g, '&quot;'); }

  // ── Legend ────────────────────────────────────────────────────────
  function renderLegend(viz) {
    const colors = viz.group_colors || {};
    const names  = viz.group_names  || {};
    const items  = Object.keys(colors).sort((a, b) => +a - +b);
    if (!items.length) { dom.legendCard.innerHTML = ''; return; }
    const row = document.createElement('div');
    row.className = 'row';
    for (const gid of items) {
      const item = document.createElement('span');
      item.className = 'item';
      item.innerHTML = `<span class="swatch" style="background:${colors[gid]}"></span>${names[gid] || ('Group ' + gid)}`;
      row.appendChild(item);
    }
    dom.legendCard.innerHTML = '';
    dom.legendCard.appendChild(row);
  }

  // ── Metrics (hero KPIs + fullscreen strip) ───────────────────────
  function updateMetrics(snap) {
    const m = snap.metrics;
    const tiles = [
      { label: 'polarization',         value: fmtNum(m.polarization), trend: trendLine(), accent: true },
      { label: 'cross-talk',           value: fmtPct(m.cross_talk),   trend: '↓ as parties split' },
      { label: 'largest faction',      value: fmtPct(m.largest_faction), trend: 'leader share' },
      { label: 'affective polarization', value: m.affect == null ? 'n/a' : fmtSigned(m.affect),
        trend: 'lower = more polarized' },
    ];
    dom.heroStats.innerHTML = tiles.map(t => `
      <div class="stat-tile">
        <div class="stat-label">${t.label}</div>
        <div class="stat-value">${t.value}</div>
        <div class="stat-trend${t.accent ? ' accent' : ''}">${t.trend}</div>
      </div>
    `).join('');
    dom.fsKpis.innerHTML = tiles.map(t => `
      <span class="fs-kpi${t.accent ? ' accent' : ''}">
        <span class="lbl">${t.label}</span>
        <span class="val">${t.value}</span>
        ${t.accent ? `<span class="tr">↑</span>` : ''}
      </span>
    `).join('');
    dom.sparkValue.textContent = fmtNum(m.polarization);
  }

  function trendLine() {
    const h = state.polHistory;
    if (h.length < 6) return '— starting';
    const recent = h[h.length - 1], older = h[Math.max(0, h.length - 30)];
    const diff = recent - older;
    const pct = older > 0 ? (diff / older) * 100 : 0;
    return `${diff >= 0 ? '↑' : '↓'} ${Math.abs(pct).toFixed(0)}% this run`;
  }

  const fmtNum = (v) => v == null || isNaN(v) ? '—' : v.toFixed(2);
  const fmtPct = (v) => v == null || isNaN(v) ? '—' : Math.round(v * 100) + '%';
  const fmtSigned = (v) => v == null || isNaN(v) ? '—' : (v >= 0 ? '+' : '') + v.toFixed(2);
  const signedFixed = (v, n) => (v >= 0 ? '+' : '') + v.toFixed(n);

  // ── Sparkline ─────────────────────────────────────────────────────
  function drawSparkline() {
    const svg = dom.sparkline;
    const h = state.polHistory;
    if (!h.length) { svg.innerHTML = ''; return; }
    const W = 176, H = 28;
    const max = Math.max(0.001, ...h);
    const min = Math.min(0, ...h);
    const norm = (v) => H - 2 - ((v - min) / (max - min || 1)) * (H - 6);
    const xs = h.map((_, i) => (i / (h.length - 1 || 1)) * W);
    const ys = h.map(norm);
    let d = `M${xs[0].toFixed(1)},${ys[0].toFixed(1)}`;
    for (let i = 1; i < h.length; i++) d += ` L${xs[i].toFixed(1)},${ys[i].toFixed(1)}`;
    svg.innerHTML = `
      <line x1="0" y1="14" x2="${W}" y2="14" stroke="var(--border)" stroke-dasharray="2 3"/>
      <path d="${d}" fill="none" stroke="var(--r)" stroke-width="1.5"/>
    `;
  }

  // ── Inspector ─────────────────────────────────────────────────────
  function renderInspector() {
    if (!state.inspectorAgent) {
      dom.inspectorId.textContent = '—';
      dom.inspectorParty.textContent = 'hover any dot';
      dom.inspectorParty.className = 'pos-pill';
      dom.inspectorRows.innerHTML =
        '<div class="inspector-row"><span class="lbl">economic stance</span><span class="val">—</span></div>' +
        '<div class="inspector-row"><span class="lbl">cultural stance</span><span class="val">—</span></div>' +
        '<div class="inspector-row"><span class="lbl">close neighbours</span><span class="val">—</span></div>';
      dom.inspectorMap.innerHTML = '';
      dom.inspectorDiv.textContent = '—';
      dom.inspectorAlike.textContent = '—';
      dom.inspectorRisk.textContent = '—';
      dom.inspectorDiet.hidden = true;
      return;
    }
    const a = state.inspectorAgent;
    dom.inspectorId.textContent = `#${a.id}`;
    const groupNames = state.viz?.group_names || {};
    if (a.party != null) {
      const partyName = groupNames[a.party] || `party ${a.party}`;
      dom.inspectorParty.textContent = partyName;
      dom.inspectorParty.className = 'pos-pill ' + (a.party === 1 ? 'r' : 'b');
    } else {
      dom.inspectorParty.textContent = groupNames[a.group] || `group ${a.group}`;
      dom.inspectorParty.className = 'pos-pill';
    }
    const rows = [
      ['economic stance',  signedFixed(a.x, 2)],
      ['cultural stance',  signedFixed(a.y, 2)],
      ['close neighbours', a.neighbours.length],
    ];
    if (a.identity_strength != null) rows.push(['party loyalty', a.identity_strength.toFixed(2)]);
    // Legacy scalar diet (older scenarios) — show as a row; rich dict diet
    // gets its own section further down with the editable bar.
    if (typeof a.media_diet === 'number') {
      rows.push(['partisan media diet', a.media_diet.toFixed(2)]);
    }
    dom.inspectorRows.innerHTML = rows.map(([k, v]) =>
      `<div class="inspector-row"><span class="lbl">${k}</span><span class="val">${v}</span></div>`
    ).join('');

    renderDietSection(a);
    drawNeighbourhoodMap(a);
    dom.inspectorDiv.textContent = a.diversity.toFixed(2);

    let alike = 0, out = 0;
    for (const n of a.neighbours) {
      if (n.party != null && a.party != null) {
        if (n.party === a.party) alike++; else out++;
      } else if (n.group === a.group) alike++; else out++;
    }
    dom.inspectorAlike.textContent = `${alike} alike · ${out} outlier${out !== 1 ? 's' : ''}`;
    dom.inspectorRisk.textContent = out === 0 ? 'pure echo chamber ↑' :
      (alike / Math.max(1, alike + out) >= 0.7 ? 'echo-chamber risk ↑' : 'cross-cutting exposure');
  }

  // ── Media diet section: stacked bar + preset buttons ─────────────
  function renderDietSection(agent) {
    const outlets = state.viz?.outlets;
    const hasRich = outlets && Array.isArray(outlets) && outlets.length
                    && agent.media_diet && typeof agent.media_diet === 'object';
    if (!hasRich) {
      dom.inspectorDiet.hidden = true;
      return;
    }
    dom.inspectorDiet.hidden = false;
    const diet = agent.media_diet;
    const total = Object.values(diet).reduce((a, b) => a + b, 0) || 1;
    // Order outlets left → right by position.x so bar reads ideologically
    const sortedOutlets = outlets.slice().sort((a, b) => a.position[0] - b.position[0]);
    // Stacked bar
    dom.dietBar.innerHTML = sortedOutlets.map(o => {
      const w = (diet[o.id] || 0) / total;
      if (w < 0.005) return '';
      return `<span class="diet-seg" style="width:${(w * 100).toFixed(1)}%; background:${o.color};"
                title="${o.name} · ${(w * 100).toFixed(0)}%"></span>`;
    }).join('');
    // Top outlet readout
    let top = sortedOutlets[0], topW = 0;
    for (const o of sortedOutlets) {
      const w = (diet[o.id] || 0) / total;
      if (w > topW) { topW = w; top = o; }
    }
    dom.dietTopOutlet.innerHTML = `mostly <strong style="color:${top.color}">${top.name}</strong> · ${(topW * 100).toFixed(0)}%`;

    // Quick presets. Each generates a diet dict.
    const byName = Object.fromEntries(outlets.map(o => [o.name, o]));
    const presetsList = [
      { label: 'Pure Fox',     diet: pureDiet(byName['Fox News']) },
      { label: 'Pure MSNBC',   diet: pureDiet(byName['MSNBC']) },
      { label: 'Mainstream',   diet: mixDiet([byName['New York Times'], byName['Wall St Journal'], byName['Local TV']]) },
      { label: 'Balanced',     diet: balanced(outlets) },
      { label: 'Centrist',     diet: pureDiet(byName['Local TV']) },
    ].filter(p => p.diet);
    dom.dietPresets.innerHTML = presetsList.map((p, i) =>
      `<button class="diet-preset" data-i="${i}">${p.label}</button>`
    ).join('');
    dom.dietPresets.querySelectorAll('.diet-preset').forEach((btn, i) => {
      btn.addEventListener('click', () => {
        sim.setDiet(agent.id, presetsList[i].diet);
      });
    });
  }

  function pureDiet(outlet) {
    if (!outlet) return null;
    return { [outlet.id]: 1.0 };
  }
  function mixDiet(outlets) {
    const valid = outlets.filter(Boolean);
    if (!valid.length) return null;
    const w = 1 / valid.length;
    return Object.fromEntries(valid.map(o => [o.id, w]));
  }
  function balanced(outlets) {
    return Object.fromEntries(outlets.map(o => [o.id, 1]));
  }

  function drawNeighbourhoodMap(a) {
    const svg = dom.inspectorMap;
    const W = 220, H = 72;
    const cx = W / 2, cy = H / 2 + 4;
    const neighbours = a.neighbours.slice(0, 6);
    const placed = neighbours.map((n, i) => {
      const angle = (i / neighbours.length) * Math.PI * 2 - Math.PI / 2;
      return { ...n, nx: cx + Math.cos(angle) * 80, ny: cy + Math.sin(angle) * 22 };
    });
    const lines = placed.map(n => `<line x1="${cx}" y1="${cy}" x2="${n.nx}" y2="${n.ny}" stroke="var(--border)" stroke-width=".9" />`).join('');
    const ringColor = a.party != null ? (a.party === 1 ? 'var(--r)' : 'var(--b)') : 'var(--ink)';
    const dots = placed.map(n => {
      const c = n.party != null ? (n.party === 1 ? 'var(--r)' : 'var(--b)') : 'var(--ink-3)';
      return `<circle cx="${n.nx}" cy="${n.ny}" r="5" fill="${c}" opacity=".75" />`;
    }).join('');
    svg.innerHTML = `
      ${lines}
      ${dots}
      <circle cx="${cx}" cy="${cy}" r="10" fill="none" stroke="${ringColor}" stroke-width="1.25" />
      <circle cx="${cx}" cy="${cy}" r="5" fill="${ringColor}" />
    `;
  }

  // ── Canvas hover / click ─────────────────────────────────────────
  dom.canvas.addEventListener('mousemove', (ev) => {
    const r = dom.canvas.getBoundingClientRect();
    const idx = compass.pickAgent(ev.clientX - r.left, ev.clientY - r.top, 12);
    compass.setHover(idx);
  });
  dom.canvas.addEventListener('mouseleave', () => compass.setHover(-1));
  dom.canvas.addEventListener('click', (ev) => {
    const r = dom.canvas.getBoundingClientRect();
    const idx = compass.pickAgent(ev.clientX - r.left, ev.clientY - r.top, 14);
    if (idx >= 0 && state.lastSnapshot) {
      sim.selectAgent(idx);
    } else {
      sim.selectAgent(null);
      state.pinnedAgentId = null;
      compass.setPinned(-1);
      state.inspectorAgent = null;
      renderInspector();
    }
  });

  // ── Transport ─────────────────────────────────────────────────────
  function syncPlayBtn() {
    dom.btnPlay.querySelector('span').textContent = state.playing ? '⏸' : '▶';
  }
  dom.btnPlay.addEventListener('click', () => {
    state.playing = !state.playing;
    if (state.playing) sim.play(); else sim.pause();
    syncPlayBtn();
  });
  dom.btnStep.addEventListener('click', () => { sim.pause(); state.playing = false; syncPlayBtn(); sim.step(); });
  dom.btnReset.addEventListener('click', () => { sim.reset(); state.polHistory = []; });

  dom.speedPills.querySelectorAll('span').forEach(pill => {
    pill.addEventListener('click', () => {
      const fps = Number(pill.dataset.fps);
      state.fps = fps;
      sim.setSpeed(fps);
      dom.speedPills.querySelectorAll('span').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
    });
  });

  // ── Fullscreen ────────────────────────────────────────────────────
  function setFullscreen(on) {
    document.body.classList.toggle('fullscreen', on);
    requestAnimationFrame(() => requestAnimationFrame(() => compass._resize()));
  }
  dom.openFs.addEventListener('click', () => setFullscreen(true));
  dom.exitFs.addEventListener('click', () => setFullscreen(false));
  window.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape' && document.body.classList.contains('fullscreen')) {
      setFullscreen(false);
    }
  });

  dom.fsScenarioPill.addEventListener('click', () => {
    if (!state.scenarios.length) return;
    const i = state.scenarios.findIndex(s => s.key === state.currentKey);
    const next = state.scenarios[(i + 1) % state.scenarios.length];
    sim.load(next.key); sim.play(); state.playing = true; syncPlayBtn();
  });
  function renderFsScenarioPill() {
    const s = state.scenarios.find(x => x.key === state.currentKey);
    if (!s) return;
    dom.fsScenarioPill.querySelector('.fs-sp-name').textContent = `${s.lead} ${s.tail}`;
  }

  // ── Dark mode ─────────────────────────────────────────────────────
  dom.modeToggle.addEventListener('click', () => {
    const dark = !document.body.classList.contains('dark');
    document.body.classList.toggle('dark', dark);
    document.body.classList.toggle('light', !dark);
    localStorage.setItem('mode', dark ? 'dark' : 'light');
    compass.setDarkMode(dark);
  });
  if (localStorage.getItem('mode') === 'dark') {
    document.body.classList.add('dark');
    document.body.classList.remove('light');
    compass.setDarkMode(true);
  }

  // ── Info popovers ─────────────────────────────────────────────────
  document.addEventListener('click', (ev) => {
    const chip = ev.target.closest('.info-chip');
    if (chip && chip.dataset.info) {
      ev.stopPropagation();
      showInfo(chip, chip.dataset.info, INFO_TEXTS[chip.dataset.info] || '');
      return;
    }
    if (chip && chip.dataset.infoText) {
      ev.stopPropagation();
      showInfo(chip, chip.dataset.infoTitle, chip.dataset.infoText);
      return;
    }
    if (!ev.target.closest('.info-pop')) {
      dom.infoPop.hidden = true;
    }
  });

  function showInfo(anchor, title, body) {
    dom.infoPopTitle.textContent = (title || '').toUpperCase();
    dom.infoPopBody.textContent = body || '';
    dom.infoPop.hidden = false;
    const r = anchor.getBoundingClientRect();
    const popW = 280;
    let left = r.left + r.width / 2 - popW / 2;
    if (left < 12) left = 12;
    if (left + popW > window.innerWidth - 12) left = window.innerWidth - popW - 12;
    let top = r.bottom + 8;
    const popH = 120;
    if (top + popH > window.innerHeight - 12) top = r.top - popH - 8;
    dom.infoPop.style.left = left + 'px';
    dom.infoPop.style.top = top + 'px';
  }

  const INFO_TEXTS = {
    neighbourhood:
      'The six nearest agents on the compass right now. Colours = their party. ' +
      'Diversity = mean distance to those six — low diversity means a tight bubble.',
    'media-diet':
      'What this person reads, watches, and scrolls — each outlet weighted by how ' +
      'much of their attention it gets. They drift toward the weighted average of ' +
      'these outlets\' positions. Click a preset to rewire their diet and watch them move.',
  };

  // ── Connection chip ───────────────────────────────────────────────
  function setConn(text) {
    if (text === 'connected') {
      dom.connStatus.textContent = '● connected';
      dom.connStatus.classList.add('ok');
    } else {
      dom.connStatus.textContent = text;
      dom.connStatus.classList.remove('ok');
    }
  }

  // ── Init ──────────────────────────────────────────────────────────
  syncPlayBtn();
  setParamsOpen(false);
  setConn('connecting…');
})();
