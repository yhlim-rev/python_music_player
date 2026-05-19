import os
import io
import shutil
import subprocess
import boto3
from botocore.config import Config
from flask import Flask, render_template, jsonify, request, send_from_directory
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.cache_handler import MemoryCacheHandler

# Ingress environment variables safely
load_dotenv()

app = Flask(__name__)

# Initialize safe backend-to-backend Spotify API client manager
auth_manager = SpotifyClientCredentials(
    client_id=os.environ.get('SPOTIPY_CLIENT_ID'),
    client_secret=os.environ.get('SPOTIPY_CLIENT_SECRET'),
    cache_handler=MemoryCacheHandler() 
)
sp = spotipy.Spotify(auth_manager=auth_manager)

# Cloudflare R2 Configurations
ACCOUNT_ID = os.environ.get('CF_ACCOUNT_ID')
BUCKET_NAME = os.environ.get('CF_BUCKET_NAME')

r2_client = boto3.client(
    's3',
    endpoint_url=f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=os.environ.get('CF_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('CF_SECRET_ACCESS_KEY'),
    config=Config(signature_version='s3v4'),
    region_name='auto'
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Kept strictly for quick local scratchpad processing during runtime download
MUSIC_DIR = os.path.join(os.path.dirname(__file__), 'tmp')


def generate_r2_url(filename):
    """Helper logic to generate a secure 1-hour access stream link directly from R2."""
    return r2_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': BUCKET_NAME, 'Key': filename},
        ExpiresIn=3600
    )


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
                'spotify_url': item.get('external_urls', {}).get('spotify', '')
            })
        return jsonify(tracks)
    except Exception as e:
        print(f"Metadata fetch exception: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/download', methods=['POST'])
def handle_spotdl_download():
    """Triggers spotdl, pushes binary object to R2, and spits out a presigned streaming link."""
    data = request.get_json()
    spotify_url = data.get('spotify_url')
    track_id = data.get('id')

    if not spotify_url or not track_id:
        return jsonify({'error': 'Missing parameters'}), 400

    expected_filename = f"{track_id}.mp3"

    # 1. Serve immediately if the file already exists globally in Cloudflare R2
    try:
        r2_client.head_object(Bucket=BUCKET_NAME, Key=expected_filename)
        print(f"R2 Hit: Serving existing remote copy for track {track_id}")
        return jsonify({'audio_route': generate_r2_url(expected_filename)})
    except r2_client.exceptions.ClientError:
        # Object does not exist, proceed with download execution pipelines
        pass

    temp_dir = os.path.join(MUSIC_DIR, f"temp_{track_id}")
    try:
        print(f"SpotDL Pipeline: Fetching track from URL: {spotify_url}")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        command = [
            "spotdl", 
            str(spotify_url),
            "--output", temp_dir,
            "--format", "mp3",
            "--audio", "youtube"
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"CRITICAL SpotDL Error Log from Terminal:\n{result.stderr}")
            return jsonify({'error': 'Downloader execution blocked'}), 500
        
        downloaded_files = os.listdir(temp_dir)
        mp3_files = [f for f in downloaded_files if f.lower().endswith('.mp3')]
        
        if not mp3_files:
            print("Error: SpotDL finished but no matching MP3 output file was found.")
            return jsonify({'error': 'Scraped audio missing'}), 500
            
        local_file_path = os.path.join(temp_dir, mp3_files[0])
        
        # 2. Upload file directly into your Cloudflare R2 bucket storage instance
        print(f"R2 Pipeline: Uploading {expected_filename} to Cloudflare...")
        with open(local_file_path, 'rb') as data_stream:
            r2_client.upload_fileobj(
                data_stream, 
                BUCKET_NAME, 
                expected_filename,
                ExtraArgs={'ContentType': 'audio/mp3'}
            )
        
        # 3. Generate secure link to return to client
        presigned_url = generate_r2_url(expected_filename)
        print(f"R2 Pipeline: Successfully saved remote file -> {expected_filename}")
        return jsonify({'audio_route': presigned_url})
        
    except Exception as e:
        print(f"SpotDL Exception Pipeline Failure: {e}")
        return jsonify({'error': 'Streaming download failed'}), 500
    finally:
        # Clean up local system storage immediately
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


@app.route('/stream/<filename>')
def stream_audio(filename):
    """Fallback legacy route for default boot song assets kept on your disk."""
    return send_from_directory(MUSIC_DIR, filename, mimetype='audio/mp3')


if __name__ == '__main__':
    # Make sure local music folder scratchpad directory is present on runtime initialization
    if not os.path.exists(MUSIC_DIR):
        os.makedirs(MUSIC_DIR)
    app.run(debug=True, port=5000)
