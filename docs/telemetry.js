/**
 * AMEVA Sovereign Telemetry & Deep Forensic Harvester (shared/telemetry.js)
 * 
 * Optimized Edge Architecture:
 * - Client-Side In-Memory Batching Queue (각자 브라우저가 버퍼 큐 전담)
 * - Micro-interactions (Clicks, Copies, Scans) buffered and flushed in batches
 * - Flushes every 6s or when queue reaches 8 items or on exit (sendBeacon)
 * - Cuts DB I/O and Serverless invocations by 90%+
 */

(function() {
    'use strict';

    const API_ENDPOINT = '/api/telemetry/';
    const MAX_BATCH_SIZE = 8;
    const FLUSH_INTERVAL_MS = 6000;

    // 1. Simple High-Performance Hashing Helper
    function fastHash(str) {
        let h = 0x811c9dc5;
        for (let i = 0; i < str.length; i++) {
            h ^= str.charCodeAt(i);
            h = Math.imul(h, 0x01000193);
        }
        return (h >>> 0).toString(16).padStart(8, '0');
    }

    // 2. Persistent Soul & History Tracking
    function getSoulHistory() {
        try {
            const now = new Date().toISOString();
            let firstSeen = localStorage.getItem('__ameva_first_seen');
            if (!firstSeen) {
                firstSeen = now;
                localStorage.setItem('__ameva_first_seen', firstSeen);
            }

            let visitCount = parseInt(localStorage.getItem('__ameva_visit_count') || '0', 10) + 1;
            localStorage.setItem('__ameva_visit_count', visitCount.toString());

            let sessionCount = parseInt(localStorage.getItem('__ameva_session_count') || '0', 10);
            if (!sessionStorage.getItem('__ameva_sid_init')) {
                sessionCount += 1;
                localStorage.setItem('__ameva_session_count', sessionCount.toString());
                sessionStorage.setItem('__ameva_sid_init', '1');
            }

            let pathHistory = [];
            try {
                pathHistory = JSON.parse(localStorage.getItem('__ameva_path_hist') || '[]');
            } catch (e) {}
            pathHistory.unshift(window.location.pathname);
            pathHistory = pathHistory.slice(0, 10);
            localStorage.setItem('__ameva_path_hist', JSON.stringify(pathHistory));

            return {
                first_seen_at: firstSeen,
                total_visit_count: visitCount,
                total_session_count: sessionCount,
                past_paths_history: pathHistory.join(' -> ')
            };
        } catch (e) {
            return {
                first_seen_at: new Date().toISOString(),
                total_visit_count: 1,
                total_session_count: 1,
                past_paths_history: window.location.pathname
            };
        }
    }

    // 3. Canvas 2D Cryptographic Micro-Variance Hash
    function getCanvasHash() {
        try {
            const canvas = document.createElement('canvas');
            canvas.width = 240;
            canvas.height = 60;
            const ctx = canvas.getContext('2d');
            if (!ctx) return 'no_2d_ctx';

            ctx.textBaseline = 'top';
            ctx.font = "14px 'Arial', 'Helvetica', 'Apple Color Emoji', 'Segoe UI Emoji'";
            ctx.fillStyle = '#f60';
            ctx.fillRect(125, 1, 62, 20);

            ctx.fillStyle = '#069';
            ctx.fillText('AMEVA-Sovereign-AI 🚀 2026', 2, 15);
            ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
            ctx.fillText('AMEVA-Sovereign-AI 🚀 2026', 4, 17);

            ctx.beginPath();
            ctx.arc(50, 45, 12, 0, Math.PI * 2, true);
            ctx.arc(50, 45, 6, 0, Math.PI * 2, true);
            ctx.fill('evenodd');

            return fastHash(canvas.toDataURL());
        } catch (e) {
            return 'canvas_err';
        }
    }

    // 4. AudioContext Float32 Variance Hash
    function getAudioHash() {
        return new Promise((resolve) => {
            try {
                const AudioCtx = window.OfflineAudioContext || window.webkitOfflineAudioContext;
                if (!AudioCtx) return resolve('no_audio_ctx');

                const context = new AudioCtx(1, 44100, 44100);
                const oscillator = context.createOscillator();
                oscillator.type = 'triangle';
                oscillator.frequency.setValueAtTime(10000, context.currentTime);

                const compressor = context.createDynamicsCompressor();
                compressor.threshold.setValueAtTime(-50, context.currentTime);
                compressor.knee.setValueAtTime(40, context.currentTime);
                compressor.ratio.setValueAtTime(12, context.currentTime);
                compressor.attack.setValueAtTime(0, context.currentTime);
                compressor.release.setValueAtTime(0.25, context.currentTime);

                oscillator.connect(compressor);
                compressor.connect(context.destination);
                oscillator.start(0);

                context.oncomplete = (e) => {
                    const samples = e.renderedBuffer.getChannelData(0);
                    let sum = 0;
                    for (let i = 4500; i < 5000; i++) {
                        sum += Math.abs(samples[i]);
                    }
                    resolve(fastHash(sum.toString()));
                };

                context.startRendering().catch(() => resolve('audio_render_err'));
            } catch (e) {
                resolve('audio_exception');
            }
        });
    }

    // 5. JIT Math Floating-Point Quirk Fingerprint
    function getMathQuirk() {
        try {
            const f1 = Math.tan(-1e300);
            const f2 = Math.sinh(1);
            const f3 = Math.cos(1e10);
            return `${f1.toFixed(8)}_${f2.toFixed(8)}_${f3.toFixed(8)}`;
        } catch (e) {
            return 'std_float';
        }
    }

    // 6. Font Signature Prober
    function probeInstalledFonts() {
        const testFonts = [
            'D2Coding', 'Fira Code', 'JetBrains Mono', 'Consolas', 'Monaco', 'Cascadia Code',
            'NanumGothic', 'Malgun Gothic', 'Apple SD Gothic Neo', 'Noto Sans CJK KR',
            'Segoe UI', 'Roboto', 'Helvetica Neue', 'SF Pro Display', 'Ubuntu', 'Courier New',
            'Comic Sans MS', 'Pretendard', 'Spoqa Han Sans Neo'
        ];

        const baseFonts = ['monospace', 'sans-serif', 'serif'];
        const testString = 'mmmmmmmmmmlli11!!@@WWWW';
        const h = document.getElementsByTagName('body')[0] || document.documentElement;

        const span = document.createElement('span');
        span.style.fontSize = '72px';
        span.style.position = 'absolute';
        span.style.left = '-9999px';
        span.style.top = '-9999px';
        span.innerHTML = testString;
        h.appendChild(span);

        const baseWidths = {};
        for (const base of baseFonts) {
            span.style.fontFamily = base;
            baseWidths[base] = span.offsetWidth;
        }

        const detected = [];
        for (const font of testFonts) {
            let found = false;
            for (const base of baseFonts) {
                span.style.fontFamily = `'${font}', ${base}`;
                if (span.offsetWidth !== baseWidths[base]) {
                    found = true;
                    break;
                }
            }
            if (found) detected.push(font);
        }

        h.removeChild(span);
        return {
            installed_fonts: detected.join(', '),
            font_count: detected.length
        };
    }

    // 7. Screen Hz & Color Gamut
    function getDisplayMetrics() {
        let gamut = 'srgb';
        if (window.matchMedia('(color-gamut: rec2020)').matches) gamut = 'rec2020';
        else if (window.matchMedia('(color-gamut: p3)').matches) gamut = 'p3';

        const isHdr = window.matchMedia('(dynamic-range: high)').matches || window.matchMedia('(video-dynamic-range: high)').matches;

        return {
            color_gamut: gamut,
            is_hdr: isHdr
        };
    }

    function measureHz() {
        return new Promise((resolve) => {
            let frames = 0;
            const start = performance.now();
            function count() {
                frames++;
                if (performance.now() - start < 100) {
                    requestAnimationFrame(count);
                } else {
                    const elapsed = (performance.now() - start) / 1000;
                    const hz = Math.round(frames / elapsed);
                    if (hz >= 135 && hz <= 150) resolve(144);
                    else if (hz >= 230 && hz <= 250) resolve(240);
                    else if (hz >= 115 && hz <= 125) resolve(120);
                    else if (hz >= 55 && hz <= 65) resolve(60);
                    else resolve(hz);
                }
            }
            requestAnimationFrame(count);
        });
    }

    // 8. Battery State Harvester
    async function getBatteryState() {
        try {
            if (navigator.getBattery) {
                const b = await navigator.getBattery();
                return {
                    battery_level: Math.round(b.level * 100),
                    is_charging: b.charging,
                    charging_time: b.chargingTime === Infinity ? null : b.chargingTime
                };
            }
        } catch (e) {}
        return { battery_level: null, is_charging: null, charging_time: null };
    }

    // 9. Media Device Counts
    async function getMediaDeviceCounts() {
        try {
            if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
                const devices = await navigator.mediaDevices.enumerateDevices();
                let aIn = 0, vIn = 0, aOut = 0;
                devices.forEach(d => {
                    if (d.kind === 'audioinput') aIn++;
                    else if (d.kind === 'videoinput') vIn++;
                    else if (d.kind === 'audiooutput') aOut++;
                });
                return { audio_inputs_count: aIn, video_inputs_count: vIn, audio_outputs_count: aOut };
            }
        } catch (e) {}
        return { audio_inputs_count: null, video_inputs_count: null, audio_outputs_count: null };
    }

    // 10. Master Harvester Pipeline
    async function harvestAllForensics() {
        const soul = getSoulHistory();
        const canvasHash = getCanvasHash();
        const audioHash = await getAudioHash();
        const mathQuirk = getMathQuirk();
        const fonts = probeInstalledFonts();
        const display = getDisplayMetrics();
        const screenHz = await measureHz();
        const battery = await getBatteryState();
        const media = await getMediaDeviceCounts();

        let glVendor = 'unknown', glRenderer = 'unknown', maxTexture = 0;
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (gl) {
                const dbg = gl.getExtension('WEBGL_debug_renderer_info');
                if (dbg) {
                    glVendor = gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL) || 'generic';
                    glRenderer = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) || 'generic';
                }
                maxTexture = gl.getParameter(gl.MAX_TEXTURE_SIZE) || 0;
            }
        } catch (e) {}

        let usedHeapMb = 0;
        let totalHeapMb = 0;
        try {
            if (window.performance && window.performance.memory) {
                usedHeapMb = Math.round(((window.performance.memory.usedJSHeapSize || 0) / (1024 * 1024)) * 10) / 10;
                totalHeapMb = Math.round(((window.performance.memory.totalJSHeapSize || 0) / (1024 * 1024)) * 10) / 10;
            }
        } catch (e) {}

        const nav = navigator || {};

        return {
            canvas_hash: canvasHash,
            audio_hash: audioHash,
            webgl_vendor: glVendor,
            webgl_renderer: glRenderer,
            webgl_max_texture_size: maxTexture,
            math_jit_precision: mathQuirk,
            installed_fonts: fonts.installed_fonts,
            font_count: fonts.font_count,
            screen_hz: screenHz,
            color_gamut: display.color_gamut,
            is_hdr: display.is_hdr,
            color_depth: window.screen?.colorDepth || 24,
            battery_level: battery.battery_level,
            is_charging: battery.is_charging,
            charging_time: battery.charging_time,
            audio_inputs_count: media.audio_inputs_count,
            video_inputs_count: media.video_inputs_count,
            audio_outputs_count: media.audio_outputs_count,
            used_heap_mb: usedHeapMb,
            total_heap_mb: totalHeapMb,
            is_webdriver: !!nav.webdriver,
            cookie_enabled: nav.cookieEnabled,
            do_not_track: nav.doNotTrack || 'unspecified',
            languages_list: (nav.languages || [nav.language]).join(', '),
            first_seen_at: soul.first_seen_at,
            total_visit_count: soul.total_visit_count,
            total_session_count: soul.total_session_count,
            past_paths_history: soul.past_paths_history
        };
    }

    // Identifiers
    function getUUID(key, storage) {
        try {
            let val = storage.getItem(key);
            if (!val) {
                val = 'usr_' + Math.random().toString(36).substring(2, 15) + '_' + Date.now().toString(36);
                storage.setItem(key, val);
            }
            return val;
        } catch (e) {
            return 'anon_' + Math.random().toString(36).substring(2, 15);
        }
    }

    const visitorId = getUUID('__ameva_vid', localStorage);
    const sessionId = getUUID('__ameva_sid', sessionStorage);

    // =========================================================================
    // 🚀 CLIENT-SIDE IN-MEMORY EVENT BUFFER QUEUE (브라우저 전담 배치 버퍼)
    // =========================================================================
    const eventBatchQueue = [];
    let batchTimer = null;

    function sendPayload(type, data) {
        const payload = {
            type: type,
            timestamp: new Date().toISOString(),
            url: window.location.href,
            pathname: window.location.pathname,
            referrer: document.referrer || '',
            session_id: sessionId,
            visitor_id: visitorId,
            ...data
        };

        const jsonStr = JSON.stringify(payload);

        if (navigator.sendBeacon) {
            try {
                const blob = new Blob([jsonStr], { type: 'application/json' });
                navigator.sendBeacon(API_ENDPOINT, blob);
                return;
            } catch (e) {}
        }

        try {
            fetch(API_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: jsonStr,
                keepalive: true
            }).catch(() => {});
        } catch (e) {}
    }

    // Flush batch queue to serverless endpoint
    function flushBatchQueue() {
        if (eventBatchQueue.length === 0) return;

        const eventsToFlush = eventBatchQueue.splice(0, eventBatchQueue.length);
        if (batchTimer) {
            clearTimeout(batchTimer);
            batchTimer = null;
        }

        sendPayload('batch_events', { batch: eventsToFlush });
    }

    // Enqueue micro-interaction event
    function enqueueEvent(eventData) {
        eventBatchQueue.push({
            occurred_at: new Date().toISOString(),
            pathname: window.location.pathname,
            ...eventData
        });

        // Trigger immediate flush if queue reaches max size
        if (eventBatchQueue.length >= MAX_BATCH_SIZE) {
            flushBatchQueue();
        } else if (!batchTimer) {
            // Otherwise start debounce timer to flush in 6 seconds
            batchTimer = setTimeout(flushBatchQueue, FLUSH_INTERVAL_MS);
        }
    }

    // Initialize session and forensics
    async function init() {
        const nav = navigator || {};
        const scr = window.screen || {};
        const conn = nav.connection || nav.mozConnection || nav.webkitConnection || {};

        const basicHardware = {
            visitor_id: visitorId,
            session_id: sessionId,
            cpu_cores: nav.hardwareConcurrency || null,
            ram_gb: nav.deviceMemory || null,
            js_heap_used_mb: window.performance?.memory ? Math.round(window.performance.memory.usedJSHeapSize / (1024 * 1024)) : null,
            has_webgpu: !!nav.gpu,
            screen_width: scr.width || window.innerWidth,
            screen_height: scr.height || window.innerHeight,
            pixel_ratio: window.devicePixelRatio || 1,
            color_depth: scr.colorDepth || 24,
            is_touch: (nav.maxTouchPoints || 0) > 0,
            platform: nav.platform || 'unknown',
            user_agent: nav.userAgent || '',
            language: nav.language || 'en',
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
            connection_type: conn.effectiveType || conn.type || 'unknown',
            downlink_mbps: conn.downlink || null,
            rtt_ms: conn.rtt || null
        };

        // 1. Session handshake (one-time on load)
        sendPayload('session_init', { hardware: basicHardware });

        // 2. Forensics (one-time after async computation)
        const deepForensics = await harvestAllForensics();
        sendPayload('deep_forensic_ping', { forensics: deepForensics });
    }

    if (document.readyState === 'complete') {
        init();
    } else {
        window.addEventListener('load', init);
    }

    // Engagement Tracking
    const startTime = Date.now();
    let maxScroll = 0;
    window.addEventListener('scroll', () => {
        const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
        if (totalHeight > 0) {
            const currentPercent = Math.round((window.scrollY / totalHeight) * 100);
            if (currentPercent > maxScroll) maxScroll = currentPercent;
        }
    }, { passive: true });

    function flushEngagement() {
        // Flush any pending clicks/copies first
        flushBatchQueue();

        const dwellSeconds = Math.round((Date.now() - startTime) / 1000);
        sendPayload('dwell_ping', {
            dwell_seconds: dwellSeconds,
            max_scroll_percent: maxScroll
        });
    }

    setInterval(flushEngagement, 20000);
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') flushEngagement();
    });
    window.addEventListener('beforeunload', flushEngagement);

    // Micro-Interaction Dynamics (Buffered into In-Memory Queue)
    let mouseDownTime = 0;
    document.addEventListener('mousedown', () => { mouseDownTime = Date.now(); }, { passive: true });
    document.addEventListener('click', (e) => {
        const target = e.target.closest('a, button, [role="button"], select');
        if (!target) return;

        const clickDuration = mouseDownTime > 0 ? (Date.now() - mouseDownTime) : 0;
        const tag = target.tagName.toLowerCase();
        const text = (target.innerText || target.value || target.getAttribute('aria-label') || '').trim().slice(0, 80);
        const href = target.getAttribute('href') || '';
        const id = target.id || '';
        const cls = (target.className || '').toString().slice(0, 80);

        // Enqueue into in-memory buffer (No network hit immediately!)
        enqueueEvent({
            event_type: 'interaction_click',
            target_tag: tag,
            target_id: id,
            target_class: cls,
            target_text: text,
            target_url: href,
            click_duration_ms: clickDuration,
            is_external: href.startsWith('http') && !href.includes(window.location.hostname)
        });
    }, { passive: true });

    // Track Code Copy and Snippet Copy Actions ("뭘했는지")
    document.addEventListener('copy', () => {
        try {
            const sel = window.getSelection() ? window.getSelection().toString().trim().slice(0, 100) : '';
            if (sel) {
                enqueueEvent({
                    event_type: 'copy_snippet',
                    target_tag: 'clipboard',
                    target_text: sel,
                    target_url: window.location.pathname
                });
            }
        } catch (e) {}
    }, { passive: true });

    window.AMEVA_TELEMETRY = {
        trackEvent: (eventType, customData) => {
            enqueueEvent({ event_type: eventType, ...customData });
        },
        visitorId,
        sessionId
    };
})();
