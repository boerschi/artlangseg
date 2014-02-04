"""
  take samples and calculate a marginal posterior for each sentence

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

l2norm = log(2)

def safelog2(x):
    if x==0:
        return 0
    else:
        return log(x)/l2norm

def lToS(x):
    return "|".join(x)

def incr2(hm,i,k):
    try:
        x = hm[i]
        x[k]=x.get(k,0)+1
    except KeyError:
        hm[i] = {}
        hm[i][k] = hm[i].get(k,0)+1

def sToLex(x):
    counts = {}
    for u in x.split("|"):
        for w in u.split(" "):
            incr(counts,w)
    res = []
    for (w,c) in sorted(counts.iteritems(),lambda x,y:-cmp(x[1],y[1])):
        res.append("%s: %d"%(w,c))
    return ", ".join(res)

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
    if len(sys.argv)>2:
        threshold = float(sys.argv[2])
    else:
        threshold = 0.5 #threshold for entropy, exclusive
    counts = {}
    s = []
    i = 0
    for l in sys.stdin:
        l = l.strip().replace(" ","").replace("|"," ")
        if len(l)==0:
            i = 0
        else:
            incr2(counts,i,l)
            i+=1

    allBest = []
    entropyBest = [[] for i in range(6)]
    for i in counts.keys():
        goldwb = evaluate.words(goldsents[i].replace(".",""))
        norm = float(sum(counts[i].values()))
        ent = entropy([x / norm for x in counts[i].values()])
        highestseg = max(counts[i].iteritems(),key=lambda x:x[1])[0]
        allBest.append((highestseg.replace(".",""),i))
        for threshold in [1,2,3,4,5]:
            if ent < threshold/10.0:
                entropyBest[threshold].append((highestseg.replace(".",""),i))
        highestwb = evaluate.words(highestseg)
        expectedF = 0
        tmpFscores = []
        for (seg,count) in sorted(counts[i].iteritems(),lambda x,y:-cmp(x[1],y[1])):
            predwb = evaluate.words(seg.replace(".",""))
            tmpFscores.append(evaluate.evaluate_ind(goldwb,predwb)[2])
            expectedF += count/norm*tmpFscores[-1]
        sys.stdout.write("sent %d, %.3f, %.2f (%.2f), %s\n"%(i,ent,evaluate.evaluate_ind(goldwb,highestwb)[2],expectedF,highestseg))
        for (seg,count) in sorted(counts[i].iteritems(),lambda x,y:-cmp(x[1],y[1])):
            predwb = evaluate.words(seg.replace(".",""))
            tf = evaluate.evaluate_ind(goldwb,predwb)[2]
            sys.stdout.write("  %.2f %d %.2f\t%s\n"%(count/norm,count,tf,seg))
    allGoldWords = [evaluate.words(goldsents[x[1]]) for x in allBest]
    allGoldBounds = [evaluate.wbs(goldsents[x[1]]) for x in allBest]
    allBestWords = [evaluate.words(x[0]) for x in allBest]
    allBestBounds = [evaluate.wbs(x[0]) for x in allBest]
    allGoldTypes = evaluate.types([goldsents[x[1]] for x in allBest])
    allBestTypes = evaluate.types([x[0] for x in allBest])
    sys.stdout.write("\n")
    scores = evaluate.evaluateSets(allGoldBounds,allBestBounds)
    sys.stdout.write("all token-f: %.2f (of %d)\n"%(evaluate.evaluateSets(allGoldWords,allBestWords)[2],len(allGoldWords)))
    sys.stdout.write("all boundary-p: %.2f\nall boundary-r: %.2f\n"%(scores[0],scores[1]))
    sys.stdout.write("all lexic-p: %.2f (of %d)\n"%(evaluate.evaluate_ind(allGoldTypes,allBestTypes)[0],len(allBestTypes)))
    for threshold in [1,2,3,4,5]:
        entropyGoldWords = [evaluate.words(goldsents[x[1]]) for x in entropyBest[threshold]]
        entropyWords = [evaluate.words(x[0]) for x in entropyBest[threshold]]
        entropyGoldTypes = evaluate.types([goldsents[x[1]] for x in entropyBest[threshold]])
        entropyTypes = evaluate.types([x[0] for x in entropyBest[threshold]])
        sys.stdout.write("%.2f token-f: %.2f (of %d)\n"%(threshold/10.0,evaluate.evaluateSets(entropyGoldWords,entropyWords)[2],len(entropyBest[threshold])))
#        sys.stdout.write("  %.2f lexic-p: %.2f (of %d)\n"%(threshold/10.0,evaluate.evaluate_ind(entropyGoldTypes,entropyTypes)[0],len(entropyTypes)))
        
