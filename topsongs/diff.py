import json

def comparePlaylists(p1, p2):
    with open(p1) as f:
        playlist1 = json.load(f)

    with open(p2) as f:
        playlist2 = json.load(f)

    setplaylist1 = set(playlist1)
    setplaylist2 = set(playlist2)
    print('Same songs:')
    print(', '.join(list(setplaylist1 & setplaylist2)))
    print('\n\n\n')
    print('Different songs in first playlist:')
    print(', '.join(list(setplaylist1 - setplaylist2)))
    print('\n\n\n')
    print('Different songs in second playlist:')
    print(', '.join(list(setplaylist2 - setplaylist1)))
