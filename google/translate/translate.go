// Package translate implements translation on Google Translate.
package translate

import (
	"encoding/json"
	"errors"
	"fmt"
	"html"
	"io/ioutil"
	"net/http"
	"net/url"
)

type lresult struct {
	Data ldata
}

type ldata struct {
	Languages []Language
}

type Language struct {
	Language, Name string
}

// Languages returns the list of supported Google Translate languages for a
// given target language or empty string for all supported languages.
func Languages(target string, key string) (l []Language, e error) {
	base := "https://www.googleapis.com/language/translate/v2/languages"
	params := url.Values{}
	params.Set("key", key)
	if target != "" {
		params.Set("target", target)
	}
	resp, err := http.Get(fmt.Sprintf("%s?%s", base, params.Encode()))
	if err != nil {
		return l, err
	}
	defer resp.Body.Close()
	contents, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return l, err
	}
	var r lresult
	err = json.Unmarshal(contents, &r)
	if err != nil {
		return l, err
	}
	return r.Data.Languages, nil
}

type tresult struct {
	Data tdata
}
type tdata struct {
	Translations []Translation
}

type Translation struct {
	TranslatedText, DetectedSourceLanguage string
}

// Translate translates a text on Google Translate from a language to another.
// It requires a Google API Key (key), valid source and target languages.
// For automatic source language detection, use empty string.
func Translate(source, target, text, key string) (t Translation, e error) {
	base := "https://www.googleapis.com/language/translate/v2"
	params := url.Values{}
	params.Set("key", key)
	if source != "" {
		params.Set("source", source)
	}
	params.Set("target", target)
	params.Set("q", text)
	resp, err := http.Get(fmt.Sprintf("%s?%s", base, params.Encode()))
	if err != nil {
		return t, err
	}
	defer resp.Body.Close()
	contents, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return t, err
	}
	var r tresult
	err = json.Unmarshal(contents, &r)
	if err != nil {
		return t, err
	}
	if len(r.Data.Translations) == 0 {
		return t, errors.New("no translation")
	}
	t = r.Data.Translations[0]
	t.TranslatedText = html.UnescapeString(t.TranslatedText)
	return t, nil
}
