// ==UserScript==
// @name         f0rkn Universal Video Collector
// @namespace    https://github.com/f0rknturkoglu
// @version      2.0.1
// @description  YouTube, TikTok, Facebook ve Twitter/X video URL'lerini akıllıca toplar. Virtual DOM desteği, video filtresi ve f0rkn_d0wnl0ader CLI entegrasyonu sunar.
// @author       f0rknturkoglu
// @match        https://www.youtube.com/*
// @match        https://youtube.com/*
// @match        https://www.tiktok.com/*
// @match        https://tiktok.com/*
// @match        https://www.facebook.com/*
// @match        https://m.facebook.com/*
// @match        https://web.facebook.com/*
// @match        https://twitter.com/*
// @match        https://x.com/*
// @icon         https://raw.githubusercontent.com/f0rknturkoglu/f0rkdownloader/main/icon.png
// @grant        GM_setClipboard
// @grant        GM_setValue
// @grant        GM_getValue
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';

    // ════════════════════════════════════════════════════════════════
    // PLATFORM TESPİTİ
    // ════════════════════════════════════════════════════════════════
    const PLATFORM = (() => {
        const host = window.location.hostname;
        if (host.includes('youtube.com')) return 'youtube';
        if (host.includes('tiktok.com')) return 'tiktok';
        if (host.includes('facebook.com')) return 'facebook';
        if (host.includes('twitter.com') || host.includes('x.com')) return 'twitter';
        return null;
    })();

    if (!PLATFORM) return;

    // ════════════════════════════════════════════════════════════════
    // PLATFORM YAPILANDIRMASI
    // ════════════════════════════════════════════════════════════════
    const CONFIGS = {
        youtube: {
            name: 'YouTube',
            color: '#FF0000',
            gradient: 'linear-gradient(135deg, #FF0000 0%, #CC0000 100%)',
            icon: '▶️',
            scrollDelay: 800,
            patterns: ['/watch', '/shorts/'],
        },
        tiktok: {
            name: 'TikTok',
            color: '#fe2c55',
            gradient: 'linear-gradient(135deg, #fe2c55 0%, #25f4ee 100%)',
            icon: '🎵',
            scrollDelay: 650,
            patterns: ['/video/'],
        },
        facebook: {
            name: 'Facebook',
            color: '#1877F2',
            gradient: 'linear-gradient(135deg, #1877F2 0%, #0D47A1 100%)',
            icon: '📘',
            scrollDelay: 1200,
            patterns: ['/videos/', '/watch', '/reel/', '/share/r/', '/share/v/'],
        },
        twitter: {
            name: 'Twitter/X',
            color: '#1DA1F2',
            gradient: 'linear-gradient(135deg, #1DA1F2 0%, #0D8BD9 100%)',
            icon: '🐦',
            scrollDelay: 750,
            patterns: ['/status/'],
        },
    };

    const CONFIG = CONFIGS[PLATFORM];
    const STORAGE_KEY = `f0rkn_collector_${PLATFORM}_ids`;
    const POS_STORAGE_KEY = 'f0rkn_collector_pos';

    // Kalıcı Set Yönetimi
    let collectedUrls = new Set();
    try {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
            const parsed = JSON.parse(saved);
            if (Array.isArray(parsed)) {
                collectedUrls = new Set(parsed);
            }
        }
    } catch (e) {
        // Fallback
    }

    function persistUrls() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(collectedUrls)));
        } catch (e) {}
    }

    let isScrolling = false;
    let scrollLimit = 0; // 0 = sınırsız
    let observer = null;

    // ════════════════════════════════════════════════════════════════
    // STILLER
    // ════════════════════════════════════════════════════════════════
    const styles = `
        #universal-collector-panel {
            position: fixed;
            top: 70px;
            right: 15px;
            z-index: 2147483640;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            user-select: none;
        }

        #universal-collector-panel * {
            box-sizing: border-box;
        }

        .collector-main-btn {
            background: ${CONFIG.gradient};
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 25px;
            cursor: move;
            font-size: 13px;
            font-weight: 600;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .collector-main-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.45);
        }

        .collector-badge {
            background: rgba(0, 0, 0, 0.3);
            color: #fff;
            padding: 2px 7px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        }

        .collector-menu {
            display: none;
            background: #18181b;
            border: 1px solid #27272a;
            border-radius: 12px;
            padding: 12px;
            margin-top: 10px;
            box-shadow: 0 10px 35px rgba(0, 0, 0, 0.65);
            min-width: 260px;
            color: #f4f4f5;
        }

        .collector-menu.show {
            display: block;
            animation: f0rknFadeIn 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }

        @keyframes f0rknFadeIn {
            from { opacity: 0; transform: translateY(-8px) scale(0.98); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }

        .collector-header {
            padding: 6px 4px 10px 4px;
            color: #a1a1aa;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid #27272a;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .collector-count {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            margin: 10px 0;
        }

        .collector-count-number {
            font-size: 26px;
            font-weight: 800;
            color: #fff;
            line-height: 1.2;
        }

        .collector-count-label {
            font-size: 11px;
            color: #71717a;
            margin-top: 3px;
        }

        .collector-limit-select {
            background: #27272a;
            color: #e4e4e7;
            border: 1px solid #3f3f46;
            border-radius: 6px;
            padding: 6px 8px;
            font-size: 12px;
            width: 100%;
            margin-bottom: 8px;
            outline: none;
            cursor: pointer;
        }

        .collector-btn {
            background: transparent;
            color: #e4e4e7;
            border: 1px solid transparent;
            padding: 9px 12px;
            border-radius: 7px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            width: 100%;
            text-align: left;
            transition: all 0.15s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
        }

        .collector-btn:hover {
            background: #27272a;
            border-color: #3f3f46;
        }

        .collector-btn.primary {
            background: ${CONFIG.color};
            color: white;
        }

        .collector-btn.primary:hover {
            filter: brightness(1.15);
        }

        .collector-btn.danger {
            background: #dc2626;
            color: white;
        }

        .collector-btn.danger:hover {
            background: #b91c1c;
        }

        .collector-btn.success {
            background: #16a34a;
            color: white;
        }

        .collector-btn.success:hover {
            background: #15803d;
        }

        .collector-divider {
            height: 1px;
            background: #27272a;
            margin: 8px 0;
        }

        .collector-status {
            padding: 8px;
            text-align: center;
            font-size: 11px;
            color: #a1a1aa;
            border-radius: 6px;
            margin-top: 6px;
            word-break: break-word;
        }

        .collector-status.success { background: rgba(22, 163, 74, 0.15); color: #4ade80; border: 1px solid rgba(22, 163, 74, 0.3); }
        .collector-status.error { background: rgba(220, 38, 38, 0.15); color: #f87171; border: 1px solid rgba(220, 38, 38, 0.3); }
        .collector-status.info { background: rgba(37, 99, 235, 0.15); color: #60a5fa; border: 1px solid rgba(37, 99, 235, 0.3); }

        .collector-notification {
            position: fixed;
            bottom: 24px;
            right: 24px;
            padding: 12px 18px;
            border-radius: 8px;
            color: white;
            font-size: 13px;
            font-weight: 500;
            z-index: 2147483647;
            animation: f0rknSlideUp 0.25s ease;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        @keyframes f0rknSlideUp {
            from { opacity: 0; transform: translateY(16px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Modal Stilleri */
        #collector-modal-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(4px);
            z-index: 2147483645;
            align-items: center;
            justify-content: center;
        }

        #collector-modal-overlay.show {
            display: flex;
            animation: f0rknFadeIn 0.2s ease;
        }

        .collector-modal {
            background: #18181b;
            border: 1px solid #27272a;
            border-radius: 14px;
            width: 90%;
            max-width: 650px;
            max-height: 80vh;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8);
            color: #f4f4f5;
            font-family: inherit;
        }

        .collector-modal-header {
            padding: 14px 18px;
            border-bottom: 1px solid #27272a;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .collector-modal-header h3 {
            margin: 0;
            font-size: 16px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .collector-modal-close {
            background: transparent;
            border: none;
            color: #a1a1aa;
            font-size: 20px;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 6px;
        }

        .collector-modal-close:hover {
            color: #fff;
            background: #27272a;
        }

        .collector-modal-search {
            padding: 10px 18px;
            border-bottom: 1px solid #27272a;
        }

        .collector-modal-search input {
            width: 100%;
            background: #27272a;
            border: 1px solid #3f3f46;
            color: #fff;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 13px;
            outline: none;
        }

        .collector-modal-body {
            padding: 12px 18px;
            overflow-y: auto;
            flex: 1;
        }

        .collector-url-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 10px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 6px;
            margin-bottom: 6px;
            font-size: 12px;
            word-break: break-all;
        }

        .collector-url-item:hover {
            background: rgba(255, 255, 255, 0.05);
        }

        .collector-url-text {
            color: #60a5fa;
            text-decoration: none;
            flex: 1;
            margin-right: 12px;
        }

        .collector-url-actions {
            display: flex;
            gap: 6px;
        }

        .collector-url-actions button {
            background: #27272a;
            border: 1px solid #3f3f46;
            color: #d4d4d8;
            border-radius: 4px;
            padding: 4px 8px;
            cursor: pointer;
            font-size: 11px;
        }

        .collector-url-actions button:hover {
            background: #3f3f46;
            color: #fff;
        }

        .collector-modal-footer {
            padding: 12px 18px;
            border-top: 1px solid #27272a;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
    `;

    // ════════════════════════════════════════════════════════════════
    // URL VE VİDEO TANIMA MOTORU
    // ════════════════════════════════════════════════════════════════
    function extractVideoId(url, element = null) {
        if (!url) return null;

        if (PLATFORM === 'youtube') {
            // /watch?v=XXXXXXXXXXX
            const watchMatch = url.match(/[?&]v=([a-zA-Z0-9_-]{11})/);
            if (watchMatch) return watchMatch[1];

            // /shorts/XXXXXXXXXXX
            const shortsMatch = url.match(/\/shorts\/([a-zA-Z0-9_-]{11})/);
            if (shortsMatch) return shortsMatch[1];

            // youtu.be/XXXXXXXXXXX
            const shortUrlMatch = url.match(/youtu\.be\/([a-zA-Z0-9_-]{11})/);
            if (shortUrlMatch) return shortUrlMatch[1];

            return null;
        }

        if (PLATFORM === 'tiktok') {
            // @user/video/1234567890123456789 or /video/1234567890123456789
            const match = url.match(/\/video\/(\d+)/);
            return match ? match[1] : null;
        }

        if (PLATFORM === 'facebook') {
            // /watch/?v=123456789 or reel/123456789 or /videos/123456789
            const patterns = [
                /\/videos\/(\d+)/,
                /(?:watch\/?\?(?:.*&)?v=|reel\/)(\d+)/,
                /[?&]v=(\d+)/,
                /\/share\/[rv]\/(\w+)/,
            ];
            for (const p of patterns) {
                const m = url.match(p);
                if (m) return m[1];
            }
            return null;
        }

        if (PLATFORM === 'twitter') {
            const match = url.match(/\/status\/(\d+)/);
            if (!match) return null;
            const tweetId = match[1];

            // KRİTİK FİLTRE: Tweet'in gerçekten video içerdiğini doğrula!
            if (element) {
                const tweetArticle = element.closest('article[data-testid="tweet"]') || element.closest('article');
                if (tweetArticle) {
                    const hasVideo = !!(
                        tweetArticle.querySelector('video') ||
                        tweetArticle.querySelector('[data-testid="videoComponent"]') ||
                        tweetArticle.querySelector('[data-testid="videoPlayer"]') ||
                        tweetArticle.querySelector('[data-testid="playButton"]') ||
                        tweetArticle.querySelector('div[aria-label*="Oynat"]') ||
                        tweetArticle.querySelector('div[aria-label*="Play"]')
                    );
                    if (!hasVideo) {
                        return null; // Salt metin veya resim tweet'i, yoksay!
                    }
                }
            }
            return tweetId;
        }

        return null;
    }

    function buildCanonicalUrl(id) {
        if (!id) return null;
        if (PLATFORM === 'youtube') {
            return `https://www.youtube.com/watch?v=${id}`;
        }
        if (PLATFORM === 'tiktok') {
            return `https://www.tiktok.com/@video/video/${id}`;
        }
        if (PLATFORM === 'facebook') {
            return `https://www.facebook.com/watch/?v=${id}`;
        }
        if (PLATFORM === 'twitter') {
            return `https://x.com/i/status/${id}`;
        }
        return null;
    }

    // ════════════════════════════════════════════════════════════════
    // TARAMA & GÖZLEM MOTORU (MUTATIONOBSERVER)
    // ════════════════════════════════════════════════════════════════
    function processLink(link) {
        const href = link.href || link.getAttribute('href') || '';
        if (!href) return false;

        const matchesPattern = CONFIG.patterns.some(p => href.includes(p));
        if (!matchesPattern) return false;

        const videoId = extractVideoId(href, link);
        if (videoId && !collectedUrls.has(videoId)) {
            collectedUrls.add(videoId);
            persistUrls();
            return true;
        }
        return false;
    }

    function scanPage() {
        let added = 0;
        const links = document.querySelectorAll('a[href]');

        links.forEach(link => {
            if (processLink(link)) added++;
        });

        updateCount();
        if (added > 0) {
            showStatus(`+${added} video eklendi (Toplam: ${collectedUrls.size})`, 'success');
            notify(`+${added} video URL eklendi!`);
        } else {
            showStatus('Yeni video bulunamadı', 'info');
        }
        return added;
    }

    function startMutationObserver() {
        if (observer) return;
        observer = new MutationObserver(mutations => {
            let addedCount = 0;
            for (const mutation of mutations) {
                for (const node of mutation.addedNodes) {
                    if (node.nodeType !== Node.ELEMENT_NODE) continue;

                    if (node.tagName === 'A' && processLink(node)) {
                        addedCount++;
                    } else if (node.querySelectorAll) {
                        const links = node.querySelectorAll('a[href]');
                        links.forEach(l => {
                            if (processLink(l)) addedCount++;
                        });
                    }
                }
            }
            if (addedCount > 0) {
                updateCount();
                if (!isScrolling) {
                    notify(`Canlı yakalandı: +${addedCount} video`);
                }
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
        });
    }

    // ════════════════════════════════════════════════════════════════
    // GELİŞMİŞ OTOMATİK SCROLL
    // ════════════════════════════════════════════════════════════════
    let emptyScrollRetries = 0;

    function toggleScroll() {
        const btn = document.getElementById('btn-scroll');
        if (!btn) return;

        if (isScrolling) {
            stopScroll('Durduruldu');
            return;
        }

        const selectLimit = document.getElementById('collector-limit-select');
        scrollLimit = selectLimit ? parseInt(selectLimit.value, 10) : 0;

        isScrolling = true;
        emptyScrollRetries = 0;
        btn.textContent = '⏹️ Durdur (Alt+S)';
        btn.classList.remove('primary');
        btn.classList.add('danger');

        showStatus('Otomatik kaydırma ve toplama devrede...', 'info');
        notify('Otomatik toplama başladı');
        autoScrollStep();
    }

    function stopScroll(msg = 'Durduruldu', isSuccess = false) {
        isScrolling = false;
        const btn = document.getElementById('btn-scroll');
        if (btn) {
            btn.textContent = '🔄 Otomatik Scroll & Topla';
            btn.classList.remove('danger');
            btn.classList.add('primary');
        }
        showStatus(msg, isSuccess ? 'success' : 'info');
        notify(msg);
    }

    function autoScrollStep() {
        if (!isScrolling) return;

        // Hedef limit kontrolü
        if (scrollLimit > 0 && collectedUrls.size >= scrollLimit) {
            stopScroll(`Hedefe ulaşıldı: ${collectedUrls.size} video`, true);
            return;
        }

        scanPage();

        const scrollEl = document.scrollingElement || document.documentElement;
        const before = scrollEl.scrollTop;

        // İnsansı dinamik sıçrama (500 - 750px arası rastgele)
        const step = Math.floor(500 + Math.random() * 250);
        scrollEl.scrollTop += step;

        // İnsansı dinamik gecikme (±120ms jitter)
        const delay = Math.max(300, CONFIG.scrollDelay + Math.floor(Math.random() * 240 - 120));

        setTimeout(() => {
            if (!isScrolling) return;

            const after = scrollEl.scrollTop;
            const maxScroll = scrollEl.scrollHeight - window.innerHeight;

            // Sayfa sonuna mı gelindi?
            if (after >= maxScroll - 60 || after === before) {
                emptyScrollRetries++;
                showStatus(`Yeni içerik bekleniyor... (${emptyScrollRetries}/3)`, 'info');

                if (emptyScrollRetries >= 3) {
                    stopScroll(`Tamamlandı! Toplam ${collectedUrls.size} video toplandı`, true);
                } else {
                    // İçerik yüklenmesi için 1.5 sn bekle ve tekrar dene
                    setTimeout(autoScrollStep, 1500);
                }
            } else {
                emptyScrollRetries = 0;
                autoScrollStep();
            }
        }, delay);
    }

    // ════════════════════════════════════════════════════════════════
    // DIŞA AKTARMA, KOPYALAMA & MODAL
    // ════════════════════════════════════════════════════════════════
    function getUrlList() {
        const urls = [];
        collectedUrls.forEach(id => {
            const u = buildCanonicalUrl(id);
            if (u) urls.push(u);
        });
        return urls;
    }

    function exportUrls() {
        const urls = getUrlList();
        if (urls.length === 0) {
            showStatus('Önce video toplayın!', 'error');
            return;
        }

        const dateStr = new Date().toISOString().slice(0, 10);
        const filename = `f0rkn_${PLATFORM}_urls_${dateStr}.txt`;
        const content = urls.join('\n');

        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
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

        // 1. GM_setClipboard denemesi
        if (typeof GM_setClipboard === 'function') {
            GM_setClipboard(content);
            showStatus(`${urls.length} URL panoya kopyalandı!`, 'success');
            notify(`${urls.length} URL kopyalandı!`);
            return;
        }

        // 2. navigator.clipboard denemesi
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(content).then(() => {
                showStatus(`${urls.length} URL panoya kopyalandı!`, 'success');
                notify(`${urls.length} URL kopyalandı!`);
            }).catch(() => {
                fallbackCopy(content, urls.length);
            });
        } else {
            fallbackCopy(content, urls.length);
        }
    }

    function fallbackCopy(text, count) {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        try {
            document.execCommand('copy');
            showStatus(`${count} URL panoya kopyalandı!`, 'success');
            notify(`${count} URL kopyalandı!`);
        } catch (e) {
            showStatus('Kopyalama başarısız oldu!', 'error');
        }
        document.body.removeChild(ta);
    }

    function clearUrls() {
        if (collectedUrls.size === 0) return;
        if (confirm(`Toplanan ${collectedUrls.size} videoyu listeden silmek istediğinize emin misiniz?`)) {
            collectedUrls.clear();
            persistUrls();
            updateCount();
            renderModalList();
            showStatus('Liste temizlendi', 'info');
            notify('Liste temizlendi');
        }
    }

    // ════════════════════════════════════════════════════════════════
    // ARAYÜZ VE SÜRÜKLENEBİLİRLİK (DRAG & DROP)
    // ════════════════════════════════════════════════════════════════
    function makeDraggable(el, handle) {
        let isDragging = false;
        let startX = 0;
        let startY = 0;
        let origLeft = 0;
        let origTop = 0;

        handle.addEventListener('mousedown', e => {
            if (e.target.tagName === 'BUTTON' || e.target.tagName === 'SELECT' || e.target.tagName === 'INPUT') return;
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            const rect = el.getBoundingClientRect();
            origLeft = rect.left;
            origTop = rect.top;
            el.style.right = 'auto';
            el.style.left = `${origLeft}px`;
            el.style.top = `${origTop}px`;
            e.preventDefault();
        });

        document.addEventListener('mousemove', e => {
            if (!isDragging) return;
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            const newLeft = Math.max(10, Math.min(window.innerWidth - el.offsetWidth - 10, origLeft + dx));
            const newTop = Math.max(10, Math.min(window.innerHeight - el.offsetHeight - 10, origTop + dy));
            el.style.left = `${newLeft}px`;
            el.style.top = `${newTop}px`;
        });

        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                try {
                    localStorage.setItem(POS_STORAGE_KEY, JSON.stringify({
                        left: el.style.left,
                        top: el.style.top,
                    }));
                } catch (err) {}
            }
        });
    }

    function createPanel() {
        if (document.getElementById('universal-collector-panel')) return;

        // Stilleri ekle
        const styleEl = document.createElement('style');
        styleEl.textContent = styles;
        document.head.appendChild(styleEl);

        // Panel öğesini oluştur
        const panel = document.createElement('div');
        panel.id = 'universal-collector-panel';

        panel.innerHTML = `
            <button class="collector-main-btn" id="collector-toggle">
                <span style="font-size: 16px;">${CONFIG.icon}</span>
                <span>${CONFIG.name} Collector</span>
                <span class="collector-badge" id="url-badge">${collectedUrls.size}</span>
            </button>
            <div class="collector-menu" id="collector-menu">
                <div class="collector-header">
                    <span>${CONFIG.name} Video Toplayıcı</span>
                    <span style="font-size: 10px; opacity: 0.6;">v2.0</span>
                </div>
                <div class="collector-count">
                    <div class="collector-count-number" id="url-count">${collectedUrls.size}</div>
                    <div class="collector-count-label">Toplanan Video URL</div>
                </div>
                <select class="collector-limit-select" id="collector-limit-select" title="Hedef Sınırı">
                    <option value="0">🎯 Hedef: Sınırsız</option>
                    <option value="20">🎯 Hedef: 20 Video</option>
                    <option value="50">🎯 Hedef: 50 Video</option>
                    <option value="100">🎯 Hedef: 100 Video</option>
                    <option value="250">🎯 Hedef: 250 Video</option>
                </select>
                <button class="collector-btn primary" id="btn-scroll">
                    🔄 Otomatik Scroll & Topla
                </button>
                <button class="collector-btn" id="btn-scan">
                    🔍 Bu Sayfayı Tara
                </button>
                <button class="collector-btn" id="btn-view-list">
                    📋 Listeyi İncele / Düzenle
                </button>
                <div class="collector-divider"></div>
                <button class="collector-btn success" id="btn-export">
                    💾 TXT Olarak Kaydet (CLI Uyumlu)
                </button>
                <button class="collector-btn" id="btn-copy">
                    📋 Panoya Kopyala
                </button>
                <div class="collector-divider"></div>
                <button class="collector-btn id="btn-clear" style="color: #f87171;">
                    🗑️ Listeyi Temizle
                </button>
                <div class="collector-status" id="collector-status" style="display: none;"></div>
            </div>
        `;

        document.body.appendChild(panel);

        // Kayıtlı pozisyonu geri yükle
        try {
            const savedPos = localStorage.getItem(POS_STORAGE_KEY);
            if (savedPos) {
                const pos = JSON.parse(savedPos);
                if (pos.left && pos.top) {
                    panel.style.left = pos.left;
                    panel.style.top = pos.top;
                    panel.style.right = 'auto';
                }
            }
        } catch (e) {}

        // Sürüklenebilirlik bağla
        makeDraggable(panel, document.getElementById('collector-toggle'));

        // Modal oluştur
        createModal();

        // Event Dinleyicileri
        document.getElementById('collector-toggle').addEventListener('click', e => {
            // Sürükleme sonrası tıklamayı ayırt et
            document.getElementById('collector-menu').classList.toggle('show');
        });

        document.addEventListener('click', e => {
            if (!panel.contains(e.target) && !document.getElementById('collector-modal-overlay').contains(e.target)) {
                document.getElementById('collector-menu').classList.remove('show');
            }
        });

        document.getElementById('btn-scroll').addEventListener('click', toggleScroll);
        document.getElementById('btn-scan').addEventListener('click', scanPage);
        document.getElementById('btn-view-list').addEventListener('click', () => {
            document.getElementById('collector-menu').classList.remove('show');
            openModal();
        });
        document.getElementById('btn-export').addEventListener('click', exportUrls);
        document.getElementById('btn-copy').addEventListener('click', copyUrls);
        document.getElementById('btn-clear').addEventListener('click', clearUrls);

        // Kısayol Tuşları (Alt+S, Alt+C, Alt+E, Alt+L)
        document.addEventListener('keydown', e => {
            if (!e.altKey) return;
            if (e.key === 's' || e.key === 'S') {
                e.preventDefault();
                toggleScroll();
            } else if (e.key === 'c' || e.key === 'C') {
                e.preventDefault();
                copyUrls();
            } else if (e.key === 'e' || e.key === 'E') {
                e.preventDefault();
                exportUrls();
            } else if (e.key === 'l' || e.key === 'L') {
                e.preventDefault();
                openModal();
            }
        });

        // Canlı MutationObserver başlat
        startMutationObserver();
    }

    // ════════════════════════════════════════════════════════════════
    // LİSTE İNCELEME MODALI
    // ════════════════════════════════════════════════════════════════
    function createModal() {
        const overlay = document.createElement('div');
        overlay.id = 'collector-modal-overlay';
        overlay.innerHTML = `
            <div class="collector-modal">
                <div class="collector-modal-header">
                    <h3><span>${CONFIG.icon}</span> Toplanan Video URL Listesi (<span id="modal-total-count">0</span>)</h3>
                    <button class="collector-modal-close" id="modal-close-btn">&times;</button>
                </div>
                <div class="collector-modal-search">
                    <input type="text" id="modal-search-input" placeholder="URL veya ID ara..." />
                </div>
                <div class="collector-modal-body" id="modal-list-container"></div>
                <div class="collector-modal-footer">
                    <button class="collector-btn success" id="modal-export-btn" style="width: auto; display: inline-flex;">
                        💾 TXT İndir
                    </button>
                    <button class="collector-btn primary" id="modal-copy-btn" style="width: auto; display: inline-flex;">
                        📋 Panoya Kopyala
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        document.getElementById('modal-close-btn').addEventListener('click', closeModal);
        overlay.addEventListener('click', e => {
            if (e.target === overlay) closeModal();
        });

        document.getElementById('modal-search-input').addEventListener('input', e => {
            renderModalList(e.target.value);
        });

        document.getElementById('modal-export-btn').addEventListener('click', exportUrls);
        document.getElementById('modal-copy-btn').addEventListener('click', copyUrls);
    }

    function openModal() {
        renderModalList();
        document.getElementById('collector-modal-overlay').classList.add('show');
    }

    function closeModal() {
        document.getElementById('collector-modal-overlay').classList.remove('show');
    }

    function renderModalList(filterQuery = '') {
        const container = document.getElementById('modal-list-container');
        const countSpan = document.getElementById('modal-total-count');
        if (!container) return;

        countSpan.textContent = collectedUrls.size;
        container.innerHTML = '';

        if (collectedUrls.size === 0) {
            container.innerHTML = '<div style="text-align: center; color: #71717a; padding: 40px;">Henüz hiç video toplanmadı.</div>';
            return;
        }

        const q = filterQuery.toLowerCase().trim();
        let matchCount = 0;

        collectedUrls.forEach(id => {
            const canonicalUrl = buildCanonicalUrl(id);
            if (!canonicalUrl) return;

            if (q && !canonicalUrl.toLowerCase().includes(q) && !id.toLowerCase().includes(q)) {
                return;
            }

            matchCount++;
            const item = document.createElement('div');
            item.className = 'collector-url-item';
            item.innerHTML = `
                <a href="${canonicalUrl}" target="_blank" class="collector-url-text">${canonicalUrl}</a>
                <div class="collector-url-actions">
                    <button class="btn-copy-item" title="Kopyala">📋</button>
                    <button class="btn-del-item" title="Sil" style="color: #f87171;">🗑️</button>
                </div>
            `;

            item.querySelector('.btn-copy-item').addEventListener('click', () => {
                if (navigator.clipboard) navigator.clipboard.writeText(canonicalUrl);
                notify('URL kopyalandı');
            });

            item.querySelector('.btn-del-item').addEventListener('click', () => {
                collectedUrls.delete(id);
                persistUrls();
                updateCount();
                renderModalList(filterQuery);
                notify('Video listeden çıkarıldı');
            });

            container.appendChild(item);
        });

        if (matchCount === 0 && q) {
            container.innerHTML = `<div style="text-align: center; color: #71717a; padding: 30px;">"${filterQuery}" ile eşleşen URL bulunamadı.</div>`;
        }
    }

    // ════════════════════════════════════════════════════════════════
    // YARDIMCI GÖRSEL BİLDİRİMLER
    // ════════════════════════════════════════════════════════════════
    function updateCount() {
        const cntEl = document.getElementById('url-count');
        const badgeEl = document.getElementById('url-badge');
        if (cntEl) cntEl.textContent = collectedUrls.size;
        if (badgeEl) badgeEl.textContent = collectedUrls.size;
    }

    function showStatus(msg, type = '') {
        const el = document.getElementById('collector-status');
        if (!el) return;
        el.textContent = msg;
        el.className = 'collector-status ' + type;
        el.style.display = 'block';
    }

    function notify(msg) {
        const notif = document.createElement('div');
        notif.className = 'collector-notification';
        notif.style.background = CONFIG.color;
        notif.innerHTML = `<span>${CONFIG.icon}</span> <span>${msg}</span>`;
        document.body.appendChild(notif);
        setTimeout(() => {
            notif.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            notif.style.opacity = '0';
            notif.style.transform = 'translateY(10px)';
            setTimeout(() => notif.remove(), 300);
        }, 2500);
    }

    // ════════════════════════════════════════════════════════════════
    // BAŞLATMA
    // ════════════════════════════════════════════════════════════════
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(createPanel, 1000);
    } else {
        window.addEventListener('DOMContentLoaded', () => setTimeout(createPanel, 1000));
    }

})();
