from google.appengine.ext import db


class Title(db.Model):
    id = db.StringProperty()
    name = db.StringProperty()
    type = db.StringProperty()
    year = db.IntegerProperty()
    year_production = db.IntegerProperty()
    year_release = db.IntegerProperty()
    rating = db.StringProperty()
    duration = db.StringProperty()
    description = db.TextProperty()
    poster = db.StringProperty()
    aka = db.StringListProperty()
    genres = db.StringListProperty()
    languages = db.StringListProperty()
    nationalities = db.StringListProperty()
    directors = db.TextProperty()
    writers = db.TextProperty()
    actors = db.TextProperty()
