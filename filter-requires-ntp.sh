#!/bin/sh

/usr/lib/rpm/find-requires $* | egrep -v '^perl' | grep -v '/usr/bin/perl' | sort -u
