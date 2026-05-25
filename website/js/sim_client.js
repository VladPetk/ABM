/* WebSocket bridge to the Python engine (abm.web.server).
   Auto-reconnects with exponential backoff. Pure DOM-free. */

class SimClient {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.connected = false;
    this.backoff = 500;          // ms
    this.maxBackoff = 8000;
    this.handlers = {};          // type -> [fn]
    this.queue = [];             // outbound queue while disconnected
  }

  connect() {
    try {
      this.ws = new WebSocket(this.url);
    } catch (e) {
      console.error('WS construct failed', e);
      setTimeout(() => this.connect(), this.backoff);
      this.backoff = Math.min(this.maxBackoff, this.backoff * 2);
      return;
    }

    this.ws.onopen = () => {
      this.connected = true;
      this.backoff = 500;
      this._emit('open');
      // Flush queued messages
      while (this.queue.length && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(this.queue.shift());
      }
    };

    this.ws.onmessage = (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch { return; }
      const t = msg.type;
      this._emit(t, msg);
    };

    this.ws.onclose = () => {
      this.connected = false;
      this._emit('close');
      setTimeout(() => this.connect(), this.backoff);
      this.backoff = Math.min(this.maxBackoff, this.backoff * 2);
    };

    this.ws.onerror = (e) => {
      console.warn('WS error', e);
    };
  }

  on(type, fn) {
    if (!this.handlers[type]) this.handlers[type] = [];
    this.handlers[type].push(fn);
  }

  _emit(type, msg) {
    const fns = this.handlers[type] || [];
    for (const fn of fns) {
      try { fn(msg); } catch (e) { console.error(`handler ${type}`, e); }
    }
  }

  send(msg) {
    const data = JSON.stringify(msg);
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(data);
    } else {
      this.queue.push(data);
    }
  }

  load(scenario, params)   { this.send({ type: 'load', scenario, params: params || {} }); }
  play()                   { this.send({ type: 'play' }); }
  pause()                  { this.send({ type: 'pause' }); }
  step()                   { this.send({ type: 'step' }); }
  reset()                  { this.send({ type: 'reset' }); }
  setParam(name, value)    { this.send({ type: 'param', name, value }); }
  setSpeed(fps)            { this.send({ type: 'speed', value: fps }); }
  selectAgent(id)          { this.send({ type: 'select_agent', id }); }
  setDiet(agent_id, diet)  { this.send({ type: 'set_diet', agent_id, diet }); }
}

window.SimClient = SimClient;
