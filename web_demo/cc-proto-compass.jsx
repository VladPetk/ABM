// Calm to Camps — prototype compass (canvas-rendered for smooth animation)
// Draws the real agent cloud at a fractional tick. Crowd dots coloured by
// party; the spotlighted character is ringed with their ego edges + neighbours.
// Counterfactual mode overlays the baseline cloud (hollow ghosts) under the
// intervention cloud (solid) so divergence is visible as it accrues.

function ProtoCompass({ tick, run, baselineRun = null, spotlightIdx = 86, mode = 'normal' }) {
  const canvasRef = React.useRef(null);
  const SZ = 1100;            // internal resolution
  const C = SZ / 2, HALF = SZ * 0.40;
  const mx = (x) => C + x * HALF;
  const my = (y) => C - y * HALF;   // y hi (Traditional) → top, matches engine axes

  React.useEffect(() => {
    const cv = canvasRef.current; if (!cv) return;
    const ctx = cv.getContext('2d');
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    if (cv.width !== SZ * dpr) { cv.width = SZ * dpr; cv.height = SZ * dpr; }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, SZ, SZ);

    const isCF = mode === 'counterfactual';
    const dotR = SZ * 0.0075;

    // gridlines
    ctx.strokeStyle = CC.border; ctx.lineWidth = 1;
    [-0.5, 0.5].forEach((g) => {
      ctx.beginPath(); ctx.moveTo(mx(g), my(-1)); ctx.lineTo(mx(g), my(1)); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(mx(-1), my(g)); ctx.lineTo(mx(1), my(g)); ctx.stroke();
    });
    // axes
    ctx.strokeStyle = CC.borderS; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(mx(0), my(-1)); ctx.lineTo(mx(0), my(1)); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(mx(-1), my(0)); ctx.lineTo(mx(1), my(0)); ctx.stroke();

    // quadrant labels (engine axes: x Redistributive→Laissez-faire, y Progressive→Traditional)
    ctx.fillStyle = CC.ink4; ctx.font = 'italic 26px Newsreader, Georgia, serif';
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'left';  ctx.fillText('populist', mx(-0.95), my(0.92));
    ctx.textAlign = 'right'; ctx.fillText('traditional right', mx(0.95), my(0.92));
    ctx.textAlign = 'left';  ctx.fillText('progressive left', mx(-0.95), my(-0.92));
    ctx.textAlign = 'right'; ctx.fillText('libertarian', mx(0.95), my(-0.92));

    // axis end labels
    ctx.fillStyle = CC.ink3; ctx.font = '500 23px Geist, system-ui, sans-serif';
    ctx.textAlign = 'left';   ctx.fillText('← redistributive', mx(-1), C - 22);
    ctx.textAlign = 'right';  ctx.fillText('laissez-faire →', mx(1), C - 22);
    ctx.textAlign = 'center';
    ctx.fillText('traditional', C, my(1) - 20);
    ctx.fillText('progressive', C, my(-1) + 22);

    const pos = posAt(run, tick);
    const party = run.party[Math.round(tick)];

    // Draw the crowd with a replacement crossfade. A cohort replacement is a
    // new person in an existing slot — NOT the same dot teleporting — so for
    // the ~FADE_TICKS after a replacement we fade the departing person out at
    // their old spot (their party colour) and fade the arriving person in at
    // the new spot. Outside that window each agent is a single dot.
    const drawDot = (x, y, color, alpha, hollow) => {
      ctx.globalAlpha = alpha;
      ctx.beginPath(); ctx.arc(mx(x), my(y), dotR, 0, 6.283);
      if (hollow) { ctx.strokeStyle = color; ctx.stroke(); } else { ctx.fillStyle = color; ctx.fill(); }
    };
    const drawCrowd = (r, baseAlpha, hollow) => {
      const P = posAt(r, tick);
      const PA = r.party[Math.round(tick)];
      const fades = replacementFades(r, tick);
      ctx.lineWidth = 1.4;
      for (let i = 0; i < P.length; i++) {
        const f = fades.get(i);
        if (f) {
          drawDot(f.fromPos[0], f.fromPos[1], partyColor(f.fromParty), baseAlpha * f.outAlpha, hollow);
          drawDot(P[i][0], P[i][1], partyColor(PA[i]), baseAlpha * f.inAlpha, hollow);
        } else {
          drawDot(P[i][0], P[i][1], partyColor(PA[i]), baseAlpha, hollow);
        }
      }
    };

    if (isCF && baselineRun) {
      drawCrowd(baselineRun, 0.22, true);   // ghost = baseline (hollow)
      drawCrowd(run, 0.62, false);          // solid = intervention
    } else {
      drawCrowd(run, spotlightIdx != null ? 0.46 : 0.85, false);
    }
    ctx.globalAlpha = 1;

    // spotlight ego network + node
    if (spotlightIdx != null) {
      const sp = agentPosAt(run, tick, spotlightIdx);
      const edges = egoEdges(run, tick, spotlightIdx);
      ctx.strokeStyle = CC.ink2;
      edges.forEach((e) => {
        const other = e[0] === spotlightIdx ? e[1] : e[0];
        const op = pos[other]; if (!op) return;
        const cross = e[2] === 1;
        ctx.globalAlpha = cross ? 0.18 : 0.4; ctx.lineWidth = cross ? 1 : 1.6;
        ctx.beginPath(); ctx.moveTo(mx(sp[0]), my(sp[1])); ctx.lineTo(mx(op[0]), my(op[1])); ctx.stroke();
      });
      // neighbour dots emphasised
      ctx.globalAlpha = 0.95;
      edges.forEach((e) => {
        const other = e[0] === spotlightIdx ? e[1] : e[0];
        const op = pos[other]; if (!op) return;
        ctx.fillStyle = partyColor(party[other]);
        ctx.beginPath(); ctx.arc(mx(op[0]), my(op[1]), dotR + 1.5, 0, 6.283); ctx.fill();
      });
      ctx.globalAlpha = 1;
      // the character
      const r = SZ * 0.018;
      ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(mx(sp[0]), my(sp[1]), r + 5, 0, 6.283); ctx.fill();
      ctx.fillStyle = partyColor(party[spotlightIdx]); ctx.beginPath(); ctx.arc(mx(sp[0]), my(sp[1]), r, 0, 6.283); ctx.fill();
      ctx.strokeStyle = CC.ink; ctx.lineWidth = 2.4; ctx.beginPath(); ctx.arc(mx(sp[0]), my(sp[1]), r + 5, 0, 6.283); ctx.stroke();
      ctx.fillStyle = CC.ink; ctx.font = '600 26px Geist, system-ui, sans-serif'; ctx.textAlign = 'center';
      ctx.fillText(D.chars[Object.keys(D.chars).find((k) => D.chars[k].agent_index === spotlightIdx)]?.name || '', mx(sp[0]), my(sp[1]) - r - 18);
    }
  }, [tick, run, baselineRun, spotlightIdx, mode]);

  return <canvas ref={canvasRef} style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }} />;
}

window.ProtoCompass = ProtoCompass;
