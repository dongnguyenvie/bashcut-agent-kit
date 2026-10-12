#!/usr/bin/perl
# UserPromptSubmit input on stdin → prints the prompt as one short quote when it reads like a correction of the
# agent's work ("không, dùng X", "thật ra…", "lần sau đừng…", "no, …", "actually …"), else nothing.
# Questions, long pastes, slash commands and system messages are skipped. Cheap: regexes only, no model.
use strict;
use warnings;
use utf8;
use JSON::PP;

binmode STDOUT, ':encoding(UTF-8)';
my $raw = do { local $/; <STDIN> };
my $input = eval { JSON::PP->new->utf8->decode($raw) } or exit 0;
my $prompt = $input->{prompt};
exit 0 unless defined $prompt && !ref $prompt;
$prompt =~ s/^\s+|\s+$//g;
exit 0 if $prompt eq '' || length($prompt) > 1500 || $prompt =~ /^[<\/\[]/;
my $head = lc substr($prompt, 0, 400);

my @signals = (
  # Vietnamese (with or without tone marks)
  qr/^(không|khong|ko|k|sai)\s*[,.!:]/,
  qr/\b(sai rồi|sai roi|thật ra|that ra|thực ra|thuc ra|chứ không phải|chu khong phai)\b/,
  qr/\b(lần sau|lan sau|nhớ là|nho la|nhớ đừng|đã bảo|da bao|đã nói là|bảo rồi|không phải vậy|không đúng)\b/,
  qr/\b(đừng bao giờ|dung bao gio|sao lại|sao lai)\b/,
  # English
  qr/^(no|nope|wrong)\b\s*[,.!:]/,
  qr/\b(actually|that's wrong|that is wrong|not what i (asked|meant|wanted)|i (said|told you|asked for))\b/,
  qr/\b(next time|from now on|remember (that|to)|never do|don't ever|stop doing)\b/,
);
exit 0 unless grep { $head =~ $_ } @signals;
# A question about the edit is not a correction.
exit 0 if $head =~ /\?\s*$/ && $head !~ /\b(sao lại|sao lai|why did you)\b/;

(my $quote = $prompt) =~ s/\s+/ /g;
$quote = substr($quote, 0, 160) . '…' if length($quote) > 160;
print "$quote\n";
