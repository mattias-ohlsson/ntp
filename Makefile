# Makefile for source rpm: ntp
# $Id$
NAME := ntp
SPECFILE = $(firstword $(wildcard *.spec))

include ../common/Makefile.common
