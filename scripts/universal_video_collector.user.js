// ==UserScript==
// @name         f0rkn Universal Video Collector
// @namespace    https://github.com/f0rknturkoglu
// @version      1.0
// @description  TikTok, Facebook ve Twitter video URL'lerini tek scriptle toplar. f0rkn_d0wnl0ader uygulaması ile kullanılır.
// @author       f0rknturkoglu
// @match        https://www.tiktok.com/*
// @match        https://tiktok.com/*
// @match        https://www.facebook.com/*
// @match        https://m.facebook.com/*
// @match        https://twitter.com/*
// @match        https://x.com/*
// @icon         https://raw.githubusercontent.com/user/repo/icon.png
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';

    // ════════════════════════════════════════════════════════════════
    // PLATFORM TESPİTİ
    // ════════════════════════════════════════════════════════════════
    const PLATFORM = (() => {
        const host = window.location.hostname;
        if (host.includes('tiktok.com')) return 'tiktok';
        if (host.includes('facebook.com')) return 'facebook';
        if (host.includes('twitter.com') || host.includes('x.com')) return 'twitter';
        return null;
    })();

    if (!PLATFORM) return;

    // ════════════════════════════════════════════════════════════════
    // PLATFORM AYARLARI
    // ════════════════════════════════════════════════════════════════
    const CONFIGS = {
        tiktok: {
            name: 'TikTok',
            color: '#fe2c55',
            gradient: 'linear-gradient(135deg, #fe2c55 0%, #25f4ee 100%)',
            icon: '🎵',
            scrollDelay: 500,
            patterns: ['/video/'],
        },
        facebook: {
            name: 'Facebook',
            color: '#1877F2',
            gradient: 'linear-gradient(135deg, #1877F2 0%, #0D47A1 100%)',
            icon: '📘',
            scrollDelay: 1500,
            patterns: ['/videos/', '/watch', '/reel/'],
        },
        twitter: {
            name: 'Twitter/X',
            color: '#1DA1F2',
            gradient: 'linear-gradient(135deg, #1DA1F2 0%, #0D8BD9 100%)',
            icon: '🐦',
            scrollDelay: 800,
            patterns: ['/status/'],
        },
    };

    const CONFIG = CONFIGS[PLATFORM];
    let collectedUrls = new Set();
    let isScrolling = false;

    // ════════════════════════════════════════════════════════════════
    // STILLER
    // ════════════════════════════════════════════════════════════════
    const styles = `
        #universal-collector-panel {
            position: fixed;
            top: 70px;
            right: 15px;
            z-index: 999999;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        #universal-collector-panel * {
            box-sizing: border-box;
        }

        .collector-main-btn {
            background: ${CONFIG.gradient};
            color: white;
            border: none;
            padding: 12px 18px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .collector-main-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
        }

        .collector-menu {
            display: none;
            background: #1a1a1a;
            border-radius: 12px;
            padding: 10px;
            margin-top: 10px;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
            min-width: 240px;
        }

        .collector-menu.show {
            display: block;
            animation: fadeIn 0.2s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .collector-header {
            padding: 8px 12px;
            color: #888;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 1px solid #333;
            margin-bottom: 8px;
        }

        .collector-count {
            background: rgba(255,255,255,0.1);
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 10px;
        }

        .collector-count-number {
            font-size: 28px;
            font-weight: bold;
            color: white;
        }

        .collector-count-label {
            font-size: 11px;
            color: #888;
            margin-top: 4px;
        }

        .collector-btn {
            background: transparent;
            color: white;
            border: none;
            padding: 12px 14px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            width: 100%;
            text-align: left;
            transition: background 0.2s;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 4px;
        }

        .collector-btn:hover {
            background: #333;
        }

        .collector-btn.primary {
            background: ${CONFIG.color};
        }

        .collector-btn.primary:hover {
            background: ${CONFIG.color}dd;
        }

        .collector-btn.danger {
            background: #f44336;
        }

        .collector-btn.success {
            background: #4CAF50;
        }

        .collector-divider {
            height: 1px;
            background: #333;
            margin: 8px 0;
        }

        .collector-status {
            padding: 10px;
            text-align: center;
            font-size: 12px;
            color: #888;
            border-radius: 6px;
            margin-top: 8px;
        }

        .collector-status.success { background: rgba(76, 175, 80, 0.2); color: #4CAF50; }
        .collector-status.error { background: rgba(244, 67, 54, 0.2); color: #f44336; }
        .collector-status.info { background: rgba(33, 150, 243, 0.2); color: #2196F3; }

        .collector-notification {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 14px 20px;
            border-radius: 10px;
            color: white;
            font-family: sans-serif;
            font-size: 14px;
            z-index: 9999999;
            animation: slideUp 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }

        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
    `;

    // ════════════════════════════════════════════════════════════════
    // PANELİ OLUŞTUR
    // ════════════════════════════════════════════════════════════════
    function createPanel() {
        // Styles ekle
        const styleEl = document.createElement('style');
        styleEl.textContent = styles;
        document.head.appendChild(styleEl);

        // Panel oluştur
        const panel = document.createElement('div');
        panel.id = 'universal-collector-panel';
        panel.innerHTML = `
            <button class="collector-main-btn" id="collector-toggle">
                <span style="font-size: 18px;">${CONFIG.icon}</span>
                <span>${CONFIG.name} Collector</span>
            </button>
            <div class="collector-menu" id="collector-menu">
                <div class="collector-header">${CONFIG.name} Video URL Toplayıcı</div>
                <div class="collector-count">
                    <div class="collector-count-number" id="url-count">0</div>
                    <div class="collector-count-label">Video URL Toplandı</div>
                </div>
                <button class="collector-btn primary" id="btn-scroll">
                    🔄 Otomatik Scroll & Topla
                </button>
                <button class="collector-btn" id="btn-scan">
                    🔍 Bu Sayfayı Tara
                </button>
                <div class="collector-divider"></div>
                <button class="collector-btn success" id="btn-export">
                    💾 TXT Olarak Kaydet
                </button>
                <button class="collector-btn" id="btn-copy">
                    📋 Panoya Kopyala
                </button>
                <div class="collector-divider"></div>
                <button class="collector-btn" id="btn-clear" style="color: #f44336;">
                    🗑️ Listeyi Temizle
                </button>
                <div class="collector-status" id="collector-status" style="display: none;"></div>
            </div>
        `;
        document.body.appendChild(panel);

        // Event Listeners
        document.getElementById('collector-toggle').addEventListener('click', () => {
            document.getElementById('collector-menu').classList.toggle('show');
        });

        document.addEventListener('click', (e) => {
            if (!panel.contains(e.target)) {
                document.getElementById('collector-menu').classList.remove('show');
            }
        });

        document.getElementById('btn-scroll').addEventListener('click', toggleScroll);
        document.getElementById('btn-scan').addEventListener('click', scanPage);
        document.getElementById('btn-export').addEventListener('click', exportUrls);
        document.getElementById('btn-copy').addEventListener('click', copyUrls);
        document.getElementById('btn-clear').addEventListener('click', clearUrls);
    }

    // ════════════════════════════════════════════════════════════════
    // PLATFORM-SPESİFİK URL ÇIKARMA
    // ════════════════════════════════════════════════════════════════
    function extractVideoId(url) {
        if (PLATFORM === 'tiktok') {
            const match = url.match(/\/video\/(\d+)/);
            return match ? match[1] : null;
        }
        if (PLATFORM === 'facebook') {
            const patterns = [
                /\/videos\/(\d+)/,
                /(?:watch\/?\?(?:.*&)?v=|reel\/)(\d+)/,
                /[?&]v=(\d+)/,
            ];
            for (const p of patterns) {
                const m = url.match(p);
                if (m) return m[1];
            }
            return null;
        }
        if (PLATFORM === 'twitter') {
            const match = url.match(/\/status\/(\d+)/);
            return match ? match[1] : null;
        }
        return null;
    }

    function buildCanonicalUrl(id) {
        if (PLATFORM === 'tiktok') {
            return `https://www.tiktok.com/video/${id}`;
        }
        if (PLATFORM === 'facebook') {
            return `https://www.facebook.com/watch/?v=${id}`;
        }
        if (PLATFORM === 'twitter') {
            return `https://twitter.com/i/status/${id}`;
        }
        return null;
    }

    function scanPage() {
        let added = 0;
        const links = document.querySelectorAll('a[href]');

        links.forEach(link => {
            const href = link.href || '';
            
            // Platform pattern'lerine göre kontrol
            const matchesPattern = CONFIG.patterns.some(p => href.includes(p));
            if (!matchesPattern) return;

            const videoId = extractVideoId(href);
            if (videoId && !collectedUrls.has(videoId)) {
                collectedUrls.add(videoId);
                added++;
            }
        });

        updateCount();
        if (added > 0) {
            showStatus(`+${added} video eklendi`, 'success');
            notify(`+${added} video URL eklendi!`);
        } else {
            showStatus('Yeni video bulunamadı', 'info');
        }
    }

    // ════════════════════════════════════════════════════════════════
    // OTOMATİK SCROLL
    // ════════════════════════════════════════════════════════════════
    function toggleScroll() {
        const btn = document.getElementById('btn-scroll');

        if (isScrolling) {
            isScrolling = false;
            btn.textContent = '🔄 Otomatik Scroll & Topla';
            btn.classList.remove('danger');
            btn.classList.add('primary');
            showStatus('Durduruldu', 'info');
            return;
        }

        isScrolling = true;
        btn.textContent = '⏹️ Durdur';
        btn.classList.remove('primary');
        btn.classList.add('danger');

        autoScroll();
    }

    function autoScroll() {
        if (!isScrolling) return;

        // Sayfayı tara
        scanPage();

        // Scroll
        const scrollEl = document.scrollingElement || document.documentElement;
        const before = scrollEl.scrollTop;
        scrollEl.scrollTop += 600;

        setTimeout(() => {
            if (!isScrolling) return;

            const after = scrollEl.scrollTop;
            const maxScroll = scrollEl.scrollHeight - window.innerHeight;

            if (after >= maxScroll - 50 || after === before) {
                // Sayfa sonu, bekle ve kontrol et
                setTimeout(() => {
                    const newMax = scrollEl.scrollHeight - window.innerHeight;
                    if (newMax > maxScroll + 100) {
                        autoScroll();
                    } else {
                        // Bitti
                        isScrolling = false;
                        const btn = document.getElementById('btn-scroll');
                        btn.textContent = '🔄 Otomatik Scroll & Topla';
                        btn.classList.remove('danger');
                        btn.classList.add('primary');
                        showStatus(`Tamamlandı! ${collectedUrls.size} video`, 'success');
                        notify(`Toplama tamamlandı: ${collectedUrls.size} video`);
                    }
                }, 2000);
            } else {
                autoScroll();
            }
        }, CONFIG.scrollDelay);
    }

    // ════════════════════════════════════════════════════════════════
    // EXPORT & COPY
    // ════════════════════════════════════════════════════════════════
    function getUrlList() {
        const urls = [];
        collectedUrls.forEach(id => {
            const url = buildCanonicalUrl(id);
            if (url) urls.push(url);
        });
        return urls;
    }

    function exportUrls() {
        const urls = getUrlList();
        if (urls.length === 0) {
            showStatus('Önce video toplayın!', 'error');
            return;
        }

        const content = urls.join('\n');
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);

        const filename = `${PLATFORM}_videos_${new Date().toISOString().slice(0,10)}.txt`;
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);

        showStatus(`${urls.length} URL kaydedildi: ${filename}`, 'success');
        notify(`${urls.length} URL dosyaya kaydedildi!`);
    }

    function copyUrls() {
        const urls = getUrlList();
        if (urls.length === 0) {
            showStatus('Önce video toplayın!', 'error');
            return;
        }

        const content = urls.join('\n');
        navigator.clipboard.writeText(content).then(() => {
            showStatus(`${urls.length} URL panoya kopyalandı`, 'success');
            notify(`${urls.length} URL kopyalandı!`);
        }).catch(() => {
            showStatus('Kopyalama başarısız!', 'error');
        });
    }

    function clearUrls() {
        collectedUrls.clear();
        updateCount();
        showStatus('Liste temizlendi', 'info');
    }

    // ════════════════════════════════════════════════════════════════
    // YARDIMCI
    // ════════════════════════════════════════════════════════════════
    function updateCount() {
        document.getElementById('url-count').textContent = collectedUrls.size;
    }

    function showStatus(msg, type = '') {
        const el = document.getElementById('collector-status');
        el.textContent = msg;
        el.className = 'collector-status ' + type;
        el.style.display = 'block';
    }

    function notify(msg) {
        const notif = document.createElement('div');
        notif.className = 'collector-notification';
        notif.style.background = CONFIG.color;
        notif.textContent = `${CONFIG.icon} ${msg}`;
        document.body.appendChild(notif);
        setTimeout(() => notif.remove(), 3000);
    }

    // ════════════════════════════════════════════════════════════════
    // BAŞLAT
    // ════════════════════════════════════════════════════════════════
    setTimeout(createPanel, 2000);

})();
