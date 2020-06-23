import sys, os
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')
from spotijjjy import ABCClient


abc = ABCClient(None, "triplej")

def test_date_ranges():
    v = abc.get_songs()
    print(v)
    assert len(v) > 20