const progressSlider = document.getElementById('progress');
const currentTimeText = document.getElementById('current-time');
const totalTimeText = document.getElementById('total-time');
const waveBars = document.querySelectorAll('.wave-bar');
const masterButton = document.getElementById('btn-master');

// Hidden background HTML5 engine instantiation
const audioEngine = new Audio();

let isUserDragging = false; 
let visualizerInterval = null;
let isMetadataLoaded = false;

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

// 1. Initial Metadata Load from Flask
function initializePlayer() {
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            document.getElementById('song-title').innerText = data.song_name;
            document.getElementById('artist-name').innerText = data.artist;
            
            // Assign the Flask streaming URL source to the HTML5 audio engine
            audioEngine.src = data.audio_route;
        })
        .catch(err => console.error('Initialization error:', err));
}

// 2. Track Local Browser Audio Events to Update UI Automatically
audioEngine.addEventListener('loadedmetadata', () => {
    totalDurationSeconds = audioEngine.duration;
    progressSlider.max = Math.floor(totalDurationSeconds);
    totalTimeText.innerText = formatTime(totalDurationSeconds);
    isMetadataLoaded = true;
});

audioEngine.addEventListener('timeupdate', () => {
    // Drive the slider roller forward as the audio plays in the browser
    if (!isUserDragging && isMetadataLoaded) {
        progressSlider.value = Math.floor(audioEngine.currentTime);
        currentTimeText.innerText = formatTime(audioEngine.currentTime);
    }
});

audioEngine.addEventListener('ended', () => {
    document.getElementById('status').innerText = "Stopped";
    animateVisualizer(false);
    masterButton.innerText = "▶";
    masterButton.title = "Play";
    progressSlider.value = 0;
    currentTimeText.innerText = "0:00";
});

// 3. Handle Click Toggle Interactions locally (Zero Server Latency)
masterButton.addEventListener('click', () => {
    if (audioEngine.paused) {
        audioEngine.play()
            .then(() => {
                document.getElementById('status').innerText = "Playing";
                animateVisualizer(true);
                masterButton.innerText = "‖"; 
                masterButton.title = "Pause";
            })
            .catch(err => console.error("Playback failed:", err));
    } else {
        audioEngine.pause();
        document.getElementById('status').innerText = "Paused";
        animateVisualizer(false);
        masterButton.innerText = "⚡"; 
        masterButton.title = "Resume";
    }
});

// 4. Handle Slider Scrubbing (Jumping forward/backward instantly)
progressSlider.addEventListener('input', (e) => {
    isUserDragging = true;
    currentTimeText.innerText = formatTime(e.target.value);
});

progressSlider.addEventListener('change', (e) => {
    // Instantly seek within the browser audio buffer element
    audioEngine.currentTime = parseInt(e.target.value);
    isUserDragging = false;
});

// Trigger setup on structural load
initializePlayer();
