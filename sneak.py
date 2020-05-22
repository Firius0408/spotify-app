from spotify import *
import operator
import time
import re
import emoji

ignore = ['Post Malone', 'AJR', 'Ed Sheeran', 'Eminem', 'Logic', 'Queen', 'Bleachers', 'L?', 'IYLHLHG', 'Musical', 'Disney', 'Indie', 'Classical', 'Monstercat', 'Rap', 'House', 'The Beatles', 'Ashley', 'Jonathan', 'Daniel', 'Phillip', 'Shan']
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
    userString = userString.replace('spotify:user:', '')
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

    namesdemoji = [emoji.demojize(i) for i in playlistnames]
    playlistString = emoji.demojize(playlistString)
    playlist = process.extractOne(playlistString, namesdemoji, score_cutoff=80)
    playlistName = emoji.emojize(playlist[0])
    if playlist is None:
        print ('Unable to determine playlist')
        return

    for i in playlists:
        for s in i:
            if s['name'] == playlistName:
                return s

def getArtistsInPlaylist(s, accessToken, artists, grouped, count):
    url = s['tracks']['href'] + '?fields=next,items(track(artists))'
    headers = {'Authorization': 'Bearer ' + accessToken}
    temp = []
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
                trackartists = [i['name'] for i in p['track']['artists']]
                if count or trackartists not in temp:
                    temp.append(', '.join(trackartists))
            else:
                for i in p['track']['artists']:
                    name = i['name']
                    if count or name not in temp:
                        temp.append(name)

        if r.json()['next'] is None:
            artists.extend(temp)
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

def topArtistsInPlaylists(userString, count=False, grouped=False):
    user = getUser(userString)
    playlists = getUserPlaylists(userString)
    accessToken = accessTokenBot()
    artists = []
    threads = []
    for i in playlists:
        for s in i:
            if count and s['name'] in ignore:
                continue

            if "Top Songs of " in s['name'] or user['id'] != s['owner']['id']:
                continue

            x = threading.Thread(target=getArtistsInPlaylist, args=(s, accessToken, artists, grouped, count))
            threads.append(x)
            x.start()


    for index, thread in enumerate(threads):
        thread.join()

    counted = {i:artists.count(i) for i in artists}
    if None in list(counted.keys()):
        del counted[None]

    sortedCount = sorted(list(counted.items()), key=operator.itemgetter(1), reverse=True)
    t = './sortedArtists'
    if count:
        t += 'Count.json'
    else:
        t += '.json'
        
    with open(t, 'w') as f:
        json.dump(sortedCount, f, indent=4, separators=(', ', ': '))

    return sortedCount

def topArtistsInPlaylist(userString, playlistString, grouped=False):
    playlist = getPlaylist(userString, playlistString)
    accessToken = accessTokenBot()
    artists = []
    getArtistsInPlaylist(playlist, accessToken, artists, grouped, True)
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
    for i in range(0, len(artists), 50):
        r = ''
        while True:
            url = 'https://api.spotify.com/v1/artists/?ids=' + ','.join(artists[i:i + 50])
            r = requests.get(url, headers=headers)
            if r.status_code != 200:
                if r.status_code == 429:
                    time.sleep(float(r.headers['Retry-After']))

            else:
                break

        for j in r.json()['artists']:
            for k in j['genres']:
                genres.append(k)

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
    for i in range(0, len(artists), 50):
        r = ''
        while True:
            url = 'https://api.spotify.com/v1/artists/?ids=' + ','.join(artists[i:i + 50])
            r = requests.get(url, headers=headers)
            if r.status_code != 200:
                if r.status_code == 429:
                    time.sleep(float(r.headers['Retry-After']))

            else:
                break

        for j in r.json()['artists']:
            for k in j['genres']:
                genres.append(k)

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
            if p is None or p['track'] is None:
                continue

            if songId == p['track']['id']:
                playlist.append(s['name'])
                return

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
            if p is None or p['track'] is None:
                continue

            for j in p['track']['artists']:
                if artistId == j['id']:
                    playlist.append(s['name'])
                    return

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

    with open('./artistInPlaylists.json', 'w') as f:
        json.dump(playlist, f, indent=4, separators=(', ', ': '))

    return playlist

def search(string, kind):
    string = string.replace(' ', '%20')
    url = 'https://api.spotify.com/v1/search?q=' + string + '&type=' + kind
    headers = {'Authorization': 'Bearer ' + accessTokenBot()}
    r = requests.get(url, headers=headers)
    return [(i['name'], i['id']) for i in r.json()[kind + 's']['items']] 

def searchRPOS(song):
    song = song.lower()
    song = song.translate({ord(i): None for i in '-&()'})
    song = song.split('feat.', 1)[0]
    user = getUserFromString('firiusbob')
    accessToken = accessTokenForUser(user)
    headers = {'Authorization': 'Bearer ' + accessToken}
    url = 'https://api.spotify.com/v1/playlists/5WYRn0FxSUhVsOQpQQ0xBV/tracks?fields=next,items(track(artists(name),id,name))'
    results = []
    print('Searching RPOS...')
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))
    
            continue
    
        for p in r.json()['items']:
            if p is None or p['track'] is None:
                continue

            test = p['track']['name'].lower()
            test = test.translate({ord(i): None for i in '-&()'})
            test = test.split('feat.', 1)[0]
            if fuzz.partial_ratio(song, test) > 98 and fuzz.ratio(song, test) > 45:
                diff = len(test) - len(song)
                if diff < 100 and diff >= 0:
                    artists = [j['name'] for j in p['track']['artists']]
                    results.append((p['track']['name'], artists, p['track']['id']))
    
        if r.json()['next'] is None:
            break
    
        url = r.json()['next'] + '?fields=next,items(track(id,artists(name),name))'
    
    return results

def searchPlayliststhread(s, accessToken, songhrefs, song):
    url = s['tracks']['href'] + '?fields=next,items(track(name,href))'
    headers = {'Authorization': 'Bearer ' + accessToken}
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))

            continue

        for p in r.json()['items']:
            if p is None or p['track'] is None or p['track']['href'] in songhrefs:
                continue

            test = p['track']['name'].lower()
            test = test.translate({ord(i): None for i in '-&()'})
            test = test.split('feat.', 1)[0]
            if fuzz.partial_ratio(song, test) > 98 and fuzz.ratio(song, test) > 45:
                diff = len(test) - len(song)
                if diff < 100 and diff >= 0:
                    songhrefs.append(p['track']['href'])

        if r.json()['next'] is None:
            break

        url = r.json()['next'] + '?fields=next,items(track(name,href))'

def searchPlaylists(userString, song):
    song = song.lower()
    song = song.translate({ord(i): None for i in '-&()'})
    song = song.split('feat.', 1)[0]
    user = getUser(userString)
    if user is None:
        return

    playlists = getUserPlaylists(userString)
    accessToken = accessTokenBot()
    songhrefs = []
    threads = []
    for i in playlists:
        for s in i:
            if "Top Songs of " in s['name'] or user['id'] != s['owner']['id']:
                continue

            x = threading.Thread(target=searchPlayliststhread, args=(s, accessToken, songhrefs, song))
            threads.append(x)
            x.start()


    for index, thread in enumerate(threads):
        thread.join()

    headers = {'Authorization': 'Bearer ' + accessToken}
    songs = []
    for i in songhrefs:
        r = requests.get(i, headers=headers)
        artists = [i['name'] for i in r.json()['artists']]
        songs.append((r.json()['name'], artists, r.json()['id']))

    return songs

def convertThread(newuris, rpos, name, artists, uri):
    for i in rpos:
        if name != i[1]:
            continue

        flag = True
        for p in artists:
            if p not in i[2]:
                flag = False
                break

        if flag:
            newuris.append(i[0])
            return

    print(name)
    newuris.append(uri)

def convert(playlistString):
    playlist = getPlaylist('firiusbob', playlistString)
    user = getUserFromString('firiusbob')
    accessToken = accessTokenForUser(user)
    headers = {'Authorization': 'Bearer ' + accessToken}
    url = 'https://api.spotify.com/v1/playlists/5WYRn0FxSUhVsOQpQQ0xBV/tracks?fields=next,items(track(artists(name),uri,name))'
    rpos = []
    print('Pulling from RPOS')
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))
    
            continue
    
        for p in r.json()['items']:
            if p is None or p['track'] is None:
                continue
    
            artists = []
            for i in p['track']['artists']:
                artists.append(i['name'])
    
            rpos.append([p['track']['uri'], p['track']['name'], artists])
    
        if r.json()['next'] is None:
            break
    
        url = r.json()['next'] + '?fields=next,items(track(uri,artists(name),name))'
    
    print('Finished pulling from RPOS. Searching...')
    url = playlist['tracks']['href'] + '?fields=next,items(track(artists(name),name,uri))'
    newuris = []
    threads = []
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))
    
            continue
    
        for p in r.json()['items']:
            if p is None or p['track'] is None:
                continue
    
            name = p['track']['name']
            artists = []
            uri = p['track']['uri']
            for i in p['track']['artists']:
                artists.append(i['name'])
    
            x = threading.Thread(target=convertThread, args=(newuris, rpos, name, artists, uri))
            threads.append(x)
            x.start()
    
        if r.json()['next'] is None:
            break
    
        url = r.json()['next'] + '?fields=next,items(track(artists(name),name))'
    
    for index, thread in enumerate(threads):
        thread.join()
    
    print('Finished search. Creating playlist')
    payload = json.dumps({'name': 'Convert of ' + playlist['name']})
    url = createPlaylist(user['id'], accessToken, payload) + '/tracks'
    print('Finished. Adding to playlist')
    headers = {'Authorization': 'Bearer ' + accessToken, 'Content-Type': 'application/json'}
    for i in range(0, len(newuris), 100):
        r = requests.post(url, headers=headers, data=json.dumps({'uris': newuris[i:i + 100]}))

def notinRPOS(playlistString):
    playlist = getPlaylist('firiusbob', playlistString)
    user = getUserFromString('firiusbob')
    accessToken = accessTokenForUser(user)
    headers = {'Authorization': 'Bearer ' + accessToken}
    url = 'https://api.spotify.com/v1/playlists/5WYRn0FxSUhVsOQpQQ0xBV/tracks?fields=next,items(track(id))'
    rpos = []
    print('Pulling from RPOS')
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))
    
            continue
    
        for p in r.json()['items']:
            if p is None or p['track'] is None or p['track']['id'] is None:
                continue
    
            rpos.append(p['track']['id'])
    
        if r.json()['next'] is None:
            break
    
        url = r.json()['next'] + '?fields=next,items(track(id))'
    
    print('Finished pulling from RPOS. Comparing...')
    url  = playlist['tracks']['href'] + '?fields=next,items(track(artists(name),name,id))'
    results = []
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))
    
            continue
    
        for p in r.json()['items']:
            if p is None or p['track'] is None:
                continue

            if p['track']['id'] not in rpos:
                artists = [i['name'] for i in p['track']['artists']]
                results.append((p['track']['name'], artists, p['track']['id']))
    
    
        if r.json()['next'] is None:
            break
    
        url = r.json()['next'] + '?fields=next,items(track(artists(name),name))'

    return results

def playlistFollowersThread(nameids, followers, accessToken):
    url = 'https://api.spotify.com/v1/playlists/' + nameids[1] + '?fields=followers(total)'
    headers = {'Authorization': 'Bearer ' + accessToken}
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code == 200:
            followers.append((nameids[0], r.json()['followers']['total']))
            return

        elif r.status_code == 429:
            time.sleep(float(r.headers['Retry-After']))

def playlistFollowers(userString):
    playlists = getUserPlaylists(userString)
    user = getUser(userString)
    nameids = []
    for i in playlists:
        for s in i:
            nameids.append((s['name'], s['id'], s['owner']['id']))

    accessToken = accessTokenBot()
    followers = []
    threads = []
    for i in nameids:
        if i[0] in ignore or "Top Songs of " in i[0] or user['id'] != i[2]:
            continue

        x = threading.Thread(target=playlistFollowersThread, args=(i, followers, accessToken))
        threads.append(x)
        x.start()

    for index, thread in enumerate(threads):
        thread.join()

    sortedCount = sorted(followers, key=operator.itemgetter(1), reverse=True)
    with open('sortedPlaylistFollowers.json', 'w') as f:
        json.dump(sortedCount, f, indent=4, separators=(', ', ': '))

    return sortedCount
