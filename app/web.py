from __future__ import annotations

from fastapi.responses import HTMLResponse


def render_panel_html() -> HTMLResponse:
    html = """
<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>qq-login-adapter 面板</title>
  <style>
    body { font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif; margin: 0; background: #0b1020; color: #e5e7eb; }
    .wrap { max-width: 1100px; margin: 0 auto; padding: 24px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; }
    .card { background: #121933; border: 1px solid #26304f; border-radius: 14px; padding: 16px; }
    h1,h2 { margin: 0 0 12px; }
    input, textarea, button { width: 100%; box-sizing: border-box; border-radius: 10px; border: 1px solid #334155; background: #0f172a; color: #e5e7eb; padding: 10px 12px; margin-top: 8px; }
    button { background: #2563eb; cursor: pointer; }
    button:hover { background: #1d4ed8; }
    pre { white-space: pre-wrap; word-break: break-word; background: #020617; padding: 12px; border-radius: 10px; overflow: auto; }
    .row { display: flex; gap: 8px; }
    .row > * { flex: 1; }
    .muted { color: #94a3b8; font-size: 13px; }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <h1>qq-login-adapter 面板</h1>
    <p class=\"muted\">登录状态 / Watchdog / 消息收发 / 最近事件</p>
    <div class=\"grid\">
      <div class=\"card\">
        <h2>状态</h2>
        <button onclick=\"loadStatus()\">刷新状态</button>
        <pre id=\"status\">loading...</pre>
      </div>
      <div class=\"card\">
        <h2>Watchdog</h2>
        <div class=\"row\"><input id=\"interval\" value=\"30\" /><button onclick=\"watchdogStart()\">启动</button></div>
        <div class=\"row\"><button onclick=\"watchdogCheck()\">单次检查</button><button onclick=\"watchdogStop()\">停止</button></div>
        <pre id=\"watchdog\">-</pre>
      </div>
      <div class=\"card\">
        <h2>发送私聊</h2>
        <input id=\"privateUserId\" placeholder=\"user_id\" />
        <textarea id=\"privateMessage\" rows=\"4\" placeholder=\"消息内容\"></textarea>
        <button onclick=\"sendPrivate()\">发送私聊</button>
        <pre id=\"privateResult\">-</pre>
      </div>
      <div class=\"card\">
        <h2>发送群聊</h2>
        <input id=\"groupId\" placeholder=\"group_id\" />
        <textarea id=\"groupMessage\" rows=\"4\" placeholder=\"消息内容\"></textarea>
        <button onclick=\"sendGroup()\">发送群聊</button>
        <pre id=\"groupResult\">-</pre>
      </div>
      <div class=\"card\">
        <h2>登录辅助</h2>
        <div class=\"row\"><button onclick=\"startQr()\">获取二维码</button><button onclick=\"exportQr()\">导出二维码</button></div>
        <pre id=\"loginResult\">-</pre>
      </div>
      <div class=\"card\">
        <h2>插件/Handlers</h2>
        <div class=\"row\"><button onclick=\"handlersReload()\">重载 handlers</button><button onclick=\"loadStatus()\">刷新状态</button></div>
        <pre id=\"handlers\">-</pre>
      </div>
      <div class=\"card\">
        <h2>最近消息</h2>
        <button onclick=\"loadMessages()\">刷新消息</button>
        <pre id=\"messages\">-</pre>
      </div>
    </div>
  </div>
  <script>
    async function j(url, options={}) { const r = await fetch(url, {headers:{'Content-Type':'application/json'}, ...options}); return await r.json(); }
    function show(id, data) { document.getElementById(id).textContent = JSON.stringify(data, null, 2); }
    async function loadStatus(){ const s = await j('/healthz'); show('status', s); show('watchdog', await j('/watchdog/status')); show('handlers', {loaded: (s.handlers||{}), registry: (s.handler_registry||[])}); }
    async function loadMessages(){ show('messages', await j('/messages')); }
    async function watchdogStart(){ const interval_seconds = Number(document.getElementById('interval').value || 30); show('watchdog', await j('/watchdog/start', {method:'POST', body: JSON.stringify({interval_seconds})})); }
    async function watchdogCheck(){ show('watchdog', await j('/watchdog/check', {method:'POST', body: '{}'})); }
    async function watchdogStop(){ show('watchdog', await j('/watchdog/stop', {method:'POST', body: '{}'})); }
    async function sendPrivate(){ const user_id = Number(document.getElementById('privateUserId').value); const message = document.getElementById('privateMessage').value; show('privateResult', await j('/message/private', {method:'POST', body: JSON.stringify({user_id, message})})); loadMessages(); }
    async function sendGroup(){ const group_id = Number(document.getElementById('groupId').value); const message = document.getElementById('groupMessage').value; show('groupResult', await j('/message/group', {method:'POST', body: JSON.stringify({group_id, message})})); loadMessages(); }
    async function startQr(){ show('loginResult', await j('/login/qrcode', {method:'POST', body: JSON.stringify({account:''})})); }
    async function exportQr(){ show('loginResult', await j('/login/qrcode/export')); }
    async function handlersReload(){ show('handlers', await j('/handlers/reload', {method:'POST', body:'{}'})); await loadStatus(); }
    loadStatus();
    loadMessages();
  </script>
</body>
</html>
"""
    return HTMLResponse(html)
