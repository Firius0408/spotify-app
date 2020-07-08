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

def songTrend(song, length):
    try:
        dirlist = os.listdir(length)
    except FileNotFoundError:
        print(length + 'is not a valid length')
        return

    result = []
    for i in dirlist:
        with open(length + '/' + i) as f:
            songs = json.load(f)

        if song in songs:
            result.append((i.replace('.json', ''), songs.index(song) + 1))

        else:
            result.append((i.replace('.json', ''), -1))

    return sorted(result, key=operator.itemgetter(0))

def presence(length):
    try:
        dirlist = os.listdir(length)
    except FileNotFoundError:
        print(length + 'is not a valid length')
        return

    result = []
    for i in dirlist:
        with open(length + '/' + i) as f:
            songs = json.load(f)

        for song in songs:
            result.append(song)

    count = {i:result.count(i) for i in result}
    sortedcount = sorted(list(count.items()), key=operator.itemgetter(1), reverse=True)
    return sortedcount

def weight(length):
    try:
        dirlist = os.listdir(length)
    except FileNotFoundError:
        print(length + 'is not a valid length')
        return

    dates = []
    ranks = {}
    for i in dirlist:
        with open(length + '/' + i) as f:
            songs = json.load(f)

        date = datetime.datetime.strptime(i.replace('.json', ''), '%Y-%m-%d').date()
        dates.append(date)
        for song in songs:
            if song not in ranks.keys():
                ranks[song] = {} 

            ranks[song][date] = songs.index(song) + 1

    areas = {}
    for key,value in ranks.items():
        area = 0.0
        count = 0.0
        for i in range(0,len(dates) - 1):
            date = dates[i]
            date1 = dates[i+1]
            if date not in value.keys() or date1 not in value.keys():
                continue
                
            temp = value[date]
            temp1 = value[date1]
            counttemp = (date1 - date).total_seconds()
            area +=  counttemp * ((temp + temp1) / 2)
            count += counttemp

        if count:
            areas[key] = area/count

    sort = sorted(list(areas.items()), key=operator.itemgetter(1))
    return sort
