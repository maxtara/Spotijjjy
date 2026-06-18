import sys, os
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')
from unittest import mock
from spotipy.oauth2 import SpotifyOauthError
from spotijjjy import SpotifyOathDynamoDBStore, SpotifyOathFileStore, SpotifyPlaylistUpdater, RefreshTokenExpiredError
from spotijjjy import spotify_oauth_cache
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


class _FakePlaylistUpdater:
    client_id = client_secret = redirect_url = ''
    spotify_scope = 'playlist-modify-public'


def test_file_store_set_token_then_refresh_roundtrip(tmp_path, monkeypatch):
    """
    reauth writes a token dict via set_token; get_and_refresh must read back the raw
    refresh-token string (not a dict repr) so the next refresh works. Guards bug where a
    re-authed file store fed a dict-repr to Spotify and got invalid_grant again.
    """
    token_file = tmp_path / "token.txt"
    store = SpotifyOathFileStore(str(token_file))

    # reauth.complete() hands the whole token dict to set_token.
    store.set_token({"access_token": "a1", "refresh_token": "REFRESH1", "expires_in": 3600})
    assert token_file.read_text() == "REFRESH1"  # only the refresh token, no dict repr

    class FakeOAuth:
        def __init__(self, **kwargs):
            pass

        def refresh_access_token(self, refresh_token):
            assert refresh_token == "REFRESH1"  # got the raw token, not "{...}"
            return {"access_token": "a2", "refresh_token": "REFRESH2", "expires_in": 3600}

    monkeypatch.setattr(spotify_oauth_cache, "SpotifyOAuth", FakeOAuth)
    new_token = store.get_and_refresh(_FakePlaylistUpdater())
    assert new_token["refresh_token"] == "REFRESH2"
    assert token_file.read_text() == "REFRESH2"


def test_file_store_discard_token(tmp_path):
    token_file = tmp_path / "token.txt"
    token_file.write_text("REFRESH1")
    SpotifyOathFileStore(str(token_file)).discard_token()
    assert not token_file.exists()
    # discarding an already-missing token is a no-op, not an error.
    SpotifyOathFileStore(str(token_file)).discard_token()

