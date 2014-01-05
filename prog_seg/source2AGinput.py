#!/usr/bin/python

import random

usage = """%prog
 (c) Mark Johnson, 26th July 2012
 modified by ben boerschinger, 25/01/2013

Prepare AG input from training data."""

import optparse, re, sys

if __name__ == '__main__':
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-s", "--segb", dest="segBound", default=" ")
    parser.add_option("-w", "--wb", dest="wBound", default=" # ")
    parser.add_option("-g", "--gold", dest="gold", default=False, action="store_true",
                      help="prepare gold evaluation data")
    parser.add_option("-l", "--lexicon", dest="lexicon")
    options, args = parser.parse_args()
    segBound = options.segBound
    wBound = options.wBound
    #lexicon = [x.strip() for x in open(options.lexicon).readlines()]
    #for l in lexicon:
	#k=random.randint(0,3)
	#if k==0:
           #print "lexentry",l
    for l in sys.stdin:
        l = l.strip().replace("<s> ","").replace(" </s>","")
        if options.gold:
            print l.replace(wBound,"??TT").replace(segBound,"").replace("??TT"," ")
        else:
            print l.replace(wBound," ").replace(segBound," ")
