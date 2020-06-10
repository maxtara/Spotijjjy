import json
import requests
import spotipy
import spotipy.util as util
from datetime import datetime, timedelta
import difflib
from datetime import datetime


class SpotifyPlaylistUpdater:
    ###### Private Members ####
    #
    # __sp - Spotippy client
    # __whole_access_token - copy of the access token
    #
    def __init__(self, config, playlist_id):
        self.__sp = None
        self.__whole_access_token = None
        self.username = config['__USERNAME__']
        self.spotify_scope = config['__SPOTIFY_SCOPE__']
        self.client_id = config['__CLIENT_ID__']
        self.client_secret = config['__CLIENT_SECRET__']
        self.redirect_url = config['__REDIRECT_URL__']
        self.spotify_search_limit = config['__SPOTIFY_SEARCH_LIMIT__']
        self.playlist_id = playlist_id

    def connect_prompt(self):
        """
        Connects to spotify using prompt
        """
        token = util.prompt_for_user_token(
            self.username, scope=self.spotify_scope, client_id=self.client_id, client_secret=self.client_secret,
            redirect_uri=self.redirect_url)
        # Create Client  refresh_access_token(refresh_token)
        self.__sp = spotipy.Spotify(auth=token)

    def connect_non_authenticated(self):
        """
        Connects to spotify using client Creds (limited use, only really used for testing)
        """
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
        client_credentials_manager = SpotifyClientCredentials(
            client_id=self.client_id, client_secret=self.client_secret)
        self.__sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    def connect_oauth_store(self, oath_cache, *args):
        """
        Connects to spotify using oath
        """
        cache_store = oath_cache(*args)
        new_token = cache_store.get_and_refresh(self)
        access_token = new_token['access_token']
        self.__sp = spotipy.Spotify(auth=access_token)
        self.__whole_access_token = new_token

    def is_connected(self):
        return self.__sp is not None

    def check_connected(self):
        if not self.is_connected():
            raise Exception("Not connected to spotify, run one of the connect functions first")

    def find_one_song_spotify(self, song_pair, cutoff=0.6, search_include_first_artist=False, do_general_search=False, verbose=False):
        """
        Returns one track id for an input song.

        Arguments
        song_pair - (title - string, artists - collection of strings) - eg ('blood', frozenset({'gang of youths'}))
        cutoff - RE difflib.get_close_matches cutoff. 
        search_include_first_artist - if to include the first artist in the spotify query. Has mixed results.
        do_general_search - don't tell spotify its a song, can be useful in some cases (when the artist is in the title string)

        Returns - id - string
        """
        #import pdb
        # pdb.set_trace()
        self.check_connected()
        song = song_pair[0]
        artists = song_pair[1]
        q = r"track:" + song
        if do_general_search:
            q = song  # don't specify its a track, can be useful
        if(search_include_first_artist):
            q += r" artist:" + list(artists)[0]
        searched_songs = self.__sp.search(q, limit=self.spotify_search_limit, type='track')['tracks']['items']
        for searched_song in searched_songs:
            searched_artists = searched_song['artists']
            for searched_artist in searched_artists:
                searched_artist_name = searched_artist['name'].lower()
                score = len(difflib.get_close_matches(searched_artist_name, artists, 1, cutoff))
                if score > 0:
                    if verbose:
                        print(
                            "FOUND - " + str(song_pair) + " ==== " + searched_artist_name + ":" + searched_song['name'])
                    return searched_song['id']
        return None  # None Found

    def add_tracks_to_playlist(self, tracks):
        self.check_connected()
        # Hack to clear the playlist
        self.__sp.user_playlist_replace_tracks(self.username, self.playlist_id, [])
        #user_playlist_add_tracks(self, user, playlist_id, tracks, position=None)
        self.__sp.user_playlist_add_tracks(self.username, self.playlist_id, tracks)

    def convert_song_pairs_to_spotify_ids(self, song_pairs):
        tracks = []
        for song_pair in song_pairs:
            track = self.find_one_song_spotify(song_pair)
            if track is None:
                # Try again with different search parameters
                track = self.find_one_song_spotify(song_pair, 0.6, True)
            if track is None:
                # Try with different parameters again!
                track = self.find_one_song_spotify(song_pair, 0.6, False, True)
            if track is None:
                # Give up
                print("Could not find spotify song for " + str(song_pair))
            else:
                tracks.append(track)
        return list(set(tracks))

    def set_token(self, oath_cache, *args):
        """
        Connects to spotify using oath
        """
        cache_store = oath_cache(*args)
        cache_store.set_token(self.__whole_access_token)
