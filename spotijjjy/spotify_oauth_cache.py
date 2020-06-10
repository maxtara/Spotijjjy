import json
import requests
import spotipy
import spotipy.util as util
from datetime import datetime, timedelta
import difflib
from datetime import datetime
from spotipy.oauth2 import SpotifyOAuth
from spotijjjy import SpotifyPlaylistUpdater


class SpotifyOauthCache(object):
    def get_and_refresh(self, spotify_playlist_updater):
        raise NotImplementedError('subclasses must override get_and_refresh()!')

    def set_token(self, token):
        raise NotImplementedError('subclasses must override get_and_refresh()!')


class SpotifyOathFileStore(SpotifyOauthCache):

    # Cache file contents example
    def __init__(self, fileCacheLocation):
        self.__file = fileCacheLocation

    def get_and_refresh(self, spotify_playlist_updater):
        """
        1. Gets old token from file
        2. Refreshes token using SpotifyOAuth
        3. Saves new token to file
        4. Returns access token (String)
        """
        #import pdb
        # pdb.set_trace()
        # I'm assuming this is a trusted location, otherwise obviously use pickle
        old_token = None
        with open(self.__file, 'r') as f:
            s = f.read()
            old_token = eval(s)

        if old_token is None:
            raise Exception("Error reading from file")

        # Get Refresh Token
        refresh_token = old_token['refresh_token']

        # Create oauth manager
        client_credentials_manager = SpotifyOAuth(client_id=spotify_playlist_updater.client_id, client_secret=spotify_playlist_updater.client_secret, redirect_uri=spotify_playlist_updater.redirect_url,
                                                  state=None, scope=spotify_playlist_updater.spotify_scope)

        # Refresh token
        new_token = client_credentials_manager.refresh_access_token(refresh_token)

        with open(self.__file, 'w') as f:
            f.write(str(old_token))

        return new_token

    def set_token(self, token):
        with open(self.__file, 'w') as f:
            f.write(str(token))


class SpotifyOathDynamoDBStore(SpotifyOauthCache):

    # Cache file contents example
    __DYNAMO_KEY__ = "spotijjjy_token"

    def __init__(self, table_name):
        import boto3
        dynamodb = boto3.resource('dynamodb')
        self.__table = dynamodb.Table(table_name)

    def get_and_refresh(self, spotify_playlist_updater):
        """
        1. Gets old token from DynamoDB
        2. Refreshes token using SpotifyOAuth
        3. Saves new token to DynamoDB
        4. Returns access token (String)
        """
        old_token = self.__table.get_item(Key={'key': self.__DYNAMO_KEY__})['Item']
        if old_token is None:
            raise Exception("Error reading from DynamoDB")

        # Get Refresh Token
        refresh_token = old_token['refresh_token']

        # Create oauth manager
        client_credentials_manager = SpotifyOAuth(client_id=spotify_playlist_updater.client_id, client_secret=spotify_playlist_updater.client_secret, redirect_uri=spotify_playlist_updater.redirect_url,
                                                  state=None, scope=spotify_playlist_updater.spotify_scope)

        # Refresh token
        new_token = client_credentials_manager.refresh_access_token(refresh_token)

        new_token['key'] = self.__DYNAMO_KEY__

        # Put token back
        self.__table.put_item(Item=new_token)
        return new_token

    def set_token(self, token):
        token['key'] = self.__DYNAMO_KEY__
        self.__table.put_item(Item=token)
