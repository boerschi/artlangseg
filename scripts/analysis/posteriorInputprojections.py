"""
  take samples and calculate input-projection posteriors

  usage: cat <samples> | python posteriorSentences.py <goldfile>

  where <samples> provides sampled analyses, one line per utterance and each
  sample separated by an empty line
  
  <goldfile> is needed to provide segmentation scores for individual sentences / the corpus,
  and can be strictly bigger than the corpus for which samples were obtained (that is, if
  you only performed inference over a prefix of a corpus, you can still pass the whole
  corpus), but you need to ensure that the ith utterance in the samples is the ith utterance
  in the goldfile
"""

import sys, evaluate
from math import log
from inputOutputProjections import inputprojections

l2norm = log(2)

def safelog2(x):
    if x==0:
        return 0
    else:
        return log(x)/l2norm

def incr2(hm,i,k):
    try:
        x = hm[i]
        x[k]=x.get(k,0)+1
    except KeyError:
        hm[i] = {}
        hm[i][k] = hm[i].get(k,0)+1

def entropy(l):
    res = 0
    for p in l:
        res += p*safelog2(p)
    if abs(res)==0:
        return 0
    else:
        return -res


if __name__=="__main__":
    goldsents = [x.strip() for x in open(sys.argv[1])]
    counts = {}
    s = []
    i = 0
    samples = 0
    for l in sys.stdin:
        l = l.strip()
        if len(l)==0:
            samples+=1
            i = 0
        else:
            gold = goldsents[i]
            outs = inputprojections(gold,l)
            for (p,g) in outs:
                incr2(counts,p,g)
            i+=1

    for i in sorted(counts.keys(),lambda x,y:-cmp(sum(counts[x].values()),sum(counts[y].values()))):
        norm = float(sum(counts[i].values()))
        ent = entropy([x / norm for x in counts[i].values()])
        (highestp,highestpp) = max(counts[i].iteritems(),key=lambda x:x[1])
        sys.stdout.write("%s %.3f, %s (%.2f)\n"%(i,ent,highestp,highestpp/norm))
        for (p,count) in sorted(counts[i].iteritems(),lambda x,y:-cmp(x[1],y[1])):
            sys.stdout.write("  %.2f %.2f \t%s\n"%(count/norm,count/float(samples),p))
