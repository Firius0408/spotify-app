from spotifywebapi import StatusCodeError, User
from fuzzywuzzy import process
import random
import string
import json
import threading
import sys
import requests
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor
from update import getAuthUser, updatePlaylist, userFile, sp, date, updateIndividual, botuser

# not used, needed to satisfy spotify auth
redirect_uri = 'http://localhost:8081/callback'

#generates a random string. Used for state in auth


def generateRandomString(length: int) -> str:
    possible = string.ascii_letters + string.digits
    return ''.join(random.choice(possible) for i in range(length))

#searches users.json and returns user object from string arg

userids = []
for i in userFile['users']:
    userids.append(i['id'])

def getUserFromString(userString: str) -> dict[str]:
    userid = process.extractOne(userString, userids, score_cutoff=80)
    if userid is None:
        raise LookupError('Could not find user')

    for j in userFile['users']:
        if (j['id'] == userid[0]):
            return j

# creates snapshot playlist of user with given userid, accessToken, time and term (time and term should match)


def playlistIndividual(userobj: User, time: str, term: str) -> None:
    playlistobj = userobj.createPlaylist(
        "Top Songs of " + time + " as of " + date.strftime("%m/%d/%Y"))
    playlistid = playlistobj['id']
    updatePlaylist(userobj, userobj, term, playlistid, userobj.getUser()['display_name'])

# auth new user, add to users.json, create continuously updated playlists
# re auth old user


def authUser() -> None:
    client_id = sp.client_id
    client_secret = sp.client_secret
    state = generateRandomString(16)
    scope = 'playlist-modify-public playlist-modify-private user-top-read'
    url = 'https://accounts.spotify.com/authorize?client_id=' + client_id + \
        '&response_type=code&redirect_uri=' + redirect_uri + \
        '&scope=' + scope + '&state=' + state
    print('Go to the following url and paste your url after you login')
    # janky way of authorizing user. Go to url and parse the returned url for code
    redirect = input(url + " ")
    queries = parse_qs(urlparse(redirect).query)
    if ('state' not in queries or queries['state'][0] != state):
        print('Error: state mismatch. Aborting...')
        return

    code = queries['code'][0]
    url = 'https://accounts.spotify.com/api/token'
    payload = {
        'code': code,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'client_secret': client_secret
    }
    r = requests.post(url, data=payload)
    if r.status_code != 200:
        print('Error! API returned a bad status code')
        return

    refreshToken = r.json()['refresh_token']
    user = sp.getAuthUser(refreshToken)
    userid = user.getUser()['id']
    name = user.getUser()['display_name']
    users = userFile['users']
    if userid not in [i['id'] for i in users]:
        print('new user found')
        try:
            playlistlong = botuser.createPlaylist(
                "Top Songs of All-Time for " + name, public=True)
            playlistmid = botuser.createPlaylist(
                "Top Songs of 6 Months for " + name, public=True)
            playlistshort = botuser.createPlaylist(
                "Top Songs of 4 Weeks for " + name, public=True)
        except StatusCodeError as err:
            print(err)
            return

        user = {'id': userid,
                'refresh_token': refreshToken,
                'playlistidlong': playlistlong['id'],
                'playlistidmid': playlistmid['id'],
                'playlistidshort': playlistshort['id']}
        bottomexecutor = ThreadPoolExecutor()
        updateIndividual(user, bottomexecutor)
        bottomexecutor.shutdown()
        users.append(user)
    else:
        print('user found')
        for j in users:
            if j['id'] == userid:
                j['refresh_token'] = refreshToken
                break

    userFile['users'] = users
    if __name__ == '__main__':
        with open(sys.path[0] + '/users.json', 'w') as f:
            json.dump(userFile, f, indent=4, separators=(',', ': '))
    else:
        with open('./users.json', 'w') as f:
            json.dump(userFile, f, indent=4, separators=(',', ': '))

# creates the three snapshot playlists for the user string


def playlist(userString: str) -> None:
    user = getUserFromString(userString)
    userobj = getAuthUser(user)
    username = userobj.getUser()['display_name']
    print('creating playlists for user ' + username)
    x = threading.Thread(target=playlistIndividual,
                         args=(userobj, "All-Time", 'long_term',))
    y = threading.Thread(target=playlistIndividual, args=(
        userobj, "the Past 6 Months", 'medium_term',))
    z = threading.Thread(target=playlistIndividual, args=(
        userobj, "the Past 4 Weeks", 'short_term',))
    x.start()
    print('creating long playlist for user ' + username)
    y.start()
    print('creating mid playlist for user ' + username)
    z.start()
    print('creating short playlist for user ' + username)
    x.join()
    print('finished creating long playlist for user ' + username)
    y.join()
    print('finished creating mid playlist for user ' + username)
    z.join()
    print('finished creating short playlist for user ' + username)


if __name__ == '__main__':
    if (len(sys.argv) > 1):
        if (sys.argv[1] == 'list'):
            for i in userFile['users']:
                print(i['id'])

        elif (sys.argv[1] == 'authUser'):
            authUser()
        else:
            playlist(sys.argv[1])
