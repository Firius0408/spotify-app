from spotify import *
import operator
import time

def getUserPlaylists(userString):
    user = getUserFromString(userString)
    if user is None:
        return

    accessToken = accessTokenForUser(user)
    playlists = list()
    url = 'https://api.spotify.com/v1/me/playlists?limit=50'
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
        
#    if __name__ == '__main__':
#        with open(sys.path[0] + '/playlists.json', 'w') as f:
#            json.dump(playlists, f, indent=4, separators=(',', ': '))
#    else:
#        with open('./playlists.json', 'w') as f:
#            json.dump(playlists, f, indent=4, separators=(',', ': '))

    return playlists

def getArtistsInPlaylist(s, accessToken, artists):
    url = s['tracks']['href'] + '?fields=next,items(track(artists))'
    headers = {'Authorization': 'Bearer ' + accessToken}
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))

            continue

        for p in r.json()['items']:
            for i in p['track']['artists']:
                artists.append(i['name'])

        if r.json()['next'] is None:
            break

        url = r.json()['next']

def getSongsInPlaylist(s, accessToken, tracks, name):
    url = s['tracks']['href'] + '?fields=next,items(track(name,id))'
    headers = {'Authorization': 'Bearer ' + accessToken}
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))

            continue

        for p in r.json()['items']:
             tracks.append(p['track']['id'])
             name[p['track']['id']] = p['track']['name']

        if r.json()['next'] is None:
            break

        url = r.json()['next']

def topArtistsInPlaylists(userString):
    user = getUserFromString(userString)
    if user is None:
        return

    playlists = getUserPlaylists(userString)
    accessToken = accessTokenForUser(user)
    artists = list()
    threads = list()
    for i in playlists:
        for s in i:
            if "Top Songs of " in s['name'] or user['id'] != s['owner']['id']:
                continue

            x = threading.Thread(target=getArtistsInPlaylist, args=(s, accessToken, artists))
            threads.append(x)
            x.start()


    for index, thread in enumerate(threads):
        thread.join()
    
    count = {i:artists.count(i) for i in artists}
    if None in count.keys():
        del count[None]

    sortedCount = sorted(count.items(), key=operator.itemgetter(1), reverse=True)
    with open('./sortedArtistsCount.json', 'w') as f:
        json.dump(sortedCount, f, indent=4, separators=(', ', ': '))

    return sortedCount

def topSongsInPlaylists(userString):
    user = getUserFromString(userString)
    if user is None:
        return

    playlists = getUserPlaylists(userString)
    accessToken = accessTokenForUser(user)
    tracks = list()
    name = {}
    threads = list()
    for i in playlists:
        for s in i:
            if "Top Songs of " in s['name'] or user['id'] != s['owner']['id']:
                continue

            x = threading.Thread(target=getSongsInPlaylist, args=(s, accessToken, tracks, name))
            threads.append(x)
            x.start()


    for index, thread in enumerate(threads):
        thread.join()
    
    if None in name.keys():
        del name[None]

    count = {i:tracks.count(i) for i in tracks} 
    if None in count.keys():
        del count[None]
        
    nameCount = {name[key] : value for key, value in count.items() }
    sortedCount = sorted(nameCount.items(), key=operator.itemgetter(1), reverse=True)
    with open('./sortedCount.json', 'w') as f:
        json.dump(sortedCount, f, indent=4, separators=(', ', ': '))

    return sortedCount

def both(userString):
    t = topSongsInPlaylists(userString)
    b = topArtistsInPlaylists(userString)
