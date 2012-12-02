#!/usr/bin/python
# Tests for AlloCine web API.

import allocine
import unittest

allocine.CACHE_DIR = ''


class TestMovie(unittest.TestCase):

    def testFrench(self):
        movie = allocine.Movie(16718)
        self.assertEqual('1 chance sur 2', movie.name)
        self.assertEqual('1 chance sur 2', movie.original_name)
        self.assertEqual(1998, movie.year)
        self.assertEqual(1998, movie.year_production)
        self.assertEqual(1998, movie.year_release)
        self.assertEqual('1h50m', movie.duration)
        self.assertEqual(['Patrice Leconte'], movie.directors)
        self.assertEqual(['Jean-Paul Belmondo', 'Alain Delon',
                         'Vanessa Paradis'], movie.actors)
        self.assertEqual(['Aventure'], movie.genres)
        self.assertEqual([u'Fran\xe7ais'], movie.nationalities)
        self.assertEqual(1.9, movie.rating)
        self.assertEqual(1.9, movie.rating_spectators)
        self.assertEqual(None, movie.rating_press)

    def testAmerican(self):
        movie = allocine.Movie(128377)
        self.assertEqual('(500) jours ensemble', movie.name)
        self.assertEqual('(500) Days of Summer', movie.original_name)
        self.assertEqual(2009, movie.year)
        self.assertEqual(2009, movie.year_production)
        self.assertEqual(2009, movie.year_release)
        self.assertEqual('1h36m', movie.duration)
        self.assertEqual(['Marc Webb'], movie.directors)
        self.assertEqual(['Joseph Gordon-Levitt', 'Zooey Deschanel',
                         'Geoffrey Arend'], movie.actors)
        self.assertEqual([u'Com\xe9die', 'Drame', 'Romance'], movie.genres)
        self.assertEqual([u'Am\xe9ricain'], movie.nationalities)
        self.assertEqual(4.0, movie.rating)
        self.assertEqual(4.0, movie.rating_spectators)
        self.assertEqual(3.3, movie.rating_press)

    def testMultipleDirectors(self):
        movie = allocine.Movie(19776)
        self.assertEqual('Matrix', movie.name)
        self.assertEqual(['Larry Wachowski', 'Andy Wachowski'],
                         movie.directors)

    def testMultipleNationalities(self):
        movie = allocine.Movie(135259)
        self.assertEqual('From Paris With Love', movie.name)
        self.assertEqual([u'Am\xe9ricain', u'Fran\xe7ais'],
                         movie.nationalities)

    def testEncodedName(self):
        movie = allocine.Movie(57615)
        self.assertEqual('La marche de l\'empereur', movie.name)


if __name__ == '__main__':
    unittest.main()
