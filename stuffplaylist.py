from spotify import *

def playlistStuff():
    user = getUserFromString('firiusbob')
    accessToken = accessTokenForUser(user)
    name = list()
    url = 'https://api.spotify.com/v1/playlists/5WYRn0FxSUhVsOQpQQ0xBV/tracks?fields=next,items(track(name,artists(name)))'
    headers = {'Authorization': 'Bearer ' + accessToken}
    while True:
        r = requests.get(url, headers=headers) 
        if r.status_code != 200:
            if r.status_code == 429:
                time.sleep(float(r.headers['Retry-After']))

            continue

        for p in r.json()['items']:
             artists = list()
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
