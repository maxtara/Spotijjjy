from ABCClient import ABCClient
from SpotifyPlaylistUpdater import SpotifyPlaylistUpdater
from SpotifyOauthCache import SpotifyOathFileStore
from SpotifyOauthCache import SpotifyOathDynamoDBStore
import sys
import json
import os

# Two arguments required for Lambda


def main(event, arg2):
    # Get config from either file or enviromental Variable (Json in either case)
    print(str(event))
    print(str(arg2))
    if 'CONFIG_FILE' in event:
        config = json.loads(event['CONFIG_FILE'])  # Open and read config file
        count = int(event['STATION_ID'])
    elif 'CONFIG_FILE' in os.environ:
        config = json.loads(os.environ['CONFIG_FILE'])
        count = int(os.environ['STATION_ID'])
    else:
        raise("Config not specified in enviroment or arguments (did you forget to add the envirment variable in AWS?)")
    # Connect to ABC
    abc = ABCClient(ranges=None, station_id=count)
    # Get Song Pairs
    song_pairs = abc.get_songs_for_urls()
    # Connect to Spotify
    sp = SpotifyPlaylistUpdater(config, count)
    sp.connect_oauth_store(SpotifyOathDynamoDBStore,  "general")
    # Get tracks from spotify search
    tracks = sp.convert_song_pairs_to_spotify_ids(song_pairs)
    # Add tracks to playlist
    sp.add_tracks_to_playlist(tracks)
    #sp.set_token(SpotifyOathDynamoDBStore,  "general")


if __name__ == "__main__":
    event = {}
    if len(sys.argv) > 1:
        event["CONFIG_FILE"] = open(sys.argv[1]).read()  # Custom config file
        event['STATION_ID'] = 1
    else:
        event["CONFIG_FILE"] = open("config.json").read()  # Default config file
        event['STATION_ID'] = 1
    main(event, "")
