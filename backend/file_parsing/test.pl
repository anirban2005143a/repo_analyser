use strict;
use warnings;

print "Enter numbers separated by spaces: ";
my $input = <STDIN>;
chomp $input;

my @numbers = split /\s+/, $input;

if (!@numbers) {
    print "No numbers entered.\n";
    exit;
}

my $count = scalar @numbers;
my $sum = 0;

foreach my $number (@numbers) {
    if ($number =~ /^-?\d+(?:\.\d+)?$/) {
        $sum += $number;
    } else {
        print "Invalid number: $number\n";
        exit;
    }
}

my $average = $sum / $count;

my $min = $numbers[0];
my $max = $numbers[0];

foreach my $number (@numbers) {
    $min = $number if $number < $min;
    $max = $number if $number > $max;
}

print "\nResults:\n";
print "--------------------\n";
print "Count   : $count\n";
print "Sum     : $sum\n";
print "Average : $average\n";
print "Minimum : $min\n";
print "Maximum : $max\n";
print "--------------------\n";

print "\nNumbers in ascending order:\n";

my @sorted = sort { $a <=> $b } @numbers;

foreach my $number (@sorted) {
    print "$number ";
}

print "\n";

print "\nNumbers in descending order:\n";

@sorted = sort { $b <=> $a } @numbers;

foreach my $number (@sorted) {
    print "$number ";
}

print "\n";

my $positive = 0;
my $negative = 0;
my $zero = 0;

foreach my $number (@numbers) {
    if ($number > 0) {
        $positive++;
    } elsif ($number < 0) {
        $negative++;
    } else {
        $zero++;
    }
}

print "\nPositive numbers: $positive\n";
print "Negative numbers: $negative\n";
print "Zeroes: $zero\n";
