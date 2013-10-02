#!/usr/bin/python
# Tests for IMDb web API.

import imdb
import unittest

imdb.CACHE_DIR = ''


class TestTitle(unittest.TestCase):

    def testBadId(self):
        self.assertRaises(ValueError, imdb.Title, 'wrong')

    def testRedirectId(self):
        tt = imdb.Title('tt0437804')
        self.assertTrue(tt._page)
        self.assertEqual('tt0437803', tt.id)

    def testItalian(self):
        tt = imdb.Title('tt0073845')
        self.assertEqual(u'L\'uomo che sfid\xf2 l\'organizzazione', tt.name)
        self.assertEqual([u'Antimetopos me tin mafia',
                          u'El hombre que desafi\xf3 a la organizaci\xf3n',
                          u"L'homme qui d\xe9fia l'organisation",
                          u'One Man Against the Organization'], tt.aka)
        self.assertEqual('', tt.type)
        self.assertEqual(1975, tt.year)
        self.assertEqual(1975, tt.year_production)
        self.assertEqual(1977, tt.year_release)
        self.assertEqual('5.4', tt.rating)
        self.assertEqual('87m', tt.duration)
        self.assertEqual(['Sergio Grieco'], [d.name for d in tt.directors])
        self.assertEqual(['Sergio Grieco', 'Rafael Romero Marchent'],
                         [w.name for w in tt.writers])
        self.assertEqual(11, len(tt.actors))
        self.assertEqual(u'Alberto Dalb\xe9s', tt.actors[4].name)
        self.assertEqual(['Crime', 'Drama'], tt.genres)
        self.assertEqual(['Italian'], tt.languages)
        self.assertEqual(['Italy', 'France', 'Spain'], tt.nationalities)
        self.assertEqual('', tt.description)

    def testTv(self):
        tt = imdb.Title('tt0437803')
        self.assertEqual('Alien Siege', tt.name)
        self.assertEqual([u'A F\xf6ld ostroma', u'Alien Blood',
                          u'Alien Siege - Tod aus dem All',
                          u'Etat de si\xe8ge', u'O Perigo Alien\xedgena',
                          u'Obca krew'], tt.aka)
        self.assertEqual('TV Movie', tt.type)
        self.assertEqual(2005, tt.year)
        self.assertEqual(2005, tt.year_production)
        self.assertEqual(2005, tt.year_release)
        self.assertEqual('3.6', tt.rating)
        self.assertEqual('90m', tt.duration)
        self.assertEqual(['Robert Stadd'], [d.name for d in tt.directors])
        self.assertEqual(['Bill Lundy', 'Paul Salamoff'],
                         [w.name for w in tt.writers])
        self.assertEqual(15, len(tt.actors))
        self.assertEqual('Brad Johnson', tt.actors[0].name)
        self.assertEqual(['Sci-Fi'], tt.genres)
        self.assertEqual(['English'], tt.languages)
        self.assertEqual(['USA'], tt.nationalities)
        self.assertEqual('Earth is attacked by the Kulku', tt.description[:30])
        self.assertEqual(tt.id, tt.poster.title.id)

    def testMultipleLanguages(self):
        tt = imdb.Title('tt1179034')
        self.assertEqual('From Paris with Love', tt.name)
        self.assertEqual(['English', 'French', 'Mandarin', 'German'],
                         tt.languages)

    def testMultipleDirectors(self):
        tt = imdb.Title('tt0133093')
        self.assertEqual('The Matrix', tt.name)
        self.assertEqual(['Andy Wachowski', 'Lana Wachowski'],
                         [d.name for d in tt.directors])

    def testEmptyAka(self):
        tt = imdb.Title('tt0291830')
        self.assertEqual(u'Corps \xe0 coeur', tt.name)
        self.assertEqual([], tt.aka)

    def testYearWithHtmlOrSerie(self):
        tt = imdb.Title('tt1965639')
        self.assertEqual('El clima y las cuatro estaciones', tt.name)
        self.assertEqual(1994, tt.year)
        tt = imdb.Title('tt0086677')
        self.assertEqual('Brothers', tt.name)
        self.assertEqual(1984, tt.year)    # TV Series 1984-1989

    def testVideoGame(self):
        tt = imdb.Title('tt1371159')
        self.assertEqual('Iron Man 2', tt.name)
        self.assertEqual(2010, tt.year)
        self.assertEqual('Video Game', tt.type)

    def testPoster(self):
        tt = imdb.Title('tt0437803')
        self.assertEqual(tt.poster.id, 'rm3287190272')
        self.assertTrue(tt.poster.content_url.endswith('.jpg'))


class TestName(unittest.TestCase):

    def testBadId(self):
        self.assertRaises(ValueError, imdb.Name, 'wrong')

    def testDirector(self):
        nm = imdb.Name('nm0905152')
        self.assertEqual('Andy Wachowski', nm.name)

    def testActor(self):
        nm = imdb.Name('nm0130952')
        self.assertEqual(u'Jos\xe9 Calvo', nm.name)


class TestMedia(unittest.TestCase):

    def testMedia(self):
        rm = imdb.Media('rm1064868096', imdb.Title('tt0167261'))
        self.assertEqual('tt0167261', rm.title.id)
        self.assertTrue(rm.content_url.endswith('.jpg'))


class TestSearch(unittest.TestCase):

    def testSearchTitle(self):
        search = imdb.SearchTitle('Lord of the rings')
        self.assertTrue(len(search) > 50)

        self.assertEqual('tt0120737', search[0].id)
        self.assertEqual('The Lord of the Rings: The Fellowship of the Ring',
                         search[0].name)
        self.assertEqual(2001, search[0].year)
        self.assertFalse(search[0]._page_loaded)

    def testSearchTitleRedirect(self):
        search = imdb.SearchTitle('Rocky Marciano vs. Rex Layne')

        self.assertEqual(1, len(search))
        self.assertEqual('tt2351044', search[0].id)
        self.assertEqual('Rocky Marciano vs. Rex Layne', search[0].name)
        self.assertEqual(1951, search[0].year)

    def testSearchTitleUnicode(self):
        search1 = imdb.SearchTitle('Les Filles De L\'Oc\xc3\xa9an')
        search2 = imdb.SearchTitle(u'Les Filles De L\'Oc\xe9an')
        self.assertEqual(len(search1), len(search2))

    def testSearchWithOneTwo(self):
        search = imdb.SearchTitle('Burlesque')
        self.assertEqual('tt1126591', search[0].id)
        self.assertEqual('tt1586713', search[1].id)


if __name__ == '__main__':
    unittest.main()
