use strict;
use warnings;
use Irssi;
use Irssi::Irc;
use vars qw($VERSION %IRSSI);

$VERSION = "0.0.3";
%IRSSI = (
        authors     => "Sebastian 'yath' Schmidt, Tom Wesley",
        contact     => "yathen\@web.de, tom\@tomaw.net",
        name        => "Command dispatcher",
        description => "This scripts sends unknown commands to the server",
        license     => "GNU GPLv2",
        changed     => "Tue Mar  5 14:55:29 CET 2002",
);

sub event_default_command {
        my ($command, $server) = @_;

        if ($command =~ /^\d+$/) {
                Irssi::command("window goto $command");
                Irssi::signal_stop();
                return;
        }

        return if (Irssi::settings_get_bool("dispatch_unknown_commands") == 0
                || !$server
                || $command =~ tr/\/// != 0);
        $server->send_raw($command);
        Irssi::signal_stop();
}

Irssi::settings_add_bool("misc", "dispatch_unknown_commands", 1);
Irssi::signal_add_first("default command", "event_default_command");
