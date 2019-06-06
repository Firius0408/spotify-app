from update import *
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import random
import string
from urlparse import urlparse, parse_qs

redirect_uri = 'http://localhost:8081/callback'

def generateRandomString(length):
   possible = string.ascii_letters + string.digits 
   return ''.join(random.choice(possible) for i in range(length))

def getUserFromString(userString):
    userids = list()
    for i in userFile['users']:
        userids.append(i['id'])

    userid = process.extractOne(userString, userids, score_cutoff=80)
    if userid is None:
        print('Unable to determine user you want')
        return

    for i in userFile['users']:
        if (i['id'] == userid[0]):
            return i

def createPlaylist(userid, accessToken, payload):
    url = 'https://api.spotify.com/v1/users/' + userid + '/playlists/'
    headers =  { 
            'Authorization': 'Bearer ' + accessToken,
            'Content-Type': 'application/json'
            }
    r = requests.post(url, headers=headers, data=payload)
    return r.json()['href']

def playlistIndividual(userid, accessToken, time, term):
    payload = json.dumps({ 'name': "Top Songs of " + time + " as of " + date.strftime("%m") + "/" + date.strftime("%d") + "/" + date.strftime("%Y") })
    playlisthref = createPlaylist(userid, accessToken, payload)
    updatePlaylist(accessToken, accessToken, term, playlisthref)

def newUser():
    state = generateRandomString(16)
    scope = 'playlist-modify-public playlist-modify-private user-top-read'
    url = 'https://accounts.spotify.com/authorize?client_id=' + client_id + '&response_type=code&redirect_uri=' + redirect_uri + '&scope=' + scope + '&state=' + state
    print 'Go to the following url and paste your url after you login'
    redirect = raw_input(url + " ")
    queries = parse_qs(urlparse(redirect).query)
    if ('state' not in queries or queries['state'][0] != state):
        print 'Error: state mismatch. Aborting...'
        return

    code = queries['code'][0]
    url = 'https://accounts.spotify.com/api/token'
    headers = { 'Authorization': 'Basic ' + base64.b64encode(client_id + ':' + client_secret) }
    payload = {
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
            }
    r = requests.post(url, headers=headers, data=payload)
    if (r.status_code == 200):
        accessToken = r.json()['access_token']
        refreshToken = r.json()['refresh_token']

    url = 'https://api.spotify.com/v1/me'
    headers = { 'Authorization': 'Bearer ' + accessToken }
    r = requests.get(url, headers=headers)
    userid = r.json()['id']
    print userid
    print refreshToken
    print r.json()['display_name']
    BotToken = accessTokenBot()
    for i in userFile['users']:
        if (userid == i['id'] and i['refresh_token'] is not None):
            print 'user already exists'
            updateIndividual(i, BotToken)
            return

    playlisthreflong = createPlaylist(useridme, BotToken, json.dumps({ 'name': "Top Songs of All-Time for " + userid, 'public': 'true' }))
    playlisthrefmid = createPlaylist(useridme, BotToken, json.dumps({ 'name': "Top Songs of 6 Months for " + userid, 'public': 'true' }))
    playlisthrefshort = createPlaylist(useridme, BotToken, json.dumps({ 'name': "Top Songs of 4 Weeks for " + userid, 'public': 'true' }))
    user = {'id': userid,
        'refresh_token': refreshToken,
        'playlisthreflong': playlisthreflong,
        'playlisthrefmid': playlisthrefmid,
        'playlisthrefshort': playlisthrefshort}
    x = threading.Thread(target=updateIndividual, args=(user, BotToken,))
    x.start()
    users = userFile['users']
    users.append(user)
    userFile['users'] = users
    if __name__ == '__main__':
        with open(sys.path[0] + '/users.json', 'w') as f:
            json.dump(userFile, f, indent=4, separators=(',', ': '))
    else:
        with open('./users.json', 'w') as f:
            json.dump(userFile, f, indent=4, separators=(',', ': '))

    x.join()

def playlist(userString):
    user = getUserFromString(userString)
    accessToken = accessTokenForUser(user)
    userid = user['id']
    print('creating playlists for user ' + userid)
    x = threading.Thread(target=playlistIndividual, args=(userid, accessToken, "All-Time", 'long_term',))
    y = threading.Thread(target=playlistIndividual, args=(userid, accessToken, "the Past 6 Months", 'medium_term',))
    z = threading.Thread(target=playlistIndividual, args=(userid, accessToken, "the Past 4 Weeks", 'short_term',))
    x.start()
    print('creating long playlist for user ' + userid)
    y.start()
    print('creating mid playlist for user ' + userid)
    z.start()
    print('creating short playlist for user ' + userid)
    x.join()
    print('finished creating long playlist for user ' + userid)
    y.join()
    print('finished creating mid playlist for user ' + userid)
    z.join()
    print('finished creating short playlist for user ' + userid)

if __name__ == '__main__':
    if (len(sys.argv) > 1):
        if (sys.argv[1] == 'list'):
            for i in userFile['users']:
                print i['id']
        elif (sys.argv[1] == 'newUser'):
            newUser()
        else:
            playlist(sys.argv[1])
    else:
        update()
