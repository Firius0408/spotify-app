from spotify import *
import operator

def getUserPlaylists(userString):
    user = getUserFromString(userString)
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
    playlists = getUserPlaylists(userString)
    accessToken = accessTokenForUser(user)
    tracks = list()
    headers = {'Authorization': 'Bearer ' + accessToken}
    for i in playlists:
        for s in i:
            if "Top Songs of " in s['tracks'] or user['id'] != s['owner']['id']:
                print s['owner']['id']
                continue

            url = s['tracks']['href'] + '?fields=next,items(track(tracks,id))'
            while True:
                r = requests.get(url, headers=headers) 
                for p in r.json()['items']:
                     tracks.append(p['track']['id'])

                if r.json()['next'] is None:
                    break

                url = r.json()['next']


    count = {i:tracks.count(i) for i in tracks} 
    sortedCount = sorted(count.items(), key=operator.itemgetter(1), reverse=True)
    with open('./sortedCount.json', 'w') as f:
        json.dump(sortedCount, f, indent=4, separators=(', ', ': '))

    return sortedCount

