import requests
from spotijjjy import SongService

class RedditException(Exception):
    pass


class Reddit:
    TimePeriods = set(['day', 'week', 'month', 'year', 'all'])
    BaseUrl = 'https://www.reddit.com'

    def __init__(self, subreddit):
        self.subreddit = subreddit

    def top(self, period, limit):
        if period not in Reddit.TimePeriods:
            raise RedditException('Invalid time period string: {}. Expected one of {}'.format(period, ', '.join(Reddit.TimePeriods)))

        params = {'t': period, 'limit': limit}
        listing = self.__get('top', params)
        return listing        

    def __get(self, dest, params):
        url = '{}/r/{}/{}.json'.format(Reddit.BaseUrl, self.subreddit, dest)

        headers = {
            'User-Agent': 'spotijjjy',
            'Accept': 'application/json'
        }

        r = requests.get(url, params=params, headers=headers)

        if not r.raise_for_status():
            return r.json()

class ListenToThis(Reddit, SongService):
    ThreadType = "t3"

    def __init__(self):
        self.subreddit = 'listentothis'
        

    def get_songs(self, period, limit):
        # Returns song_pairs = [ (title, frozenset(artists)) ]
        listing = super().top(period, limit)
        titles = [l['data']['title'] for l in listing['data']['children'] if l['kind'] == ListenToThis.ThreadType]
        # MainArtistName -- trackName [genre / genres] (year)
        # objs format = (title, frozenset(artists))
        objs = []
        for title in titles:
            t = title.replace("--", "-") # format is double, but people dont always follow the format! Crazy!
            # No '-' means either not a song, on not following the format
            if '-' not in t:
                continue
            probably_song_title = t.split('-')[1]
            probably_artist = t.split('-')[0]
            if '[' in probably_song_title:
                probably_song_title = probably_song_title.split('[')[0]
                # Strip spaces
                probably_song_title = ' '.join(probably_song_title.split())
                probably_artist = ' '.join(probably_artist.split())

                objs.append( ( probably_song_title, frozenset( (probably_artist ,) )  ))
        return objs

if __name__ == "__main__":
    songs = ListenToThis().top('week', 50)
    for song in songs:
        print(song)