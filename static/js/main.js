// ==========================================================================
// AUDIO STREAMING ENGINE WITH DIRECT INLINE SVG TRANSITIONS
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
    const progressSlider = document.getElementById('progress');
    const currentTimeText = document.getElementById('current-time');
    const totalTimeText = document.getElementById('total-time');
    const waveBars = document.querySelectorAll('.wave-bar');
    const masterButton = document.getElementById('btn-master');
    const lyricsContainer = document.getElementById('lyrics-container');
    const lyricLines = document.querySelectorAll('.lyric-line');

    const audioEngine = new Audio();

    let isUserDragging = false; 
    let visualizerInterval = null;
    let isMetadataLoaded = false;

    // --- RAW HARDWARE-NATIVE VECTOR INJECTIONS ---
    const PLAY_SVG = `
        <svg viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="6 3 20 12 6 21 6 3"></polygon>
        </svg>
    `;

    const PAUSE_SVG = `
        <svg viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="14" y="4" width="4" height="16" rx="1"></rect>
            <rect x="6" y="4" width="4" height="16" rx="1"></rect>
        </svg>
    `;

    function formatTime(seconds) {
        if (isNaN(seconds)) return "0:00";
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
    }

    function animateVisualizer(isRunning) {
        if (!isRunning) {
            clearInterval(visualizerInterval);
            visualizerInterval = null;
            waveBars.forEach(bar => bar.style.height = '15%'); 
            return;
        }
        if (visualizerInterval) return; 

        visualizerInterval = setInterval(() => {
            waveBars.forEach(bar => {
                const activeHeight = Math.floor(Math.random() * 75) + 20;
                bar.style.height = `${activeHeight}%`;
            });
        }, 120);
    }

    function initializePlayer() {
        fetch('/status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('song-title').innerText = data.song_name;
                document.getElementById('artist-name').innerText = data.artist;
                audioEngine.src = data.audio_route;
            })
            .catch(err => console.error('Initialization error:', err));
    }

    audioEngine.addEventListener('loadedmetadata', () => {
        totalDurationSeconds = audioEngine.duration;
        progressSlider.max = Math.floor(totalDurationSeconds);
        totalTimeText.innerText = formatTime(totalDurationSeconds);
        isMetadataLoaded = true;
    });

    audioEngine.addEventListener('timeupdate', () => {
        const currentTime = audioEngine.currentTime;

        if (!isUserDragging && isMetadataLoaded) {
            progressSlider.value = Math.floor(currentTime);
            currentTimeText.innerText = formatTime(currentTime);
        }

        let currentActiveLine = null;
        lyricLines.forEach((line) => {
            const lineTime = parseFloat(line.getAttribute('data-time'));
            if (currentTime >= lineTime) { currentActiveLine = line; }
        });

        if (currentActiveLine && !currentActiveLine.classList.contains('active')) {
            lyricLines.forEach(line => line.classList.remove('active'));
            currentActiveLine.classList.add('active');
            currentActiveLine.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });

    audioEngine.addEventListener('ended', () => {
        document.getElementById('status').innerText = "Stopped";
        animateVisualizer(false);
        masterButton.innerHTML = PLAY_SVG;
        masterButton.title = "Play";
        progressSlider.value = 0;
        currentTimeText.innerText = "0:00";
    });

    masterButton.addEventListener('click', () => {
        if (audioEngine.paused) {
            audioEngine.play()
                .then(() => {
                    document.getElementById('status').innerText = "Playing";
                    animateVisualizer(true);
                    masterButton.innerHTML = PAUSE_SVG; // Direct raw hardware injection
                    masterButton.title = "Pause";
                })
                .catch(err => console.error("Playback failed:", err));
        } else {
            audioEngine.pause();
            document.getElementById('status').innerText = "Paused";
            animateVisualizer(false);
            masterButton.innerHTML = PLAY_SVG; // Direct raw hardware injection
            masterButton.title = "Resume";
        }
    });

    progressSlider.addEventListener('input', (e) => {
        isUserDragging = true;
        currentTimeText.innerText = formatTime(e.target.value);
    });

    progressSlider.addEventListener('change', (e) => {
        audioEngine.currentTime = parseInt(e.target.value);
        isUserDragging = false;
    });

    initializePlayer();
});
