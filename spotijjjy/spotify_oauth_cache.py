import logging
from spotipy.oauth2 import SpotifyOAuth, SpotifyOauthError

logger = logging.getLogger("spotijjjy.oauth")


class RefreshTokenExpiredError(Exception):
    """
    Raised when Spotify rejects a stored refresh token with ``invalid_grant``.

    As of July 20, 2026, Spotify expires user refresh tokens six months after the
    user authorized the app (the clock is NOT extended by refreshing). When this
    happens the stored token is permanently dead and must be replaced by re-running
    the authorization flow (see ``spotijjjy.reauth``) and saving the new refresh
    token into the configured store. Per Spotify's guidance, do NOT retry the
    refresh with the same token - discard it first.
    """
    pass


def _refresh_access_token_or_raise(oauth_manager, refresh_token):
    """
    Wraps ``SpotifyOAuth.refresh_access_token`` and converts an ``invalid_grant``
    failure (an expired or revoked refresh token) into a clear, actionable
    ``RefreshTokenExpiredError``. Any other error is re-raised unchanged.
    """
    try:
        return oauth_manager.refresh_access_token(refresh_token)
    except SpotifyOauthError as e:
        error_code = getattr(e, "error", None)
        if error_code == "invalid_grant" or "invalid_grant" in str(e):
            raise RefreshTokenExpiredError(
                "Spotify rejected the stored refresh token (invalid_grant). It has "
                "expired (Spotify expires user refresh tokens 6 months after "
                "authorization) or been revoked, and cannot be reused. Re-run the "
                "authorization flow (python -m spotijjjy.reauth ...) and save the new "
                "refresh token into the store."
            ) from e
        raise


class SpotifyOauthCache(object):
    def get_and_refresh(self, spotify_playlist_updater):
        raise NotImplementedError('subclasses must override get_and_refresh()!')

    def set_token(self, token):
        raise NotImplementedError('subclasses must override set_token()!')

    def discard_token(self):
        raise NotImplementedError('subclasses must override discard_token()!')


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
        # I'm assuming this is a trusted location, otherwise obviously use pickle
        refresh_token = None
        with open(self.__file, 'r') as f:
            # Get Refresh Token
            refresh_token = f.read()

        if refresh_token is None:
            raise Exception("Error reading from file")

        # Create oauth manager
        client_credentials_manager = SpotifyOAuth(client_id=spotify_playlist_updater.client_id, client_secret=spotify_playlist_updater.client_secret, redirect_uri=spotify_playlist_updater.redirect_url,
                                                  state=None, scope=spotify_playlist_updater.spotify_scope)

        # Refresh token. On invalid_grant this raises RefreshTokenExpiredError and we
        # deliberately leave the stored token untouched (the write below is skipped) so
        # the caller can discard it explicitly and trigger re-authorization.
        new_token = _refresh_access_token_or_raise(client_credentials_manager, refresh_token)

        with open(self.__file, 'w') as f:
            f.write(str(new_token['refresh_token']))

        return new_token

    def set_token(self, token):
        with open(self.__file, 'w') as f:
            f.write(str(token))

    def discard_token(self):
        """
        Removes the stored refresh token so an expired token is not retried. Spotify's
        guidance is to discard a token that failed with invalid_grant before sending the
        user through authorization again.
        """
        import os
        try:
            os.remove(self.__file)
            logger.warning("Discarded expired refresh token file: %s", self.__file)
        except FileNotFoundError:
            pass


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

        # Refresh token. On invalid_grant this raises RefreshTokenExpiredError and we
        # leave the stored item untouched so the caller can discard it and re-authorize.
        new_token = _refresh_access_token_or_raise(client_credentials_manager, refresh_token)

        new_token['key'] = self.__DYNAMO_KEY__

        # Put token back
        self.__table.put_item(Item=new_token)
        return new_token

    def set_token(self, token):
        token['key'] = self.__DYNAMO_KEY__
        self.__table.put_item(Item=token)

    def discard_token(self):
        """
        Removes the stored refresh token so an expired token is not retried. Spotify's
        guidance is to discard a token that failed with invalid_grant before sending the
        user through authorization again.
        """
        self.__table.delete_item(Key={'key': self.__DYNAMO_KEY__})
        logger.warning("Discarded expired refresh token from DynamoDB (key=%s)", self.__DYNAMO_KEY__)
