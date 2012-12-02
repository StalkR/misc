#!/usr/bin/python
# Search a title on IMDb and display a nice line.

import imdb
import sys


def main(argv):
    if len(argv) < 2:
        print 'Usage: %s <search query>' % argv[0]
        raise SystemExit(0)

    result = imdb.SearchTitle(' '.join(argv[1:]))
    if not result:
        print 'Not found.'
        raise SystemExit(1)

    t = result[0]
    infos = [t.name + (' (%i)' % t.year if t.year else '')]
    if t.genres:
        infos.append(', '.join(t.genres[:3]))
    if t.directors:
        infos.append(', '.join(d.name for d in t.directors[:2]))
    if t.actors:
        infos.append(', '.join(a.name for a in t.actors[:3]))
    if t.duration:
        infos.append(t.duration)
    if t.rating:
        infos.append('%.1f/10' % t.rating)
    infos.extend([t.url, 'tg'])
    print ' - '.join(infos)


if __name__ == '__main__':
    main(sys.argv)
