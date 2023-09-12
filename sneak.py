from fuzzywuzzy import process, fuzz
import json
import operator
import re
import sys
import emoji
from concurrent.futures import ThreadPoolExecutor, wait
import datetime
import os
from update import getAuthUser, userFile, sp
from spotify import getUserFromString

ignore = ['Post Malone', 'AJR', 'Ed Sheeran', 'Eminem', 'Logic', 'Queen', 'Bleachers', 'L?', 'IYLHLHG', 'Musical', 'Disney', 'Indie', 'Classical', 'Monstercat', 'Rap', 'House', 'The Beatles', 'Ashley', 'Jonathan', 'Daniel', 'Phillip', 'Shan', 'Pegboard Nerds', 'Drake', 'Hardwell',
          'Martin Garrix', 'Maroon 5', 'Taylor Swift', 'Andrea Bocelli', 'Kygo', 'Zedd', 'OneRepublic', 'Album Worthy', 't', 'Memories', 'Last 100 songs in RPoS', 'Top Danceability Songs for firiusbob', 'Top Valence Songs for firiusbob', 'Top Energy Songs for firiusbob', 'Lauv', 'Illenium', 'Mitis']

users = {}
userplaylists = {}
playlisttracks = {}
files = set()

def clearCache() -> None:
    global users, userplaylists, playlisttracks
    users = {}
    userplaylists = {}
    playlisttracks = {}


def refreshCacheUsers(k) -> None:
    global users
    users[k] = sp.getUser(k)


def refreshCachePlaylists(k) -> None:
    global userplaylists
    userplaylists[k] = sp.getUserPlaylists({'id': k})


def refreshCacheTracks(k) -> None:
    global playlisttracks
    playlisttracks[k] = sp.getTracksFromItem(
        {'tracks': {'href': 'https://api.spotify.com/v1/playlists/' + k + '/tracks'}})


def refreshCache() -> None:
    global users, userplaylists, playlisttracks
    with ThreadPoolExecutor() as executor:
        for k in users.keys():
            executor.submit(refreshCacheUsers, k)

        for k in userplaylists.keys():
            executor.submit(refreshCachePlaylists, k)

        for k in playlisttracks.keys():
            executor.submit(refreshCacheTracks, k)


def getUserPlaylists(user: dict) -> list[dict]:
    global userplaylists
    iid = user['id']
    if iid in userplaylists.keys():
        return userplaylists[iid]
    else:
        temp = sp.getUserPlaylists(user)
        userplaylists[iid] = temp
        return temp


def getUser(userString: str) -> dict:
    global users
    userString = userString.replace('spotify:user:', '')
    if userString in users.keys():
        return users[userString]
    else:
        temp = sp.getUser(userString)
        users[userString] = temp
        return temp


def getTracksFromItem(playlist: dict) -> list[dict]:
    global playlisttracks
    iid = playlist['id']
    if iid in playlisttracks.keys():
        return playlisttracks[iid]
    else:
        temp = sp.getTracksFromItem(playlist)
        playlisttracks[iid] = temp
        return temp


def appendTracksFromItem(playlist: dict, tracks: list[dict]) -> None:
    global playlisttracks
    iid = playlist['id']
    if iid in playlisttracks.keys():
        tracks.append(playlisttracks[iid])
    else:
        temp = sp.getTracksFromItem(playlist)
        playlisttracks[iid] = temp
        tracks.append(temp)


def saveToFile(data, filename) -> None:
    global files
    files.add(filename)
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4, separators=(', ', ': '))


def clearFiles() -> None:
    global files
    for ffile in files:
        if os.path.isfile(ffile):
            os.remove(ffile)

    files = set()


def getPlaylist(playlists: list[dict], playliststring: str) -> dict:
    demojidict = {emoji.demojize(
        playlist['name']): playlist for playlist in playlists}
    playlistString = emoji.demojize(playliststring)
    playlist = process.extractOne(
        playlistString, list(demojidict.keys()), score_cutoff=80)
    if playlist is None:
        raise LookupError('Unable to determine playlist')

    return demojidict[playlist[0]]


def getSongsPlaylist(playlist: dict) -> None:
    if "Past 4 Weeks" in playlist['name']:
        directory = 'month'
    elif "Past 6 Months" in playlist['name']:
        directory = '6month'
    elif "All-Time" in playlist['name']:
        directory = 'all'
    else:
        return

    match = re.search(r'\d{1,2}/\d{1,2}/\d{4}', playlist['name'])
    if match is None:
        print(playlist['name'])
        return

    date = datetime.datetime.strptime(match.group(), '%m/%d/%Y').date()
    filename = date.strftime('%Y-%m-%d')
    if os.path.lexists('./topsongs/' + directory + '/' + filename + '.json'):
        print(directory + '     ' + filename + ' found')
    else:
        tracks = getTracksFromItem(playlist)
        name = [track['track']['name'] for track in tracks]
        filtered = [i for i in name if i]
        print('writing ' + directory + '     ' + filename)
        with open('./topsongs/' + directory + '/' + filename + '.json', 'w') as f:
            json.dump(filtered, f, indent=4, separators=(', ', ': '))


def topArtistsInPlaylists(userString: str, count: bool = False, grouped: bool = False) -> list[tuple]:
    user = getUser(userString)
    if user is None:
        return

    playlists = getUserPlaylists(user)
    trackss = []
    with ThreadPoolExecutor() as executor:
        for playlist in playlists:
            if count and playlist['name'] in ignore:
                continue

            if "Top Songs of " in playlist['name'] or user['id'] != playlist['owner']['id']:
                continue

            executor.submit(appendTracksFromItem, playlist, trackss)

    artists = []
    for tracks in trackss:
        if grouped:
            temp = [', '.join([artist['name'] for artist in track['track']['artists']])
                    for tracks in trackss for track in tracks]
        else:
            temp = [artist['name']
                    for track in tracks if track and track['track'] for artist in track['track']['artists'] if artist and artist['name']]

        if not count:
            temp = list(set(temp))

        artists.extend(temp)

    count = {i: artists.count(i) for i in artists}
    if None in list(count.keys()):
        del count[None]

    sortedCount = sorted(list(count.items()),
                         key=operator.itemgetter(1), reverse=True)
    return sortedCount


def topArtistsInPlaylist(userString: str, playlistString: str, grouped: bool = False) -> list[tuple]:
    playlist = getPlaylist(getUserPlaylists(
        getUser(userString)), playlistString)
    tracks = getTracksFromItem(playlist)
    if grouped:
        artists = [', '.join(
            [artist['name'] for artist in track['track']['artists']]) for track in tracks]
    else:
        artists = [artist['name']
                   for track in tracks for artist in track['track']['artists']]
    count = {i: artists.count(i) for i in artists}
    if None in list(count.keys()):
        del count[None]

    sortedCount = sorted(list(count.items()),
                         key=operator.itemgetter(1), reverse=True)
    return sortedCount


def topGenresInPlaylists(userString: str) -> list[tuple]:
    user = getUser(userString)
    if user is None:
        return

    playlists = getUserPlaylists(user)
    trackss = []
    with ThreadPoolExecutor() as executor:
        for playlist in playlists:
            if "Top Songs of " in playlist['name'] or user['id'] != playlist['owner']['id'] or playlist['name'] in ignore:
                continue

            executor.submit(appendTracksFromItem, playlist, trackss)

    artistids = [artist['id']
                 for tracks in trackss for track in tracks for artist in track['track']['artists']]
    artistids = list(filter(None.__ne__, artistids))
    artists = sp.getArtistsFromIds(artistids)
    genres = [genre for artist in artists for genre in artist['genres']]
    count = {i: genres.count(i) for i in genres}
    if None in list(count.keys()):
        del count[None]

    sortedCount = sorted(list(count.items()),
                         key=operator.itemgetter(1), reverse=True)
    return sortedCount


def topGenresInPlaylist(userString: str, playlistString: str) -> list[tuple]:
    playlist = getPlaylist(getUserPlaylists(
        getUser(userString)), playlistString)
    tracks = getTracksFromItem(playlist)
    artistids = [artist['id']
                 for track in tracks for artist in track['track']['artists']]
    artists = sp.getArtistsFromIds(artistids)
    genres = [genre for artist in artists for genre in artist['genres']]
    count = {i: genres.count(i) for i in genres}
    if None in list(count.keys()):
        del count[None]

    sortedCount = sorted(list(count.items()),
                         key=operator.itemgetter(1), reverse=True)
    return sortedCount


def topSongsInPlaylistsSub(userString: str) -> tuple[list[str], dict[str, dict]]:
    user = getUser(userString)
    if user is None:
        return

    playlists = getUserPlaylists(user)
    trackss = []
    with ThreadPoolExecutor() as executor:
        for playlist in playlists:
            if "Top Songs of " in playlist['name'] or user['id'] != playlist['owner']['id'] or playlist['name'] in ignore or "Common Songs " in playlist['name']:
                continue

            executor.submit(appendTracksFromItem, playlist, trackss)

    trackids = []
    trackinfo = {}
    for tracks in trackss:
        for track in tracks:
            if track['track'] is None or track['track']['id'] is None:
                continue

            iid = track['track']['id']
            trackids.append(iid)
            trackinfo[iid] = {'Name': track['track']['name'],
                              'Artists': [artist['name'] for artist in track['track']['artists']],
                              'Album': track['track']['album']['name'],
                              'Popularity': track['track']['popularity']}

    return trackids, trackinfo


def topSongsInPlaylists(userString: str) -> list[tuple[dict, int]]:
    trackids, trackinfo = topSongsInPlaylistsSub(userString)
    trackids = list(filter(None.__ne__, trackids))
    if None in list(trackinfo.keys()):
        del trackinfo[None]

    count = {i: trackids.count(i) for i in trackids}
    if None in list(count.keys()):
        del count[None]

    infoCount = [(trackinfo[k], v) for k, v in list(count.items())]
    sortedName = sorted(infoCount, key=operator.itemgetter(1), reverse=True)
    return sortedName


def topSongsPlaylists(userString: str) -> None:
    user = getUser(userString)
    playlists = getUserPlaylists(user)
    with ThreadPoolExecutor() as executor:
        for playlist in playlists:
            if "Top Songs of " not in playlist['name']:
                continue

            executor.submit(getSongsPlaylist, playlist)


def topArtists(userString: str, term: str = 'long_term') -> list[str]:
    user = getUserFromString(userString)
    userobj = getAuthUser(user)
    return [artist['name'] for artist in userobj.getTopArtists(term, limit=50)['items']]


def songPopularity(userString: str, playlistString: str) -> list[dict[str, str]]:
    user = getUser(userString)
    playlist = getPlaylist(getUserPlaylists(user), playlistString)
    tracks = getTracksFromItem(playlist)
    trackinfo = [{'Name': track['track']['name'],
                  'Artists': [artist['name'] for artist in track['track']['artists']],
                  'Album': track['track']['album']['name'],
                  'Popularity': track['track']['popularity']} for track in tracks]

    sortedCount = sorted(trackinfo, key=operator.itemgetter(
        'Popularity'), reverse=True)
    return sortedCount


def playlistRepeats(userString: str, playlistString: str) -> list[tuple[str, list[str]]]:
    playlist = getPlaylist(getUserPlaylists(
        getUser(userString)), playlistString)
    results = []
    playlistRepeatsthread(playlist, results)
    return results


def playlistRepeatsthread(playlist: dict, results: list) -> None:
    tracks = getTracksFromItem(playlist)
    name = [track['track']['name'] + ' : ' + ', '.join(
        [artist['name'] for artist in track['track']['artists']]) for track in tracks]
    while None in name:
        name.remove(None)

    result = findRepeats(name)
    if result:
        results.append((playlist['name'], result))


def playlistRepeatsAll(userString: str) -> list[tuple[str, list[str]]]:
    user = getUser(userString)
    playlists = getUserPlaylists(user)
    results = []
    with ThreadPoolExecutor() as executor:
        for playlist in playlists:
            if "Top Songs of " in playlist['name'] or user['id'] != playlist['owner']['id']:
                continue

            executor.submit(playlistRepeatsthread, playlist, results)

    return results


def findRepeats(L: list[str]) -> list[str]:
    seen = set()
    seen2 = set()
    seen_add = seen.add
    seen2_add = seen2.add
    for item in L:
        if item in seen:
            seen2_add(item)
        else:
            seen_add(item)
    return list(seen2)


def ratio(userString: str = 'firiusbob', playlistString: str = 'Random Pool of Stuff') -> list[tuple[str, float]]:
    user = getUser(userString)
    playlists = getUserPlaylists(user)
    playlist = getPlaylist(playlists, playlistString)
    tracks = getTracksFromItem(playlist)
    artists = [artist['name']
               for track in tracks for artist in track['track']['artists']]
    countplaylist = {i: artists.count(i) for i in artists}
    if None in list(countplaylist.keys()):
        del countplaylist[None]

    trackss = []
    with ThreadPoolExecutor() as executor:
        for playlist in playlists:
            if "Top Songs of " in playlist['name'] or user['id'] != playlist['owner']['id'] or playlist['name'] in ignore:
                continue

            executor.submit(appendTracksFromItem, playlist, trackss)

    artists = [artist['name']
               for tracks in trackss for track in tracks for artist in track['track']['artists']]
    count = {i: artists.count(i) for i in artists}
    if None in list(count.keys()):
        del count[None]

    ratio = {}
    for i in count:
        if i not in list(countplaylist.keys()):
            print('Could not find ' + i)
            continue

        allNumber = count[i]
        poolNumber = countplaylist[i]
        ratio[i] = allNumber / poolNumber

    sortedCount = sorted(list(ratio.items()),
                         key=operator.itemgetter(1), reverse=True)
    return sortedCount


def ratioGrouped(userString: str = 'firiusbob', playlistString: str = 'Random Pool of Stuff') -> list[tuple[tuple[str, ...], float]]:
    user = getUser(userString)
    playlists = getUserPlaylists(user)
    playlist = getPlaylist(playlists, playlistString)
    tracks = getTracksFromItem(playlist)
    artists = [tuple(artist['name']
                     for artist in track['track']['artists']) for track in tracks]
    countplaylist = {i: artists.count(i) for i in artists}
    if None in list(countplaylist.keys()):
        del countplaylist[None]

    trackss = []
    with ThreadPoolExecutor() as executor:
        for playlist in playlists:
            if "Top Songs of " in playlist['name'] or user['id'] != playlist['owner']['id'] or playlist['name'] in ignore:
                continue

            executor.submit(appendTracksFromItem, playlist, trackss)

    artists = [tuple(artist['name'] for artist in track['track']['artists'])
               for tracks in trackss for track in tracks]
    count = {i: artists.count(i) for i in artists}
    if None in list(count.keys()):
        del count[None]

    ratio = {}
    for i in count:
        if i not in list(countplaylist.keys()):
            print('Could not find artist(s) ' + ', '.join(i))
            continue

        allNumber = count[i]
        poolNumber = countplaylist[i]
        ratio[i] = allNumber / poolNumber

    sortedCount = sorted(list(ratio.items()),
                         key=operator.itemgetter(1), reverse=True)
    return sortedCount


def findSongInPlayliststhread(playlist: dict, results: list, songId: str) -> None:
    tracks = getTracksFromItem(playlist)
    for track in tracks:
        if track['track']['id'] == songId:
            results.append(playlist['name'])
            return


def findSongInPlaylists(userString: str, songId: str) -> list[str]:
    user = getUser(userString)
    if user is None:
        return

    songId = songId.replace('spotify:track:', '')
    playlists = getUserPlaylists(user)
    results = []
    with ThreadPoolExecutor() as executor:
        for playlist in playlists:
            if "Top Songs of " in playlist['name'] or user['id'] != playlist['owner']['id']:
                continue

            executor.submit(findSongInPlayliststhread, playlist, results, songId)

    return results


def dateAddedSongInPlayliststhread(playlist: dict, results: list, songId: str) -> None:
    tracks = getTracksFromItem(playlist)
    for track in tracks:
        if track['track']['id'] == songId:
            results.append(
                (playlist['name'], track['added_at'].replace('T', ' ').replace('Z', '')))
            return


def dateAddedSongInPlaylists(userString: str, songId: str) -> list[tuple[str, str]]:
    user = getUser(userString)
    if user is None:
        return

    songId = songId.replace('spotify:track:', '')
    playlists = getUserPlaylists(user)
    results = []
    with ThreadPoolExecutor() as executor:
        for playlist in playlists:
            if "Top Songs of " in playlist['name'] or user['id'] != playlist['owner']['id']:
                continue

            executor.submit(dateAddedSongInPlayliststhread, playlist, results, songId)

    return sorted(results, key=operator.itemgetter(1))


def findArtistInPlayliststhread(playlist: dict, results: list, artistId: str) -> None:
    tracks = getTracksFromItem(playlist)
    data = [(track['track']['name'], [artist['id']
                                      for artist in track['track']['artists']]) for track in tracks]
    temp = []
    for i, j in data:
        if artistId in j:
            temp.append(i)

    if temp:
        results.append((playlist['name'], temp))


def findArtistInPlaylists(userString: str, artistId: str) -> list[tuple[str, list[str]]]:
    user = getUser(userString)
    if user is None:
        return

    artistId = artistId.replace('spotify:artist:', '')
    playlists = getUserPlaylists(user)
    results = []
    with ThreadPoolExecutor() as executor:
        for playlist in playlists:
            if "Top Songs of " in playlist['name'] or user['id'] != playlist['owner']['id']:
                continue

            executor.submit(findArtistInPlayliststhread, playlist, results, artistId)

    return results


def search(string: str, kind: str) -> list[tuple[str, str]]:
    string = string.replace(' ', '%20')
    return [(i['name'], i['id']) for i in sp.search(string, kind)[kind + 's']['items']]


def searchRPOS(song: str) -> list[tuple[str, list[str], str]]:
    song = song.lower()
    song = song.translate({ord(i): None for i in ':&()'})
    song = song.split('feat.', 1)[0]
    song = song.split('-', 1)[0]
    playlist = sp.getPlaylistFromId('5WYRn0FxSUhVsOQpQQ0xBV')
    tracks = getTracksFromItem(playlist)
    results = []
    print('Searching RPOS...')
    for track in tracks:
        if track is None or track['track'] is None:
            continue

        test = track['track']['name'].lower()
        test = test.translate({ord(i): None for i in ':&()'})
        test = test.split('feat.', 1)[0]
        test = test.split('-', 1)[0]
        if fuzz.partial_ratio(song, test) > 98 and fuzz.ratio(song, test) > 45:
            diff = len(test) - len(song)
            if diff < 100 and diff >= 0:
                results.append((track['track']['name'], [
                               artist['name'] for artist in track['track']['artists']], track['track']['id']))

    return results


def searchPlayliststhread(playlist: dict, songids: list, song: str) -> None:
    tracks = getTracksFromItem(playlist)
    for track in tracks:
        if track is None or track['track'] is None:
            continue

        test = track['track']['name'].lower()
        test = test.translate({ord(i): None for i in ':&()'})
        test = test.split('feat.', 1)[0]
        test = test.split('-', 1)[0]
        if fuzz.partial_ratio(song, test) > 98 and fuzz.ratio(song, test) > 45:
            diff = len(test) - len(song)
            if diff < 100 and diff >= 0:
                songids.append(track['track']['id'])


def searchPlaylists(userString: str, song: str) -> list[tuple[str, list[str], str, str]]:
    song = song.lower()
    song = song.translate({ord(i): None for i in ':&()'})
    song = song.split('feat.', 1)[0]
    song = song.split('-', 1)[0]
    user = getUser(userString)
    if user is None:
        return

    playlists = getUserPlaylists(user)
    songids = []
    with ThreadPoolExecutor() as executor:
        for playlist in playlists:
            if "Top Songs of " in playlist['name'] or user['id'] != playlist['owner']['id']:
                continue

            executor.submit(searchPlayliststhread, playlist, songids, song)

    songids = list(filter(None.__ne__, songids))
    songids = list(set(songids))
    tracks = sp.getTracksFromIds(songids)
    results = [(track['name'], [artist['name'] for artist in track['artists']],
                track['id'], track['album']['name']) for track in tracks]
    return results


def convertThread(track: dict, name: str, artists: list[str], rposdata: list[tuple[str, list[str], str]], uris: list) -> None:
    for i in rposdata:
        if name == i[0] and set(artists) == set(i[1]):
            uris.append(i[2])
            return

    print(name)
    uris.append(track['track']['uri'])


def convert(playlistString: str) -> None:
    user = getUserFromString('firiusbob')
    rposplaylist = sp.getPlaylistFromId('5WYRn0FxSUhVsOQpQQ0xBV')
    print('Pulling from RPOS')
    rpostracks = getTracksFromItem(rposplaylist)
    rposdata = [(track['track']['name'], [artist['name'] for artist in track['track']
                                          ['artists']], track['track']['uri']) for track in rpostracks]
    print('Finished pulling from RPOS. Searching...')
    playlist = getPlaylist(getUserPlaylists(user), playlistString)
    tracks = getTracksFromItem(playlist)
    uris = []
    for track in tracks:
        if track is None or track['track'] is None:
            continue

        name = track['track']['name']
        artists = [artist['name'] for artist in track['track']['artists']]
        convertThread(track, name, artists, rposdata, uris)

    print('Finished search. Creating playlist')
    userobj = getAuthUser(user)
    newplaylist = userobj.createPlaylist('Convert of ' + playlist['name'])
    print('Finished. Adding to playlist')
    userobj.addSongsToPlaylist(newplaylist['id'], uris)


def notinRPOS(playlistString: str) -> list[tuple[str, list[str], str]]:
    user = getUser('firiusbob')
    rposplaylist = sp.getPlaylistFromId('5WYRn0FxSUhVsOQpQQ0xBV')
    print('Pulling from RPOS')
    rpostracks = getTracksFromItem(rposplaylist)
    rposids = [track['track']['id'] for track in rpostracks]
    print('Finished pulling from RPOS. Comparing...')
    playlist = getPlaylist(getUserPlaylists(user), playlistString)
    tracks = getTracksFromItem(playlist)
    results = [track for track in tracks if track['track']['id'] not in rposids]
    return [(track['track']['name'], [artist['name'] for artist in track['track']['artists']], track['track']['id']) for track in results]


def playlistFollowersThread(playlist: dict, followers: list) -> None:
    playlistdata = sp.getPlaylistFromId(playlist['id'])
    followers.append(
        (playlistdata['name'], playlistdata['followers']['total']))


def playlistFollowers(userString: str) -> list[tuple[str, int]]:
    user = getUser(userString)
    playlists = getUserPlaylists(user)
    followers = []
    with ThreadPoolExecutor() as executor:
        for playlist in playlists:
            name = playlist['name']
            ownerid = playlist['owner']['id']
            if name not in ignore and "Top Songs of " not in name and ownerid == user['id']:
                executor.submit(playlistFollowersThread, playlist, followers)

    sortedCount = sorted(followers, key=operator.itemgetter(1), reverse=True)
    return sortedCount

def commonSongsUsersThread(userid: str, tracksss: list, executor: ThreadPoolExecutor):
    user = getUser(userid)
    playlists = getUserPlaylists(user)
    trackss = []
    futures = []
    for playlist in playlists:
        if playlist['owner']['id'] != userid or "Top Songs of " in playlist['name'] or playlist['id'] == '5eS0KgG63Opb1EqOE63Gpa':
            continue

        futures.append(executor.submit(appendTracksFromItem, playlist, trackss))

    wait(futures)
    tracksss.append(trackss)

def commonSongsUsers(*userids: str) -> str:
    userids = [i.replace('spotify:user:', '') for i in userids]
    if len(userids) < 2:
        print('You need at least 2 users bruh')
        return

    refreshtoken = 'AQAcsVCKBnutCWVRPih8OsU1ScZRFjPTePJNaY0GSehMefJmFdscQlGeGuIoU4fAfZ0rkOrx2SCOW3zVMEt3zKJG0mt2yBgKJwilvgCdoZ-ftJBh6AK1PjNVOPWlbbb6vFs'
    botuser = sp.getAuthUser(refreshtoken)
    commonsongs = userFile['commonsongs']
    print('Pulling songs...')
    tracksss = []
    executor = ThreadPoolExecutor()
    futures = []
    for userid in userids:
        futures.append(executor.submit(commonSongsUsersThread, userid, tracksss, executor))

    wait(futures)
    executor.shutdown()
    print('Finding common songs...')
    trackuri = []
    for trackss in tracksss:
        trackuri.append([track['track']['uri']
                         for tracks in trackss for track in tracks if track['track'] is not None])

    commonuri = set(trackuri[0])
    for i in trackuri[1:]:
        commonuri.intersection_update(i)

    if None in commonuri:
        commonuri.remove(None)

    for playlist in commonsongs:
        if set(userids) == set(playlist[0]):
            playlistid = playlist[1]
            tempplaylist = sp.getPlaylistFromId(playlistid)
            playlisttracks = getTracksFromItem(tempplaylist)
            playlisttracksset = {i['track']['uri'] for i in playlisttracks}
            newtracksset = commonuri - playlisttracksset
            if newtracksset:
                print('Adding to playlist...')
                botuser.addSongsToPlaylist(playlistid, list(newtracksset))
            else:
                print('Playlist already up to date')

            return playlistid

    commonuri = [i for i in commonuri if i is not None]
    names = [getUser(i)['display_name'] for i in userids]
    name = 'Common Songs between ' + ' and '.join(names)
    print('Creating playlist...')
    playlistid = botuser.createPlaylist(name)['id']
    commonsongs.append((userids, playlistid))
    userFile['commonsongs'] = commonsongs
    if __name__ == '__main__':
        with open(sys.path[0] + '/data.json', 'w') as f:
            json.dump(userFile, f, indent=4, separators=(',', ': '))
    else:
        with open('./data.json', 'w') as f:
            json.dump(userFile, f, indent=4, separators=(',', ': '))

    botuser.addSongsToPlaylist(playlistid, commonuri)
    return playlistid


def commonSongsUsersAll() -> None:
    commonsongs = userFile['commonsongs']
    for commonsong in commonsongs:
        while True:
            print(', '.join(commonsong[0]))
            try:
                commonSongsUsers(*commonsong[0])
            except Exception as err:
                print(err)
                continue

            break


def commonSongsTopSongs(*userids: str) -> list[tuple[str, int]]:
    commonsongs = userFile['commonsongs']
    playlistid = None
    for playlist in commonsongs:
        if set(userids) == set(playlist[0]):
            playlistid = playlist[1]
            break

    if playlistid is None:
        print('Could not find existing playlist. Creating one...')
        playlistid = commonSongsUsers(*userids)

    print('Retrieving common songs...')
    playlist = sp.getPlaylistFromId(playlistid)
    tracks = getTracksFromItem(playlist)
    tracks = {i['track']['id']: i['track']['name'] for i in tracks}
    trackids = [j for i in userids for j in topSongsInPlaylistsSub(i)[0]]
    trackids = list(filter(None.__ne__, trackids))
    count = {i: trackids.count(i) for i in list(tracks.keys())}
    if None in list(count.keys()):
        del count[None]

    result = [(tracks[i], j) for i, j in list(count.items())]
    sortedResult = sorted(result, key=operator.itemgetter(1), reverse=True)
    return sortedResult


def getAudioFeatures(ids: list[str]) -> list[dict]:
    return sp.getAudioFeatures(ids)


def playlistDiff(userString1: str, playlistString1: str, userString2: str, playlistString2: str) -> tuple[list[str], list[str], list[str]]:
    playlist1 = getPlaylist(getUserPlaylists(
        getUser(userString1)), playlistString1)
    playlist2 = getPlaylist(getUserPlaylists(
        getUser(userString2)), playlistString2)
    tracks1 = getTracksFromItem(playlist1)
    tracks2 = getTracksFromItem(playlist2)
    trackids1 = [track['track']['id'] for track in tracks1]
    trackids2 = [track['track']['id'] for track in tracks2]
    setplaylist1 = set(trackids1)
    setplaylist2 = set(trackids2)
    if None in setplaylist1:
        setplaylist1.remove(None)

    if None in setplaylist2:
        setplaylist2.remove(None)

    same = list(setplaylist1 & setplaylist2)
    diff1 = list(setplaylist1 - setplaylist2)
    diff2 = list(setplaylist2 - setplaylist1)
    same = sp.getTracksFromIds(list(same))
    diff1 = sp.getTracksFromIds(list(diff1))
    diff2 = sp.getTracksFromIds(list(diff2))
    same = [track['name'] for track in same]
    diff1 = [track['name'] for track in diff1]
    diff2 = [track['name'] for track in diff2]
    return (same, diff1, diff2)


def checkWd() -> tuple[list[str], list[str], list[str]]:
    user = getUser('firiusbob')
    playlists = getUserPlaylists(user)
    filtered = [playlist for playlist in playlists if 'Wd' in playlist['name']]
    wd = []
    subs = []
    for playlist in filtered:
        tracks = getTracksFromItem(playlist)
        if playlist['name'] == 'Weekend (Wd)':
            wd = [track['track']['id'] for track in tracks]
        else:
            subs.extend([track['track']['id'] for track in tracks])

    repeats = findRepeats(subs)
    wd = set(wd)
    subs = set(subs)
    diff1 = list(wd - subs)
    diff2 = list(subs - wd)
    repeats = [track['name'] for track in sp.getTracksFromIds(repeats)]
    diff1 = [track['name'] for track in sp.getTracksFromIds(diff1)]
    diff2 = [track['name'] for track in sp.getTracksFromIds(diff2)]
    return (diff1, diff2, repeats)


def topFeaturesPlaylists() -> None:
    user = getUserFromString('firiusbob')
    userobj = getAuthUser(user)
    rpos = getPlaylist(userobj.getPlaylists(), 'Random Pool of Stuff')
    tracks = getTracksFromItem(rpos)
    trackids = [track['track']['id'] for track in tracks]
    setids = set(trackids)
    if None in setids:
        setids.remove(None)

    ids = list(setids)
    features = getAudioFeatures(ids)
    dance = [(i['uri'], i['danceability']) for i in features]
    energy = [(i['uri'], i['energy']) for i in features]
    valence = [(i['uri'], i['valence']) for i in features]
    sorteddance = sorted(dance, key=operator.itemgetter(1), reverse=True)
    sortedenergy = sorted(energy, key=operator.itemgetter(1), reverse=True)
    sortedvalence = sorted(valence, key=operator.itemgetter(1), reverse=True)
    danceuris = [i[0] for i in sorteddance[0:250]]
    energyuris = [i[0] for i in sortedenergy[0:250]]
    valenceuris = [i[0] for i in sortedvalence[0:250]]
    danceobj = userobj.createPlaylist(
        'Top Danceability Songs for ' + userobj.user['display_name'])
    energyobj = userobj.createPlaylist(
        'Top Energy Songs for ' + userobj.user['display_name'])
    valenceobj = userobj.createPlaylist(
        'Top Valence Songs for ' + userobj.user['display_name'])
    userobj.addSongsToPlaylist(danceobj['id'], danceuris)
    userobj.addSongsToPlaylist(energyobj['id'], energyuris)
    userobj.addSongsToPlaylist(valenceobj['id'], valenceuris)


def newPlaylistsPullThread(playlist: dict, filename) -> None:
    tracks = getTracksFromItem(playlist)
    name = [track['track']['name'] for track in tracks]
    filtered = [i for i in name if i]
    print('writing ' + filename)
    with open('./newplaylists/' + filename + '.json', 'w') as f:
        json.dump(filtered, f, indent=4, separators=(', ', ': '))


def newPlaylistsPull() -> None:
    user = getUser('firiusbob')
    playlists = getUserPlaylists(user)
    with ThreadPoolExecutor() as executor:
        for playlist in playlists:
            match = re.search(r'\d{4}-\d{1,2}-\d{1,2}', playlist['name'])
            if match is None:
                continue
            
            executor.submit(newPlaylistsPullThread, playlist, match.group())


def artistCheckThread(artist: str, playlists: list[dict], rpostracks: list[dict]) -> None:
    playlist = getPlaylist(playlists, artist)
    tracks = getTracksFromItem(playlist)
    inrpos = [track['track']['name'] for track in rpostracks if artist in [
        i['name'] for i in track['track']['artists']]]
    inplaylist = [track['track']['name'] for track in tracks]
    diff = list(set(inrpos) - set(inplaylist))
    if diff:
        print('{}: {}'.format(artist, ', '.join(diff)))


def artistCheck() -> None:
    artists = ['AJR', 'Andrea Bocelli', 'The Beatles', 'Bleachers', 'Drake', 'Ed Sheeran', 'Eminem', 'Gryffin', 'Hardwell', 'Illenium', 'Kygo', 'Lauv',
               'Logic', 'Maroon 5', 'Martin Garrix', 'Mitis', 'OneRepublic', 'Pegboard Nerds', 'Post Malone', 'Queen', 'Taylor Swift', 'Zedd']
    user = getUser('firiusbob')
    playlists = getUserPlaylists(user)
    rpos = getPlaylist(playlists, 'Random Pool of Stuff')
    rpostracks = getTracksFromItem(rpos)
    with ThreadPoolExecutor() as executor:
        for artist in artists:
            executor.submit(artistCheckThread, artist, playlists, rpostracks)


def checkAll() -> None:
    print(artistCheck())
    print(checkWd())
    output = playlistRepeatsAll('firiusbob')
    output = [i for i in output if i[0] != 'Track']
    print(output)


def userUpToDate(userString: str) -> datetime.timedelta:
    user = getUser(userString)
    if user is None:
        return

    playlists = getUserPlaylists(user)
    trackss = []
    with ThreadPoolExecutor() as executor:
        for playlist in playlists:
            if "Top Songs of " in playlist['name'] or user['id'] != playlist['owner']['id'] or playlist['name'] in ignore or "Common Songs " in playlist['name']:
                continue
            
            executor.submit(appendTracksFromItem, playlist, trackss)

    tracks = [track for i in trackss for track in i]
    albums = {}
    for track in tracks:
        albumid = track['track']['album']['id']
        if albumid is None:
            continue

        if albumid not in albums.keys():
            releasedate = track['track']['album']['release_date']
            precision = track['track']['album']['release_date_precision']
            if precision == 'day':
                albums[albumid] = datetime.datetime.strptime(
                    releasedate, '%Y-%m-%d')
            elif precision == 'month':
                albums[albumid] = datetime.datetime.strptime(
                    releasedate, '%Y-%m')
            elif precision == 'year':
                albums[albumid] = datetime.datetime.strptime(releasedate, '%Y')
            else:
                print('uh oh')
                print(releasedate + precision)
                return

    trackidsdates = {}
    for track in tracks:
        idd = track['track']['id']
        if idd is None or track['track']['album']['id'] is None:
            continue

        dateadded = datetime.datetime.strptime(
            track['added_at'], '%Y-%m-%dT%H:%M:%SZ')
        if idd in trackidsdates.keys():
            currentdateadded = trackidsdates[idd][0]
            if currentdateadded < dateadded:
                dateadded = currentdateadded

        trackidsdates[idd] = (dateadded, track['track']['album']['id'])

    difference = []
    for v in trackidsdates.values():
        dateadded = v[0]
        albumid = v[1]
        releasedate = albums[albumid]
        difference.append(dateadded - releasedate)

    averagediff = sum(difference, datetime.timedelta(0)) / len(difference)
    return averagediff


def latestAddedSongs(userString: str) -> list[tuple[str, str]]:
    user = getUser(userString)
    if user is None:
        return

    playlists = getUserPlaylists(user)
    trackss = []
    with ThreadPoolExecutor() as executor:
        for playlist in playlists:
            if "Top Songs of " in playlist['name'] or user['id'] != playlist['owner']['id'] or playlist['name'] in ignore or "Common Songs " in playlist['name']:
                continue
            
            executor.submit(appendTracksFromItem, playlist, trackss)

    tracks = [track for i in trackss for track in i]
    dateAdded = []
    for track in tracks:
        dateadded = datetime.datetime.strptime(track['added_at'], '%Y-%m-%dT%H:%M:%SZ')
        dateAdded.append((track['track']['name'], dateadded))

    sorteddateAdded = sorted(dateAdded, key=lambda x: x[1], reverse=True)
    output = [(i, datetime.datetime.strftime(j, '%m/%d/%Y %H:%M:%S')) for i,j in sorteddateAdded]
    return output