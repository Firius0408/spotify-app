import requests
import json
import datetime
import base64
import threading
import sys

client_id = 'bda7b557a026402d92584e140e291f57'
client_secret = '160f08d795334c85a7227b695b1d54f3'
refreshtokenme = 'AQBzPXpkLqDOctHGd092exRtHaw0WIg7wtgNB9BFKlJtMJboyq_EFHruvhUbLKp38AByxmss_kN1ViTwaroT0T_QbpOuEV9tn4O8AvXxsawTHnrap8pnwG98u3qYw1j8rS8'
useridme = 'ohjber0jdol59842ilmd8w0a2'

# returns a valid access token for the bot
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

# returns a valid access token for the user object
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

# updates the three continuously updated playlists for the given user object
def updateIndividual(user, botToken):
    playlisthreflong = user['playlisthreflong']
    playlisthrefmid = user['playlisthrefmid']
    playlisthrefshort = user['playlisthrefshort']
    accessTokenUser = accessTokenForUser(user)
    if accessTokenUser is None:
        print 'app not authorized for user ' + user['id']
        return

    x = threading.Thread(target=updatePlaylist, args=(accessTokenUser, botToken, 'long_term', playlisthreflong,))
    y = threading.Thread(target=updatePlaylist, args=(accessTokenUser, botToken, 'medium_term', playlisthrefmid,))
    z = threading.Thread(target=updatePlaylist, args=(accessTokenUser, botToken, 'short_term', playlisthrefshort,))
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

# Populates the given playlist with the current top songs for the given term for the user with accessTokenForUser
# accessTokenPlaylist for access token of owner of given playlist in playlisthref
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

# updates all continuously updated playlists for all users in users.json
def update():
    print('update initiated at ' + date.strftime("%Y-%m-%d %H:%M:%S"))
    print('\n\n\n')
    botToken = accessTokenBot()
    threads = list()
    for i in userFile['users']:
        print('updating playlists for user ' + i['id'])
        x = threading.Thread(target=updateIndividual, args=(i, botToken))
        threads.append(x)
        x.start()

    for index, thread in enumerate(threads):
        thread.join()

date = datetime.datetime.today()
if __name__ == '__main__':
    with open(sys.path[0] + '/users.json') as json_file:
        userFile = json.load(json_file)

    update()
else:
    with open('./users.json') as json_file:
        userFile = json.load(json_file)
