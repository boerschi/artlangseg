#!/usr/bin/python
#
# read in a frequency ordered word-list

import sys

if __name__=="__main__":
    words = []
    total = 0
    for l in sys.stdin:
        count_word = l.strip().split(" ",1)
        words.append((float(count_word[0]),count_word[1]))
        total+=float(count_word[0])
    for (c,w) in words:
        print "%s %s"%(c/total,w.replace(" ",""))
    
