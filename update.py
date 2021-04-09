import spotifywebapi
import json
import datetime
from concurrent.futures import ThreadPoolExecutor
import sys
import os

def getAuthUser(user: dict[str, str]) -> spotifywebapi.User:
    return sp.getAuthUser(user['refresh_token'])

# updates the three continuously updated playlists for the given user object


def updateIndividual(user: dict[str, str], bottomexecutor: ThreadPoolExecutor) -> None:
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
    bottomexecutor.submit(updatePlaylist, userobj, botuser, 'long_term', playlistidlong, name)
    print('updating long playlist for user ' + name)
    bottomexecutor.submit(updatePlaylist, userobj, botuser, 'medium_term', playlistidmid, name)
    print('updating mid playlist for user ' + name)
    bottomexecutor.submit(updatePlaylist, userobj, botuser, 'short_term', playlistidshort, name)
    print('updating short playlist for user ' + name)

# Populates the given playlist with the current top songs for the given term for the user with accessTokenForUser
# accessTokenPlaylist for access token of owner of given playlist in playlistid


def updatePlaylist(user: spotifywebapi.User, playlistuser: spotifywebapi.User, term: str, playlistid: str, name: str) -> None:
    topsongs = user.getTopSongs(term, limit=50)
    uris = [i['uri'] for i in topsongs['items']]
    try:
        playlistuser.replacePlaylistItems(playlistid, uris)
    except spotifywebapi.StatusCodeError as err:
        print(err + ' for ' + user.getUser()['display_name'])
    else:
        print('finished ' + term.removesuffix('_term') + ' playlist for user ' + name)

# updates all continuously updated playlists for all users in users.json


def update() -> None:
    print('update initiated at ' + date.strftime("%Y-%m-%d %H:%M:%S"))
    print('\n\n\n')
    with ThreadPoolExecutor() as bottomexecutor:
        with ThreadPoolExecutor() as executor:
            for user in userFile['users']:
                executor.submit(updateIndividual, user, bottomexecutor)


def last100RandomPool() -> None:
    print('updating last 100 RPOS')
    userme = getAuthUser(userFile['users'][0])
    rpos = sp.getPlaylistFromId('5WYRn0FxSUhVsOQpQQ0xBV')
    total = rpos['tracks']['total']
    offset = total - 100
    tracks = sp.getTracksFromItem(rpos)
    uris = [i['track']['uri']
            for i in tracks[offset:] if i['is_local'] is False]
    userme.replacePlaylistItems('1iAyKjAS15OOlFBFtnWX1n', uris)
    print('finished last 100 RPOS')


date = datetime.datetime.today()
refreshtokenme = os.getenv('REFRESHTOKENME')
try:
    sp = spotifywebapi.Spotify(
        os.getenv('CLIENT_ID'), os.getenv('CLIENT_SECRET'))
except spotifywebapi.SpotifyError as err:
    print('Error loading bot')
    print(err)
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
