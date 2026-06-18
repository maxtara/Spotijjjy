# Spotijjjy
  
A python script to generate Spotify playlists from rest services. Currently works for Any ABC (Australian Broadcasting Corporation) radio stations and with the subreddit /r/listentothis.
  
Originally designed for Triple J - thus the name.  
  
## Inputs  
  
### ABC  
  
Any ABC (Australian Broadcasting Corporation) radio station  
Known ABC stations are: jazz,dig,doublej,unearthed,country,triplej,classic  
You can choose what timeframe to create a playlist from, it defaults to the previous aired standard morning and afternoon sessions   
  
### Reddit
  
The subreddit 'listentothis'.
Ranges can be any of day,week,month,year,all
  
## Setup
  
### From source
  
```
# Clone the repo
git clone git@github.com:maxtara/Spotijjjy.git
cd Spotijjjy

# Create a [virtualenv](https://virtualenv.pypa.io/en/stable/)
virtualenv env
source env/bin/activate

# install requirements
pip install -r requirements.txt
``` 
  
### From pip
  
```
pip install spotijjjy  
```  
   
### Spotify Intructions
  
To get a Spotify client id, client secret and refresh token, follow instructions at [Spotify Web API Tutorial](https://developer.spotify.com/web-api/tutorial/)  
  
### Oauth token store
  
The oauth token needs to be stored to be refreshed, there are currently two storage options, DynamoDB or a file, specified in the STORE option below.  
If storing the oauth token in DynamoDB, the key to store it is 'spotijjjy_token'.  
  
If using the DynamoDB store, boto3 is required - pip install boto3  

### Refresh token expiry / re-authorization

As of **July 20, 2026**, Spotify expires user refresh tokens **6 months after the user
authorized the app**. Importantly, this lifetime is **not** extended by refreshing — per
[Spotify's docs](https://developer.spotify.com/documentation/web-api/tutorials/refreshing-tokens)
"refreshing an access token does not extend the refresh token's lifetime". Running the
jobs often does **not** keep it alive. Because Spotijjjy edits a playlist on your behalf
(scope `playlist-modify-public`), it must use a user token — the Client Credentials flow
cannot modify playlists, so this expiry is unavoidable and re-auth is needed ~twice a year.

When a token expires, the next refresh fails with `invalid_grant`. Spotijjjy detects this,
raises `RefreshTokenExpiredError`, **discards the dead token** (it is never retried),
logs a loud `ERROR`, fires an alert (see below), and exits with code `2`.

**To re-authorize** (mint and store a fresh refresh token) use `spotijjjy.reauth`:

```
# Easiest - interactive, for a human at a terminal:
python -m spotijjjy.reauth interactive personal_config.json dydb:general

# Or two steps (handy for scripting / agents):
python -m spotijjjy.reauth url personal_config.json
# ...open the URL, sign in, copy the http://localhost/?code=... URL you land on...
python -m spotijjjy.reauth complete personal_config.json dydb:general "http://localhost/?code=AQD..."
```

`<store>` uses the same format as the CLI: `file:<path>` or `dydb:<table>`. The client
secret and tokens are never printed.

**Agent shortcut:** an agent skill is included at
`.github/skills/refresh-spotify-token/`. With it you can just tell your agent
*"refresh the spotify token"* and it will drive the flow above and write the new token
into your real DynamoDB store.

### Alerting when re-auth is needed (AWS, free)

So an expired token never silently breaks your playlists, the Lambda publishes an alert
to an SNS topic when it hits `invalid_grant`. SNS email for this volume (a few alerts a
year) stays within the AWS always-free tier.

The `serverless.yml` creates an SNS topic `spotijjjy-alerts` and an email subscription.
Add your email to `secrets.json` as `ALERT_EMAIL` and deploy:

```
# secrets.json
{ "TABLE_ARN": "...", "ALERT_EMAIL": "you@example.com", ... }

sls deploy
```

AWS sends a one-time "Confirm subscription" email — click it once. After that, any
re-auth-required event emails you. The Lambda reads the topic ARN from the
`ALERT_SNS_TOPIC_ARN` env var (wired automatically by serverless); if that var is unset
(e.g. running the CLI locally) alerting is silently skipped.

  
### CLI Usage
  
```
usage: python -m spotijjjy.main config.json abc:station_id    playlist_id <STORE>
usage: python -m spotijjjy.main config.json reddit:subreddit  playlist_id <STORE>
  
e.g.: python -m spotijjjy.main config.json abc:doublej 2jhfs98s3finafzgfse9u3 file:foo.txt [ranges]
e.g.: python -m spotijjjy.main config.json abc:triplej sfiujh38f9hs983fjs3fj9 dydb:tablename [ranges]
  
Optional argument ranges differs for each input.
  
For abc, it is in the format - comma seperated list of from%to in iso format.
e.g. 2020-01-01T12:00:00%2020-01-01T13:00:00,2020-02-01T12:00:00%2020-02-01T13:00:00
turns into 
    from - 2020-01-01T12:00:00
    to   - 2020-01-01T13:00:00 
and from - 2020-02-01T12:00:00
    to   - 2020-02-01T13:00:00
  
For reddit, it is in the format "period,limit" where period is one of day,week,month,year,all and limit is 1-100"
  
```
  
### Deploy on Serverless (AWS Lambda) Setup
  
Requires serverless (sls) to be installed, and aws credentials setup. More help here: https://www.serverless.com/framework/docs/getting-started/  
```
sls plugin install --name serverless-python-requirements
sls deploy
```
  
Arguments are passed in a env variables, which you can put in the serverless.yml, or a secrets.json like the yaml provided.  
  
## Notes
### Spotify searching
  
I do my best to find the correct song via the spotify search api, using a variety of methods. I use Multiple API options (searching with the artist, or artists, or full text search), and from the returned search results, I try to find the exact song using fuzzy string matching. YMMV  
  
### Deploying
  
```
pytest -vs
python3 setup.py sdist bdist_wheel
python3 -m twine upload dist/*
```
