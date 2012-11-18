#!/usr/bin/python
# Tests for AlloCine web API.

import allocine
import unittest


class TestMovie(unittest.TestCase):

  def testFrenchMovie(self):
    self.movie = allocine.Movie(16718, cache_dir='')
    self.assertEqual('1 chance sur 2', self.movie.title)
    self.assertEqual('1 chance sur 2', self.movie.original_title)
    self.assertEqual('1998', self.movie.year)
    self.assertEqual('1998', self.movie.year_release)
    self.assertEqual('1998', self.movie.year_production)
    self.assertEqual('1h50m', self.movie.duration)
    self.assertEqual('Patrice Leconte', self.movie.director)
    self.assertEqual(['Jean-Paul Belmondo', 'Alain Delon',
                      'Vanessa Paradis'], self.movie.actors)
    self.assertEqual(['Aventure'], self.movie.genres)
    self.assertEqual(u'Fran\xe7ais', self.movie.nationality)
    self.assertEqual('1.9', self.movie.rating)
    self.assertEqual('1.9', self.movie.rating_spectators)
    self.assertEqual('', self.movie.rating_press)

  def testAmericanMovie(self):
    self.movie = allocine.Movie(128377, cache_dir='')
    self.assertEqual('(500) jours ensemble', self.movie.title)
    self.assertEqual('(500) Days of Summer', self.movie.original_title)
    self.assertEqual('2009', self.movie.year)
    self.assertEqual('2009', self.movie.year_release)
    self.assertEqual('2009', self.movie.year_production)
    self.assertEqual('1h36m', self.movie.duration)
    self.assertEqual('Marc Webb', self.movie.director)
    self.assertEqual(['Joseph Gordon-Levitt', 'Zooey Deschanel',
                      'Geoffrey Arend'], self.movie.actors)
    self.assertEqual([u'Com\xe9die', 'Drame', 'Romance'], self.movie.genres)
    self.assertEqual(u'Am\xe9ricain', self.movie.nationality)
    self.assertEqual('4.0', self.movie.rating)
    self.assertEqual('4.0', self.movie.rating_spectators)
    self.assertEqual('3.3', self.movie.rating_press)

if __name__ == '__main__':
    unittest.main()
