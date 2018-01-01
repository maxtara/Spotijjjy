from ABCClient import ABCClient
from SpotifyPlaylistUpdater import SpotifyPlaylistUpdater
from SpotifyOauthCache import SpotifyOathFileStore
from SpotifyOauthCache import SpotifyOathDynamoDBStore
import sys
import json
import os

##Two arguments required for Lambda
def main(event, arg2):
    #Get config from either file or enviromental Variable (Json in either case)
    if 'CONFIG_FILE' in event:
        config = json.loads(open(event['CONFIG_FILE']).read()) #Open and read config file
    elif 'CONFIG_FILE' in os.environ:
        config = json.loads(os.environ['CONFIG_FILE'])
    else:
        raise("Config not specified in enviroment or arguments (did you forget to add the envirment variable in AWS?)")
    #Connect to ABC
    abc = ABCClient(None) 
    #Get Song Pairs
    song_pairs = abc.get_songs_for_urls()
    #Connect to Spotify
    sp = SpotifyPlaylistUpdater(config)
    sp.connect_oauth_store(SpotifyOathDynamoDBStore,  "general")
    # Get tracks from spotify search
    tracks = sp.convert_song_pairs_to_spotify_ids(song_pairs)
    #Add tracks to playlist
    sp.add_tracks_to_playlist( tracks)
    #sp.set_token(SpotifyOathDynamoDBStore,  "general")


if __name__ == "__main__":
    event = {}
    if len(sys.argv) > 1:
        event["CONFIG_FILE"] =  sys.argv[1] # Custom config file
    else:
        event["CONFIG_FILE"] =  "config.json" # Default config file
    main(event,"") 
    
    
