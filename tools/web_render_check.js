#!/usr/bin/env node
// web_render_check.js — drive headless Chrome over CDP, wait REAL wall-clock time for
// the engine to boot, then capture the canvas.
//
// The trap this avoids: `chrome --headless --screenshot` captures at the load event,
// which for a 37 MB Godot wasm build is BEFORE the engine has drawn anything. The
// result is a picture of the Godot loading screen (the template's #242424 background
// plus the progress bar) that looks like "a dark screen" and gets misread as a broken
// build. Over CDP we can wait for real time to pass and for the engine to log its
// banner, then capture.
//
// --enable-unsafe-swiftshader --use-angle=swiftshader (set by the caller) is what
// gives headless Chrome a WebGL2 context; without it the engine never gets a renderer.
//
// Env: OUT_FILE (png path to write), WEB_URL, CDP_PORT, WAIT_MS (default 15000).

const fs = require('fs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const PORT = process.env.CDP_PORT || '9222';
const URL = process.env.WEB_URL;
const OUT = process.env.OUT_FILE;
const WAIT = parseInt(process.env.WAIT_MS || '15000', 10);

(async () => {
  let page = null;
  for (let i = 0; i < 40 && !page; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
      page = list.find((t) => t.type === 'page' && t.webSocketDebuggerUrl);
    } catch (e) { /* browser not up yet */ }
    if (!page) await sleep(1000);
  }
  if (!page) { console.error('   no CDP page target'); process.exit(1); }

  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0;
  const pend = {};
  const logs = [];
  const send = (method, params = {}) =>
    new Promise((res) => { const i = ++id; pend[i] = res; ws.send(JSON.stringify({ id: i, method, params })); });

  await new Promise((r) => { ws.onopen = r; });
  ws.onmessage = (e) => {
    const m = JSON.parse(e.data);
    if (m.id && pend[m.id]) { pend[m.id](m.result); delete pend[m.id]; }
    if (m.method === 'Runtime.consoleAPICalled') {
      logs.push((m.params.args || []).map((a) => a.value ?? a.description ?? a.type).join(' '));
    }
    if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error') {
      logs.push('ERROR: ' + m.params.entry.text);
    }
  };

  await send('Runtime.enable');
  await send('Log.enable');
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride',
    { width: 720, height: 1280, deviceScaleFactor: 1, mobile: true });
  await send('Page.navigate', { url: URL });
  await sleep(WAIT);

  const shot = await send('Page.captureScreenshot', { format: 'png' });
  if (!shot || !shot.data) { console.error('   capture failed'); process.exit(2); }
  fs.writeFileSync(OUT, Buffer.from(shot.data, 'base64'));

  const banner = logs.filter((l) => /Godot Engine|OpenGL API|ERROR/i.test(l));
  console.log('   engine log:');
  banner.slice(0, 6).forEach((l) => console.log('     ' + l));
  const booted = logs.some((l) => /Godot Engine v4/.test(l));
  const gl = logs.some((l) => /OpenGL API/.test(l));
  if (!booted) { console.error('   engine never booted'); process.exit(3); }
  if (!gl) { console.error('   engine booted without a GL context'); process.exit(4); }
  process.exit(0);
})();
