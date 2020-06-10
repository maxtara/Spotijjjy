# Spotijjjy

A python script to generate Spotify playlists from rest services. Currently works for Any ABC (Australian Broadcasting Corporation) with a /r/listentothis playlist generator in progress

Originally designed for Triple J - thus the name.

## Inputs

### ABC

Any ABC (Australian Broadcasting Corporation) radio station (TrippleJ, DoubleJ etc)

## Setup

### From source

```
# Clone the repo
git clone git@github.com:maxtarasuik/Spotijjjy.git
cd Spotijjjy

# Create a [virtualenv](https://virtualenv.pypa.io/en/stable/)
virtualenv env
source env/bin/activate

# install requirements
pip install -r requirements.txt
```

### From pip

TODO

## Run

### Spotify Intructions

To get a Spotify client id, client secret and refresh token, follow instructions at [Spotify Web API Tutorial](https://developer.spotify.com/web-api/tutorial/)

### Oauth token store

The oauth token needs to be stored to be refreshed, there are currently two storage options, DynamoDB or a file, specified in the STORE option below.
If storing the oauth token in DynamoDB, the key to store it is 'spotijjjy_token'.

### CLI Usage

```
usage: python -m spotijjjy.main config.json station_id playlist_id <STORE>

e.g.: python -m spotijjjy.main config.json doublej 2jhfs98s3finafzgfse9u3 file:foo.txt
e.g.: python -m spotijjjy.main config.json triplej sfiujh38f9hs983fjs3fj9 dydb:tablename

```

### Deploy on Serverless (AWS Lambda) Setup

Requires serverless (sls) to be installed, and aws credentials setup. More help here: https://www.serverless.com/framework/docs/getting-started/
```
sls plugin install --name serverless-python-requirements
sls deploy
```

Arguments are passed in a env variables, which you can put in the serverless.yml, or a secrets.json like the yaml provided.