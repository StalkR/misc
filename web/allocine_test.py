#!/usr/bin/python
# Tests for AlloCine web API.

import allocine
import unittest


class TestMovie(unittest.TestCase):

  def testFrenchMovie(self):
    movie = allocine.Movie(16718, cache_dir='')
    self.assertEqual('1 chance sur 2', movie.title)
    self.assertEqual('1 chance sur 2', movie.original_title)
    self.assertEqual('1998', movie.year)
    self.assertEqual('1998', movie.year_release)
    self.assertEqual('1998', movie.year_production)
    self.assertEqual('1h50m', movie.duration)
    self.assertEqual('Patrice Leconte', movie.director)
    self.assertEqual(['Jean-Paul Belmondo', 'Alain Delon',
                      'Vanessa Paradis'], movie.actors)
    self.assertEqual(['Aventure'], movie.genres)
    self.assertEqual(u'Fran\xe7ais', movie.nationality)
    self.assertEqual('1.9', movie.rating)
    self.assertEqual('1.9', movie.rating_spectators)
    self.assertEqual('', movie.rating_press)

  def testAmericanMovie(self):
    movie = allocine.Movie(128377, cache_dir='')
    self.assertEqual('(500) jours ensemble', movie.title)
    self.assertEqual('(500) Days of Summer', movie.original_title)
    self.assertEqual('2009', movie.year)
    self.assertEqual('2009', movie.year_release)
    self.assertEqual('2009', movie.year_production)
    self.assertEqual('1h36m', movie.duration)
    self.assertEqual('Marc Webb', movie.director)
    self.assertEqual(['Joseph Gordon-Levitt', 'Zooey Deschanel',
                      'Geoffrey Arend'], movie.actors)
    self.assertEqual([u'Com\xe9die', 'Drame', 'Romance'], movie.genres)
    self.assertEqual(u'Am\xe9ricain', movie.nationality)
    self.assertEqual('4.0', movie.rating)
    self.assertEqual('4.0', movie.rating_spectators)
    self.assertEqual('3.3', movie.rating_press)

if __name__ == '__main__':
    unittest.main()
