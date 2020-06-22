import spotifywebapi
import json
import datetime
import threading
import sys
import os
import dotenv

dotenv.load_dotenv()

try:
    sp = spotifywebapi.Spotify(os.getenv('CLIENT_ID'), os.getenv('CLIENT_SECRET'))
except spotifywebapi.SpotifyError:
    print('Error loading bot')
    exit()

# returns a valid access token for the bot
def accessTokenBot():
    return sp.accessToken

def getUser(user):
    return sp.getAuthUser(user['refresh_token'])

# updates the three continuously updated playlists for the given user object
def updateIndividual(user, botuser):
    playlistidlong = user['playlistidlong']
    playlistidmid = user['playlistidmid']
    playlistidshort = user['playlistidshort']
    try:
        userobj = getUser(user)
    except spotifywebapi.SpotifyError:
        print('app not authorized for user ' + user['id'])
        return

    print('updating playlists for user ' + userobj.getUser()['display_name'])
    x = threading.Thread(target=updatePlaylist, args=(userobj, botuser, 'long_term', playlistidlong,))
    y = threading.Thread(target=updatePlaylist, args=(userobj, botuser, 'medium_term', playlistidmid,))
    z = threading.Thread(target=updatePlaylist, args=(userobj, botuser, 'short_term', playlistidshort,))
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
# accessTokenPlaylist for access token of owner of given playlist in playlistid
def updatePlaylist(user, playlistuser, term, playlistid):
    topsongs = user.getTopSongs(term, limit=50)
    uris = [i['uri'] for i in topsongs['items']]
    try:
        playlistuser.replacePlaylistItems(playlistid, uris)
    except spotifywebapi.StatusCodeError as err:
        print(err.message + ' for ' + user.getUser()['display_name'])

# updates all continuously updated playlists for all users in users.json
def update():
    print('update initiated at ' + date.strftime("%Y-%m-%d %H:%M:%S"))
    print('\n\n\n')
    botuser = sp.getAuthUser(os.getenv('REFRESHTOKENME'))
    threads = []
    for i in userFile['users']:
        x = threading.Thread(target=updateIndividual, args=(i, botuser))
        threads.append(x)
        x.start()

    for thread in threads:
        thread.join()

def last100RandomPool():
    userme = getUser(userFile['users'][0])
    rpos = sp.getPlaylistFromId('5WYRn0FxSUhVsOQpQQ0xBV')
    total = rpos['tracks']['total']
    offset = total - 100
    tracks = sp.getTracksFromItem(rpos)
    uris = [i['track']['uri'] for i in tracks[offset:] if i['is_local'] is False]
    userme.replacePlaylistItems('1iAyKjAS15OOlFBFtnWX1n', uris)

date = datetime.datetime.today()
if __name__ == '__main__':
    with open(sys.path[0] + '/users.json') as json_file:
        userFile = json.load(json_file)

    update()
    last100RandomPool()
else:
    with open('./users.json') as json_file:
        userFile = json.load(json_file)
