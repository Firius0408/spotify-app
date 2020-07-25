import spotifywebapi
import json
import datetime
import multiprocessing
import sys
import os
import dotenv

def getAuthUser(user):
    return sp.getAuthUser(user['refresh_token'])

# updates the three continuously updated playlists for the given user object
def updateIndividual(user):
    playlistidlong = user['playlistidlong']
    playlistidmid = user['playlistidmid']
    playlistidshort = user['playlistidshort']
    try:
        userobj = getAuthUser(user)
    except spotifywebapi.SpotifyError:
        print('app not authorized for user ' + user['id'])
        return

    name = userobj.getUser()['display_name']
    print('updating playlists for user ' + name)
    x = multiprocessing.Process(target=updatePlaylist, args=(userobj, botuser, 'long_term', playlistidlong,))
    y = multiprocessing.Process(target=updatePlaylist, args=(userobj, botuser, 'medium_term', playlistidmid,))
    z = multiprocessing.Process(target=updatePlaylist, args=(userobj, botuser, 'short_term', playlistidshort,))
    x.start()
    print('updating long playlist for user ' + name)
    y.start()
    print('updating mid playlist for user ' + name)
    z.start()
    print('updating short playlist for user ' + name)
    x.join()
    print('finished updating long playlist for user ' + name)
    y.join()
    print('finished updating mid playlist for user ' + name)
    z.join()
    print('finished updating short playlist for user ' + name)

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
    processes = []
    for i in userFile['users']:
        x = multiprocessing.Process(target=updateIndividual, args=(i,))
        processes.append(x)
        x.start()

    for process in processes:
        process.join()

def last100RandomPool():
    userme = getAuthUser(userFile['users'][0])
    rpos = sp.getPlaylistFromId('5WYRn0FxSUhVsOQpQQ0xBV')
    total = rpos['tracks']['total']
    offset = total - 100
    tracks = sp.getTracksFromItem(rpos)
    uris = [i['track']['uri'] for i in tracks[offset:] if i['is_local'] is False]
    userme.replacePlaylistItems('1iAyKjAS15OOlFBFtnWX1n', uris)

date = datetime.datetime.today()
dotenv.load_dotenv()
refreshtokenme = os.getenv('REFRESHTOKENME')
try:
    sp = spotifywebapi.Spotify(os.getenv('CLIENT_ID'), os.getenv('CLIENT_SECRET'))
except spotifywebapi.SpotifyError:
    print('Error loading bot')
    exit()

botuser = sp.getAuthUser(refreshtokenme)
if __name__ == '__main__':
    with open(sys.path[0] + '/data.json') as json_file:
        userFile = json.load(json_file)

    update()
    last100RandomPool()
else:
    with open('./data.json') as json_file:
        userFile = json.load(json_file)
