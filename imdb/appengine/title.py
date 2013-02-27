import json
import os
import webapp2

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.runtime import apiproxy_errors

import imdb
import models


class Title(object):
    @classmethod
    def FromImdb(cls, tid):
        i = imdb.Title(tid)
        if not i.name:
            return None
        t = cls()
        t.id = i.id
        t.name = i.name
        t.type = i.type
        t.year = i.year
        t.year_production = i.year_production
        t.year_release = i.year_release
        t.rating = i.rating
        t.duration = i.duration
        t.description = i.description
        t.poster = i.poster.content_url if i.poster else ''
        t.aka = i.aka
        t.genres = i.genres
        t.languages = i.languages
        t.nationalities = i.nationalities
        t.directors = [{'id': d.id, 'name': d.name} for d in i.directors]
        t.writers = [{'id': w.id, 'name': w.name} for w in i.writers]
        t.actors = [{'id': a.id, 'name': a.name} for a in i.actors]
        return t

    @classmethod
    def FromDataStore(cls, tid):
        ds = db.get(db.Key.from_path('Title', tid))
        if not ds:
            return None
        t = cls()
        t.id = ds.id
        if ds.id != tid:
            return t
        t.name = ds.name
        t.type = ds.type
        t.year = ds.year
        t.year_production = ds.year_production
        t.year_release = ds.year_release
        t.rating = ds.rating
        t.duration = ds.duration
        t.description = ds.description
        t.poster = ds.poster
        t.aka = ds.aka
        t.genres = ds.genres
        t.languages = ds.languages
        t.nationalities = ds.nationalities
        t.directors = json.loads(ds.directors)
        t.writers = json.loads(ds.writers)
        t.actors = json.loads(ds.actors)
        return t

    def ToDataStore(self, tid):
        ds = models.Title(key_name=tid)
        ds.id = self.id
        if self.id == tid:
            ds.name = self.name
            ds.type = self.type
            ds.year = self.year
            ds.year_production = self.year_production
            ds.year_release = self.year_release
            ds.rating = self.rating
            ds.duration = self.duration
            ds.description = self.description
            ds.poster = self.poster
            ds.aka = self.aka
            ds.genres = self.genres
            ds.languages = self.languages
            ds.nationalities = self.nationalities
            ds.directors = json.dumps(self.directors)
            ds.writers = json.dumps(self.writers)
            ds.actors = json.dumps(self.actors)
        try:
            ds.put()
        except apiproxy_errors.CapabilityDisabledError:
            pass


class Handler(webapp2.RequestHandler):
    def get(self, tid):
        reply = memcache.get(tid)
        if not reply:
            t = Title.FromDataStore(tid)
            if not t:
                t = Title.FromImdb(tid)
                if t:
                    t.ToDataStore(tid)
            if not t:
                reply = '404'
            elif t.id != tid:
                reply = t.id
            else:
                reply = json.dumps(t.__dict__, indent=2)
            memcache.add(tid, reply)
        if reply == '404':
            self.abort(404)
        if reply.startswith('tt'):
            self.redirect('/title/%s' % reply)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(reply)


app = webapp2.WSGIApplication([
    (r'/title/(tt\d+)', Handler),
], debug=os.environ.get('SERVER_SOFTWARE', '').startswith('Dev'))
