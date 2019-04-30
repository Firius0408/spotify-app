import requests
import json
import datetime
import base64
import threading
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

client_id = 'bda7b557a026402d92584e140e291f57'
client_secret = '160f08d795334c85a7227b695b1d54f3'
refreshtokenme = 'AQBzPXpkLqDOctHGd092exRtHaw0WIg7wtgNB9BFKlJtMJboyq_EFHruvhUbLKp38AByxmss_kN1ViTwaroT0T_QbpOuEV9tn4O8AvXxsawTHnrap8pnwG98u3qYw1j8rS8'

def update():
    url = 'https://accounts.spotify.com/api/token'
    headers = { 'Authorization': 'Basic ' + base64.b64encode(client_id + ':' + client_secret) }
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refreshtokenme
    }
    r = requests.post(url, headers=headers, data=payload)
    if (r.status_code == 200):
        access_token = r.json()['access_token']

    threads = list()
    for i in userFile['users']:
        print('updating playlists for user ' + i['id'])
        x = threading.Thread(target=updateIndividual, args=(i, access_token))
        threads.append(x)
        x.start()

    for index, thread in enumerate(threads):
        thread.join()

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
        access_token = r.json()['access_token']

    return access_token

def updateIndividual(user, access_token):
    playlisthreflong = user['playlisthreflong']
    playlisthrefmid = user['playlisthrefmid']
    playlisthrefshort = user['playlisthrefshort']
    access_token0 = accessTokenForUser(user)
    x = threading.Thread(target=updatePlaylist, args=(access_token0, access_token, 'long_term', playlisthreflong,))
    y = threading.Thread(target=updatePlaylist, args=(access_token0, access_token, 'medium_term', playlisthrefmid,))
    z = threading.Thread(target=updatePlaylist, args=(access_token0, access_token, 'short_term', playlisthrefshort,))
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

def updatePlaylist(access_token0, access_token, term, playlisthref):
    url = 'https://api.spotify.com/v1/me/top/tracks?limit=50&time_range=' + term
    headers = {'Authorization': 'Bearer ' + access_token0 }

    r = requests.get(url, headers=headers)
    uri = []
    for i in r.json()['items']:
        uri.append(i['uri'])
    
    url = playlisthref + '/tracks/'
    headers = { 
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json'
            }
    r = requests.put(url, headers=headers, data=json.dumps({'uris': uri}))

def playlist(userString):
    userids = list()
    for i in userFile['users']:
        userids.append(i['id'])

    userid = process.extractOne(userString, userids)[0]
    for i in userFile['users']:
        if (i['id'] == userid):
            user = i
            break

    accesstoken = accessTokenForUser(user)
    print('creating playlists')
    playlisthreflong = playlistIndividual(userid, accesstoken, "All-Time")
    playlisthrefmid = playlistIndividual(userid, accesstoken, "the Past 6 Months")
    playlisthrefshort = playlistIndividual(userid, accesstoken, "the Past 4 Weeks")

def playlistIndividual(userid, accesstoken, term):
    url = 'https://api.spotify.com/v1/users/' + userid + '/playlists/'
    headers =  { 
            'Authorization': 'Bearer ' + accesstoken,
            'Content-Type': 'application/json'
            }
    payload = json.dumps({ 'name': "Top Songs of " + term + " as of " + date.strftime("%m") + "/" + date.strftime("%d") + "/" + date.strftime("%Y") })
    r = requests.post(url, headers=headers, data=payload)
    return r.json()['href']

date = datetime.datetime.today()
print('update initiated at ' + date.strftime("%Y-%m-%d %H:%M:%S"))
print('\n\n\n')
with open('./users.json') as json_file:
    userFile = json.load(json_file)
#update()
playlist("firius")
