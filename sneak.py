from spotify import *
import operator
import time
import re

ignore = ['Post Malone', 'AJR', 'Ed Sheeran', 'Eminem', 'Logic', 'Queen', 'Bleachers', 'L?', 'IYLHLHG', 'Wd', 'Hh', 'Nc', 'Defined', 'Musical', 'Disney', 'Indie', 'Classical', 'Monstercat', 'Rap', 'House', 'U+1F494', 'The Beatles', 'Ashley', 'Jonathan', 'Daniel', 'Phillip', 'Shan']
#ignore = ['Post Malone', 'AJR', 'Ed Sheeran', 'Eminem', 'Logic', 'Queen', 'Bleachers', 'The Beatles']

def getUserPlaylists(userString):
    user = getUserFromString(userString)
    userid = ''
    if user is not None:
        userid = user['id'] 
    else:
        userid = userString

    accessToken = accessTokenBot()
    playlists = []
    url = 'https://api.spotify.com/v1/users/' + userid + '/playlists?limit=50'
    headers = {'Authorization': 'Bearer ' + accessToken}
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))

            continue

        playlists.append(r.json()['items'])
        if r.json()['next'] is None:
            break

        url = r.json()['next']

    return playlists

def getUser(userString):
    user = getUserFromString(userString)
    userid = ''
    if user is not None:
        userid = user['id'] 
    else:
        userid = userString

    url = 'https://api.spotify.com/v1/users/' + userid
    headers = {'Authorization': 'Bearer ' + accessTokenBot()}
    r = requests.get(url, headers=headers)
    return r.json()

def getPlaylist(userString, playlistString):
    playlists = getUserPlaylists(userString)
    playlistnames = []
    for i in playlists:
        for s in i:
            playlistnames.append(s['name'])

    playlist = process.extractOne(playlistString, playlistnames, score_cutoff=80)
    if playlist is None:
        print ('Unable to determine playlist')
        return

    for i in playlists:
        for s in i:
            if s['name'] == playlist[0]:
                return s

def getArtistsInPlaylist(s, accessToken, artists, grouped):
    url = s['tracks']['href'] + '?fields=next,items(track(artists))'
    headers = {'Authorization': 'Bearer ' + accessToken}
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))

            continue

        for p in r.json()['items']:
            if p is None: 
                continue

            if grouped:
                trackartists = []
                for i in p['track']['artists']:
                    trackartists.append(i['name'])

                artists.append(', '.join(trackartists))
            else:
                for i in p['track']['artists']:
                    artists.append(i['name'])

        if r.json()['next'] is None:
            break

        url = r.json()['next'] + '?fields=next,items(track(artists))'

def getGenresInPlaylist(s, accessToken, artists):
    url = s['tracks']['href'] + '?fields=next,items(track(artists))'
    headers = {'Authorization': 'Bearer ' + accessToken}
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))

            continue

        for p in r.json()['items']:
            if p is None:
                continue

            for i in p['track']['artists']:
                if i['id'] is not None and i['id'] not in artists: 
                    artists.append(i['id'])

        if r.json()['next'] is None:
            break

        url = r.json()['next'] + '?fields=next,items(track(artists))'

def getSongsInPlaylist(s, accessToken, tracks, name):
    url = s['tracks']['href'] + '?fields=next,items(track(name,id,artists,popularity,album(name)))'
    headers = {'Authorization': 'Bearer ' + accessToken}
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))

            continue

        for p in r.json()['items']:
            if p is None:
                continue

            tracks.append(p['track']['id'])
            artists = []
            for i in p['track']['artists']:
                artists.append(i['name'])

            name[p['track']['id']] = 'Title: ' + p['track']['name'] + '    Artists: ' + ', '.join(artists) + '     Album: ' + p['track']['album']['name'] + '  Popularity: ' + str(p['track']['popularity'])
        if r.json()['next'] is None:
            break

        url = r.json()['next'] + '?fields=next,items(track(name,id,artists,album(name)))'

def getSongsPlaylist(s, accessToken):
    if "Past 4 Weeks" in s['name']:
        directory = 'month'
    elif "Past 6 Months" in s['name']:
        directory = '6month'
    elif "All-Time" in s['name']:
        directory = 'all'
    else:
        return

    match = re.search(r'\d{1,2}/\d{1,2}/\d{4}', s['name'])
    if match is None:
        print(s['name'])
        return

    date = datetime.datetime.strptime(match.group(), '%m/%d/%Y').date()
    filename = date.strftime('%Y-%m-%d')
    print(directory + '     ' + filename)
    url = s['tracks']['href'] + '?fields=next,items(track(name))'
    name = []
    headers = {'Authorization': 'Bearer ' + accessToken}
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))

            continue

        for p in r.json()['items']:
            name.append(p['track']['name'])

        if r.json()['next'] is None:
            break

        url = r.json()['next'] + '?fields=next,items(track(name))'

    filtered = [i for i in name if i]
    with open('./topsongs/' + directory + '/' + filename + '.json', 'w') as f:
        json.dump(filtered, f, indent=4, separators=(', ', ': '))

def topArtistsInPlaylists(userString, grouped=False):
    user = getUser(userString)
    playlists = getUserPlaylists(userString)
    accessToken = accessTokenBot()
    artists = []
    threads = []
    for i in playlists:
        for s in i:
            if "Top Songs of " in s['name'] or user['id'] != s['owner']['id'] or s['name'] in ignore:
                continue

            x = threading.Thread(target=getArtistsInPlaylist, args=(s, accessToken, artists, grouped))
            threads.append(x)
            x.start()


    for index, thread in enumerate(threads):
        thread.join()

    count = {i:artists.count(i) for i in artists}
    if None in list(count.keys()):
        del count[None]

    sortedCount = sorted(list(count.items()), key=operator.itemgetter(1), reverse=True)
    with open('./sortedArtistsCount.json', 'w') as f:
        json.dump(sortedCount, f, indent=4, separators=(', ', ': '))

    return sortedCount

def topArtistsInPlaylist(userString, playlistString, grouped=False):
    playlist = getPlaylist(userString, playlistString)
    accessToken = accessTokenBot()
    artists = []
    getArtistsInPlaylist(playlist, accessToken, artists, grouped)
    count = {i:artists.count(i) for i in artists} 
    if None in list(count.keys()):
        del count[None]

    sortedCount = sorted(list(count.items()), key=operator.itemgetter(1), reverse=True)
    with open('./sortedArtistsCount.json', 'w') as f:
        json.dump(sortedCount, f, indent=4, separators=(', ', ': '))

    return sortedCount

def topArtistsInPlaylisthref(playlisthref, grouped=False):
    accessToken = accessTokenBot()
    url = playlisthref + '?fields=next,items(track(artists))'
    artists = []
    headers = {'Authorization': 'Bearer ' + accessToken}
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))

            continue

        for p in r.json()['items']:
            if p is None:
                continue

            if grouped:
                trackartists = []
                for i in p['track']['artists']:
                    trackartists.append(i['name'])

                artists.append(', '.join(trackartists))
            else:
                for i in p['track']['artists']:
                    artists.append(i['name'])

        if r.json()['next'] is None:
            break

        url = r.json()['next'] + '?fields=next,items(track(artists))'

    count = {i:artists.count(i) for i in artists} 
    if None in list(count.keys()):
        del count[None]

    sortedCount = sorted(list(count.items()), key=operator.itemgetter(1), reverse=True)
    with open('./sortedArtistsCount.json', 'w') as f:
        json.dump(sortedCount, f, indent=4, separators=(', ', ': '))

    return sortedCount

def topGenresInPlaylists(userString):
    user = getUser(userString)
    if user is None:
        return

    playlists = getUserPlaylists(userString)
    accessToken = accessTokenBot()
    artists  = []
    threads = []
    for i in playlists:
        for s in i:
            if "Top Songs of " in s['name'] or user['id'] != s['owner']['id'] or s['name'] in ignore:
                continue

            x = threading.Thread(target=getGenresInPlaylist, args=(s, accessToken, artists,))
            threads.append(x)
            x.start()


    for index, thread in enumerate(threads):
        thread.join()

    genres = []
    headers = {'Authorization': 'Bearer ' + accessToken}
    for i in artists:
        r = ''
        while True:
            url = 'https://api.spotify.com/v1/artists/' + i
            r = requests.get(url, headers=headers)
            if r.status_code != 200:
                if r.status_code == 429:
                    time.sleep(float(r.headers['Retry-After']))

            else:
                break

        for j in r.json()['genres']:
            genres.append(j)

    count = {i:genres.count(i) for i in genres}
    if None in list(count.keys()):
        del count[None]

    sortedCount = sorted(list(count.items()), key=operator.itemgetter(1), reverse=True)
    with open('./sortedGenreCount.json', 'w') as f:
        json.dump(sortedCount, f, indent=4, separators=(', ', ': '))

    return sortedCount

def topGenresInPlaylist(userString, playlistString):
    playlist = getPlaylist(userString, playlistString)
    accessToken = accessTokenBot()
    artists = []
    getGenresInPlaylist(playlist, accessToken, artists)
    genres = []
    headers = {'Authorization': 'Bearer ' + accessToken}
    for i in artists:
        r = ''
        while True:
            url = 'https://api.spotify.com/v1/artists/' + i
            r = requests.get(url, headers=headers)
            if r.status_code != 200:
                if r.status_code == 429:
                    time.sleep(float(r.headers['Retry-After']))

            else:
                break

        for j in r.json()['genres']:
            genres.append(j)

    count = {i:genres.count(i) for i in genres}
    if None in list(count.keys()):
        del count[None]

    sortedCount = sorted(list(count.items()), key=operator.itemgetter(1), reverse=True)
    with open('./sortedGenreCount.json', 'w') as f:
        json.dump(sortedCount, f, indent=4, separators=(', ', ': '))

    return sortedCount

def topSongsInPlaylists(userString):
    user = getUser(userString)
    if user is None:
        return

    playlists = getUserPlaylists(userString)
    accessToken = accessTokenBot()
    tracks = []
    name = {}
    threads = []
    for i in playlists:
        for s in i:
            if "Top Songs of " in s['name'] or user['id'] != s['owner']['id'] or s['name'] in ignore:
                continue

            x = threading.Thread(target=getSongsInPlaylist, args=(s, accessToken, tracks, name))
            threads.append(x)
            x.start()


    for index, thread in enumerate(threads):
        thread.join()

    if None in list(name.keys()):
        del name[None]

    count = {i:tracks.count(i) for i in tracks} 
    if None in list(count.keys()):
        del count[None]

    nameCount = {name[key] : value for key, value in list(count.items()) }
    sortedCount = sorted(list(nameCount.items()), key=operator.itemgetter(1), reverse=True)
    with open('./sortedCount.json', 'w') as f:
        json.dump(sortedCount, f, indent=4, separators=(', ', ': '))

    return sortedCount

def topSongsPlaylists(userString):
    playlists = getUserPlaylists(userString)
    accessToken = accessTokenBot()
    threads = []
    for i in playlists:
        for s in i:
            if "Top Songs of " not in s['name']:
                continue

            x = threading.Thread(target=getSongsPlaylist, args=(s, accessToken))
            threads.append(x)
            x.start()


    for index, thread in enumerate(threads):
        thread.join()

def topArtists(userString, term='long_term'):
    user = getUserFromString(userString)
    accessToken = accessTokenForUser(user)
    url = 'https://api.spotify.com/v1/me/top/artists?limit=50&time_range=' + term
    headers = {'Authorization': 'Bearer ' + accessToken}
    r = requests.get(url, headers=headers)
    artists = []
    for i in r.json()['items']:
        artists.append(i['name'])

    with open('./topArtists.json', 'w') as f:
        json.dump(artists, f, indent=4, separators=(', ', ': '))
    return artists

def songPopularity(userString, playlistString):
    playlist = getPlaylist(userString, playlistString)
    accessToken = accessTokenBot()
    popularity = []
    name = {}
    url = playlist['tracks']['href'] + '?fields=next,items(track(name,id,artists,popularity,album(name)))'
    headers = {'Authorization': 'Bearer ' + accessToken}
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))

            continue

        for p in r.json()['items']:
            if p is None:
                continue

            popularity.append(p['track']['popularity'])
            artists = []
            for i in p['track']['artists']:
                artists.append(i['name'])

            name['Title: ' + p['track']['name'] + '    Artists: ' + ', '.join(artists) + '     Album: ' + p['track']['album']['name']] = p['track']['popularity']
        if r.json()['next'] is None:
            break

        url = r.json()['next'] + '?fields=next,items(track(name,id,artists,album(name)))'

    sortedCount = sorted(list(name.items()), key=operator.itemgetter(1), reverse=True)
    with open('./songPopularity.json', 'w') as f:
        json.dump(sortedCount, f, indent=4, separators=(', ', ': '))

    return sortedCount

def songPopularityhref(playlisthref):
    accessToken = accessTokenBot()
    popularity = []
    name = {}
    url = playlisthref + '?fields=next,items(track(name,id,artists,popularity,album(name)))'
    headers = {'Authorization': 'Bearer ' + accessToken}
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))

            continue

        for p in r.json()['items']:
            if p is None:
                continue

            popularity.append(p['track']['popularity'])
            artists = []
            for i in p['track']['artists']:
                artists.append(i['name'])

            name['Title: ' + p['track']['name'] + '    Artists: ' + ', '.join(artists) + '     Album: ' + p['track']['album']['name']] = p['track']['popularity']
        if r.json()['next'] is None:
            break

        url = r.json()['next'] + '?fields=next,items(track(name,id,artists,album(name)))'

    sortedCount = sorted(list(name.items()), key=operator.itemgetter(1), reverse=True)
    with open('./songPopularity.json', 'w') as f:
        json.dump(sortedCount, f, indent=4, separators=(', ', ': '))

    return sortedCount

def playlistRepeats(userString, playlistString):
    playlist = getPlaylist(userString, playlistString)
    accessToken = accessTokenBot()
    name = []
    url = playlist['tracks']['href'] + '?fields=next,items(track(name,artists(name)))'
    headers = {'Authorization': 'Bearer ' + accessToken}
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))

            continue

        for p in r.json()['items']:
            if p is None:
                continue

            artists = []
            for i in p['track']['artists']:
                artists.append(i['name'])

            name.append('Title: ' + p['track']['name'] + '    Artists: ' + ', '.join(artists))
        if r.json()['next'] is None:
            break

        url = r.json()['next']

    while None in name:
        name.remove(None)

    return findRepeats(name)

def playlistRepeatshref(playlisthref):
    accessToken = accessTokenBot()
    url = playlisthref + '?fields=next,items(track(name,artists(name)))'
    name = []
    headers = {'Authorization': 'Bearer ' + accessToken}
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))

            continue

        for p in r.json()['items']:
            if p is None:
                continue

            artists = []
            for i in p['track']['artists']:
                artists.append(i['name'])

            name.append('Title: ' + p['track']['name'] + '    Artists: ' + ', '.join(artists))
        if r.json()['next'] is None:
            break

        url = r.json()['next']

    while None in name:
        name.remove(None)

    return findRepeats(name)

def findRepeats(L):
    seen = set()
    seen2 = set()
    seen_add = seen.add
    seen2_add = seen2.add
    for item in L:
        if item in seen:
            seen2_add(item)
        else:
            seen_add(item)
    return list(seen2)

def ratio(userString = 'firiusbob', playlistString = 'Random Pool of Stuff'):
    playlist = getPlaylist(userString, playlistString)
    accessToken = accessTokenBot()
    artists = []
    getArtistsInPlaylist(playlist, accessToken, artists, False)
    countplaylist = {i:artists.count(i) for i in artists} 
    if None in list(countplaylist.keys()):
        del countplaylist[None]

    user = getUser(userString)
    playlists = getUserPlaylists(userString)
    accessToken = accessTokenBot()
    artists = []
    threads = []
    for i in playlists:
        for s in i:
            if "Top Songs of " in s['name'] or user['id'] != s['owner']['id'] or s['name'] in ignore:
                continue

            x = threading.Thread(target=getArtistsInPlaylist, args=(s, accessToken, artists, False))
            threads.append(x)
            x.start()


    for index, thread in enumerate(threads):
        thread.join()

    count = {i:artists.count(i) for i in artists}
    if None in list(count.keys()):
        del count[None]

    ratio = {}
    for i in count:
        if i not in list(countplaylist.keys()):
            print('Could not find ' + i)
            continue

        allNumber = count[i]
        poolNumber = countplaylist[i]
        ratio[i] = allNumber / poolNumber

    sortedCount = sorted(list(ratio.items()), key=operator.itemgetter(1), reverse=True)
    with open('./sortedRatioCount.json', 'w') as f:
        json.dump(sortedCount, f, indent=4, separators=(', ', ': '))

    return sortedCount

def findSongInPlayliststhread(s, accessToken, playlist, songId):
    url = s['tracks']['href'] + '?fields=next,items(track(id))'
    headers = {'Authorization': 'Bearer ' + accessToken}
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))

            continue

        for p in r.json()['items']:
            if p is None:
                continue

            if songId == p['track']['id']:
                playlist.append(s['name'])

        if r.json()['next'] is None:
            break

        url = r.json()['next'] + '?fields=next,items(track(id))'

def findSongInPlaylists(userString, songId):
    user = getUser(userString)
    if user is None:
        return

    playlists = getUserPlaylists(userString)
    accessToken = accessTokenBot()
    playlist = []
    threads = []
    for i in playlists:
        for s in i:
            if "Top Songs of " in s['name'] or user['id'] != s['owner']['id']:
                continue

            x = threading.Thread(target=findSongInPlayliststhread, args=(s, accessToken, playlist, songId))
            threads.append(x)
            x.start()


    for index, thread in enumerate(threads):
        thread.join()

    with open('./songInPlaylists.json', 'w') as f:
        json.dump(playlist, f, indent=4, separators=(', ', ': '))

    return playlist

def findArtistInPlayliststhread(s, accessToken, playlist, artistId):
    url = s['tracks']['href'] + '?fields=next,items(track(artists))'
    headers = {'Authorization': 'Bearer ' + accessToken}
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))

            continue

        for p in r.json()['items']:
            if p is None:
                continue

            for j in p['track']['artists']:
                if artistId == j['id']:
                    playlist.append(s['name'])
                    break

        if r.json()['next'] is None:
            break

        url = r.json()['next'] + '?fields=next,items(track(artists))'

def findArtistInPlaylists(userString, artistId):
    user = getUser(userString)
    if user is None:
        return

    playlists = getUserPlaylists(userString)
    accessToken = accessTokenBot()
    playlist = []
    threads = []
    for i in playlists:
        for s in i:
            if "Top Songs of " in s['name'] or user['id'] != s['owner']['id']:
                continue

            x = threading.Thread(target=findArtistInPlayliststhread, args=(s, accessToken, playlist, artistId))
            threads.append(x)
            x.start()


    for index, thread in enumerate(threads):
        thread.join()

    playlist = list(set(playlist))

    with open('./artistInPlaylists.json', 'w') as f:
        json.dump(playlist, f, indent=4, separators=(', ', ': '))

    return playlist

def search(string, kind):
    string = string.replace(' ', '%20')
    url = 'https://api.spotify.com/v1/search?q=' + string + '&type=' + kind
    headers = {'Authorization': 'Bearer ' + accessTokenBot()}
    r = requests.get(url, headers=headers)
    results = [] 
    for i in r.json()[kind + 's']['items']:
        results.append((i['name'], i['id']))

    return results
