import json
import os
import webapp2

from google.appengine.api import memcache

import imdb


def Title(q):
    titles = imdb.SearchTitle(q)
    results = []
    for t in titles:
        results.append({'id': t.id, 'name': t.name, 'year': t.year})
    return json.dumps(results)


class Handler(webapp2.RequestHandler):
    def get(self):
        s, q = self.request.get('s'), self.request.get('q')
        if not s or not q:
            self.abort(501)
        key = 's=%s&q=%s' % (s, q)
        reply = memcache.get(key)
        if not reply:
            if s == 'tt':
                reply = Title(q)
            else:
                self.abort(501)
            memcache.add(key, reply)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(reply)


app = webapp2.WSGIApplication([
    (r'/find', Handler),
], debug=os.environ.get('SERVER_SOFTWARE', '').startswith('Dev'))
