import os
import subprocess
from flask import Flask, render_template, jsonify, request, send_from_directory
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Ingress environment variables safely
load_dotenv()

app = Flask(__name__)

# Initialize safe backend-to-backend Spotify API client manager
auth_manager = SpotifyClientCredentials(
    client_id=os.environ.get('SPOTIPY_CLIENT_ID'),
    client_secret=os.environ.get('SPOTIPY_CLIENT_SECRET')
)
sp = spotipy.Spotify(auth_manager=auth_manager)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MUSIC_DIR = "/tmp/music"

# Guarantee the local music library folder exists
if not os.path.exists(MUSIC_DIR):
    os.makedirs(MUSIC_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status', methods=['GET'])
def get_status():
    """Initial baseline music metadata configurations on boot."""
    return jsonify({
        'song_name': 'Harehareya',
        'artist': 'Sou',
        'audio_route': '/stream/harehareya.mp3',
        'album_art': '/static/images/default-cover.jpg'
    })

@app.route('/api/search', methods=['GET'])
def search_spotify():
    """Searches Spotify for rich track metadata and high-res album artwork."""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    try:
        results = sp.search(q=query, limit=5, type='track')
        tracks = []
        
        if not results or 'tracks' not in results or 'items' not in results['tracks']:
            return jsonify([])
        
        for item in results['tracks']['items']:
            track_name = item.get('name', 'Unknown Track')
            
            artists_list = item.get('artists', [])
            artist_name = artists_list[0].get('name', 'Unknown Artist') if artists_list else 'Unknown Artist'
            
            album_images = item.get('album', {}).get('images', [])
            album_art = album_images[0].get('url', '') if album_images else ''
            
            tracks.append({
                'id': item.get('id', ''),
                'name': track_name,
                'artist': artist_name,
                'album_art': album_art,
                # spotDL can download any track directly using its public web link
                'spotify_url': item.get('external_urls', {}).get('spotify', '')
            })
        return jsonify(tracks)
    except Exception as e:
        print(f"Metadata fetch exception: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def handle_spotdl_download():
    """Triggers spotdl safely, captures the file, and names it using the explicit track ID."""
    data = request.get_json()
    spotify_url = data.get('spotify_url')
    track_id = data.get('id')

    if not spotify_url or not track_id:
        return jsonify({'error': 'Missing parameters'}), 400

    expected_filename = f"{track_id}.mp3"
    target_path = os.path.join(MUSIC_DIR, expected_filename)

    # 1. Serve immediately if the file already exists from a prior download
    if os.path.exists(target_path):
        return jsonify({'audio_route': f'/stream/{expected_filename}'})

    try:
        print(f"SpotDL Pipeline: Fetching track from URL: {spotify_url}")
        
        # 2. Download the track into a isolated tracking directory using default naming.
        # This completely removes complex template compilation syntax bugs.
        temp_dir = os.path.join(MUSIC_DIR, f"temp_{track_id}")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        command = [
                "spotdl", 
                str(spotify_url),
                "--output", temp_dir,
                "--format", "mp3",
                "--audio", "youtube" # Forces spotdl to authenticate as a human
            ]
        
        # 3. Run command and check terminal error logs
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"CRITICAL SpotDL Error Log from Terminal:\n{result.stderr}")
            return jsonify({'error': 'Downloader execution blocked'}), 500
        
        # 4. Scan the temp folder to grab the newly compiled mp3 file
        downloaded_files = os.listdir(temp_dir)
        mp3_files = [f for f in downloaded_files if f.lower().endswith('.mp3')]
        
        if not mp3_files:
            print("Error: SpotDL finished but no matching MP3 output file was found.")
            return jsonify({'error': 'Scraped audio missing'}), 500
            
        # 5. Move and rename the file into your main music/ directory
        downloaded_file_path = os.path.join(temp_dir, mp3_files[0])
        os.rename(downloaded_file_path, target_path)
        
        # Clean up the temporary folder
        os.rmdir(temp_dir)
        
        print(f"SpotDL Pipeline: Successfully saved local file -> {expected_filename}")
        return jsonify({'audio_route': f'/stream/{expected_filename}'})
        
    except Exception as e:
        print(f"SpotDL Exception Pipeline Failure: {e}")
        return jsonify({'error': 'Streaming download failed'}), 500


@app.route('/stream/<filename>')
def stream_audio(filename):
    """Streams full-length raw audio binaries directly from the local folder."""
    return send_from_directory(MUSIC_DIR, filename, mimetype='audio/mp3')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
