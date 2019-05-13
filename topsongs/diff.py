import json

def comparePlaylists(p1, p2):
    with open(p1) as f:
        playlist1 = json.load(f)

    with open(p2) as f:
        playlist2 = json.load(f)

    setplaylist1 = set(playlist1)
    setplaylist2 = set(playlist2)
    print 'Same songs:'
    print setplaylist1 & setplaylist2
    print 'Different songs in first playlist:'
    print setplaylist1 - setplaylist2
    print 'Different songs in second playlist:'
    print setplaylist2 - setplaylist1
