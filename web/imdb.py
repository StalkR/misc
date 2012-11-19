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
    title: String with title name.
    title_aka: String with also known as title name.
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

  def __init__(self, imdb_id, cache_dir='.'):
    """Create a new IMDb title object.

    Args:
      imdb_id: String with IMDb title ID.
      cache_dir: String with a cache directory, empty to disable.
    """
    self.id = imdb_id
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
  def title(self):
    m = re.search('Title: <strong>([^<]+)</strong>', self.page)
    return Decode(m.group(1)) if m else ''

  @property
  def title_aka(self):
    m = re.search('Also Known As:</h4> (.*)', self.page)
    return Decode(m.group(1)) if m else ''

  @property
  def type(self):
    m = re.search('<div class="infobar">([^<]+)', self.page)
    return Decode(m.group(1)).strip(u'\r\n\xa0-') if m else ''

  @property
  def year(self):
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
    matches = re.findall(regexp, self.page)
    return [Name(nm, name=Decode(name)) for nm, name in matches]

  @property
  def writers(self):
    m = re.search('href="/name/([nm0-9]+)/" +itemprop="director"', self.page)
    return Name(m.group(1)) if m else None

  @property
  def actors(self):
    regexp = 'class="name">.*?href="/name/([nm0-9]+)/".*?>([^<]+)'
    matches = re.findall(regexp, self.page, re.S)
    return [Name(nm, name=Decode(name)) for nm, name in matches]

  @property
  def genres(self):
    return re.findall('itemprop="genre"\s*>([^<]+)', self.page)

  @property
  def languages(self):
    return re.findall('itemprop="inLanguage"\s*>([^<]+)', self.page)

  @property
  def nationalities(self):
    return re.findall('href="/country/[^"]+"[^>]+>([^<]+)', self.page)

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
      name: String with full name if known (used if page not loaded).
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
