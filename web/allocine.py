#!/usr/bin/python
# AlloCine web API.

import os
import re
import urllib


class UrlOpener(urllib.FancyURLopener):
  version = ('Mozilla/6.0 (Windows NT 6.2; WOW64; rv:16.0.1) Gecko/20121011 '
             'Firefox/16.0.1')


class Movie(object):
  """Class to represent an AlloCine Movie with its information.

  Attributes:
    id: Integer with AlloCine movie ID.
    cache_dir: String with a cache directory, empty to disable.

  Properties, empty when not available:
    page: String with AlloCine html page of this movie.
    title: String with movie title.
    original_title: String with original movie title if foreign movie.
    year: String with movie year (production or release).
    production_year: String with production year.
    release_year: String with release year.
    duration: String with duration (e.g. 1h30m).
    directors: List of strings with directors names.
    actors: List of strings with actors names.
    genres: List of strings with genre names.
    nationalities: List of strings with movie nationalities.
    rating: String with rating (spectators or press, between 0 and 5).
    rating_spectators: String with spectators rating.
    rating_press: String with press rating.
  """

  def __init__(self, allocine_id, cache_dir='.'):
    """Create a new AlloCine Movie object.

    Args:
      allocine_id: Integer with AlloCine movie ID.
      cache_dir: String with a cache directory, empty to disable.
    """
    self.id = allocine_id
    self.cache_dir = cache_dir
    self._page = ''

  def __repr__(self):
    return '<AlloCine %i>' % self.id

  def _LoadPage(self):
    cache = os.path.join(self.cache_dir, '%i.html' % self.id)
    if self.cache_dir and os.path.exists(cache):
      page = open(cache).read()
    else:
      url = 'http://www.allocine.fr/film/fichefilm_gen_cfilm=%i.html' % self.id
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
    m = re.search('property="og:title" content="([^"]+)"', self.page)
    return m.group(1) if m else ''

  @property
  def original_title(self):
    m = re.search('Titre original</div></th><td>([^<]+)</td>', self.page)
    return m.group(1) if m else self.title

  @property
  def year(self):
    if self.year_production:
      return self.year_production
    return self.year_release

  @property
  def year_production(self):
    m = re.search(' de production</div></th><td><span[^>]*>([^<]+)', self.page)
    return m.group(1) if m else ''

  @property
  def year_release(self):
    m = re.search('itemprop="datePublished" content="([^-"]+)', self.page)
    return m.group(1) if m else ''

  @property
  def duration(self):
    m = re.search('itemprop="duration" content="(?:PT)?([0-9HM]+)"', self.page)
    return m.group(1).lower() if m else ''

  @property
  def directors(self):
    regexp = 'itemprop="director" .*? itemprop="name">([^<]+)'
    return re.findall(regexp, self.page)

  @property
  def actors(self):
    m = re.search('itemprop="actors" (.*)', self.page)  # This stops at \n.
    return re.findall('itemprop="name">([^<]+)', m.group(1)) if m else []

  @property
  def genres(self):
    return re.findall('itemprop="genre">([^<]+)', self.page)

  @property
  def nationalities(self):
    p = self.page.find('Nationalit')
    q = self.page.find('</div>', p)
    zone = self.page[p:q].replace('\n', '')
    return [n.capitalize() for n in re.findall('<span[^>]*>([^<]+)', zone)]

  @property
  def rating(self):
    if self.rating_spectators:
      return self.rating_spectators
    return self.rating_press

  @property
  def rating_spectators(self):
    p = self.page.find('Spectateurs\n</span>')
    q = self.page.find('</div>', p)
    m = re.search('<span[^>]*>([0-9,]+)<', self.page[p:q])
    return m.group(1).replace(',', '.') if m else ''

  @property
  def rating_press(self):
    p = self.page.find('Presse\n</span>')
    q = self.page.find('</div>', p)
    m = re.search('<span[^>]*>([0-9,]+)<', self.page[p:q])
    return m.group(1).replace(',', '.') if m else ''
