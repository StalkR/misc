<?php
if ( !defined( 'MEDIAWIKI' ) ) {
  die( 'This file is a MediaWiki extension, it is not a valid entry point' );
}

$wgExtensionCredits['other'][] = array(
  'path'           => __FILE__,
  'name'           => 'Google Analytics',
  'version'        => '1.0',
  'author'         => 'StalkR',
  'descriptionmsg' => 'Google Analytics',
  'url'            => 'https://github.com/StalkR/misc/tree/master/mediawiki/GoogleAnalytics',
);

$wgHooks['BeforePageDisplay'][] = 'GoogleAnalytics';

function GoogleAnalytics( &$out, &$skin ) {
  global $wgGoogleAnalyticsAccount;

  if (!empty($wgGoogleAnalyticsAccount)) {
    $out->AddScript("<script type=\"text/javascript\">
  var _gaq = _gaq || [];
  _gaq.push(['_setAccount', '{$wgGoogleAnalyticsAccount}']);
  _gaq.push(['_trackPageview']);

  (function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
  })();
</script>");
  }

  return true;
}
?>
