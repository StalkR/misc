#!/usr/bin/python
# IMDb web API.

import htmlentitydefs
import os
import re
import urllib


def Decode(s):
  def DecodeEntities(m):
    return unichr(ord(htmlentitydefs.entitydefs.get(m.group(1), m.group(0))))

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


class UrlOpener(urllib.FancyURLopener):
  version = ('Mozilla/6.0 (Windows NT 6.2; WOW64; rv:16.0.1) Gecko/20121011 '
             'Firefox/16.0.1')


class Title(object):
  """Class to represent an IMDb title with its information.

  Attributes:
    id: String with IMDb title ID.
    cache_dir: String with a cache directory, empty to disable.

  Properties, empty when not available:
    page: String with IMDb html page of this title.
    name: String with title name.
    aka: String with also known as title name.
    type: String with title type (e.g. 'TV Movie', usually empty for movie).
    year: String with movie year (production or release).
    production_year: String with production year.
    release_year: String with release year.
    rating: String with rating (between 0 and 10).
    duration: String with duration (e.g. 90m).
    directors: List of directors as Name objects.
    writers: List of actors as Name objects.
    actors: List of actors as Name objects.
    genres: List of string with genre names.
    languages: List of strings with movie languages.
    nationalities: List of strings with movie nationalities.
    description: String with short movie description, if available.
  """

  def __init__(self, imdb_id, name='', year='', ttype='', cache_dir='.'):
    """Create a new IMDb title object.

    Args:
      imdb_id: String with IMDb title ID.
      name: String with title name if known, used if page not loaded.
      year: String with title year if known, used if page not loaded.
      ttype: String with title type if known, used if page not loaded.
      cache_dir: String with a cache directory, empty to disable.
    """
    self.id = imdb_id
    self._name = name
    self._year = year
    self._type = ttype
    self.cache_dir = cache_dir
    self._page = ''

  def __repr__(self):
    return '<IMDb %s>' % self.id

  def _LoadPage(self):
    cache = os.path.join(self.cache_dir, '%s.html' % self.id)
    if self.cache_dir and os.path.exists(cache):
      page = open(cache).read()
    else:
      url = 'http://www.imdb.com/title/%s/' % self.id
      page = UrlOpener().open(url).read()
      if self.cache_dir:
        open(cache, 'w').write(page)
    return page.decode('utf-8')

  @property
  def page(self):
    if not self._page:
      self._page = self._LoadPage()
    return self._page

  @property
  def name(self):
    if not self._page and self._name:
      return self._name
    m = re.search('Title: <strong>([^<]+)</strong>', self.page)
    return Decode(m.group(1)) if m else ''

  @property
  def aka(self):
    m = re.search('Also Known As:</h4> (.*)', self.page)
    return Decode(m.group(1)) if m else ''

  @property
  def year(self):
    if not self._page and self._year:
      return self._year
    if self.year_production:
      return self.year_production
    return self.year_release

  @property
  def year_production(self):
    m = re.search('\((?:<a[^>]*>)?([0-9]+)(?:</a>)?\)</span>', self.page)
    return m.group(1) if m else ''

  @property
  def year_release(self):
    m = re.search('itemprop="datePublished" datetime="([^-"]+)', self.page)
    return m.group(1) if m else ''

  @property
  def type(self):
    if not self._page and self._type:
      return self._type
    m = re.search('<div class="infobar">([^<]+)', self.page)
    return Decode(m.group(1)).strip(u'\r\n\xa0-') if m else ''

  @property
  def rating(self):
    m = re.search('star-box-giga-star">([0-9.]+)', self.page.replace('\n', ''))
    return m.group(1) if m else ''

  @property
  def duration(self):
    m = re.search('itemprop="duration" datetime="(?:PT)?([0-9HM]+)"', self.page)
    return m.group(1).lower() if m else ''

  @property
  def directors(self):
    regexp = 'href="/name/([nm0-9]+)/" +itemprop="director"[^>]*>([^<]+)'
    matches = NoDups(re.findall(regexp, self.page))
    return [Name(nm, name=Decode(name)) for nm, name in matches]

  @property
  def writers(self):
    m = re.search('Writers:\s*</h4>(.*?)</div>', self.page, re.S)
    if not m:
      return []
    regexp = 'href="/name/([nm0-9]+)/".*?>([^<]+)'
    matches = NoDups(re.findall(regexp, m.group(1)))
    return [Name(nm, name=Decode(name)) for nm, name in matches]

  @property
  def actors(self):
    regexp = 'td class="name">.*?href="/name/([nm0-9]+)/".*?>([^<]+)'
    matches = NoDups(re.findall(regexp, self.page, re.S))
    return [Name(nm, name=Decode(name)) for nm, name in matches]

  @property
  def genres(self):
    matches = NoDups(re.findall('itemprop="genre"\s*>([^<]+)', self.page))
    return [Decode(genre) for genre in matches]

  @property
  def languages(self):
    matches = NoDups(re.findall('itemprop="inLanguage"\s*>([^<]+)', self.page))
    return [Decode(language) for language in matches]

  @property
  def nationalities(self):
    regexp = 'href="/country/[^"]+"[^>]+>([^<]+)'
    matches = NoDups(re.findall(regexp, self.page))
    return [Decode(nationality) for nationality in matches]

  @property
  def description(self):
    m = re.search('<p itemprop="description">([^<]+)', self.page)
    return Decode(m.group(1).strip()) if m else ''


class Name(object):
  """Class to represent an IMDb name with its information.

  Attributes:
    id: String with IMDb name ID.
    cache_dir: String with a cache directory, empty to disable.

  Properties, empty when not available:
    page: String with IMDb html page of this name.
    name: String with full name.
  """

  def __init__(self, imdb_id, name='', cache_dir='.'):
    """Create a new IMDb name object.

    Args:
      imdb_id: String with IMDb name ID.
      name: String with full name if known, used if page not loaded.
      cache_dir: String with a cache directory, empty to disable.
    """
    self.id = imdb_id
    self._name = name
    self.cache_dir = cache_dir
    self._page = ''

  def __repr__(self):
    return '<IMDb %s>' % self.id

  def _LoadPage(self):
    cache = os.path.join(self.cache_dir, '%s.html' % self.id)
    if self.cache_dir and os.path.exists(cache):
      page = open(cache).read()
    else:
      url = 'http://www.imdb.com/name/%s/' % self.id
      page = UrlOpener().open(url).read()
      if self.cache_dir:
        open(cache, 'w').write(page)
    return page.decode('utf-8')

  @property
  def page(self):
    if not self._page:
      self._page = self._LoadPage()
    return self._page

  @property
  def name(self):
    if not self._page and self._name:
      return self._name
    m = re.search('class="header" itemprop="name">([^<]+)', self.page)
    return Decode(m.group(1).strip()) if m else ''


def SearchTitle(title):
  # From http://www.imdb.com/search/title - all except TV Episode, Video Game
  types = ('feature', 'tv_movie', 'tv_series', 'tv_special', 'mini_series',
           'documentary', 'short', 'video', 'unknown')
  params = {'title': title, 'title_type': ','.join(types)}
  url = 'http://www.imdb.com/search/title?%s' % urllib.urlencode(params)
  page = UrlOpener().open(url).read().decode('utf-8')
  regexp = ('<a href="/title/([tt0-9]+)/">([^<]+)</a>\s*'
            '<span class="year_type">\(([0-9]+)\s?(.*?)\)')
  results = []
  for tt, name, year, ttype in re.findall(regexp, page):
    results.append(Title(tt, name=name, year=year, ttype=ttype))
  return results
