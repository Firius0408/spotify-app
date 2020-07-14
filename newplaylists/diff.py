import json
import os
import operator
import datetime
import time

def comparePlaylists(p1, p2):
    with open(p1) as f:
        playlist1 = json.load(f)

    with open(p2) as f:
        playlist2 = json.load(f)

    setplaylist1 = set(playlist1)
    setplaylist2 = set(playlist2)
    print('Same songs:')
    print(', '.join(list(setplaylist1 & setplaylist2)))
    print('\n\n\n')
    print('Different songs in first playlist:')
    print(', '.join(list(setplaylist1 - setplaylist2)))
    print('\n\n\n')
    print('Different songs in second playlist:')
    print(', '.join(list(setplaylist2 - setplaylist1)))

def songTrend(song):
    dirlist = os.listdir('.')
    result = []
    for i in dirlist:
        if '.json' not in i:
            continue

        with open(i) as f:
            songs = json.load(f)

        if song in songs:
            result.append(i.replace('.json', ''))

    return sorted(result)

def presence():
    dirlist = os.listdir('.')
    result = []
    for i in dirlist:
        if '.json' not in i:
            continue

        with open(i) as f:
            songs = json.load(f)

        result.extend(songs)

    count = {i:result.count(i) for i in result}
    sortedcount = sorted(list(count.items()), key=operator.itemgetter(1), reverse=True)
    return sortedcount