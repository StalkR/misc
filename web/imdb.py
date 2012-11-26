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
    version = ('Mozilla/6.0 (Windows NT 6.2; WOW64; rv:16.0.1) Gecko/20121011 '
               'Firefox/16.0.1')

  opener = UrlOpener()
  opener.addheader('Accept-Language', 'en-US,en')
  return opener.open(url).read()


def LoadPage(path):
  url = 'http://www.imdb.com/%s' % path
  name = re.sub('[^-.\w]', '', url[7:].strip('/').replace('/', '-'))
  cache = os.path.join(CACHE_DIR, name + '.html')
  if CACHE_DIR and os.path.isfile(cache):
    page = open(cache).read()
  else:
    page = OpenUrl(url)
    if CACHE_DIR:
      open(cache, 'w').write(page)
  return page.decode('utf-8')


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


class Title(object):
  """Class to represent an IMDb title with its information.

  Attributes:
    id: String with IMDb title ID.

  Properties, empty when not available:
    page: String with IMDb html page of this title.
    releaseinfo: String with IMDb release info html page of this title.
    name: String with title name.
    aka: List of strings with title names this release is also known as.
    type: String with title type (e.g. 'TV Movie', usually empty for movie).
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
    url: Link to IMDb page of this title.
  """

  def __init__(self, imdb_id, name='', year=''):
    """Create a new IMDb title object.

    Args:
      imdb_id: String with IMDb title ID.
      name: String with title name if known, used if page not loaded.
      year: Integer with title year if known, used if page not loaded.
    """
    self.id = imdb_id
    self._name = name
    self._year = year
    self._page = ''
    self._releaseinfo = ''

  def __repr__(self):
    return '<IMDb %s>' % self.id

  @property
  def page(self):
    if not self._page:
      self._page = LoadPage('title/%s/' % self.id)
    return self._page

  @property
  def releaseinfo(self):
    if not self._releaseinfo:
      self._releaseinfo = LoadPage('title/%s/releaseinfo' % self.id)
    return self._releaseinfo

  @property
  def name(self):
    if not self._page and self._name:
      return self._name
    m = re.search('Title: <strong>([^<]+)</strong>', self.page)
    if not m:
      m = re.search('<meta property="og:title" content="(.*?) \(', self.page)
    return Decode(m.group(1)) if m else ''

  @property
  def aka(self):
    if 'Also Known As:</h4>' not in self.page:
      return []
    m = re.search('Also Known As \(AKA\)(.*?)</table>', self.releaseinfo, re.S)
    if not m:
      return []
    names = []
    for name in re.findall('<tr>\s*<td>([^<]+)', m.group(1)):
      names.append(Decode(name.strip()))
    return names

  @property
  def year(self):
    if not self._page and self._year:
      return self._year
    if self.year_production:
      return self.year_production
    return self.year_release

  @property
  def year_production(self):
    m = re.search('(?:\(| )([0-9]{4})(?:&\w+;)*\) - IMDb</title>', self.page)
    return int(m.group(1)) if m else None

  @property
  def year_release(self):
    m = re.search('itemprop="datePublished" datetime="([^-"]+)', self.page)
    return int(m.group(1)) if m else None

  @property
  def type(self):
    m = re.search('<div class="infobar">([^<]+)', self.page)
    return Decode(m.group(1)).strip(u'\r\n\xa0-') if m else ''

  @property
  def rating(self):
    m = re.search('star-box-giga-star">([0-9.]+)', self.page.replace('\n', ''))
    return float(m.group(1)) if m else None

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

  @property
  def url(self):
    return 'http://www.imdb.com/title/%s/' % self.id


class Name(object):
  """Class to represent an IMDb name with its information.

  Attributes:
    id: String with IMDb name ID.

  Properties, empty when not available:
    page: String with IMDb html page of this name.
    name: String with full name.
    url: Link to IMDb page of this name.
  """

  def __init__(self, imdb_id, name=''):
    """Create a new IMDb name object.

    Args:
      imdb_id: String with IMDb name ID.
      name: String with full name if known, used if page not loaded.
    """
    self.id = imdb_id
    self._name = name
    self._page = ''

  def __repr__(self):
    return '<IMDb %s>' % self.id

  @property
  def page(self):
    if not self._page:
      self._page = LoadPage('name/%s/' % self.id)
    return self._page

  @property
  def name(self):
    if not self._page and self._name:
      return self._name
    m = re.search('class="header" itemprop="name">([^<]+)', self.page)
    return Decode(m.group(1).strip()) if m else ''

  @property
  def url(self):
    return 'http://www.imdb.com/name/%s/' % self.id


def SearchTitle(title):
  """Search a title name (popular, partial, approx or exact match).

  Args:
    title: Search query to search for (title, name, episode, etc.).

  Returns:
    Dict with keys popular, partial, approx and exact, value a list of Titles.
  """
  # Sections: all, tt, ep, nm, co, kw, ch, vi, qu, bi, pl
  params = {'q': title.encode('utf-8'), 's': 'tt'}
  page = OpenUrl('http://www.imdb.com/find?%s' % urllib.urlencode(params))

  result = {'popular': [], 'partial': [], 'approx': [], 'exact': []}

  # IMDb redirects to title page when there is only one result.
  regexp = '<link rel="canonical" href="http://www.imdb.com/title/(tt[0-9]+)/"'
  match = re.search(regexp, page)
  if match:
    result['exact'] = [Title(match.group(1))]
    return result

  def ParseResults(page, section):
    results = []
    match = re.search(re.escape(section) + '(.*?)</table>', page)
    if match:
      regexp = '<a href="/title/([tt0-9]+)/"[^>]+>([^<]+)</a> \(([0-9]+)\)'
      for tt, name, year in re.findall(regexp, match.group(1)):
        results.append(Title(tt, name=Decode(name), year=int(year)))
    return results

  result['popular'] = ParseResults(page, 'Popular Titles')
  result['partial'] = ParseResults(page, 'Titles (Partial Matches)')
  result['approx'] = ParseResults(page, 'Titles (Approx Matches)')
  result['exact'] = ParseResults(page, 'Titles (Exact Matches)')
  return result
