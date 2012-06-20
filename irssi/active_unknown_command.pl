#!/usr/bin/perl -w
use strict;
use Irssi;
use vars qw($VERSION %IRSSI);

$VERSION = "0.1";

%IRSSI = (
    authors     => 'StalkR',
    contact     => 'stalkr@stalkr.net',
    name        => 'active_unknown_command.pl',
    description => 'This script shows server "unknown commands" into the active window (dispatch.pl recommended).',
    license     => 'GNU General Public License',
    url         => 'https://github.com/StalkR/misc/blob/master/irssi/active_unknown_command.pl',
    changed     => 'Fri Jan  7 13:51:06 CET 2011',
);

Irssi::theme_register([
    'active_unknown_command_loaded', '%R>>%n %_Scriptinfo:%_ Loaded $0 version $1 by $2.',
    'active_unknown_command', '%_$0:%_ $1'
]);

sub event_421 {
    my ($server, $data) = @_;
    my ($cmd, $msg);
    if ($data =~ /^\S+ (\S+) :(.*)/) {
        $cmd = $1;
        $msg = $2;
        my $awin = Irssi::active_win();
        # it is already displayed in status with server name, therefore do not
        if ($awin->{active}->{name} ne "") {
            $awin->printformat(MSGLEVEL_CLIENTCRAP, 'active_unknown_command', $cmd, $msg);
        }
    }
}

Irssi::signal_add("event 421", "event_421");
Irssi::printformat(MSGLEVEL_CLIENTCRAP, 'active_unknown_command_loaded', $IRSSI{name}, $VERSION, $IRSSI{authors});
