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
  
### CLI Usage
  
```
usage: python -m spotijjjy.main config.json abc:station_id    playlist_id <STORE>
usage: python -m spotijjjy.main config.json reddit:subreddit  playlist_id <STORE>
  
e.g.: python -m spotijjjy.main config.json doublej 2jhfs98s3finafzgfse9u3 file:foo.txt [ranges]
e.g.: python -m spotijjjy.main config.json triplej sfiujh38f9hs983fjs3fj9 dydb:tablename [ranges]
  
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
