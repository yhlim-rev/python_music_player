const progressSlider = document.getElementById('progress');
const currentTimeText = document.getElementById('current-time');
const totalTimeText = document.getElementById('total-time');
const waveBars = document.querySelectorAll('.wave-bar');
const masterButton = document.getElementById('btn-master');

let totalDurationSeconds = 0;
let isUserDragging = false; 
let visualizerInterval = null;
let currentButtonAction = "PLAY"; // Internal tracker state: "PLAY", "PAUSE", or "RESUME"

function formatTime(seconds) {
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

function updateStatusLoop() {
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            document.getElementById('song-title').innerText = data.song_name;
            document.getElementById('artist-name').innerText = data.artist;
            
            totalDurationSeconds = data.total_duration;
            progressSlider.max = totalDurationSeconds; 
            totalTimeText.innerText = formatTime(totalDurationSeconds);

            if (!isUserDragging) {
                progressSlider.value = data.current_position;
                currentTimeText.innerText = formatTime(data.current_position);
            }

            // Route single button icons and behavior matching the Flask backend status
            if (data.is_playing) {
                document.getElementById('status').innerText = "Playing";
                animateVisualizer(true);
                masterButton.innerText = "‖"; // Render pause icon when track is active
                masterButton.title = "Pause";
                currentButtonAction = "PAUSE";
            } else if (data.current_position > 0 && !data.is_playing) {
                document.getElementById('status').innerText = "Paused";
                animateVisualizer(false);
                masterButton.innerText = "⚡"; // Render resume lightning bolt icon when paused
                masterButton.title = "Resume";
                currentButtonAction = "RESUME";
            } else {
                document.getElementById('status').innerText = "Stopped";
                animateVisualizer(false);
                masterButton.innerText = "▶"; // Render base triangle play icon when stopped/idle
                masterButton.title = "Play";
                currentButtonAction = "PLAY";
            }
        })
        .catch(err => console.error('Status sync error:', err));
}

updateStatusLoop();
setInterval(updateStatusLoop, 1000);

function sendCommand(route) {
    fetch(route, { method: 'POST' })
        .then(response => response.json())
        .then(() => {
            updateStatusLoop(); 
        })
        .catch(err => console.error('Command routing error:', err));
}

// Intercept clicks and switch target routes contextually
masterButton.addEventListener('click', () => {
    if (currentButtonAction === "PAUSE") {
        sendCommand('/pause');
    } else if (currentButtonAction === "RESUME") {
        sendCommand('/resume');
    } else {
        sendCommand('/play');
    }
});

// Slider Track Interceptors
progressSlider.addEventListener('input', (e) => {
    isUserDragging = true;
    currentTimeText.innerText = formatTime(e.target.value);
});

progressSlider.addEventListener('change', (e) => {
    const targetSeconds = parseInt(e.target.value);
    
    fetch('/seek', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ position: targetSeconds })
    })
    .then(res => res.json())
    .then(() => {
        isUserDragging = false;
    })
    .catch(err => {
        console.error(err);
        isUserDragging = false;
    });
});
