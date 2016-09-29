package debugger

import (
	"io/ioutil"
	"testing"
)

func TestAnalyze(t *testing.T) {
	for _, tt := range []struct {
		filename string
		want     string
		status   Status
	}{
		{
			filename: "testdata/green.htm",
			want: `# .
- [OK] Found 3 DNSKEY records for .
- [OK] DS=19036/SHA-1 verifies DNSKEY=19036/SEP
- [OK] Found 1 RRSIGs over DNSKEY RRset
- [OK] RRSIG=19036 and DNSKEY=19036/SEP verifies the DNSKEY RRset
# net
- [OK] Found 1 DS records for net in the . zone
- [OK] Found 1 RRSIGs over DS RRset
- [OK] RRSIG=46551 and DNSKEY=46551 verifies the DS RRset
- [OK] Found 2 DNSKEY records for net
- [OK] DS=35886/SHA-256 verifies DNSKEY=35886/SEP
- [OK] Found 1 RRSIGs over DNSKEY RRset
- [OK] RRSIG=35886 and DNSKEY=35886/SEP verifies the DNSKEY RRset
# stalkr.net
- [OK] Found 1 DS records for stalkr.net in the net zone
- [OK] Found 1 RRSIGs over DS RRset
- [OK] RRSIG=2480 and DNSKEY=2480 verifies the DS RRset
- [OK] Found 3 DNSKEY records for stalkr.net
- [OK] DS=4789/SHA-256 verifies DNSKEY=4789/SEP
- [OK] Found 1 RRSIGs over DNSKEY RRset
- [OK] RRSIG=4789 and DNSKEY=4789/SEP verifies the DNSKEY RRset
- [OK] stalkr.net A RR has value 37.187.31.39
- [OK] Found 1 RRSIGs over A RRset
- [OK] RRSIG=61206 and DNSKEY=61206 verifies the A RRset
`,
			status: OK,
		},
		{
			filename: "testdata/yellow.htm",
			want: `# .
- [OK] Found 3 DNSKEY records for .
- [OK] DS=19036/SHA-1 verifies DNSKEY=19036/SEP
- [OK] Found 1 RRSIGs over DNSKEY RRset
- [OK] RRSIG=19036 and DNSKEY=19036/SEP verifies the DNSKEY RRset
# net
- [OK] Found 1 DS records for net in the . zone
- [OK] Found 1 RRSIGs over DS RRset
- [OK] RRSIG=46551 and DNSKEY=46551 verifies the DS RRset
- [OK] Found 2 DNSKEY records for net
- [OK] DS=35886/SHA-256 verifies DNSKEY=35886/SEP
- [OK] Found 1 RRSIGs over DNSKEY RRset
- [OK] RRSIG=35886 and DNSKEY=35886/SEP verifies the DNSKEY RRset
# stalkr.net
- [OK] Found 1 DS records for stalkr.net in the net zone
- [OK] Found 1 RRSIGs over DS RRset
- [OK] RRSIG=2480 and DNSKEY=2480 verifies the DS RRset
- [OK] Found 3 DNSKEY records for stalkr.net
- [OK] DS=4789/SHA-256 verifies DNSKEY=4789/SEP
- [OK] Found 1 RRSIGs over DNSKEY RRset
- [OK] RRSIG=4789 and DNSKEY=4789/SEP verifies the DNSKEY RRset
- [WARNING] ns1.rollernet.us serial (2016092303) differs from ns2.rollernet.us serial (2016092304)
- [OK] stalkr.net A RR has value 37.187.31.39
- [OK] Found 1 RRSIGs over A RRset
- [OK] RRSIG=61206 and DNSKEY=61206 verifies the A RRset
`,
			status: WARNING,
		},
	} {
		b, err := ioutil.ReadFile(tt.filename)
		if err != nil {
			t.Errorf("%s: %v", tt.filename, err)
			continue
		}
		analysis, err := parse(string(b))
		if err != nil {
			t.Errorf("%s: %v", tt.filename, err)
			continue
		}
		if got := analysis.String(); got != tt.want {
			t.Errorf("%s: got %s; want %s", tt.filename, got, tt.want)
		}
		if got := analysis.Status(); got != tt.status {
			t.Errorf("%s: got %s; want %s", tt.filename, got, tt.status)
		}
	}
}
