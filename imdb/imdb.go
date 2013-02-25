package imdb

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"net/url"
	"strings"
)

type Result struct {
	Id, Name string
	Year     int
}

type Title struct {
	Id, Name, Type, Rating, Duration, Description, Poster string
	Year, Year_production, Year_release                   int
	Aka, Genres, Languages, Nationalities                 []string
	Directors, Writers, Actors                            []Name
}

type Name struct {
	Id, Name string
}

func (t *Title) String() string {
	var infos []string
	name := t.Name
	if t.Year != 0 {
		name = fmt.Sprintf("%s (%d)", name, t.Year)
	}
	infos = append(infos, name)
	if len(t.Genres) > 0 {
		infos = append(infos, strings.Join(t.Genres[:3], ", "))
	}
	if len(t.Directors) > 0 {
		max := len(t.Directors)
		if max > 3 {
			max = 3
		}
		var directors []string
		for _, director := range t.Directors {
			directors = append(directors, director.String())
		}
		infos = append(infos, strings.Join(directors, ", "))
	}
	if len(t.Actors) > 0 {
		max := len(t.Actors)
		if max > 3 {
			max = 3
		}
		var actors []string
		for _, actor := range t.Actors[:max] {
			actors = append(actors, actor.String())
		}
		infos = append(infos, strings.Join(actors, ", "))
	}
	if t.Duration != "" {
		infos = append(infos, t.Duration)
	}
	if t.Rating != "" {
		infos = append(infos, t.Rating)
	}
	infos = append(infos, fmt.Sprintf("http://www.imdb.com/title/%s", t.Id))
	infos = append(infos, "tg")
	return strings.Join(infos, " - ")
}

func (n *Name) String() string {
	return n.Name
}

// NewTitle obtains a Title ID with its information and returns a Title.
func NewTitle(id string) (t Title, e error) {
	base := "http://movie-db-api.appspot.com/title"
	resp, err := http.Get(fmt.Sprintf("%s/%s", base, id))
	if err != nil {
		return t, err
	}
	defer resp.Body.Close()
	contents, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return t, err
	}
	err = json.Unmarshal(contents, &t)
	if err != nil {
		return t, err
	}
	return t, nil
}

// FindTitle searches a Title and returns a list of Result.
func FindTitle(q string) (r []Result, e error) {
	base := "http://movie-db-api.appspot.com/find"
	params := url.Values{}
	params.Set("s", "tt")
	params.Set("q", q)
	resp, err := http.Get(fmt.Sprintf("%s?%s", base, params.Encode()))
	if err != nil {
		return r, err
	}
	defer resp.Body.Close()
	contents, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return r, err
	}
	err = json.Unmarshal(contents, &r)
	if err != nil {
		return r, err
	}
	return r, nil
}
