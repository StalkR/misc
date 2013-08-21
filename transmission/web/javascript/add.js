function Add() {}
Add.prototype = {
  ByURL: function(url) {
    remote = new TransmissionRemote(this);
    remote.addTorrentByUrl(url, { paused: false });
  },
  togglePeriodicSessionRefresh: function(enabled) {},
  refreshTorrents: function() {
    window.close();
  },
  loadDaemonPrefs: function(async) {},
};

$(document).ready(function() {
  if (location.search.length <= 1) return;
  document.body.innerText = 'Adding URL... will close when done.';
  (new Add()).ByURL(location.search.substr(1));
});
