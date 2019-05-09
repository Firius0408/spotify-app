from spotify import *
import operator

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

def topSongsInPlaylists(userString):
    user = getUserFromString(userString)
    if user is None:
        return

    playlists = getUserPlaylists(userString)
    accessToken = accessTokenForUser(user)
    tracks = list()
    name = {}
    headers = {'Authorization': 'Bearer ' + accessToken}
    for i in playlists:
        for s in i:
            if "Top Songs of " in s['name'] or user['id'] != s['owner']['id']:
                print s['owner']['id']
                continue

            url = s['tracks']['href'] + '?fields=next,items(track(name,id))'
            while True:
                r = requests.get(url, headers=headers) 
                for p in r.json()['items']:
                     tracks.append(p['track']['id'])
                     name[p['track']['id']] = p['track']['name']

                if r.json()['next'] is None:
                    break

                url = r.json()['next']


    with open('./tracks.json', 'w') as f:
        json.dump(tracks, f, indent=4, separators=(', ', ': '))

    if None in name.keys():
        del name[None]

    with open('./name.json', 'w') as f:
        json.dump(name, f, indent=4, separators=(', ', ': '))

    count = {i:tracks.count(i) for i in tracks} 
    if None in count.keys():
        del count[None]
        
    with open('./count.json', 'w') as f:
        json.dump(count, f, indent=4, separators=(', ', ': '))

    #nameCount = {name[key] : value for key, value in count.items() }
    nameCount = {}
    for key, value in count.items():
        #if name[key] in nameCount:
            nameCount[name[key]] += value
        #else:
        #    nameCount[name[key]] = value

    with open('./nameCount.json', 'w') as f:
        json.dump(nameCount, f, indent=4, separators=(', ', ': '))

    sortedCount = sorted(nameCount.items(), key=operator.itemgetter(1), reverse=True)
    with open('./sortedCount.json', 'w') as f:
        json.dump(sortedCount, f, indent=4, separators=(', ', ': '))

    return sortedCount

