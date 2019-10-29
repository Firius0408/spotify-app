from update import *
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import random
import string
from urllib.parse import urlparse, parse_qs

redirect_uri = 'http://localhost:8081/callback' # not used, needed to satisfy spotify auth

#generates a random string. Used for state in auth
def generateRandomString(length):
   possible = string.ascii_letters + string.digits 
   return ''.join(random.choice(possible) for i in range(length))

#searches users.json and returns user object from string arg
def getUserFromString(userString):
    userids = []
    for i in userFile['users']:
        userids.append(i['id'])

    userid = process.extractOne(userString, userids, score_cutoff=80)
    if userid is None:
        return

    for i in userFile['users']:
        if (i['id'] == userid[0]):
            return i

#creates playlist. Pass in userid and accessToken for user. Payload contains playlist's name. Returns playlist's href
def createPlaylist(userid, accessToken, payload):
    url = 'https://api.spotify.com/v1/users/' + userid + '/playlists/'
    headers =  { 
            'Authorization': 'Bearer ' + accessToken,
            'Content-Type': 'application/json'
            }
    r = requests.post(url, headers=headers, data=payload)
    return r.json()['href']

# creates snapshot playlist of user with given userid, accessToken, time and term (time and term should match)
def playlistIndividual(userid, accessToken, time, term):
    payload = json.dumps({ 'name': "Top Songs of " + time + " as of " + date.strftime("%m/%d/%Y")})
    playlisthref = createPlaylist(userid, accessToken, payload)
    updatePlaylist(accessToken, accessToken, term, playlisthref)

# auth new user, add to users.json, create continuously updated playlists
# re auth old user
def authUser():
    state = generateRandomString(16)
    scope = 'playlist-modify-public playlist-modify-private user-top-read'
    url = 'https://accounts.spotify.com/authorize?client_id=' + client_id + '&response_type=code&redirect_uri=' + redirect_uri + '&scope=' + scope + '&state=' + state
    print('Go to the following url and paste your url after you login')
    redirect = eval(input(url + " ")) # janky way of authorizing user. Go to url and parse the returned url for code
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
    if (r.status_code == 200):
        accessToken = r.json()['access_token']
        refreshToken = r.json()['refresh_token']

    url = 'https://api.spotify.com/v1/me'
    headers = { 'Authorization': 'Bearer ' + accessToken }
    r = requests.get(url, headers=headers)
    userid = r.json()['id']
    print(userid)
    print(refreshToken)
    print(r.json()['display_name'])
    users = userFile['users']
    flag = False
    for i in users:
        if (userid == i['id']):
            print('user found')
            i['refresh_token'] = refreshToken
            flag = True
            break

    if not flag:
        print('new user found')
        botToken = accessTokenBot()
        playlisthreflong = createPlaylist(useridme, botToken, json.dumps({ 'name': "Top Songs of All-Time for " + userid, 'public': 'true' }))
        playlisthrefmid = createPlaylist(useridme, botToken, json.dumps({ 'name': "Top Songs of 6 Months for " + userid, 'public': 'true' }))
        playlisthrefshort = createPlaylist(useridme, botToken, json.dumps({ 'name': "Top Songs of 4 Weeks for " + userid, 'public': 'true' }))
        user = {'id': userid,
            'refresh_token': refreshToken,
            'playlisthreflong': playlisthreflong,
            'playlisthrefmid': playlisthrefmid,
            'playlisthrefshort': playlisthrefshort}
        updateIndividual(user, botToken)
        users.append(user)

    userFile['users'] = users
    if __name__ == '__main__':
        with open(sys.path[0] + '/users.json', 'w') as f:
            json.dump(userFile, f, indent=4, separators=(',', ': '))
    else:
        with open('./users.json', 'w') as f:
            json.dump(userFile, f, indent=4, separators=(',', ': '))

# creates the three snapshot playlists for the user string
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
                print(i['id'])
        elif (sys.argv[1] == 'newUser'):
            newUser()
        else:
            playlist(sys.argv[1])
    else:
        update()
