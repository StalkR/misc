#!/usr/bin/python
# Tests for IMDb web API.

import imdb
import unittest

imdb.CACHE_DIR = 'cache'


class TestTitle(unittest.TestCase):

  def testItalian(self):
    tt = imdb.Title('tt0073845')
    self.assertEqual(u'L\'uomo che sfid\xf2 l\'organizzazione', tt.name)
    self.assertEqual(u'El hombre que desafi\xf3 a la organizaci\xf3n', tt.aka)
    self.assertEqual('', tt.type)
    self.assertEqual(1975, tt.year)
    self.assertEqual(1975, tt.year_production)
    self.assertEqual(1977, tt.year_release)
    self.assertEqual(4.3, tt.rating)
    self.assertEqual('87m', tt.duration)
    self.assertEqual(['Sergio Grieco'], [d.name for d in tt.directors])
    self.assertEqual(['Sergio Grieco'], [w.name for w in tt.writers])
    self.assertEqual(11, len(tt.actors))
    self.assertEqual(u'Alberto Dalb\xe9s', tt.actors[4].name)
    self.assertEqual(['Crime', 'Drama'], tt.genres)
    self.assertEqual(['Italian'], tt.languages)
    self.assertEqual(['Italy', 'France', 'Spain'], tt.nationalities)
    self.assertEqual('', tt.description)

  def testTv(self):
    tt = imdb.Title('tt0437803')
    self.assertEqual('Alien Siege', tt.name)
    self.assertEqual(u'A F\xf6ld ostroma', tt.aka)
    self.assertEqual('TV Movie', tt.type)
    self.assertEqual(2005, tt.year)
    self.assertEqual(2005, tt.year_production)
    self.assertEqual(2005, tt.year_release)
    self.assertEqual(3.6, tt.rating)
    self.assertEqual('90m', tt.duration)
    self.assertEqual(['Robert Stadd'], [d.name for d in tt.directors])
    self.assertEqual(['Bill Lundy', 'Paul Salamoff'],
                     [w.name for w in tt.writers])
    self.assertEqual(15, len(tt.actors))
    self.assertEqual('Brad Johnson', tt.actors[0].name)
    self.assertEqual(['Sci-Fi'], tt.genres)
    self.assertEqual(['English'], tt.languages)
    self.assertEqual(['USA'], tt.nationalities)
    self.assertEqual('Earth is attacked by the Kulkus, a hostile alien breed '
                     'infected by a lethal virus and needing human blood to '
                     'develop an antidote...', tt.description)

  def testMultipleLanguages(self):
    tt = imdb.Title('tt1179034')
    self.assertEqual('From Paris with Love', tt.name)
    self.assertEqual(['English', 'French', 'Mandarin', 'German'], tt.languages)

  def testMultipleDirectors(self):
    tt = imdb.Title('tt0133093')
    self.assertEqual('The Matrix', tt.name)
    self.assertEqual(['Andy Wachowski', 'Lana Wachowski'],
                     [d.name for d in tt.directors])


class TestName(unittest.TestCase):

  def testDirector(self):
    nm = imdb.Name('nm0905152')
    self.assertEqual('Andy Wachowski', nm.name)

  def testActor(self):
    nm = imdb.Name('nm0130952')
    self.assertEqual(u'Jos\xe9 Calvo', nm.name)


class TestSearch(unittest.TestCase):

  def testSearchTitle(self):
    search = imdb.SearchTitle('Lord of the rings')
    self.assertEqual(sorted(['popular', 'partial', 'approx', 'exact']),
                     sorted(search.keys()))

    self.assertNotEqual(0, len(search['popular']))
    self.assertEqual('tt0120737', search['popular'][0].id)
    self.assertEqual('The Lord of the Rings: The Fellowship of the Ring',
                     search['popular'][0].name)
    self.assertEqual(2001, search['popular'][0].year)
    self.assertEqual('', search['popular'][0]._page)

    self.assertNotEqual(0, len(search['partial']))
    self.assertEqual('tt0387360', search['partial'][0].id)
    self.assertEqual('The Lord of the Rings: The Return of the King',
                     search['partial'][0].name)
    self.assertEqual(2003, search['partial'][0].year)
    self.assertEqual('', search['partial'][0]._page)

    self.assertNotEqual(0, len(search['exact']))
    self.assertEqual('tt0154789', search['exact'][0].id)
    self.assertEqual('Lord of the Rings', search['exact'][0].name)
    self.assertEqual(1990, search['exact'][0].year)
    self.assertEqual('', search['exact'][0]._page)

  def testSearchTitleApprox(self):
    search = imdb.SearchTitle('rox rouky')

    self.assertNotEqual(0, len(search['approx']))
    self.assertEqual('tt2351044', search['approx'][0].id)
    self.assertEqual('Rocky Marciano vs. Rex Layne', search['approx'][0].name)
    self.assertEqual(1951, search['approx'][0].year)
    self.assertEqual('', search['approx'][0]._page)

  def testAdvancedSearchTitle(self):
    search = imdb.AdvancedSearchTitle('27 dresses')

    self.assertEqual(2, len(search))
    self.assertEqual('tt0988595', search[0].id)
    self.assertEqual('27 Dresses', search[0].name)
    self.assertEqual(2008, search[0].year)
    # Not checking for type as it is empty and would trigger a page load.
    self.assertEqual('', search[0]._page)

    self.assertEqual('tt1204215', search[1].id)
    self.assertEqual('27 Dresses: Movie Special', search[1].name)
    self.assertEqual(2008, search[1].year)
    self.assertEqual('Documentary', search[1].type)
    self.assertEqual('', search[1]._page)

  def testAdvancedSearchTitleEncoded(self):
    search = imdb.AdvancedSearchTitle(u'The Lion King 1\xbd')
    self.assertEqual(1, len(search))
    self.assertEqual(u'The Lion King 1\xbd', search[0].name)

  def testAdvancedSearchTitleReturnsUtf8Page(self):
    search = imdb.AdvancedSearchTitle('The Three Caballeros')
    self.assertTrue(search)


if __name__ == '__main__':
  unittest.main()
