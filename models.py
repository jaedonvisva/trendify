class Song:
    def __init__(self, track_id, name, artist, album_cover, spotify_url, added_by, playlist_id):
        self.track_id = track_id
        self.name = name
        self.artist = artist
        self.album_cover = album_cover
        self.spotify_url = spotify_url
        self.added_by = added_by
        self.playlist_id = playlist_id
        self.votes = []
    
    def to_dict(self):
        return{
            "track_id": self.track_id,
            "name": self.name,
            "artist": self.artist,
            "album_cover": self.album_cover,
            "spotify_url": self.spotify_url,
            "added_by": self.added_by,
            "playlist_id": self.playlist_id,
            "votes": self.votes
        }

class User:
    def __init__(self, spotify_id, profile_url, name):
        self.spotify_id = spotify_id
        self.profile_url = profile_url
        self.name = name

    def to_dict(self):
        return {
            "spotify_id": self.spotify_id,
            "profile_url": self.profile_url,
            "name":self.name
        }

class Playlist:
    def __init__(self, playlist_id, name, created_by, members):
        self.playlist_id = playlist_id
        self.name = name
        self.created_by = created_by
        self.members = members

    def to_dict(self):
        return{
            "playlist_id": self.playlist_id,
            "name": self.name,
            "created_by": self.created_by,
            "members": self.members
        }

class Vote:
    def __init__(self, spotify_id, track_id, playlist_id):
        self.user_id = spotify_id
        self.song_id = track_id
        self.playlist_id = playlist_id

    def to_dict(self):
        return{
            "user_id": self.user_id,
            "song_id": self.song_id,
            "playlist_id": self.playlist_id
        }
    