from sneak import *

def playlistStuff():
    user = getUserFromString('firiusbob')
    accessToken = accessTokenForUser(user)
    tracks = list()
    name = {}
    url = 'https://api.spotify.com/v1/playlists/5WYRn0FxSUhVsOQpQQ0xBV/tracks?fields=next,items(track(name,id))'
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

    count = {i:tracks.count(i) for i in tracks}
    sortedCount = sorted(count.items(), key=operator.itemgetter(1), reverse=True)
    with open('./sortedCount.json', 'w') as f:
        json.dump(sortedCount, f, indent=4, separators=(', ', ': '))
