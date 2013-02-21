#!/usr/bin/python
# IMDb web API.

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


def NoDups(inlist):
    outlist = []
    for element in inlist:
        if element not in outlist:
            outlist.append(element)
    return outlist


class Title(object):
    """Class to represent an IMDb title with its information.

    Attributes:
        id: String with IMDb title ID.

    Properties, empty when not available:
        url: Link to IMDb page of this title.
        name: String with title name.
        aka: List of strings with title names this release is also known as.
        type: String with title type (e.g. 'TV Series', 'TV Movie', etc.).
        year: Integer with movie year (production or release).
        production_year: Integer with production year.
        release_year: Integer with release year.
        rating: Float with rating (between 0 and 10).
        duration: String with duration (e.g. 90m).
        directors: List of directors as Name objects.
        writers: List of actors as Name objects.
        actors: List of actors as Name objects.
        genres: List of string with genre names.
        languages: List of strings with movie languages.
        nationalities: List of strings with movie nationalities.
        description: String with short movie description, if available.
        poster: Poster as a Media object.
        media: List of all Media objects.
    """

    def __init__(self, imdb_id, name='', year=''):
        """Create a new IMDb title object.

        Args:
            imdb_id: String with IMDb title ID.
            name: String with title name if known, used if page not loaded.
            year: Integer with title year if known, used if page not loaded.
        """
        if not re.match('^tt[0-9]+$', imdb_id):
            raise ValueError('Incorrect IMDb id')
        self.id = str(imdb_id.lower())
        self._name = name
        self._year = year
        self.__page = ''
        self.__releaseinfo = ''

    def __repr__(self):
        name = self.name.encode('utf-8')
        if self.year:
            name = '%s (%i)' % (name, self.year)
        return '<IMDb %s: %s>' % (self.id, name)

    @property
    def url(self):
        return 'http://www.imdb.com/title/%s' % self.id

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
        if not self._page_loaded and self._name:
            return self._name
        m = re.search('Title: <strong>([^<]+)</strong>', self._page)
        if not m:
            regexp = '<meta property=.og:title. content="(.*?) \('
            m = re.search(regexp, self._page)
        return Decode(m.group(1)) if m else ''

    @property
    def _releaseinfo(self):
        if not self.__releaseinfo:
            url = self.url + '/releaseinfo'
            self.__releaseinfo = LoadUrl(url).decode('utf-8')
        return self.__releaseinfo

    @property
    def aka(self):
        if 'Also Known As:</h4>' not in self._page:
            return []
        regexp = 'Also Known As \(AKA\)(.*?)</table>'
        m = re.search(regexp, self._releaseinfo, re.S)
        if not m:
            return []
        names = []
        for name in re.findall('<tr>\s*<td>([^<]+)', m.group(1)):
            names.append(Decode(name.strip()))
        return names

    @property
    def year(self):
        if not self._page_loaded and self._year:
            return self._year
        if self.year_production:
            return self.year_production
        return self.year_release

    @property
    def year_production(self):
        rxp = 'property=.og:title. content="[^(]+ \(.*?([0-9]{4}).*?\)" />'
        m = re.search(rxp, self._page)
        return int(m.group(1)) if m else None

    @property
    def year_release(self):
        m = re.search('itemprop="datePublished" content="([^-"]+)', self._page)
        return int(m.group(1)) if m else None

    @property
    def type(self):
        m = re.search('<div class="infobar">([^<&]+)', self._page)
        if m:
            s = m.group(1).strip()
            if s:
                return Decode(s)
        rxp = 'property=.og:title. content="[^(]+ \((.*?) [0-9]{4}.*?\)" />'
        m = re.search(rxp, self._page)
        return Decode(m.group(1).strip()) if m else ''

    @property
    def rating(self):
        regexp = 'star-box-giga-star">\s*([0-9.]+)'
        m = re.search(regexp, self._page.replace('\n', ''))
        return float(m.group(1)) if m else None

    @property
    def duration(self):
        regexp = 'itemprop="duration" datetime="(?:PT)?([0-9HM]+)"'
        m = re.search(regexp, self._page)
        return m.group(1).lower() if m else ''

    @property
    def directors(self):
        regexp = '<div class="txt-block" itemprop="director"[^>]+>(.*?)</div>'
        m = re.search(regexp, self._page, re.S)
        if not m:
            return []
        regexp = '<a href="/name/(nm[0-9]+)/.*?itemprop="name">([^<]+)'
        matches = NoDups(re.findall(regexp, m.group(1)))
        return [Name(nm, name=Decode(name)) for nm, name in matches]

    @property
    def writers(self):
        regexp = '<div class="txt-block" itemprop="creator"[^>]+>(.*?)</div>'
        m = re.search(regexp, self._page, re.S)
        if not m:
            return []
        regexp = '<a href="/name/(nm[0-9]+)/.*?itemprop="name">([^<]+)'
        matches = NoDups(re.findall(regexp, m.group(1)))
        return [Name(nm, name=Decode(name)) for nm, name in matches]

    @property
    def actors(self):
        regexp = ('<td class="itemprop" itemprop="actor".*?'
                  'href="/name/(nm[0-9]+)/.*?itemprop="name">([^<]+)')
        matches = NoDups(re.findall(regexp, self._page, re.S))
        return [Name(nm, name=Decode(name)) for nm, name in matches]

    @property
    def genres(self):
        regexp = '<div class="[^"]+" itemprop="genre">(.*?)</div>'
        m = re.search(regexp, self._page, re.S)
        if not m:
            return []
        matches = NoDups(re.findall('>(.*?)</a>', m.group(1)))
        return [Decode(genre.strip()) for genre in matches]

    @property
    def languages(self):
        regexp = 'Language:</h4>(.*?)</div>'
        m = re.search(regexp, self._page, re.S)
        if not m:
            return []
        regexp = 'itemprop=.url.>([^<]+)</a>'
        matches = NoDups(re.findall(regexp, m.group(1)))
        return [Decode(language) for language in matches]

    @property
    def nationalities(self):
        regexp = 'href="/country/[^"]+"[^>]+>([^<]+)'
        matches = NoDups(re.findall(regexp, self._page))
        return [Decode(nationality) for nationality in matches]

    @property
    def description(self):
        m = re.search('<p itemprop="description">([^<]+)', self._page)
        return Decode(m.group(1).strip()) if m else ''

    @property
    def poster(self):
        regexp = 'id="img_primary">.*?href="/media/([^/]+).*?<img src="([^"]+)'
        m = re.search(regexp, self._page, re.S)
        if not m:
            return None
        return Media(m.group(1), self, content_url=m.group(2))

    @property
    def media(self):
        raise NotImplementedError


class Name(object):
    """Class to represent an IMDb name with its information.

    Attributes:
        id: String with IMDb name ID.

    Properties, empty when not available:
        url: Link to IMDb page of this name.
        name: String with full name.
    """

    def __init__(self, imdb_id, name=''):
        """Create a new IMDb name object.

        Args:
            imdb_id: String with IMDb name ID.
            name: String with full name if known, used if page not loaded.
        """
        if not re.match('^nm[0-9]+$', imdb_id):
            raise ValueError('Incorrect IMDb id')
        self.id = str(imdb_id)
        self._name = name
        self.__page = ''

    def __repr__(self):
        return '<IMDb %s: %s>' % (self.id, self.name.encode('utf-8'))

    @property
    def url(self):
        return 'http://www.imdb.com/name/%s' % self.id

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
        if not self._page_loaded and self._name:
            return self._name
        m = re.search('class="header" itemprop="name">([^<]+)', self._page)
        return Decode(m.group(1).strip()) if m else ''


class Media(object):
    """Class to represent an IMDb media with its information.

    Attributes:
        id: String with IMDb media ID.
        title: IMDb Title it belongs to.

    Properties, empty when not available:
        url: Link to IMDb page of this media.
        content_url: Link to IMDb image of this media, full-size.
        content: IMDb image of this media, full-size.
    """

    def __init__(self, imdb_id, title, content_url=''):
        """Create a new IMDb media object.

        Args:
            imdb_id: String with IMDb media ID.
            title: Title object it belongs to.
            content_url: String with url if known, used if page not loaded.
        """
        if not re.match('^rm[0-9]+$', imdb_id):
            raise ValueError('Incorrect IMDb id')
        self.id = str(imdb_id)
        self.title = title
        self._content_url = content_url
        self.__page = ''

    def __repr__(self):
        return '<IMDb %s/%s>' % (self.id, self.title.id)

    @property
    def url(self):
        return 'http://www.imdb.com/media/%s/%s' % (self.id, self.title.id)

    @property
    def _page(self):
        if not self._page_loaded:
            self.__page = LoadUrl(self.url).decode('utf-8')
        return self.__page

    @property
    def _page_loaded(self):
        return bool(self.__page)

    @property
    def content_url(self):
        if not self._page_loaded and self._content_url:
            url = self._content_url
        else:
            m = re.search('<img id="primary-img".*?src="([^"]+)', self._page)
            url = m.group(1) if m else ''
        # Remove everything after @@ except extension for full image version.
        return re.sub('@@.*?\.jpg', '@@.jpg', url)

    @property
    def content(self):
        return LoadUrl(self.content_url) if self.content_url else ''


def SearchTitle(title):
    """Search a title name.

    Args:
        title: Search query to search for (title, name, episode, etc.).

    Returns:
        List with matching Titles.
    """
    if type(title) is unicode:
        title = title.encode('utf-8')
    # Sections: all, tt, ep, nm, co, kw, ch, vi, qu, bi, pl
    params = {'q': title, 's': 'tt'}
    url = 'http://www.imdb.com/find?%s' % urllib.urlencode(params)
    page = OpenUrl(url).decode('utf-8')

    # IMDb redirects to title page when there is only one result.
    match = re.search('<link rel="canonical" '
                      'href="http://www.imdb.com/title/(tt[0-9]+)/"', page)
    if match:
        return [Title(match.group(1))]

    results = []
    match = re.search('<table class="findList">(.*?)</table>', page, re.S)
    if match:
        regexp = '<a href="/title/(tt[0-9]+)[^>]+>([^<]+)</a> \(([0-9]+)'
        for tt, name, year in re.findall(regexp, match.group(1)):
            results.append(Title(tt, name=Decode(name), year=int(year)))
    return results
