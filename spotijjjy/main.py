import sys
import json
import os
from spotijjjy import ABCClient, SpotifyPlaylistUpdater, SpotifyOathDynamoDBStore, SpotifyOathFileStore
# Two arguments required for Lambda


def main(event, arg2):
    # Get config from either file or enviromental Variable (Json in either case)
    print("event-" + str(event))
    print("arg2-" + str(arg2))
    if 'CONFIG_FILE' in event: # From CLI or from ENVIROMENT (aws)
        config = json.loads(open(event['CONFIG_FILE']).read())  # Open and read config file
        station_id = event['STATION_ID']
        playlist_id = event['PLAYLIST_ID']
        store = event['STORE'] # file:filename.txt or ddb
    elif 'CONFIG_FILE' in os.environ: #
        config = json.loads(open(os.environ['CONFIG_FILE']).read())
        station_id = os.environ['STATION_ID']
        playlist_id = os.environ['PLAYLIST_ID']
        store = os.environ['STORE'] # file:filename.txt or ddb
    else:
        raise("Config not specified in enviroment or arguments (did you forget to add the envirment variable in AWS?)")
    print("config-" + str(config))
    print("station_id-" + str(station_id))
    # Connect to ABC
    abc = ABCClient(ranges=None, station_id=station_id)
    # Get Song Pairs
    song_pairs = abc.get_songs_for_urls()
    # print(song_pairs)
    
    # Connect to Spotify
    sp = SpotifyPlaylistUpdater(config, playlist_id)
    if store.startswith("file"): # file:filename.txt or ddb
        sp.connect_oauth_store(SpotifyOathFileStore, store[5:]) # file:filename.txt
    else: # dydb
        sp.connect_oauth_store(SpotifyOathDynamoDBStore,  store[5:])
    # Get tracks from spotify search
    tracks = sp.convert_song_pairs_to_spotify_ids(song_pairs)
    # Add tracks to playlist
    sp.add_tracks_to_playlist(tracks)



if __name__ == "__main__":
    event = {}
    event["CONFIG_FILE"] = sys.argv[1]
    event['STATION_ID'] = sys.argv[2]
    event['PLAYLIST_ID'] = sys.argv[3]
    event['STORE'] = sys.argv[4]
    main(event, "")
