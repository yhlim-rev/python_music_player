const progressSlider = document.getElementById('progress');
const currentTimeText = document.getElementById('current-time');
const totalTimeText = document.getElementById('total-time');
const waveBars = document.querySelectorAll('.wave-bar');
const playButton = document.getElementById('btn-play');

let totalDurationSeconds = 0;
let isUserDragging = false; 
let visualizerInterval = null;
let isTrackPausedState = false; // Tracks if the player is currently paused

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

            // Route UI changes based on exact player state
            if (data.is_playing) {
                document.getElementById('status').innerText = "Playing";
                animateVisualizer(true);
                playButton.innerText = "▶";
                playButton.title = "Play";
                isTrackPausedState = false;
            } else if (data.current_position > 0 && !data.is_playing) {
                document.getElementById('status').innerText = "Paused";
                animateVisualizer(false);
                // Transform Play button into Resume appearance
                playButton.innerText = "⚡";
                playButton.title = "Resume Music";
                isTrackPausedState = true;
            } else {
                document.getElementById('status').innerText = "Stopped";
                animateVisualizer(false);
                playButton.innerText = "▶";
                playButton.title = "Play";
                isTrackPausedState = false;
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

// Smart Play/Resume Toggle Listener
playButton.addEventListener('click', () => {
    if (isTrackPausedState) {
        sendCommand('/resume');
    } else {
        sendCommand('/play');
    }
});

// Control Events
document.getElementById('btn-pause').addEventListener('click', () => sendCommand('/pause'));
document.getElementById('btn-stop').addEventListener('click', () => sendCommand('/stop'));

// Slider Tracking
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
