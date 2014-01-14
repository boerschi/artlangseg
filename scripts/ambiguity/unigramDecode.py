#!/usr/bin/python
# author: bborschi
# date: 29/03/13
#
# grammar has to be in CNF (add: perform transform)
# e.g.
"""0.5 S Word Words
0.15 S I
0.15 S scream
0.1 S Iscream
0.1 S for
0.3 Word I
0.3 Word scream
0.2 Word Iscream
0.2 Word for
0.15 Words I
0.15 Words scream
0.1 Words Iscream
0.1 Words for
0.5 Words Word Words"""

import sys,math

class Unigram:
    def __init__(self,gf):
        self.wprobs = {} #maps word to probability
        # p LHS RHS
        for l in open(gf,"r"):
            l = l.strip()
            l = l.split()
            p = float(l[0])
            self.wprobs[l[1]]=p
    

    def prob(self,w):
        try:
            return self.wprobs[w]
        except KeyError:
            return 0.0

    def parse(self,text):
        #we use length-addressing
        #chart[0] stores all analyses ranging from 0 to 1
        chart = [[] for i in range(len(text))]
#        chart[0] = [(w,p) for w in self.wprobs.keys() if w==text[0]]
        for slen in range(len(text)):
            w = "".join(text[:slen+1])
            p = self.prob(w)
#            print w,p
            if p>0:
#                p = math.log(p)
                chart[slen].append((-1,p))
            for spos in range(1,slen+1):
                w = "".join(text[spos:slen+1])
                p = self.prob(w)
                if p>0:
#                    p = math.log(p)
                    for (oldseg,oldp) in chart[spos-1]:
                        chart[slen].append((spos-1,oldp*p))
        return chart

def log2(x):
    return math.log(x)/math.log(2)

def findbestparse(text,chart,cell):
    wspos = cell[0]
    if wspos==-1:
        return ["".join(text)]
    else:
#        print wspos
#        print "".join(text[wspos:])
#        print chart[wspos]
#        print max(chart[wspos],key=lambda x:x[1])
        return ["".join(text[wspos+1:])]+findbestparse(text[0:wspos+1],chart,max(chart[wspos],key=lambda x:x[1]))
        

if __name__=="__main__":
    g = Unigram(sys.argv[1])
    print "entropyseg entropyall entropyred nparses \"bestparse\" p(bestparse)"
    for l in sys.stdin:
        chart = g.parse(l.strip().split())
        parses = chart[-1]
        ent = 0.0
        entropyall = log2(2**(len(l.split())-1))
        bestparse=-1
        bestp=0
        normalize = sum([x[1] for x in parses]) #[math.exp(x[1]) for x in parses]) 
        for (i,parse) in enumerate(parses):
#            p = math.exp(parse[1])/normalize
            p = parse[1]/normalize
            ent = ent - p*log2(p)
            if p>bestp:
                bestparse=parse
                bestp=p
        bestseg = findbestparse(l.strip().split(),chart,bestparse)
        bestseg.reverse()
        bestseg = " ".join(bestseg)
        try:
            entropyred = 1-ent/entropyall
        except ZeroDivisionError:
            entropyred = "NaN"
        print "%s %s %s %s \"%s\" %s"%(ent,entropyall,entropyred,len(parses),bestseg,bestp)

