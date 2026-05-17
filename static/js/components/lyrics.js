document.addEventListener("DOMContentLoaded", () => {
    const lines = document.querySelectorAll('.lyric-line');

    window.CyberPlayer.audioEngine.addEventListener('timeupdate', () => {
        const ct = window.CyberPlayer.audioEngine.currentTime;
        let active = null;

        lines.forEach(l => { if (ct >= parseFloat(l.getAttribute('data-time'))) active = l; });

        if (active && !active.classList.contains('active')) {
            lines.forEach(l => l.classList.remove('active'));
            active.classList.add('active');
            active.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });
});
