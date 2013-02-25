#!/usr/bin/python
# AlloCine web API.

import htmlentitydefs
import os
import re
import urllib

# Module global: directory to cache result pages, empty to disable.
CACHE_DIR = ''


def OpenUrl(url):

    class UrlOpener(urllib.FancyURLopener):
        version = ('Mozilla/6.0 (Windows NT 6.2; WOW64; rv:16.0.1) '
                   'Gecko/20121011 Firefox/16.0.1')

    opener = UrlOpener()
    opener.addheader('Accept-Language', 'en-US,en')
    return opener.open(url).read()


def LoadUrl(url):
    name = re.sub('[^-.\w]', '', url[7:].strip('/').replace('/', '-'))
    cache = os.path.join(CACHE_DIR, name)
    if CACHE_DIR and os.path.isfile(cache):
        content = open(cache).read()
    else:
        content = OpenUrl(url)
        if CACHE_DIR:
            open(cache, 'w').write(content)
    return content


def Decode(s):

    def DecodeEntities(m):
        entity = htmlentitydefs.entitydefs.get(m.group(1), m.group(0))
        return unichr(ord(entity))

    s = re.sub('&#([0-9a-fA-F]+);', lambda m: unichr(int(m.group(1))), s)
    s = re.sub('&#x([0-9a-fA-F]+);', lambda m: unichr(int(m.group(1), 16)), s)
    s = re.sub('&(\w+?);', DecodeEntities, s)
    return s


class Movie(object):
    """Class to represent an AlloCine Movie with its information.

    Attributes:
        id: Integer with AlloCine movie ID.

    Properties, empty when not available:
        url: Link to AlloCine page of this movie.
        name: String with movie name.
        original_name: String with original movie name if foreign movie.
        year: Integer with movie year (production or release).
        production_year: Integer with production year.
        release_year: Integer with release year.
        duration: String with duration (e.g. 1h30m).
        directors: List of strings with directors names.
        actors: List of strings with actors names.
        genres: List of strings with genre names.
        nationalities: List of strings with movie nationalities.
        rating: Float with rating (spectators or press, between 0 and 5).
        rating_spectators: Float with spectators rating.
        rating_press: Float with press rating.
    """

    def __init__(self, allocine_id):
        """Create a new AlloCine Movie object.

        Args:
            allocine_id: Integer with AlloCine movie ID.
        """
        self.id = int(allocine_id)    # Work if a string number is supplied.
        self.__page = ''

    def __repr__(self):
        return '<AlloCine %i>' % self.id

    @property
    def url(self):
        return ('http://www.allocine.fr/film/fichefilm_gen_cfilm=%i.html'
                % self.id)

    @property
    def _page(self):
        if not self._page_loaded:
            self.__page = LoadUrl(self.url).decode('utf-8')
        return self.__page

    @property
    def _page_loaded(self):
        return bool(self.__page)

    @property
    def name(self):
        m = re.search('property="og:title" content="([^"]+)"', self._page)
        return Decode(m.group(1)) if m else ''

    @property
    def original_name(self):
        m = re.search('Titre original</div></th><td>([^<]+)</td>', self._page)
        return Decode(m.group(1)) if m else self.name

    @property
    def year(self):
        if self.year_production:
            return self.year_production
        return self.year_release

    @property
    def year_production(self):
        m = re.search(' de production</div></th><td><span[^>]*>([^<]+)', self._page)
        return int(m.group(1)) if m else None

    @property
    def year_release(self):
        m = re.search('itemprop="datePublished" content="([^-"]+)', self._page)
        return int(m.group(1)) if m else None

    @property
    def duration(self):
        m = re.search('itemprop="duration" content="(?:PT)?([0-9HM]+)"', self._page)
        return m.group(1).lower() if m else ''

    @property
    def directors(self):
        regexp = 'itemprop="director" .*? itemprop="name">([^<]+)'
        return [Decode(name) for name in re.findall(regexp, self._page)]

    @property
    def actors(self):
        m = re.search('itemprop="actors" (.*)', self._page)
        if not m:
            return []
        matches = re.findall('itemprop="name">([^<]+)', m.group(1))
        return [Decode(name) for name in matches]

    @property
    def genres(self):
        matches = re.findall('itemprop="genre">([^<]+)', self._page)
        return [Decode(name) for name in matches]

    @property
    def nationalities(self):
        m = re.search('Nationalit(.*?)</div>', self._page, re.S)
        if not m:
            return []
        matches = re.findall('<span[^>]*>([^<]+)', m.group(1))
        return [Decode(n.strip()).capitalize() for n in matches]

    @property
    def rating(self):
        if self.rating_spectators:
            return self.rating_spectators
        return self.rating_press

    @property
    def rating_spectators(self):
        p = self._page.find('Spectateurs\n</span>')
        q = self._page.find('</div>', p)
        m = re.search('<span[^>]*>([0-9,]+)<', self._page[p:q])
        return float(m.group(1).replace(',', '.')) if m else None

    @property
    def rating_press(self):
        p = self._page.find('Presse\n</span>')
        q = self._page.find('</div>', p)
        m = re.search('<span[^>]*>([0-9,]+)<', self._page[p:q])
        return float(m.group(1).replace(',', '.')) if m else None
