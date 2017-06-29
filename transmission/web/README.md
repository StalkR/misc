= Add torrents to Transmission with a GET request

Last tested working with transmission 2.92.

== Setup
Copy `add.html` and `javascript/add.js` to transmission web folder.
On Debian: `/usr/share/transmission/web`.

== Usage
Visit `http://<host>/transmission/web/add.html?<torrent URL>` to add torrents.
