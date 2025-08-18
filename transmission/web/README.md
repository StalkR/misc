= Add torrents to Transmission with a GET request

Last tested working with transmission 4.1.0.

== Setup
Copy `add.html` to transmission web folder.
On Debian 13 Trixie: `/usr/share/transmission/public_html`.

== Usage
Visit `http://<host>/transmission/web/add.html?<torrent URL>` to add torrents.
