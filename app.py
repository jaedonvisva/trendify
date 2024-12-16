from flask import Flask, redirect, request, session, url_for, render_template
import requests
import os
import base64
from dotenv import load_dotenv
from pymongo import MongoClient
from models import *

load_dotenv()

app = Flask(__name__)
app.secret_key = 'key_to_be_added'

# spotify API
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:5000/callback"
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_SEARCH_URL = "https://api.spotify.com/v1/search"

# initalize mongodb
MONGO_URI = os.getenv("MONGO_URI")
mgclient = MongoClient(MONGO_URI)
database = mgclient.get_database("trendify")
song_collection = database.get_collection("songs")
votes_collection = database.get_collection("votes")
playlist_collection = database.get_collection("playlists")
users_collection = database.get_collection("users")

# index route
@app.route('/', methods=['GET', 'POST'])
def index():
    songs = []
    error = None
    query = None

    access_token = session.get('access_token')
    if not access_token:
        return redirect(url_for('login_page'))
    
    user = session.get("user")
    username = user["name"]
    id = user['id']

    if request.method == 'POST':
        query = request.form.get('query')
        
        if not query:
            error = "Please enter a song name."
        else:
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
    
    return render_template('index.html', songs=songs, error=error, query=query, username = username, id=id)

# login page
@app.route('/login_page')
def login_page():
    return render_template('login.html')

# login route
@app.route('/login', methods=["GET", "POST"])
def login():
    scope = "playlist-read-private playlist-modify-public user-read-email user-read-private user-library-read"
    auth_url = f"{SPOTIFY_AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={scope}"
    return redirect(auth_url)


@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Error: Authorization failed."
    
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
    
    # Use Bearer token to get user profile
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    user_profile_response = requests.get("https://api.spotify.com/v1/me", headers=headers)
    if user_profile_response.status_code != 200:
        return f"Error fetching user profile: {user_profile_response.text}"
    
    user_profile = user_profile_response.json()

    session['access_token'] = access_token
    session['refresh_token'] = refresh_token
    session['user'] = {
        "id": user_profile.get('id'),
        "name": user_profile.get('display_name'),
        "email": user_profile.get('email')
    }
    
    return redirect(url_for('index'))


@app.route('/add', methods=['POST'])
def add():
    song_id = request.args.get('song_id')
    user_id = session['user']['id']
    return f"Added {song_id} by {user_id} to {None}"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/playlist/<playlist_id>')
def playlist_details(playlist_id):
    user_id = session['user']['id']
    if not user_id:
        return redirect('/login')

    # Fetch the playlist by ID
    playlist = playlist_collection.find_one({"playlist_id": playlist_id})

    # Check if the user has access to the playlist
    if not playlist or (user_id not in playlist['members'] and user_id != playlist['created_by']):
        return "You do not have access to this playlist", 403

    playlist_songs = list(song_collection.find({"spotify_id": {"$in": playlist['songs']}}))

    return render_template('playlist_details.html', playlist=playlist, songs=playlist_songs)

@app.route('/playlists')
def playlists():
    user_id = session['user']['id']
    if not user_id:
        return redirect('/login')

    user_playlists = list(playlist_collection.find({
        "$or": [
            {"created_by": user_id},
            {'members': user_id}
        ]
    }))

    return render_template('playlists.html', playlists=user_playlists)

if __name__ == '__main__':
    app.run(debug=True)
