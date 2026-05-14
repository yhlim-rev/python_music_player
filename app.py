import os
from flask import Flask, render_template, jsonify, send_from_directory

app = Flask(__name__)

# Absolute path targeting the directory where app.py actually lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

player_state = {
    'song_name': 'Harehareya',
    'artist': 'Sou',
    # Points cleanly to your streaming route with the explicit filename
    'audio_route': '/stream/harehareya.mp3'  
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status', methods=['GET'])
def get_status():
    """Returns baseline music metadata to the browser configuration loader."""
    return jsonify(player_state)

@app.route('/stream/<filename>')
def stream_audio(filename):
    """Safely extracts chunks from the root folder and pipes them to the user."""
    try:
        # Pulls directly from the absolute root path, bypassing Vercel local tracking issues
        return send_from_directory(BASE_DIR, filename, mimetype='audio/mp3')
    except FileNotFoundError:
        return "Audio File Not Found on Server", 404

if __name__ == '__main__':
    app.run(debug=True)
