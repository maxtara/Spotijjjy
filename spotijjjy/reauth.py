"""
Re-authorize Spotijjjy and store a fresh refresh token.

Spotify expires *user* refresh tokens 6 months after authorization (effective
2026-07-20). When that happens the scheduled job fails with ``invalid_grant`` and a
human (or an agent) must mint a new refresh token by completing the OAuth
authorization-code flow once, then write it into the store the job reads from.

This module makes that a ~20 second task and is safe for an agent to drive, because the
browser/consent step is split out from the secret-handling step:

  # 1. Get the Spotify sign-in URL (no secrets printed):
  python -m spotijjjy.reauth url personal_config.json

  # 2. Open it, sign in (you already granted the app, so it just redirects), copy the
  #    URL you land on (looks like http://localhost/?code=...) and finish the exchange,
  #    writing the new refresh token into the real store:
  python -m spotijjjy.reauth complete personal_config.json dydb:general "http://localhost/?code=AQD..."

  # Or, for a human at a terminal, do both steps interactively:
  python -m spotijjjy.reauth interactive personal_config.json dydb:general

Security notes:
* The authorize URL contains only your (non-secret) client_id.
* The redirect URL contains a short-lived single-use auth code - it is never logged.
* The client secret and the resulting refresh/access tokens are never printed.
"""
import argparse
import json
import logging

from spotipy.oauth2 import SpotifyOAuth

from spotijjjy import SpotifyOathDynamoDBStore, SpotifyOathFileStore
from spotijjjy.logsetup import setup_logging

logger = logging.getLogger("spotijjjy.reauth")


def _oauth_manager(config):
    return SpotifyOAuth(
        client_id=config["__CLIENT_ID__"],
        client_secret=config["__CLIENT_SECRET__"],
        redirect_uri=config["__REDIRECT_URL__"],
        scope=config["__SPOTIFY_SCOPE__"],
        state=None,
        open_browser=False,
    )


def _store_from_arg(store):
    """
    Turns a ``file:foo.txt`` / ``dydb:tablename`` store argument (same format as
    ``main.py``) into a cache-store instance.
    """
    if store.startswith("file:"):
        return SpotifyOathFileStore(store[5:])
    if store.startswith("dydb:"):
        return SpotifyOathDynamoDBStore(store[5:])
    raise ValueError("Unknown store '%s' - expected 'file:<path>' or 'dydb:<table>'" % store)


def load_config(config_path):
    with open(config_path) as f:
        return json.load(f)


def build_authorize_url(config):
    """Returns the Spotify authorization URL to open in a browser."""
    return _oauth_manager(config).get_authorize_url()


def complete(config, store, redirect_response):
    """
    Exchanges the auth code (from the URL the user was redirected to) for tokens and
    writes the fresh refresh token into ``store``. Returns nothing sensitive.
    """
    oauth = _oauth_manager(config)
    code = oauth.parse_response_code(redirect_response)
    if not code or code == redirect_response:
        raise ValueError(
            "Could not find an auth 'code' in the supplied redirect URL. Paste the full "
            "URL you were redirected to, e.g. http://localhost/?code=AQD..."
        )
    token_info = oauth.get_access_token(code, as_dict=True, check_cache=False)

    cache_store = _store_from_arg(store)
    # The DynamoDB/file stores persist the whole token dict (incl. refresh_token).
    cache_store.set_token(token_info)
    logger.warning("Stored a fresh refresh token into %s. Spotijjjy is reauthorized.", store)


def interactive(config, store):
    """Human-friendly flow: show the URL, read the redirect URL from stdin, finish."""
    url = build_authorize_url(config)
    logger.info("Open this URL in your browser and sign in to Spotify:")
    logger.info("    %s", url)
    logger.info("After signing in you'll be redirected to a URL like http://localhost/?code=...")
    redirect_response = input("Paste that full redirect URL here: ").strip()
    complete(config, store, redirect_response)
    logger.info("Done - fresh refresh token stored. You can re-run your playlist jobs now.")


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m spotijjjy.reauth",
        description="Re-authorize Spotijjjy and store a fresh Spotify refresh token.",
    )
    store_help = "Token store: 'file:<path>' or 'dydb:<table>' (same format as main.py)."
    sub = parser.add_subparsers(dest="command", required=True)

    p_url = sub.add_parser("url", help="Print the Spotify sign-in URL (no secrets).")
    p_url.add_argument("config", help="Path to the config JSON (e.g. personal_config.json).")

    p_complete = sub.add_parser(
        "complete", help="Exchange the redirect URL for tokens and store the refresh token.")
    p_complete.add_argument("config", help="Path to the config JSON.")
    p_complete.add_argument("store", help=store_help)
    p_complete.add_argument(
        "redirect_url", help="The full URL you were redirected to (contains ?code=...).")

    p_interactive = sub.add_parser(
        "interactive", help="Guided flow: prints the URL and prompts for the redirect URL.")
    p_interactive.add_argument("config", help="Path to the config JSON.")
    p_interactive.add_argument("store", help=store_help)

    return parser


def main(argv=None):
    args = _build_parser().parse_args(argv)
    if args.command == "url":
        # Printed (not logged) because this value is meant to be captured/piped.
        print(build_authorize_url(load_config(args.config)))
    elif args.command == "complete":
        complete(load_config(args.config), args.store, args.redirect_url)
    elif args.command == "interactive":
        interactive(load_config(args.config), args.store)
    return 0


if __name__ == "__main__":
    setup_logging()
    raise SystemExit(main())
