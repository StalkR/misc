#!/usr/bin/python
# Tests for IMDb web API.

import imdb
import unittest

CACHE_DIR = '.'


class TestTitle(unittest.TestCase):

  def testItalian(self):
    tt = imdb.Title('tt0073845', cache_dir=CACHE_DIR)
    self.assertEqual(u'L\'uomo che sfid\xf2 l\'organizzazione', tt.title)
    self.assertEqual(u'El hombre que desafi\xf3 a la organizaci\xf3n',
                     tt.title_aka)
    self.assertEqual('', tt.type)
    self.assertEqual('1975', tt.year)
    self.assertEqual('1975', tt.year_production)
    self.assertEqual('1977', tt.year_release)
    self.assertEqual('4.3', tt.rating)
    self.assertEqual('87m', tt.duration)
    self.assertEqual(['Sergio Grieco'], [d.name for d in tt.directors])
    self.assertEqual(11, len(tt.actors))
    self.assertEqual(u'Alberto Dalb\xe9s', tt.actors[4].name)
    self.assertEqual(['Crime', 'Drama'], tt.genres)
    self.assertEqual(['Italian'], tt.languages)
    self.assertEqual(['Italy', 'France', 'Spain'], tt.nationalities)
    self.assertEqual('', tt.description)

  def testTv(self):
    tt = imdb.Title('tt0437803', cache_dir=CACHE_DIR)
    self.assertEqual('Alien Siege', tt.title)
    self.assertEqual(u'A F\xf6ld ostroma', tt.title_aka)
    self.assertEqual('TV Movie', tt.type)
    self.assertEqual('2005', tt.year)
    self.assertEqual('2005', tt.year_production)
    self.assertEqual('2005', tt.year_release)
    self.assertEqual('3.6', tt.rating)
    self.assertEqual('90m', tt.duration)
    self.assertEqual(1, len(tt.directors))
    self.assertEqual('Robert Stadd', tt.directors[0].name)
    self.assertEqual(15, len(tt.actors))
    self.assertEqual('Brad Johnson', tt.actors[0].name)
    self.assertEqual(['Sci-Fi'], tt.genres)
    self.assertEqual(['English'], tt.languages)
    self.assertEqual(['USA'], tt.nationalities)
    self.assertEqual('Earth is attacked by the Kulkus, a hostile alien breed '
                     'infected by a lethal virus and needing human blood to '
                     'develop an antidote...', tt.description)

  def testMultipleLanguages(self):
    tt = imdb.Title('tt1179034', cache_dir=CACHE_DIR)
    self.assertEqual('From Paris with Love', tt.title)
    self.assertEqual(['English', 'French', 'Mandarin', 'German'], tt.languages)

  def testMultipleDirectors(self):
    tt = imdb.Title('tt0133093', cache_dir=CACHE_DIR)
    self.assertEqual('The Matrix', tt.title)
    self.assertEqual(['Andy Wachowski', 'Lana Wachowski'],
                     [d.name for d in tt.directors])


class TestName(unittest.TestCase):

    def testDirector(self):
        nm = imdb.Name('nm0905152')
        self.assertEqual('Andy Wachowski', nm.name)

    def testActor(self):
        nm = imdb.Name('nm0130952')
        self.assertEqual(u'Jos\xe9 Calvo', nm.name)


if __name__ == '__main__':
    unittest.main()
