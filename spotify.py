import requests
import json
import datetime
import base64
import threading
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import sys
import random
import string
from urlparse import urlparse, parse_qs

client_id = 'bda7b557a026402d92584e140e291f57'
client_secret = '160f08d795334c85a7227b695b1d54f3'
refreshtokenme = 'AQBzPXpkLqDOctHGd092exRtHaw0WIg7wtgNB9BFKlJtMJboyq_EFHruvhUbLKp38AByxmss_kN1ViTwaroT0T_QbpOuEV9tn4O8AvXxsawTHnrap8pnwG98u3qYw1j8rS8'
useridme = 'ohjber0jdol59842ilmd8w0a2'
redirect_uri = 'http://localhost:8081/callback'

def generateRandomString(length):
   possible = string.ascii_letters + string.digits 
   return ''.join(random.choice(possible) for i in range(length))

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
    users = userFile['users']
    users.append({'id': userid,
        'refresh_token': refreshToken,
        'playlisthreflong': playlisthreflong,
        'playlisthrefmid': playlisthrefmid,
        'playlisthrefshort': playlisthrefshort})
    userFile['users'] = users
    if __name__ == '__main__':
        with open(sys.path[0] + '/users.json') as f:
            json.dump(userFile, f, indent=4, separators=(',', ': '))
    else:
        with open('./users.json', 'w') as f:
            json.dump(userFile, f, indent=4, separators=(',', ': '))

    update()

def createPlaylist(userid, accessToken, payload):
    url = 'https://api.spotify.com/v1/users/' + userid + '/playlists/'
    headers =  { 
            'Authorization': 'Bearer ' + accessToken,
            'Content-Type': 'application/json'
            }
    r = requests.post(url, headers=headers, data=payload)
    return r.json()['href']

def update():
    print('update initiated at ' + date.strftime("%Y-%m-%d %H:%M:%S"))
    print('\n\n\n')
    BotToken = accessTokenBot()
    threads = list()
    for i in userFile['users']:
        print('updating playlists for user ' + i['id'])
        x = threading.Thread(target=updateIndividual, args=(i, BotToken))
        threads.append(x)
        x.start()

    for index, thread in enumerate(threads):
        thread.join()

def updateIndividual(user, BotToken):
    playlisthreflong = user['playlisthreflong']
    playlisthrefmid = user['playlisthrefmid']
    playlisthrefshort = user['playlisthrefshort']
    accessTokenUser = accessTokenForUser(user)
    x = threading.Thread(target=updatePlaylist, args=(accessTokenUser, BotToken, 'long_term', playlisthreflong,))
    y = threading.Thread(target=updatePlaylist, args=(accessTokenUser, BotToken, 'medium_term', playlisthrefmid,))
    z = threading.Thread(target=updatePlaylist, args=(accessTokenUser, BotToken, 'short_term', playlisthrefshort,))
    x.start()
    print('updating long playlist for user ' + user['id'])
    y.start()
    print('updating mid playlist for user ' + user['id'])
    z.start()
    print('updating short playlist for user ' + user['id'])
    x.join()
    print('finished updating long playlist for user ' + user['id'])
    y.join()
    print('finished updating mid playlist for user ' + user['id'])
    z.join()
    print('finished updating short playlist for user ' + user['id'])

def accessTokenBot():
    url = 'https://accounts.spotify.com/api/token'
    headers = { 'Authorization': 'Basic ' + base64.b64encode(client_id + ':' + client_secret) }
    payload = {
            'grant_type': 'refresh_token',
            'refresh_token': refreshtokenme
            }
    r = requests.post(url, headers=headers, data=payload)
    if (r.status_code == 200):
        return r.json()['access_token']

def accessTokenForUser(user):
    refresh_token = user['refresh_token']
    url = 'https://accounts.spotify.com/api/token'
    headers = { 'Authorization': 'Basic ' + base64.b64encode(client_id + ':' + client_secret) }
    payload = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
            }
    r = requests.post(url, headers=headers, data=payload)
    if (r.status_code == 200):
        return r.json()['access_token']

def updatePlaylist(accessTokenUser, accessTokenPlaylist, term, playlisthref):
    url = 'https://api.spotify.com/v1/me/top/tracks?limit=50&time_range=' + term
    headers = {'Authorization': 'Bearer ' + accessTokenUser }
    r = requests.get(url, headers=headers)
    uri = []
    for i in r.json()['items']:
        uri.append(i['uri'])

    url = playlisthref + '/tracks/'
    headers = { 
            'Authorization': 'Bearer ' + accessTokenPlaylist,
            'Content-Type': 'application/json'
            }
    r = requests.put(url, headers=headers, data=json.dumps({'uris': uri}))

def playlist(userString):
    userids = list()
    for i in userFile['users']:
        userids.append(i['id'])

    userid = process.extractOne(userString, userids, score_cutoff=80)
    if userid is None:
        print('Unable to determine user you want')
        return

    userid = userid[0]
    for i in userFile['users']:
        if (i['id'] == userid):
            user = i
            break

    accessToken = accessTokenForUser(user)
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

def playlistIndividual(userid, accessToken, time, term):
    payload = json.dumps({ 'name': "Top Songs of " + time + " as of " + date.strftime("%m") + "/" + date.strftime("%d") + "/" + date.strftime("%Y") })
    playlisthref = createPlaylist(userid, accessToken, payload)
    updatePlaylist(accessToken, accessToken, term, playlisthref)

date = datetime.datetime.today()
if __name__ == '__main__':
    with open(sys.path[0] + '/users.json') as json_file:
        userFile = json.load(json_file)
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
else:
    with open('./users.json') as json_file:
        userFile = json.load(json_file)
