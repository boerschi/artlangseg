"""
  calculates statistics of a corpus
"""

import sys
from math import sqrt,log

def frequencyTable(l):
    res = {}
    for u in l:
        for w in u.split(" # "):
            res[w] = res.get(w,0)+1
    return res

if __name__=="__main__":
    corpus = [l.strip() for l in sys.stdin if len(l.strip())>0]
    nTokens = sum(len(x.split(" # ")) for x in corpus)
    avgWU = nTokens/float(len(corpus))
    varAvgWU = sum((len(x.split(" # "))-avgWU)**2 for x in corpus)/float(len(corpus))
    counts = frequencyTable(corpus)
    sys.stdout.write("Words:\t\t\t%d\n"%(nTokens))
    sys.stdout.write("Types:\t\t\t%d\n"%(len(counts)))
    sys.stdout.write("Hapaxes:\t\t%d\n"%(sum(1 for x in counts.iteritems() if x[1]==1)))
    sys.stdout.write("Utterances:\t\t%d\n"%(len(corpus)))
    sys.stdout.write("Avg Words/Utterance:\t%.3f\n"%(avgWU))
    sys.stdout.write("SD Words/Utterance:\t%.3f\n"%(sqrt(varAvgWU)))
    sys.stdout.write("Avg Type-Length:\t%.3f\n"%(sum(len(x.split(" ")) for x in counts.keys())/len(counts)))
    sys.stdout.write("Avg Token-Length:\t%.3f\n"%(sum(len(x[0].split(" "))*x[1] for x in counts.iteritems())/float(sum(counts.values()))))
    top10 = sorted(counts.items(),lambda x,y:-cmp(x[1],y[1]))[:10]
    sys.stdout.write("Top 10 make up %.3f of corpus\n"%(sum(x[1] for x in top10)/float(nTokens)))
    sys.stdout.write("rank\tcount\tfrac\tword\n")
    for (i,wc) in enumerate(top10):
        sys.stdout.write("%d\t%d\t%.3f\t%s\n"%(i+1,wc[1],wc[1]/float(nTokens),wc[0]))
