"""
Debug Preview Dashboard — Real-time browser view + AI State overlay.
Halaman terpisah /debug di server yang sama, streaming langsung dari Playwright.
"""

# Template HTML untuk halaman Debug Preview
DEBUG_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔍 Realtime Debug Preview — AU Bot</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        
        :root {
            --bg-deep: #050a14;
            --bg-panel: #0a1628;
            --bg-card: #0f1d32;
            --border: #1a2d4a;
            --accent-blue: #3b82f6;
            --accent-cyan: #06b6d4;
            --accent-green: #10b981;
            --accent-amber: #f59e0b;
            --accent-red: #ef4444;
            --accent-purple: #8b5cf6;
            --text-primary: #f0f6ff;
            --text-secondary: #7d8da6;
            --text-dim: #4a5b75;
            --glow-blue: rgba(59, 130, 246, 0.15);
            --glow-green: rgba(16, 185, 129, 0.15);
            --glow-amber: rgba(245, 158, 11, 0.15);
        }

        body {
            font-family: 'Inter', system-ui, sans-serif;
            background: var(--bg-deep);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* Background animation */
        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: 
                radial-gradient(ellipse at 15% 20%, rgba(59, 130, 246, 0.06) 0%, transparent 50%),
                radial-gradient(ellipse at 85% 80%, rgba(139, 92, 246, 0.04) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(6, 182, 212, 0.03) 0%, transparent 60%);
            pointer-events: none;
            z-index: 0;
        }

        /* Header */
        .header {
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(5, 10, 20, 0.85);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border);
            padding: 12px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .header-logo {
            font-size: 20px;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
        }

        .header-nav a {
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 13px;
            font-weight: 600;
            padding: 6px 14px;
            border-radius: 6px;
            transition: all 0.2s;
        }
        .header-nav a:hover { color: var(--text-primary); background: rgba(255,255,255,0.05); }
        .header-nav a.active { color: var(--accent-cyan); background: rgba(6, 182, 212, 0.1); }

        .connection-dot {
            width: 8px; height: 8px;
            border-radius: 50%;
            background: var(--accent-red);
            display: inline-block;
            margin-right: 6px;
            transition: background 0.3s;
        }
        .connection-dot.connected { background: var(--accent-green); box-shadow: 0 0 8px rgba(16,185,129,0.5); }

        .header-status {
            display: flex;
            align-items: center;
            font-size: 12px;
            font-weight: 600;
            color: var(--text-secondary);
        }

        /* Main Grid */
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 420px;
            grid-template-rows: auto 1fr;
            gap: 0;
            height: calc(100vh - 56px);
            position: relative;
            z-index: 1;
        }

        /* Browser Preview Panel */
        .preview-panel {
            grid-row: 1 / -1;
            display: flex;
            flex-direction: column;
            border-right: 1px solid var(--border);
            background: var(--bg-panel);
            position: relative;
            overflow: hidden;
        }

        .preview-toolbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 16px;
            background: var(--bg-card);
            border-bottom: 1px solid var(--border);
        }

        .toolbar-label {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            color: var(--text-dim);
        }

        .toolbar-badges {
            display: flex;
            gap: 8px;
        }

        .badge {
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 20px;
            border: 1px solid;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge-fps { color: var(--accent-green); border-color: rgba(16,185,129,0.3); background: var(--glow-green); }
        .badge-res { color: var(--accent-blue); border-color: rgba(59,130,246,0.3); background: var(--glow-blue); }
        .badge-state { color: var(--accent-amber); border-color: rgba(245,158,11,0.3); background: var(--glow-amber); }

        .preview-viewport {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 16px;
            position: relative;
            overflow: hidden;
            background: 
                linear-gradient(45deg, rgba(0,0,0,0.03) 25%, transparent 25%),
                linear-gradient(-45deg, rgba(0,0,0,0.03) 25%, transparent 25%),
                linear-gradient(45deg, transparent 75%, rgba(0,0,0,0.03) 75%),
                linear-gradient(-45deg, transparent 75%, rgba(0,0,0,0.03) 75%);
            background-size: 20px 20px;
            background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
        }

        .browser-frame {
            position: relative;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 
                0 0 0 1px rgba(255,255,255,0.06),
                0 20px 60px rgba(0,0,0,0.5),
                0 0 40px rgba(59,130,246,0.08);
            max-height: 100%;
            transition: box-shadow 0.3s;
        }
        .browser-frame.active {
            box-shadow: 
                0 0 0 1px rgba(6,182,212,0.3),
                0 20px 60px rgba(0,0,0,0.5),
                0 0 60px rgba(6,182,212,0.1);
        }

        .browser-frame img {
            display: block;
            max-height: calc(100vh - 160px);
            width: auto;
            background: #000;
        }

        .no-stream {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 12px;
            color: var(--text-dim);
            padding: 60px;
        }
        .no-stream svg { opacity: 0.3; }
        .no-stream p { font-size: 13px; }

        /* Click Overlay */
        .click-marker {
            position: absolute;
            width: 24px; height: 24px;
            border: 2px solid var(--accent-amber);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            pointer-events: none;
            animation: click-ping 1s ease-out forwards;
        }
        @keyframes click-ping {
            0% { transform: translate(-50%, -50%) scale(0.5); opacity: 1; }
            100% { transform: translate(-50%, -50%) scale(3); opacity: 0; }
        }

        /* Right Sidebar */
        .sidebar {
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        /* AI State Panel */
        .state-panel {
            padding: 16px;
            border-bottom: 1px solid var(--border);
            background: var(--bg-card);
        }

        .state-panel-title {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            color: var(--text-dim);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .state-panel-title::before {
            content: '';
            width: 6px; height: 6px;
            border-radius: 50%;
            background: var(--accent-purple);
            box-shadow: 0 0 8px rgba(139,92,246,0.5);
        }

        .state-current {
            font-family: 'JetBrains Mono', monospace;
            font-size: 22px;
            font-weight: 700;
            color: var(--accent-cyan);
            margin-bottom: 8px;
            text-shadow: 0 0 20px rgba(6,182,212,0.3);
        }

        .state-desc {
            font-size: 12px;
            color: var(--text-secondary);
            line-height: 1.5;
        }

        .state-step {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 10px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: var(--text-dim);
        }
        .state-step span {
            color: var(--accent-blue);
            font-weight: 700;
        }

        /* Debug Image Panel */
        .debug-image-panel {
            padding: 16px;
            border-bottom: 1px solid var(--border);
            background: var(--bg-card);
        }

        .debug-image-panel .state-panel-title::before {
            background: var(--accent-amber);
            box-shadow: 0 0 8px rgba(245,158,11,0.5);
        }

        .debug-img-container {
            border-radius: 8px;
            overflow: hidden;
            border: 1px dashed rgba(245,158,11,0.3);
            background: #000;
        }
        .debug-img-container img {
            width: 100%;
            display: block;
        }
        .debug-placeholder {
            padding: 30px;
            text-align: center;
            font-size: 12px;
            color: var(--text-dim);
        }

        /* OCR Text Panel */
        .ocr-panel {
            padding: 16px;
            border-bottom: 1px solid var(--border);
            background: var(--bg-panel);
            max-height: 180px;
            overflow-y: auto;
        }

        .ocr-panel .state-panel-title::before {
            background: var(--accent-green);
            box-shadow: 0 0 8px rgba(16,185,129,0.5);
        }

        .ocr-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
        }
        .ocr-tag {
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            padding: 2px 8px;
            border-radius: 4px;
            background: rgba(16,185,129,0.1);
            border: 1px solid rgba(16,185,129,0.2);
            color: var(--accent-green);
        }
        .ocr-tag.matched {
            background: rgba(245,158,11,0.15);
            border-color: rgba(245,158,11,0.3);
            color: var(--accent-amber);
            font-weight: 700;
        }

        /* Log Panel */
        .log-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            background: var(--bg-deep);
        }

        .log-panel .state-panel-title {
            padding: 12px 16px 8px;
        }
        .log-panel .state-panel-title::before {
            background: var(--accent-blue);
            box-shadow: 0 0 8px rgba(59,130,246,0.5);
        }

        .log-scroll {
            flex: 1;
            overflow-y: auto;
            padding: 0 12px 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            line-height: 1.7;
        }

        .log-entry {
            padding: 2px 0;
            border-bottom: 1px solid rgba(255,255,255,0.02);
            display: flex;
            gap: 8px;
            animation: log-in 0.2s ease-out;
        }
        @keyframes log-in {
            from { opacity: 0; transform: translateY(4px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .log-time {
            color: var(--text-dim);
            white-space: nowrap;
            flex-shrink: 0;
        }
        .log-msg { color: var(--text-secondary); word-break: break-word; }
        .log-msg.state { color: var(--accent-cyan); }
        .log-msg.vision { color: var(--accent-amber); }
        .log-msg.error { color: var(--accent-red); }
        .log-msg.success { color: var(--accent-green); }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-dim); }

        /* Pulse animation for live indicator */
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }
        .live-indicator {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            font-weight: 700;
            color: var(--accent-red);
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .live-indicator .dot {
            width: 6px; height: 6px;
            background: var(--accent-red);
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }
        .live-indicator.active { color: var(--accent-green); }
        .live-indicator.active .dot { background: var(--accent-green); }

        /* State Flow Visualization */
        .state-flow {
            display: flex;
            gap: 2px;
            margin-top: 10px;
            flex-wrap: wrap;
        }
        .state-flow-item {
            width: 6px; height: 16px;
            border-radius: 2px;
            background: var(--border);
            transition: all 0.3s;
        }
        .state-flow-item.active { background: var(--accent-cyan); }
        .state-flow-item.past { background: rgba(6,182,212,0.3); }

        /* Responsive */
        @media (max-width: 900px) {
            .main-grid {
                grid-template-columns: 1fr;
                grid-template-rows: 50vh 1fr;
            }
            .preview-panel { border-right: none; border-bottom: 1px solid var(--border); }
        }
    </style>
</head>
<body>
    <!-- Header -->
    <header class="header">
        <div class="header-left">
            <div class="header-logo">AU Debug</div>
            <nav class="header-nav">
                <a href="/">Dashboard</a>
                <a href="/debug" class="active">Debug Preview</a>
            </nav>
        </div>
        <div class="header-status">
            <span class="connection-dot" id="conn-dot"></span>
            <span id="conn-text">Disconnected</span>
        </div>
    </header>

    <!-- Main Grid -->
    <div class="main-grid">
        <!-- Left: Browser Preview -->
        <div class="preview-panel">
            <div class="preview-toolbar">
                <div style="display:flex;align-items:center;gap:12px;">
                    <span class="toolbar-label">Browser Preview</span>
                    <div class="live-indicator" id="live-ind">
                        <span class="dot"></span>
                        <span>OFFLINE</span>
                    </div>
                </div>
                <div class="toolbar-badges">
                    <span class="badge badge-fps" id="badge-fps">-- FPS</span>
                    <span class="badge badge-res" id="badge-res">-- x --</span>
                    <span class="badge badge-state" id="badge-state">IDLE</span>
                </div>
            </div>
            <div class="preview-viewport" id="preview-viewport">
                <div class="no-stream" id="no-stream">
                    <svg width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                        <path d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                    </svg>
                    <p>Menunggu stream dari bot...</p>
                    <p style="font-size:11px;color:var(--text-dim);">Jalankan bot dari Dashboard untuk memulai preview</p>
                </div>
                <div class="browser-frame" id="browser-frame" style="display:none;">
                    <img id="live-view" src="" alt="Live Preview">
                </div>
            </div>
        </div>

        <!-- Right: Sidebar -->
        <div class="sidebar">
            <!-- AI State -->
            <div class="state-panel">
                <div class="state-panel-title">AI Brain State</div>
                <div class="state-current" id="current-state">IDLE</div>
                <div class="state-desc" id="state-desc">Bot belum berjalan. Jalankan bot dari dashboard utama.</div>
                <div class="state-step">
                    Step: <span id="step-count">0</span> / 150
                </div>
                <div class="state-flow" id="state-flow"></div>
            </div>

            <!-- Debug Image (Klik AI) -->
            <div class="debug-image-panel">
                <div class="state-panel-title">AI Click Debug</div>
                <div class="debug-img-container">
                    <img id="debug-view" src="" alt="" style="display:none;">
                    <div class="debug-placeholder" id="debug-placeholder">
                        <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" style="opacity:0.3;margin-bottom:6px;">
                            <path d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122M5.05 13.95l-2.122-2.122"/>
                        </svg>
                        <div>Belum ada aksi klik</div>
                    </div>
                </div>
            </div>

            <!-- Session & Tools Info -->
            <div class="state-panel">
                <div class="state-panel-title" style="padding: 12px 16px 8px;">Session & System Tools</div>
                <div style="padding: 0 16px 16px; font-size: 12px; color: var(--text-secondary);">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                        <span>Proxy Aktif Bot:</span>
                        <span id="bot-current-proxy" style="color: var(--accent-cyan); font-weight: bold;">Direct (Tanpa Proxy)</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span>Email/Akun Bot:</span>
                        <span id="bot-current-account" style="color: var(--accent-amber); font-weight: bold;">Tidak ada</span>
                    </div>
                    <div style="font-size: 11px; color: var(--text-dim); margin-bottom: 4px;">Tools & Teknologi Utama:</div>
                    <div style="font-size: 10px; background: rgba(0,0,0,0.2); padding: 8px; border-radius: 4px; line-height: 1.5;">
                        <div>• 🐍 <b>Python 3.12</b> (Core Engine & FastAPI)</div>
                        <div>• 🎭 <b>Playwright</b> (Automated Chromium Controller)</div>
                        <div>• 🖥️ <b>Xvfb</b> (X Virtual display :99)</div>
                        <div>• 👁️ <b>Pytesseract OCR</b> (Vision Text Scan)</div>
                        <div>• 🖼️ <b>PIL / Pillow</b> (Image manipulation & logs)</div>
                        <div>• 🔄 <b>PM2</b> (Process Manager, Auto-restart)</div>
                    </div>
                </div>
            </div>

            <!-- Proxy Stats -->
            <div class="state-panel">
                <div class="state-panel-title" style="padding: 12px 16px 8px;">Proxy Hunter Stats</div>
                <div style="padding: 0 16px 16px; font-size: 12px; color: var(--text-secondary);">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span>Pool Siap Pakai:</span>
                        <span id="proxy-active" style="color: var(--accent-green); font-weight: bold;">0</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                        <span>IP Terblokir (Blacklist):</span>
                        <span id="proxy-used" style="color: var(--accent-red); font-weight: bold;">0</span>
                    </div>
                    <div style="font-size: 11px; color: var(--text-dim); margin-bottom: 4px;">Sumber Scraping Aktif:</div>
                    <div id="proxy-sources" style="font-size: 10px; max-height: 80px; overflow-y: auto; background: rgba(0,0,0,0.2); padding: 8px; border-radius: 4px;">
                        Memuat sumber...
                    </div>
                </div>
            </div>

            <!-- OCR Detected Text -->
            <div class="ocr-panel">
                <div class="state-panel-title">OCR Detected Text</div>
                <div class="ocr-tags" id="ocr-tags">
                    <span class="ocr-tag" style="opacity:0.3;">menunggu scan...</span>
                </div>
            </div>

            <!-- Activity Log -->
            <div class="log-panel">
                <div class="state-panel-title" style="padding: 12px 16px 8px;">Activity Stream</div>
                <div class="log-scroll" id="log-scroll"></div>
            </div>
        </div>
    </div>

    <script>
        // === WebSocket Connection ===
        let ws;
        let frameCount = 0;
        let lastFpsTime = Date.now();
        let fps = 0;
        let stepCount = 0;
        let stateHistory = [];
        const MAX_STATE_HISTORY = 60;

        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/debug`;
            ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                document.getElementById('conn-dot').classList.add('connected');
                document.getElementById('conn-text').textContent = 'Connected';
                addLog('system', 'Terhubung ke server debug');
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };

            ws.onerror = (e) => {
                console.error('WS Error:', e);
                addLog('error', 'WebSocket error');
            };

            ws.onclose = () => {
                document.getElementById('conn-dot').classList.remove('connected');
                document.getElementById('conn-text').textContent = 'Disconnected';
                const liveInd = document.getElementById('live-ind');
                liveInd.classList.remove('active');
                liveInd.querySelector('span:last-child').textContent = 'OFFLINE';
                addLog('system', 'Koneksi terputus. Reconnecting...');
                setTimeout(connect, 2000);
            };
        }

        function handleMessage(data) {
            switch(data.type) {
                case 'image':
                    showFrame(data.content);
                    break;
                case 'debug_image':
                    showDebugImage(data.content);
                    break;
                case 'log':
                    processLog(data.content);
                    break;
                case 'status':
                    updateBotStatus(data.content);
                    break;
                case 'ai_state':
                    updateAIState(data);
                    break;
                case 'ocr_text':
                    updateOCRTags(data.content, data.matched || []);
                    break;
            }
        }

        // === Frame Rendering ===
        function showFrame(b64) {
            const img = document.getElementById('live-view');
            const frame = document.getElementById('browser-frame');
            const noStream = document.getElementById('no-stream');

            img.src = 'data:image/jpeg;base64,' + b64;
            frame.style.display = 'block';
            frame.classList.add('active');
            noStream.style.display = 'none';

            // FPS Counter
            frameCount++;
            const now = Date.now();
            if (now - lastFpsTime >= 1000) {
                fps = frameCount;
                frameCount = 0;
                lastFpsTime = now;
                document.getElementById('badge-fps').textContent = fps + ' FPS';
            }

            // Live indicator
            const liveInd = document.getElementById('live-ind');
            liveInd.classList.add('active');
            liveInd.querySelector('span:last-child').textContent = 'LIVE';

            // Resolution from naturalWidth once loaded
            img.onload = () => {
                document.getElementById('badge-res').textContent = img.naturalWidth + ' x ' + img.naturalHeight;
            };
        }

        function showDebugImage(b64) {
            const img = document.getElementById('debug-view');
            const placeholder = document.getElementById('debug-placeholder');
            img.src = 'data:image/jpeg;base64,' + b64;
            img.style.display = 'block';
            placeholder.style.display = 'none';
        }

        // === AI State ===
        function updateAIState(data) {
            const stateEl = document.getElementById('current-state');
            const descEl = document.getElementById('state-desc');
            const stepEl = document.getElementById('step-count');
            const badgeState = document.getElementById('badge-state');

            stateEl.textContent = data.state || 'UNKNOWN';
            descEl.textContent = data.description || '';
            stepCount = data.step || stepCount;
            stepEl.textContent = stepCount;
            badgeState.textContent = data.state || 'IDLE';

            // Color-code state
            const stateColors = {
                'HOME_SCREEN': 'var(--accent-green)',
                'APP_STORE': 'var(--accent-blue)',
                'INSTALL_POPUP': 'var(--accent-amber)',
                'APP_STORE_DOWNLOADING': 'var(--accent-purple)',
                'OS_INSTALLING': 'var(--accent-purple)',
                'CHROME_FRE': 'var(--accent-cyan)',
                'CHROME_SYNC': 'var(--accent-cyan)',
                'CHROME_MAIN': 'var(--accent-green)',
                'UNKNOWN': 'var(--text-dim)',
            };
            stateEl.style.color = stateColors[data.state] || 'var(--accent-cyan)';

            // State flow visualization
            stateHistory.push(data.state);
            if (stateHistory.length > MAX_STATE_HISTORY) stateHistory.shift();
            renderStateFlow();
        }

        // === State Flow ===
        function renderStateFlow() {
            const container = document.getElementById('state-flow');
            container.innerHTML = '';
            for (let i = 0; i < MAX_STATE_HISTORY; i++) {
                const item = document.createElement('div');
                item.className = 'state-flow-item';
                if (i < stateHistory.length) {
                    item.classList.add(i === stateHistory.length - 1 ? 'active' : 'past');
                }
                container.appendChild(item);
            }
        }

        // === OCR Tags ===
        function updateOCRTags(words, matched) {
            const container = document.getElementById('ocr-tags');
            container.innerHTML = '';
            if (!words || words.length === 0) {
                container.innerHTML = '<span class="ocr-tag" style="opacity:0.3;">layar kosong</span>';
                return;
            }
            words.forEach(word => {
                const tag = document.createElement('span');
                tag.className = 'ocr-tag';
                if (matched.includes(word)) tag.classList.add('matched');
                tag.textContent = word;
                container.appendChild(tag);
            });
        }

        // === Logging ===
        function processLog(content) {
            let msgClass = '';
            if (content.includes('[Vision-State]')) msgClass = 'state';
            else if (content.includes('[Vision-OCR]') || content.includes('[Vision]')) msgClass = 'vision';
            else if (content.toLowerCase().includes('error') || content.toLowerCase().includes('gagal')) msgClass = 'error';
            else if (content.includes('GOAL') || content.includes('Sukses') || content.includes('berhasil')) msgClass = 'success';

            addLog(msgClass, content);

            // Auto extract step from Vision-State log
            const stepMatch = content.match(/posisi saat ini: (\w+)/);
            if (stepMatch) {
                stepCount++;
                document.getElementById('step-count').textContent = stepCount;
            }
        }

        function addLog(type, content) {
            const scroll = document.getElementById('log-scroll');
            const entry = document.createElement('div');
            entry.className = 'log-entry';

            const time = document.createElement('span');
            time.className = 'log-time';
            time.textContent = new Date().toLocaleTimeString();

            const msg = document.createElement('span');
            msg.className = 'log-msg ' + type;
            msg.textContent = content;

            entry.appendChild(time);
            entry.appendChild(msg);
            scroll.appendChild(entry);

            // Auto-scroll + limit entries
            while (scroll.children.length > 500) {
                scroll.removeChild(scroll.firstChild);
            }
            scroll.scrollTop = scroll.scrollHeight;
        }

        function updateBotStatus(status) {
            const badgeState = document.getElementById('badge-state');
            badgeState.textContent = status;
            if (status === 'Running') {
                badgeState.style.color = 'var(--accent-green)';
                badgeState.style.borderColor = 'rgba(16,185,129,0.3)';
                addLog('success', 'Bot status: ' + status);
            } else {
                badgeState.style.color = 'var(--accent-amber)';
                badgeState.style.borderColor = 'rgba(245,158,11,0.3)';
                addLog('system', 'Bot status: ' + status);
                const liveInd = document.getElementById('live-ind');
                liveInd.classList.remove('active');
                liveInd.querySelector('span:last-child').textContent = 'OFFLINE';
            }
        }

        async function fetchProxyStats() {
            try {
                const response = await fetch('/proxy_stats');
                const data = await response.json();
                if (!data.error) {
                    document.getElementById('proxy-active').textContent = data.active_pool;
                    document.getElementById('proxy-used').textContent = data.blacklisted;
                    if (document.getElementById('bot-current-proxy')) {
                        document.getElementById('bot-current-proxy').textContent = data.current_proxy || 'Direct (Tanpa Proxy)';
                    }
                    if (document.getElementById('bot-current-account')) {
                        document.getElementById('bot-current-account').textContent = data.current_account || 'Tidak ada';
                    }
                    if(data.sources && document.getElementById('proxy-sources').innerHTML.includes('Memuat')) {
                        document.getElementById('proxy-sources').innerHTML = data.sources.map(s => `<div>• ${s.split('/').pop().split('?')[0].substring(0, 30)}</div>`).join('');
                    }
                }
            } catch(e) {
                console.error(e);
            }
        }

        // Init
        renderStateFlow();
        connect();
        fetchProxyStats();
        setInterval(fetchProxyStats, 5000);
    </script>
</body>
</html>
"""
