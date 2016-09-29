package debugger

import (
	"fmt"
	"html"
	"regexp"
)

var (
	// domain groups, e.g. "." then ".com" then "example.com"
	headerRE = regexp.MustCompile(`(?s)<TD CLASS="T1L">(.*?)</TD>(.*?)</TABLE>`)
	// checks in a group, e.g. found keys, rrsig, etc.
	checkRE = regexp.MustCompile(`(?s)<tr class="L0".*?>\s*<td><img.*?src="([^"]+)".*?/></td>\s*<td>(.*?)</td>\s*</tr>`)
)

func parse(p string) (Analysis, error) {
	headers := headerRE.FindAllStringSubmatch(p, -1)
	if headers == nil {
		return nil, fmt.Errorf("debugger: headers not found")
	}
	var analysis Analysis
	for _, header := range headers {
		domain := header[1]
		checks := checkRE.FindAllStringSubmatch(header[2], -1)
		if checks == nil {
			return nil, fmt.Errorf("debugger: checks not found")
		}
		var results []Result
		for _, check := range checks {
			var status Status
			switch check[1] {
			case "/green.png":
				status = OK
			case "/yellow.png":
				status = WARNING
			case "/red.png":
				status = ERROR
			default:
				return nil, fmt.Errorf("debugger: unknown status color %q", check[1])
			}
			results = append(results, Result{
				Status:  status,
				Details: html.UnescapeString(stripTags(check[2])),
			})
		}
		analysis = append(analysis, Domain{
			Name:    domain,
			Results: results,
		})
	}
	return analysis, nil
}

var htmlTagsRE = regexp.MustCompile(`<[^>]*>`)

// stripTags removes all HTML tags in a string.
func stripTags(s string) string {
	return htmlTagsRE.ReplaceAllString(s, "")
}
