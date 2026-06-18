---
name: refresh-spotify-token
description: >-
  Re-authorize Spotijjjy with Spotify and store a fresh refresh token into the real
  store (DynamoDB in AWS, or a local file). Use when the user says things like "refresh
  the token", "refresh the spotify token", "spotijjjy needs re-auth", or after a job
  failed with invalid_grant. Spotify expires user refresh tokens 6 months after
  authorization, so this is needed roughly twice a year.
---

# Refresh the Spotify token (Spotijjjy)

Spotify expires *user* refresh tokens 6 months after authorization. When that happens
the scheduled playlist jobs fail with `invalid_grant` and stop updating until someone
mints a new refresh token and stores it. This skill drives that flow end to end.

The OAuth consent screen requires a real human to sign in to Spotify **once**, so this
is a guided flow: you (the agent) generate the sign-in URL and write the resulting token
to AWS; the user just clicks the link, signs in, and pastes back the URL they land on.

## Before you start

- The user's real Spotify credentials live in a gitignored config file, usually
  `personal_config.json` (fields `__CLIENT_ID__`, `__CLIENT_SECRET__`,
  `__REDIRECT_URL__`, `__SPOTIFY_SCOPE__`). Confirm the path with the user if unsure.
- The production store is `dydb:general` (DynamoDB table `general`). A local file store
  looks like `file:token.txt`. Confirm which one the user wants; default to `dydb:general`.
- Writing to DynamoDB uses the user's **real AWS account** via their default AWS
  credentials/region (boto3). Make sure AWS creds are available in the environment
  (e.g. `aws sts get-caller-identity` succeeds). Do not ask for or print AWS keys.

## Security rules (important)

- **Never print or echo** the client secret, access token, or refresh token.
- The redirect URL the user pastes back contains a short-lived auth code — do not log it
  to any persistent file; just pass it straight into the `complete` command.
- Only run the commands below; do not improvise alternative ways to handle the secrets.

## Steps

1. Generate the Spotify sign-in URL (prints only the non-secret client_id):

   ```
   python -m spotijjjy.reauth url personal_config.json
   ```

2. Give that URL to the user and ask them to:
   - open it in a browser, sign in to Spotify (they already granted the app, so it just
     redirects — no consent screen), and
   - copy the **full URL they get redirected to** (looks like
     `http://localhost/?code=AQD...`) and paste it back to you.

3. Complete the exchange and write the fresh refresh token into the real store. Pass the
   pasted URL as the last argument, quoted:

   ```
   python -m spotijjjy.reauth complete personal_config.json dydb:general "<PASTED_REDIRECT_URL>"
   ```

   On success it logs `Stored a fresh refresh token ... Spotijjjy is reauthorized.`

4. Confirm to the user that the token was refreshed and the scheduled jobs will work on
   their next run. Optionally trigger one job to verify (e.g. invoke the `doublej`
   Lambda, or run `python -m spotijjjy.main personal_config.json abc:doublej <playlist_id> dydb:general`).

## Notes

- If `python -m spotijjjy.reauth` can't import `spotipy`/`boto3`, install requirements
  first: `pip install -r requirements.txt boto3`.
- If the user is fully local (no AWS), use a `file:<path>` store instead of `dydb:general`.
- This whole flow is also documented for humans in the README under
  "Refresh token expiry / re-authorization".
