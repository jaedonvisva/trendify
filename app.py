from flask import Flask, redirect, request, session, url_for, render_template
import requests
import os
import base64
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

app = Flask(__name__)
app.secret_key = 'key_to_be_added'

MONGO_URI = os.getenv("MONGO_URI")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:5000/callback"
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_SEARCH_URL = "https://api.spotify.com/v1/search"

mgclient = MongoClient(MONGO_URI)

# Step 1: Homepage with Login Button
@app.route('/', methods=['GET', 'POST'])
def index():
    # Initialize variables
    songs = []
    error = None
    query = None

    access_token = session.get('access_token')
    if not access_token:
        return redirect(url_for('login_page'))

    if request.method == 'POST':
        query = request.form.get('query')
        
        if not query:
            error = "Please enter a song name."
        else:
            
            # Call Spotify API for search
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            params = {
                "q": query,
                "type": "track",
                "limit": 10
            }
            response = requests.get(SPOTIFY_SEARCH_URL, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                tracks = data.get('tracks', {}).get('items', [])
                
                for track in tracks:
                    songs.append({
                        'id': track['id'],
                        'name': track['name'],
                        'artist': ', '.join(artist['name'] for artist in track['artists']),
                        'cover': track['album']['images'][0]['url'] if track['album']['images'] else None,
                        'url': track['external_urls']['spotify']
                    })
            else:
                error = "Failed to fetch search results. Please try again."
    
    return render_template('index.html', songs=songs, error=error, query=query)

@app.route('/login_page')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    scope = "playlist-read-private playlist-modify-public"  # Define your scopes
    auth_url = f"{SPOTIFY_AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={scope}"
    return redirect(auth_url)


# Step 3: Handle Redirect (Callback)
@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Error: Authorization failed."
    
    # Step 4: Exchange code for access token
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    
    response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data)
    if response.status_code != 200:
        return f"Error fetching token: {response.text}"
    
    tokens = response.json()
    access_token = tokens.get('access_token')
    refresh_token = tokens.get('refresh_token')
    
    session['access_token'] = access_token
    session['refresh_token'] = refresh_token
    
    return redirect(url_for('index'))

@app.route('/vote', methods=['POST'])
def vote():
    # Placeholder for voting logic
    song_id = request.args.get('song_id')
    return f"Vote recorded for song ID: {song_id}"
# Optional: Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True)
