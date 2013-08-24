// ==UserScript==
// @match http://thepiratebay.se/*
// @match https://thepiratebay.se/*
// @match http://thepiratebay.sx/*
// @match https://thepiratebay.sx/*
// ==/UserScript==

// Change this to your Transmission web add
var addURL = 'https://example.com/transmission/web/add.html?';

// Transmission favicon
var icon = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAABwlBMVEVWWFT///+VAgJVV1OUAACUAABiZGCVAACUAACUAACUAACWAgI6S0lWWFSXAgJXWFVUVlNYWlZVV1NWWFRYWlaTAACWAABVV1NZW1dVV1NVV1NaXFhVV1OTAwOVAACTAACWAABVV1NVV1N4TEl6SEWVAABtb2tVV1NucGx7fXlVV1NVV1N9f3tVV1OTAABeYFxaXFhaXFhdX1tcXlpbXVlaXFhYWlZXWVVXWVVVV1NVV1NXWVXZ3tftRUWzAABVV1NmaGRnaWWAg35YWlZvcW3V2tNmaGUuNDbX3NXT2dK9wr1paWWMjot/gn2Ji4c5PkCQko66vbZWWFStAAAxNzl0eHOLjYngQUHS1M9YXFppaGSHiYaEh4JtcnA0Ojw2Oz2xAwNobm2Pk42Bg3+OkY3R086Agn7k5OJ+f3yeopxoaGRZW1dIS0lESUhBR0dsbmuprad2eHSRk49dX1uSlJHm5uRvcm21urO2u7VFSkhARERVWlrN0szBxb6Zm5erAADpRkaQko9dYFvLz8lARkdzeHaYmpeWmJRrb2pnaWZbXVnlRUV8f3qBhH9/gn6tsq02PD1aXVu5vLW4u7RZXFhaXFh10GDHAAAAPHRSTlP8APwI9/bv4P3xZO8Q/ez8/L8B+5/38wf1Hxv0A/fc/HY7OP7+YvFY8fp0cfpUUhCZlLy52tfw76X9/MUay33AAAAA90lEQVR4Xk3I03IEQRhA4b+nF7Ft20ZrZtbe2LZt2877pnOTyrk5VR+gnHBFUfKFKJCLKkSAQh4pPXNvzwpKaW+ShOxOxsYG+qYFY+w0VEKY2WjIXAgGRaLBmFUlASVjXK1KiMAYIwkJkQDRvxADALFxkBE/ZVl8sH18iq/v1Y2UVEhLv9Wt5F1V+52OzS1TLuSZAneE2Dt4l5N09xQVQ2XJ4NDwyCjnfvv4xGRpGZRXzM2/vi1xvrziWlv31UCtZ2eX7Pn3Dw6PyLHtpA7qzy8uCXFdXTsIseo3DdDos+h/3QeaoPnp+UXTtBmZ16tpAC2t8K+29h9ExT07kGyHzgAAAABJRU5ErkJggg==';

var links = document.getElementsByTagName('a');
var todo = [];
for (i = 0; i < links.length; i++) {
  if (links[i].href.indexOf('magnet:') != -1) {
    todo.push(links[i]);
  }
}

todo.forEach(function(a) {
  a.parentNode.innerHTML += ' <a style="background: none; padding: 0; border: 0;" href="' + addURL + a.href + '"><img width="16" height="16" src="' + icon + '" /></a>';
});
