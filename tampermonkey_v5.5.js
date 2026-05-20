// ==UserScript==
// @name         EMB Data Sender V5.5 (Host Manager + Auto-Detect + App Info)
// @namespace    http://tampermonkey.net/
// @version      5.5
// @description  TX buttons + floating panel: toggle host, app name display, ping status, reset/close/new. Double-click status to edit host manually.
// @author       Antigravity
// @match        https://portal.godgroup.com/design/manual-embroidery*
// @grant        GM_xmlhttpRequest
// @grant        GM_setValue
// @grant        GM_getValue
// ==/UserScript==

(function () {
    'use strict';

    // ── CONFIG ────────────────────────────────────────────────────────────────
    const DEFAULT_HOST  = "http://127.0.0.1:5000";
    const RECEIVE_PATH  = "/receive";
    const INFO_PATH     = "/info";          // GET endpoint trả { name, version }
    const PING_INTERVAL = 8000;             // ms giữa các lần ping
    const AUTO_DETECT_PORTS = [5000, 5001, 5002, 8000, 8080]; // Cổng auto-detect
    const PROCESSED_ATTR = "data-tx-done";
    const STORAGE_HOST  = "emb_host";
    const STORAGE_ON    = "emb_enabled";

    // ── STATE ─────────────────────────────────────────────────────────────────
    let host      = GM_getValue(STORAGE_HOST, DEFAULT_HOST).replace(/\/+$/, '');
    let enabled   = GM_getValue(STORAGE_ON, true);
    let sentCount = 0;
    let pingTimer = null;
    let connState = 'idle'; // idle | ok | err
    let autoDetecting = false;

    function getUrl(path) { return host + path; }

    // ── STYLES ────────────────────────────────────────────────────────────────
    const css = document.createElement('style');
    css.textContent = `
        .tx-btn{background:#ff003c;color:#fff;border:none;padding:2px 6px;font-size:10px;
            font-weight:bold;border-radius:3px;cursor:pointer;margin-right:8px;
            display:inline-block;vertical-align:middle}
        .tx-btn:hover{background:#ff4466}

        #emb-wrap{position:fixed;bottom:16px;right:16px;z-index:999999;font-family:monospace;user-select:none}

        #emb-panel{background:#111;color:#eee;border:1px solid #2a2a2a;border-radius:8px;
            width:234px;box-shadow:0 4px 20px rgba(0,0,0,.6)}

        #emb-hdr{background:#0d0d0d;padding:7px 10px;display:flex;align-items:center;
            gap:6px;cursor:move;border-radius:8px 8px 0 0;border-bottom:1px solid #222}
        #emb-hdr-title{flex:1;font-weight:bold;color:#ff003c;font-size:11px;letter-spacing:.5px}
        #emb-hdr button{background:none;border:none;color:#555;cursor:pointer;
            font-size:14px;line-height:1;padding:0 2px}
        #emb-hdr button:hover{color:#eee}

        #emb-body{padding:8px 10px;display:flex;flex-direction:column;gap:6px}

        #emb-conn-row{display:flex;align-items:center;gap:6px;cursor:pointer;
            padding:3px 4px;border-radius:4px;transition:background .2s}
        #emb-conn-row:hover{background:#1a1a1a}
        #emb-conn-row-hint{font-size:9px;color:#333;text-align:center;margin-top:-3px}

        #emb-dot{width:8px;height:8px;border-radius:50%;background:#555;flex-shrink:0;
            transition:background .3s}
        #emb-conn-label{font-size:10px;font-weight:bold;color:#555;transition:color .3s}
        #emb-ping-ms{font-size:10px;color:#444;margin-left:auto}

        #emb-autodetect-row{display:none;align-items:center;gap:4px;padding:4px 6px;
            background:#0d0d0d;border:1px solid #1a2a1a;border-radius:4px}
        #emb-autodetect-row.visible{display:flex}
        #emb-autodetect-status{font-size:9px;color:#555;flex:1}
        #emb-btn-autodetect{flex:0 0 auto;padding:2px 6px;border-radius:3px;border:1px solid #1a3a1a;
            background:#0a1a0a;color:#00cc44;cursor:pointer;font-size:9px;font-family:monospace}
        #emb-btn-autodetect:hover{background:#102010}

        #emb-app-box{background:#0d0d0d;border:1px solid #222;border-radius:4px;padding:5px 8px;
            transition:border-color .3s,background .3s}
        #emb-app-label{font-size:9px;color:#444;margin-bottom:2px}
        #emb-app-name{font-size:11px;color:#555;transition:color .3s}

        #emb-host-box{background:#0d0d0d;border:1px solid #2a2a2a;border-radius:4px;padding:4px 8px}
        #emb-host-label{font-size:9px;color:#444;margin-bottom:1px}
        #emb-host-val{font-size:11px;color:#aaa;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        #emb-host-input{display:none;width:100%;box-sizing:border-box;background:#0d0d0d;
            border:1px solid #555;border-radius:4px;color:#0f0;font-size:11px;
            padding:4px 8px;font-family:monospace;outline:none}
        #emb-host-input:focus{border-color:#ff003c}

        .emb-row{display:flex;gap:4px}
        .emb-row button{flex:1;padding:3px 0;border-radius:4px;border:1px solid #333;
            background:#1a1a1a;color:#888;cursor:pointer;font-size:10px;font-family:monospace;
            transition:background .15s,color .15s}
        .emb-row button:hover{background:#2a2a2a;color:#eee}
        .emb-row button.on{border-color:#1a3a1a;background:#0a1a0a;color:#00cc44}
        .emb-row button.on:hover{background:#102010}
        .emb-row button.off{border-color:#333;background:#1a1a1a;color:#555}
        .emb-row button.danger{border-color:#cc2200;color:#ff4422;background:transparent}
        .emb-row button.danger:hover{background:#1a0500}
        .emb-row button.accent{border-color:#ff003c;color:#ff003c;background:transparent}
        .emb-row button.accent:hover{background:#1a0010}

        #emb-status{font-size:10px;color:#444;text-align:center;min-height:13px;transition:color .3s}
        #emb-status.ok{color:#00cc44} #emb-status.err{color:#ff4422} #emb-status.warn{color:#ff9900}

        #emb-min{display:none;position:fixed;bottom:16px;right:16px;
            background:#ff003c;color:#fff;border:none;border-radius:6px;
            padding:5px 10px;font-size:11px;font-weight:bold;font-family:monospace;
            cursor:pointer;z-index:999999;box-shadow:0 2px 8px rgba(0,0,0,.5)}
        #emb-min:hover{background:#ff4466}

        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
        .detecting { animation: pulse 1s infinite; }
    `;
    document.head.appendChild(css);

    // ── PANEL DOM ─────────────────────────────────────────────────────────────
    const wrap = document.createElement('div'); wrap.id = 'emb-wrap';
    wrap.innerHTML = `
        <div id="emb-panel">
            <div id="emb-hdr">
                <span id="emb-hdr-title">EMB TX</span>
                <button id="emb-btn-min" title="Thu gọn">–</button>
            </div>
            <div id="emb-body">
                <div id="emb-conn-row" title="Double-click để chỉnh host thủ công">
                    <div id="emb-dot"></div>
                    <span id="emb-conn-label">Đang kiểm tra...</span>
                    <span id="emb-ping-ms"></span>
                </div>
                <div id="emb-conn-row-hint">⬆ Double-click để sửa host thủ công</div>
                <div id="emb-autodetect-row">
                    <span id="emb-autodetect-status">Không kết nối được...</span>
                    <button id="emb-btn-autodetect">🔍 Tìm</button>
                </div>
                <div id="emb-app-box">
                    <div id="emb-app-label">Ứng dụng</div>
                    <div id="emb-app-name">—</div>
                </div>
                <div id="emb-host-box">
                    <div id="emb-host-label">Host</div>
                    <div id="emb-host-val"></div>
                    <input id="emb-host-input" type="text" />
                </div>
                <div class="emb-row">
                    <button id="emb-btn-toggle"></button>
                    <button id="emb-btn-edit">✎ Edit</button>
                    <button id="emb-btn-save" style="display:none">✓ Save</button>
                    <button id="emb-btn-reset" title="Reset về mặc định">⟳</button>
                </div>
                <div class="emb-row">
                    <button id="emb-btn-close" class="danger">✕ Đóng host</button>
                    <button id="emb-btn-new"   class="accent">＋ New host</button>
                </div>
                <div id="emb-status"></div>
            </div>
        </div>
    `;
    document.body.appendChild(wrap);

    const minBtn = document.createElement('button'); minBtn.id = 'emb-min'; minBtn.textContent = '▲ TX';
    document.body.appendChild(minBtn);

    // ── REFS ──────────────────────────────────────────────────────────────────
    const panel           = wrap.querySelector('#emb-panel');
    const dot             = wrap.querySelector('#emb-dot');
    const connLabel       = wrap.querySelector('#emb-conn-label');
    const connRow         = wrap.querySelector('#emb-conn-row');
    const connHint        = wrap.querySelector('#emb-conn-row-hint');
    const pingMs          = wrap.querySelector('#emb-ping-ms');
    const autoDetectRow   = wrap.querySelector('#emb-autodetect-row');
    const autoDetectStatus= wrap.querySelector('#emb-autodetect-status');
    const btnAutoDetect   = wrap.querySelector('#emb-btn-autodetect');
    const appBox          = wrap.querySelector('#emb-app-box');
    const appName         = wrap.querySelector('#emb-app-name');
    const hostVal         = wrap.querySelector('#emb-host-val');
    const hostInput       = wrap.querySelector('#emb-host-input');
    const btnToggle       = wrap.querySelector('#emb-btn-toggle');
    const btnEdit         = wrap.querySelector('#emb-btn-edit');
    const btnSave         = wrap.querySelector('#emb-btn-save');
    const btnReset        = wrap.querySelector('#emb-btn-reset');
    const btnClose        = wrap.querySelector('#emb-btn-close');
    const btnNew          = wrap.querySelector('#emb-btn-new');
    const btnMin          = wrap.querySelector('#emb-btn-min');
    const statusEl        = wrap.querySelector('#emb-status');

    // ── UI HELPERS ────────────────────────────────────────────────────────────
    function setStatus(msg, type, ms) {
        statusEl.textContent = msg; statusEl.className = type || '';
        if (ms !== 0) setTimeout(() => { statusEl.textContent = ''; statusEl.className = ''; }, ms || 2500);
    }

    function applyConnState(state, appText, latency) {
        connState = state;
        const cfg = {
            ok:   { dot:'#00cc44', label:'Đang kết nối',   lc:'#00cc44' },
            err:  { dot:'#ff4422', label:'Mất kết nối',    lc:'#ff4422' },
            idle: { dot:'#555',    label:'Đã tắt',          lc:'#555'   }
        }[state] || {};
        dot.style.background  = cfg.dot;
        connLabel.style.color = cfg.lc;
        connLabel.textContent = cfg.label;
        pingMs.textContent    = latency != null ? `${latency}ms` : '';

        // Show auto-detect row only when error state
        autoDetectRow.classList.toggle('visible', state === 'err');

        if (state === 'ok') {
            autoDetectRow.classList.remove('visible');
            appBox.style.background   = '#0a1a0a';
            appBox.style.borderColor  = '#1a3a1a';
            appName.style.color       = '#0f0';
            appName.textContent       = appText || '—';
        } else if (state === 'err') {
            autoDetectStatus.textContent = `Không tìm thấy tại: ${host}`;
            appBox.style.background   = '#1a0800';
            appBox.style.borderColor  = '#3a1800';
            appName.style.color       = '#ff6633';
            appName.textContent       = 'Python app offline?';
        } else {
            autoDetectRow.classList.remove('visible');
            appBox.style.background   = '#0d0d0d';
            appBox.style.borderColor  = '#222';
            appName.style.color       = '#444';
            appName.textContent       = '— không kết nối —';
        }
    }

    function renderToggle() {
        if (enabled) {
            btnToggle.textContent = '● Bật';
            btnToggle.className   = 'on';
        } else {
            btnToggle.textContent = '○ Tắt';
            btnToggle.className   = 'off';
        }
    }

    function renderHost() { hostVal.textContent = host; }

    function showEditMode(on) {
        hostInput.style.display = on ? 'block' : 'none';
        hostVal.style.display   = on ? 'none'  : 'block';
        btnEdit.style.display   = on ? 'none'  : '';
        btnSave.style.display   = on ? ''      : 'none';
        connHint.style.display  = on ? 'none'  : '';
        if (on) { hostInput.value = host; hostInput.focus(); hostInput.select(); }
    }

    // ── AUTO-DETECT HOST ─────────────────────────────────────────────────────
    function tryHost(candidate) {
        return new Promise(resolve => {
            GM_xmlhttpRequest({
                method: 'GET',
                url: candidate + INFO_PATH,
                timeout: 1500,
                onload(r) {
                    try {
                        const d = JSON.parse(r.responseText);
                        resolve({ ok: true, host: candidate, appText: (d.name || 'Unknown') + (d.version ? ' v' + d.version : '') });
                    } catch { resolve({ ok: true, host: candidate, appText: 'Kết nối OK' }); }
                },
                onerror()   { resolve({ ok: false }); },
                ontimeout() { resolve({ ok: false }); }
            });
        });
    }

    async function autoDetectHost() {
        if (autoDetecting) return;
        autoDetecting = true;
        btnAutoDetect.textContent = '⏳';
        btnAutoDetect.disabled = true;
        autoDetectStatus.textContent = 'Đang tự động tìm...';
        autoDetectStatus.classList.add('detecting');

        // Build candidate list: localhost + LAN IPs × ports
        const candidates = [];
        for (const port of AUTO_DETECT_PORTS) {
            candidates.push(`http://127.0.0.1:${port}`);
            candidates.push(`http://localhost:${port}`);
        }

        for (const candidate of candidates) {
            autoDetectStatus.textContent = `Thử: ${candidate}`;
            const result = await tryHost(candidate);
            if (result.ok) {
                autoDetectStatus.textContent = `✓ Tìm thấy: ${candidate}`;
                autoDetectStatus.classList.remove('detecting');
                applyHost(candidate);
                startPing();
                setStatus(`Tìm thấy host: ${candidate}`, 'ok', 3000);
                autoDetecting = false;
                btnAutoDetect.textContent = '🔍 Tìm';
                btnAutoDetect.disabled = false;
                return;
            }
        }

        autoDetectStatus.textContent = 'Không tìm thấy — hãy nhập thủ công';
        autoDetectStatus.classList.remove('detecting');
        showEditMode(true);
        autoDetecting = false;
        btnAutoDetect.textContent = '🔍 Tìm';
        btnAutoDetect.disabled = false;
    }

    // ── PING / APP INFO ───────────────────────────────────────────────────────
    function ping() {
        if (!enabled) { applyConnState('idle'); return; }
        const t0 = Date.now();
        GM_xmlhttpRequest({
            method: 'GET',
            url: getUrl(INFO_PATH),
            timeout: 3000,
            onload(r) {
                const ms = Date.now() - t0;
                try {
                    const d = JSON.parse(r.responseText);
                    applyConnState('ok', (d.name || 'Unknown') + (d.version ? ' v' + d.version : ''), ms);
                } catch {
                    applyConnState('ok', 'Kết nối OK', ms);
                }
            },
            onerror()  { applyConnState('err'); },
            ontimeout(){ applyConnState('err'); }
        });
    }

    function startPing() {
        clearInterval(pingTimer);
        ping();
        pingTimer = setInterval(ping, PING_INTERVAL);
    }

    // ── HOST MANAGEMENT ───────────────────────────────────────────────────────
    function applyHost(newHost) {
        host = newHost.replace(/\/+$/, '');
        GM_setValue(STORAGE_HOST, host);
        renderHost();
        showEditMode(false);
        if (enabled) startPing();
        setStatus('Host đã cập nhật', 'ok');
    }

    function toggleEnabled() {
        enabled = !enabled;
        GM_setValue(STORAGE_ON, enabled);
        renderToggle();
        if (enabled) {
            startPing();
            setStatus('Đã bật TX', 'ok');
        } else {
            clearInterval(pingTimer);
            applyConnState('idle');
            setStatus('Đã tắt TX — nút TX bị chặn', 'warn', 3000);
        }
    }

    // ── TX SEND ───────────────────────────────────────────────────────────────
    function highlightOrderId(row) {
        const match = row.innerText.match(/\d{3,}-\d+/);
        if (!match) return;
        const id = match[0];
        const walker = document.createTreeWalker(row, NodeFilter.SHOW_TEXT, null, false);
        let node;
        while (node = walker.nextNode()) {
            if (!node.nodeValue.includes(id)) continue;
            const frag = document.createDocumentFragment();
            node.nodeValue.split(id).forEach((part, i, a) => {
                frag.appendChild(document.createTextNode(part));
                if (i < a.length - 1) {
                    const s = document.createElement('span');
                    s.style.cssText = 'background:rgba(0,255,65,.25);border:1px solid #00cc44;padding:1px 3px;border-radius:2px;';
                    s.textContent = id; frag.appendChild(s);
                }
            });
            node.parentNode.replaceChild(frag, node); break;
        }
    }

    function sendData(row, btn) {
        if (!enabled)            return setStatus('TX đang tắt!', 'warn');
        if (connState === 'err') return setStatus('Không có kết nối!', 'err');

        const orig = { t: btn.innerText, bg: btn.style.background, c: btn.style.color };
        btn.innerText = '…'; btn.style.background = '#ff9900'; btn.style.color = '#000';

        GM_xmlhttpRequest({
            method: 'POST',
            url: getUrl(RECEIVE_PATH),
            data: JSON.stringify({
                source_url: location.href, title: document.title,
                html_fragments: [row.outerHTML], full_text: row.innerText
            }),
            headers: { 'Content-Type': 'application/json' },
            timeout: 5000,
            onload() {
                highlightOrderId(row);
                btn.innerText = '✓'; btn.style.background = '#00cc44'; btn.style.color = '#000';
                sentCount++;
                setStatus(`Đã gửi: ${sentCount} đơn`, 'ok', 0);
            },
            onerror()   {
                btn.innerText = orig.t; btn.style.background = orig.bg; btn.style.color = orig.c;
                setStatus('Lỗi gửi!', 'err'); applyConnState('err');
            },
            ontimeout() {
                btn.innerText = orig.t; btn.style.background = orig.bg; btn.style.color = orig.c;
                setStatus('Timeout!', 'err');
            }
        });
    }

    // ── PROCESS ROWS ──────────────────────────────────────────────────────────
    function processRows(rows) {
        rows.forEach(row => {
            if (row.getAttribute(PROCESSED_ATTR)) return;
            if (!/\d{3,}-\d+/.test(row.innerText)) return;
            if (!row.cells || row.cells.length < 2) return;
            const btn = document.createElement('button');
            btn.className = 'tx-btn'; btn.innerText = 'TX'; btn.title = 'Send to host';
            btn.onclick = e => { e.stopPropagation(); e.preventDefault(); sendData(row, btn); };
            row.cells[1].insertBefore(btn, row.cells[1].firstChild);
            row.setAttribute(PROCESSED_ATTR, 'true');
        });
    }

    // ── EVENTS ────────────────────────────────────────────────────────────────
    btnToggle.onclick = toggleEnabled;

    btnEdit.onclick = () => showEditMode(true);
    btnSave.onclick = () => {
        const v = hostInput.value.trim();
        if (!v) return setStatus('Host rỗng!', 'err');
        applyHost(v);
    };
    hostInput.onkeydown = e => {
        if (e.key === 'Enter') btnSave.onclick();
        if (e.key === 'Escape') showEditMode(false);
    };

    btnReset.onclick = () => { applyHost(DEFAULT_HOST); setStatus('Đã reset về mặc định', 'ok'); };

    btnClose.onclick = () => {
        enabled = false; GM_setValue(STORAGE_ON, false);
        clearInterval(pingTimer);
        applyConnState('idle');
        renderToggle();
        setStatus('Host đã đóng', 'warn', 3000);
    };

    btnNew.onclick = () => {
        const v = prompt('Nhập host mới:', host);
        if (v && v.trim()) {
            enabled = true; GM_setValue(STORAGE_ON, true);
            applyHost(v.trim());
            renderToggle();
        }
    };

    // Double-click on connection status row → open host input
    connRow.ondblclick = () => showEditMode(true);

    btnAutoDetect.onclick = () => autoDetectHost();

    btnMin.onclick = () => { panel.style.display = 'none'; minBtn.style.display = 'block'; };
    minBtn.onclick = () => { panel.style.display = 'block'; minBtn.style.display = 'none'; };

    // ── DRAG ──────────────────────────────────────────────────────────────────
    wrap.querySelector('#emb-hdr').addEventListener('mousedown', e => {
        if (e.target.tagName === 'BUTTON') return;
        let ox = e.clientX, oy = e.clientY;
        const r  = wrap.getBoundingClientRect();
        let sr = window.innerWidth  - r.right;
        let sb = window.innerHeight - r.bottom;
        const mv = m => {
            wrap.style.right  = Math.max(0, sr  - (m.clientX - ox)) + 'px';
            wrap.style.bottom = Math.max(0, sb  + (m.clientY - oy)) + 'px';
        };
        const up = () => { removeEventListener('mousemove', mv); removeEventListener('mouseup', up); };
        addEventListener('mousemove', mv); addEventListener('mouseup', up);
    });

    // ── INIT ──────────────────────────────────────────────────────────────────
    renderHost(); renderToggle();
    if (enabled) startPing(); else applyConnState('idle');
    processRows(document.querySelectorAll('tr'));

    const observer = new MutationObserver(mutations => {
        const rows = [];
        mutations.forEach(({ addedNodes }) => addedNodes.forEach(n => {
            if (n.nodeType !== 1) return;
            n.tagName === 'TR' ? rows.push(n) : n.querySelectorAll('tr').forEach(tr => rows.push(tr));
        }));
        if (rows.length) processRows(rows);
    });
    observer.observe(document.body, { childList: true, subtree: true });

})();
