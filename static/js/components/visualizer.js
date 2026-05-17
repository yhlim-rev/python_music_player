document.addEventListener("DOMContentLoaded", () => {
    const slider = document.getElementById('progress');
    const currentTxt = document.getElementById('current-time');
    const totalTxt = document.getElementById('total-time');
    const btn = document.getElementById('btn-master');
    const bars = document.querySelectorAll('.wave-bar');

    let vInterval = null;
    const PLAY_SVG = `<svg viewBox="0 0 24 24" fill="currentColor"><polygon points="6 3 20 12 6 21 6 3"></polygon></svg>`;
    const PAUSE_SVG = `<svg viewBox="0 0 24 24" fill="currentColor"><rect x="14" y="4" width="4" height="16"></rect><rect x="6" y="4" width="4" height="16"></rect></svg>`;

    function format(s) { const m=Math.floor(s/60), r=Math.floor(s%60); return `${m}:${r<10?'0':''}${r}`; }

    function pulse(on) {
        if (!on) { clearInterval(vInterval); vInterval=null; return bars.forEach(b=>b.style.height='15%'); }
        if (vInterval) return;
        vInterval = setInterval(() => bars.forEach(b => b.style.height = `${Math.floor(Math.random()*75)+20}%`), 120);
    }

    // Connect local elements to global shared engine instance triggers
    window.CyberPlayer.audioEngine.addEventListener('loadedmetadata', () => {
        slider.max = Math.floor(window.CyberPlayer.audioEngine.duration);
        totalTxt.innerText = format(window.CyberPlayer.audioEngine.duration);
    });

    window.CyberPlayer.audioEngine.addEventListener('timeupdate', () => {
        if (!window.CyberPlayer.isUserDragging) {
            slider.value = Math.floor(window.CyberPlayer.audioEngine.currentTime);
            currentTxt.innerText = format(window.CyberPlayer.audioEngine.currentTime);
        }
    });

    btn.addEventListener('click', () => {
        const ae = window.CyberPlayer.audioEngine;
        if (ae.paused) {
            ae.play().then(() => { btn.innerHTML = PAUSE_SVG; pulse(true); });
        } else {
            ae.pause(); btn.innerHTML = PLAY_SVG; pulse(false);
        }
    });

    document.addEventListener('trackWillChange', () => { btn.innerHTML = PAUSE_SVG; pulse(true); });
    slider.addEventListener('input', () => { window.CyberPlayer.isUserDragging = true; });
    slider.addEventListener('change', () => { window.CyberPlayer.audioEngine.currentTime = slider.value; window.CyberPlayer.isUserDragging = false; });
});
