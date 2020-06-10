import json
import requests
from datetime import datetime, timedelta
import difflib
from datetime import datetime


##### APC Config #####
__ABC_URL__ = "https://music.abcradio.net.au/api/v1/plays/search.json?"
__STATIONS__ = ["doublej", "triplej", "jazz"]
__JJJ_SEARCH_LIMIT__ = 100


class ABCClient:
    
    def __init__(self, ranges=None, station_id="triplej"):
        # If ranges is None, use default (morning and arvo sessions)
        self._station_id = station_id
        if ranges is None:
            ranges = self.__get_previous_days_ranges()
        self.__urls = self.__get_staion_urls(ranges)
        

    def __get_previous_days_ranges(self):
        """
        Gets ranges for morning and arvo sessions for jjj. to use instead of default values
        """
        # We are sort of assuming this is ran at midday local time
        d = datetime.today() - timedelta(days=1)
        # Get days
        day = d.isoformat()[:11]
        return [(day + "20:00:00", day + "23:00:00"), (day + "05:00:00",  day + "07:30:00")]

    def __get_staion_urls(self, ranges):
        """
        ranges - date ranges, array of tuples of ISO to/from - [(from,to),(from,to)]
        returns - list of URLS assosiated with ranges
        e.g. #https://music.abcradio.net.au/api/v1/plays/search.json?station=triplej&from=2017-09-13T05:00:00&to=2017-09-13T07:30:00&limit=100&order=asc
        """
        limit = "&" + "limit=" + str(__JJJ_SEARCH_LIMIT__)
        station = "station=" + self._station_id
        __FULL_URL__ = __ABC_URL__ + station
        urls = []
        for ran in ranges:
            dates = "&from=" + ran[0] + "&to=" + ran[1]
            url = __FULL_URL__ + dates + limit
            urls.append(url)
        return urls

    def get_songs_for_urls(self):
        """
        Returns a list of song - artist tuples for given urls
        """
        # Query ABC urls for songs
        songs = []
        for url in self.__urls:
            resp = requests.get(url=url)
            data = json.loads(resp.text)
            songs.extend(data["items"])

        # Convert songs to tuple
        # we are using a set in case the same song is played in multiple URLs
        song_pairs = set()
        for song in songs:
            title = song['recording']['title'].lower()
            artists_json = song['recording']['artists']
            artists = set()
            if type(artists_json) is list:
                for artist in artists_json:
                    artists.add(artist['name'].lower())
            elif type(artists_json) is dict:
                for artist in artists_json.values():
                    artists.add(artist['name'].lower())
            else:
                raise IOError("Type of artist is not dict or array")
            song_pairs.add((title, frozenset(artists)))  # Potenially this could be a list, shouldnt be dupe artists
        return list(song_pairs)

