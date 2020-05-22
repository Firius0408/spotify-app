from sneak import *

def queue(uri):
    headers = {'Authorization': 'Bearer ' + accessTokenForUser(getUserFromString('firiusbob'))}
    url = 'https://api.spotify.com/v1/me/player/queue?uri=' + uri
    r = requests.post(url, headers=headers)
    return r.status_code

def queuePlaylists(*playlist):
    print('Pulling songs...')
    accessToken = accessTokenForUser(getUserFromString('firiusbob'))
    tracks = []
    name = {}
    for i in playlist:
        getSongsInPlaylist(i, accessToken, tracks, name)

    print('Shuffling songs...')
    tracks = list(set(tracks))
    random.shuffle(tracks)
    uris = ['spotify:track:' + i for i in tracks]
    print('Queuing songs...')
    for i in uris:
        x = queue(i)
        if x != 204:
            print('Error: ' + str(x))
            return
