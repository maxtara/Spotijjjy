import argparse
import json
import logging
import os
from spotijjjy import ABCClient, SpotifyPlaylistUpdater, SpotifyOathDynamoDBStore, SpotifyOathFileStore, ListenToThis, RefreshTokenExpiredError
from spotijjjy.alerts import send_alert
from spotijjjy.logsetup import setup_logging

logger = logging.getLogger("spotijjjy.main")

# Two arguments required for Lambda
def main(event, arg2):
    setup_logging()
    # Get config from either file or enviromental Variable (Json in either case)
    logger.info("event-%s", event)
    if 'CONFIG_FILE' in event: # From CLI or from ENVIROMENT (aws)
        config = json.loads(open(event['CONFIG_FILE']).read())  # Open and read config file
        station_id = event['STATION_ID']
        playlist_id = event['PLAYLIST_ID']
        store = event['STORE']  # file:filename.txt or ddb
        ranges = event['RANGES'] if "RANGES" in event else None
    elif 'CONFIG_FILE' in os.environ: #
        config = json.loads(open(os.environ['CONFIG_FILE']).read())
        station_id = os.environ['STATION_ID']
        playlist_id = os.environ['PLAYLIST_ID']
        store = os.environ['STORE']  # file:filename.txt or ddb
        ranges = os.environ['RANGES'] if "RANGES" in os.environ else None
    else:
        raise("Config not specified in enviroment or arguments (did you forget to add the envirment variable in AWS?)")
    # NB: don't log the raw config - it contains the client secret.
    logger.info("station_id-%s playlist_id-%s store-%s", station_id, playlist_id, store)
    # Connect to ABC
    if station_id.startswith("abc:"):
        try:
            if ranges is not None:
                ranges = [(x.split("%")[0], x.split("%")[1]) for x in ranges.split(",")]
        except:
            logger.error("incorrect RANGES format for ABC, should be comma seperated list of from%%to in iso format")
            logger.error("e.g. 2020-01-01T12:00:00%%2020-01-01T13:00:00,2020-02-01T12:00:00%%2020-02-01T13:00:00")
            exit(1)
        abc = ABCClient(ranges=ranges, station_id=station_id[4:])
        # Get Song Pairs
        song_pairs = abc.get_songs()
    elif station_id.startswith("reddit:"):
        subreddit = station_id[7:]
        if subreddit != "listentothis":
            raise Exception("Currently only supports listentothis. ")
        reddit = ListenToThis()
        # Parse reddit ranges:
        try:
            period = 'week'
            limit = 1000
            if ranges is not None:
                period, limit = ranges.split(",")
                limit = int(limit)
        except:
            logger.error("incorrect RANGES format for reddit. Should be 'period,limit' where period is one of day,week,month,year,all and limit is 1-100")
            logger.error("e.g. week,100 or all,10")
            exit(1)
        song_pairs = reddit.get_songs(period=period, limit=limit)

    # Connect to Spotify
    sp = SpotifyPlaylistUpdater(config, playlist_id)
    # sp.connect_prompt() ---- If you want a OAUTH Token, Uncomment this out. It then gets stored in $cwd/.cache-username. Copy out the refresh token and put it into a text file  / dynamodb
    if store.startswith("file:"): # file:filename.txt or ddb
        oauth_store_cls, oauth_store_arg = SpotifyOathFileStore, store[5:] # file:filename.txt
    else: # dydb
        oauth_store_cls, oauth_store_arg = SpotifyOathDynamoDBStore, store[5:]
    try:
        sp.connect_oauth_store(oauth_store_cls, oauth_store_arg)
    except RefreshTokenExpiredError as e:
        # Spotify expires user refresh tokens 6 months after authorization (effective
        # 2026-07-20). Per Spotify's guidance: do NOT retry, discard the dead token, and
        # re-authorize. We also fire an alert so a human knows to run the reauth flow.
        logger.error("Spotify refresh token expired (invalid_grant). %s", e)
        oauth_store_cls(oauth_store_arg).discard_token()
        logger.error("The expired refresh token has been discarded (will not be retried).")
        logger.error("ACTION REQUIRED: re-authorize with: python -m spotijjjy.reauth interactive <config.json> %s", store)
        send_alert(
            "Spotijjjy: Spotify re-auth required",
            "The Spotify refresh token expired (invalid_grant) and was discarded.\n"
            "Playlist '" + str(playlist_id) + "' (" + str(station_id) + ") did not update.\n\n"
            "Fix it by re-authorizing and storing a new refresh token:\n"
            "  python -m spotijjjy.reauth interactive <config.json> " + store + "\n\n"
            "Or ask the agent: \"refresh the spotify token\".",
        )
        exit(2)
    # Get tracks from spotify search
    tracks = sp.convert_song_pairs_to_spotify_ids(song_pairs)
    # Add tracks to playlist
    sp.add_tracks_to_playlist(tracks)



if __name__ == "__main__":
    setup_logging()
    parser = argparse.ArgumentParser(
        prog="python -m spotijjjy.main",
        description="Generate a Spotify playlist from an ABC station or a subreddit. See README for details.",
    )
    parser.add_argument("config", help="Path to the config JSON (e.g. personal_config.json).")
    parser.add_argument("station_id", help="Source, e.g. 'abc:doublej' or 'reddit:listentothis'.")
    parser.add_argument("playlist_id", help="Target Spotify playlist id.")
    parser.add_argument("store", help="Token store: 'file:<path>' or 'dydb:<table>'.")
    parser.add_argument("ranges", nargs="?", default=None, help="Optional ranges (see README).")
    args = parser.parse_args()

    event = {
        "CONFIG_FILE": args.config,
        "STATION_ID": args.station_id,
        "PLAYLIST_ID": args.playlist_id,
        "STORE": args.store,
    }
    if args.ranges is not None:
        event["RANGES"] = args.ranges
    main(event, "")
