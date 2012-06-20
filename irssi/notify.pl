#!/usr/bin/perl -w
# This script appends notifications to file for:
#  - public channel: hilight or mention (nick: message)
#  - private message
#  - dcc request
# Notifications consists of two lines (title, message).
# Up to the user how to display the notifications.
# For instance, use tail over ssh then notify-send.

use Irssi;
use vars qw($VERSION %IRSSI);

$VERSION = "0.1";
%IRSSI = (
    authors     => 'StalkR',
    contact     => 'stalkr@stalkr.net',
    name        => 'notify.pl',
    description => 'This script appends notifications to file for later display.',
    license     => 'GNU General Public License',
    url         => 'https://github.com/StalkR/misc/blob/master/irssi/notify.pl',
    changed     => 'Thu Apr 19 21:41:58 CEST 2012',
);

Irssi::settings_add_str('notify', 'notify_file', '~/.irssi/notifications');
Irssi::settings_add_bool('notify', 'notify_active', 0);

sub notify {
    my ($server, $summary, $message) = @_;

    my $file = Irssi::settings_get_str('notify_file');
    $file =~ s/~/$ENV{HOME}/;
    if (!open(FILE, ">>" . $file)) {
      Irssi::active_win()->print("Failed to write notification $file", MSGLEVEL_NOTICES);
    } else {
      print FILE "$summary\n$message\n";
      close(FILE);
    }
}

sub print_text_notify {
    my ($dest, $text, $stripped) = @_;
    my $server = $dest->{server};

    return if (!$server);

    # display for hilights + mentions (nick: message)
    if (($dest->{level} & MSGLEVEL_HILIGHT) &&
        ($dest->{level} & MSGLEVEL_NOHILIGHT) == 0)
    {
        my $sender = $stripped;
        $sender =~ s/^\<.([^\>]+)\>.+/$1/;
        $stripped =~ s/^\<.[^\>]+\>.//;
        my $summary = $dest->{target} . ": " . $sender;
        notify($server, $summary, $stripped);
    }
}

sub message_private_notify {
    my ($server, $msg, $nick, $address) = @_;
    return if (!$server);

    # do not notify when active window is the same
    return if (Irssi::settings_get_bool('notify_active') == 0 &&
               (Irssi::active_win()->{active}->{name} eq $nick));

    notify($server, "PM from ".$nick, $msg);
}

sub dcc_request_notify {
    my ($dcc, $sendaddr) = @_;
    my $server = $dcc->{server};

    return if (!$dcc);
    notify($server, "DCC ".$dcc->{type}." request", $dcc->{nick});
}

Irssi::signal_add('print text', 'print_text_notify');
Irssi::signal_add('message private', 'message_private_notify');
Irssi::signal_add('dcc request', 'dcc_request_notify');
