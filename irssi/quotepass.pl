use 5.006;
use strict;
use Irssi;

our $VERSION = '0.1';
our %IRSSI = (
	authors     => 'Nanuq',
	contact     => 'n/a',
	name        => 'quotepass',
	description => q"gets around Undernet's silly quote pass nonsense",
	license     => 'BSD (two clause)',
	changed     => '2008-12-12',
	url         => '',
);

my $network = 'undernet';

Irssi::signal_add 'event notice' => sub {
	my ($server, $data, $nick, $address) = @_;
	my ($target, $text) = split / :/, $data, 2;

	$server->send_raw("PASS $1")
    if $server->{'chatnet'} eq $network
		   and $target eq 'AUTH'
		   and $text =~ /QUOTE PASS (\d+)/;
}
