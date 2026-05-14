from flask import Flask, render_template, jsonify, request
import pygame
import time
import os

app = Flask(__name__)

if os.environ.get("VERCEL"):
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    os.environ["SDL_VIDEODRIVER"] = "dummy"

# Initialize Pygame Mixer
try:
    pygame.mixer.init()
except pygame.error as e:
    print(f"Audio device not available, skipping mixer initialization: {e}")

# Configure your song path and tracking data
SONG_FILE = "harehareya.mp3"

paused = False  # track pause state

# Load the track total length dynamically using Pygame Sound objects
pygame.mixer.music.load(SONG_FILE)
SONG_DURATION = int(pygame.mixer.Sound(SONG_FILE).get_length())

player_state = {
    'song_name': 'Midnight City Ride',
    'artist': 'Synthwave Collective',
    'total_duration': SONG_DURATION,
    'start_time': 0,        # System timestamp when playback started
    'seek_offset': 0,       # The track position (seconds) where we last jumped to
    'is_playing': False,
    'is_paused': False
}

def get_current_track_second():
    """Calculates exactly where the music engine is currently playing."""
    if not player_state['is_playing']:
        return player_state['seek_offset']
    
    if player_state['is_paused']:
        return player_state['seek_offset']
        
    # Calculated current second = position when started + time elapsed since start
    elapsed = time.time() - player_state['start_time']
    current_pos = int(player_state['seek_offset'] + elapsed)
    
    # Cap position at maximum track length
    if current_pos >= player_state['total_duration']:
        return player_state['total_duration']
    return current_pos

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status', methods=['GET'])
def get_status():
    current_sec = get_current_track_second()
    
    # Auto-reset player state if song finishes natively
    if current_sec >= player_state['total_duration'] and player_state['is_playing']:
        player_state['is_playing'] = False
        player_state['is_paused'] = False
        player_state['seek_offset'] = 0

    return jsonify({
        'song_name': player_state['song_name'],
        'artist': player_state['artist'],
        'total_duration': player_state['total_duration'],
        'current_position': current_sec,
        'is_playing': player_state['is_playing'] and not player_state['is_paused']
    })

@app.route('/play', methods=['POST'])
def play():
    pygame.mixer.music.play(start=0)
    player_state['is_playing'] = True
    player_state['is_paused'] = False
    player_state['seek_offset'] = 0
    player_state['start_time'] = time.time()
    return jsonify({'status': 'Playing'})

@app.route('/pause', methods=['POST'])
def pause():
    if player_state['is_playing'] and not player_state['is_paused']:
        # Store exact position before pausing engine
        player_state['seek_offset'] = get_current_track_second()
        pygame.mixer.music.pause()
        player_state['is_paused'] = True
    return jsonify({'status': 'Paused'})

@app.route('/resume', methods=['POST'])
def resume():
    if player_state['is_paused']:
        pygame.mixer.music.unpause()
        player_state['is_paused'] = False
        player_state['start_time'] = time.time() # Reset clock window anchor
    return jsonify({'status': 'Resumed'})

@app.route('/stop', methods=['POST'])
def stop():
    pygame.mixer.music.stop()
    player_state['is_playing'] = False
    player_state['is_paused'] = False
    player_state['seek_offset'] = 0
    return jsonify({'status': 'Stopped'})

@app.route('/seek', methods=['POST'])
def seek():
    data = request.get_json()
    target_seconds = int(data.get('position', 0))
    
    player_state['seek_offset'] = target_seconds
    player_state['start_time'] = time.time()
    
    # Force pygame engine to immediately cut audio feed and jump to new timestamp position
    if player_state['is_playing']:
        pygame.mixer.music.play(start=target_seconds)
        if player_state['is_paused']:
            pygame.mixer.music.pause()
            
    return jsonify({'status': 'Seeking', 'current_position': target_seconds})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False) # use_reloader=False stops double audio initialization
