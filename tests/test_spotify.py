import sys, os
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')
from unittest import mock
from spotipy.oauth2 import SpotifyOauthError
from spotijjjy import SpotifyOathDynamoDBStore, SpotifyPlaylistUpdater, RefreshTokenExpiredError
from spotijjjy.spotify_oauth_cache import _refresh_access_token_or_raise
from spotijjjy import reauth, alerts

def test_oath():
    pass

def test_invalid_grant_maps_to_refresh_expired():
    manager = mock.Mock()
    manager.refresh_access_token.side_effect = SpotifyOauthError('boom', error='invalid_grant')
    try:
        _refresh_access_token_or_raise(manager, 'sometoken')
        assert False, "expected RefreshTokenExpiredError"
    except RefreshTokenExpiredError:
        pass

def test_other_oauth_errors_pass_through():
    manager = mock.Mock()
    manager.refresh_access_token.side_effect = SpotifyOauthError('nope', error='server_error')
    try:
        _refresh_access_token_or_raise(manager, 'sometoken')
        assert False, "expected SpotifyOauthError"
    except RefreshTokenExpiredError:
        assert False, "should not be mapped"
    except SpotifyOauthError:
        pass

def test_alert_skipped_without_topic(monkeypatch):
    monkeypatch.delenv(alerts.ALERT_TOPIC_ENV, raising=False)
    assert alerts.send_alert('subject', 'message') is False

def test_reauth_build_authorize_url():
    config = {
        '__CLIENT_ID__': 'cid', '__CLIENT_SECRET__': 'sec',
        '__REDIRECT_URL__': 'http://localhost', '__SPOTIFY_SCOPE__': 'playlist-modify-public',
    }
    url = reauth.build_authorize_url(config)
    assert url.startswith('https://accounts.spotify.com/authorize')
    assert 'client_id=cid' in url
    assert 'sec' not in url  # secret must never leak into the URL


