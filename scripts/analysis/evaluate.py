#!/usr/local/bin/python

"""
  evaluates multiple levels, e.g. syllable boundaries and
  word boundaries
  note that given syllable boundaries, syllable internal structure
  is deterministic, assuming gold knowledge of vowels

  segmentations have same format as gold standards
"""

import sys

WBSYMBOL=" "
SBSYMBOL="."

"""
  returns a set of word pairs
"""
def words(s):
    res = set()
    i=1
    sPos=1
    start=0
    s = s.replace(SBSYMBOL,"")
    while i<len(s.replace(WBSYMBOL,"")):
        if s[sPos]==" ":
            res.add((start,i))
            sPos+=1
            start=i
        else: 
            sPos+=1
            i+=1
    res.add((start,i))
    return res

"""
  returns a set of word-boundary indices
"""
def wbs(s):
    res = set()
    i=1       
    sPos=1
    s = s.replace(SBSYMBOL,"") #syllables ignored in word-boundary eval
    while i<len(s.replace(WBSYMBOL,"")):
        if s[sPos]==WBSYMBOL:
            res.add(i)
            sPos+=1
        else: 
            sPos+=1
            i+=1
    return res


"""
  returns a set of syllable-boundary indices
"""
def sbs(s):
    res = set()
    i=1       
    sPos=1    
    while i<len(s.replace(WBSYMBOL,"").replace(SBSYMBOL,"")):
        if s[sPos]==SBSYMBOL or s[sPos]==WBSYMBOL:
            res.add(i)
            sPos+=1
        else: 
            sPos+=1
            i+=1
    return res

"""
  returns a set of syllables
"""

def syllables(s):
    res = set()
    i=1
    sPos=1
    start=0
    while i<len(s.replace(WBSYMBOL,"").replace(SBSYMBOL,"")):
        if s[sPos]==SBSYMBOL or s[sPos]==WBSYMBOL:
            res.add((start,i))
            sPos+=1
            start=i
        else: 
            sPos+=1
            i+=1
    res.add((start,i))
    return res


"""
  calculate precision, recall and f-measure for a single goldset / predset pair
"""
def evaluate_ind(goldset,predset):
    totPred = len(predset)
    totGold = len(goldset)
    corPred = len(predset.intersection(goldset))
    prec = corPred/float(totPred) if totPred>0 else 1.0
    rec = corPred/float(totGold) if totGold>0 else 1.0
    try:
        fm = 2*prec*rec / (prec+rec)
    except:
        fm = 0.0
    return (prec,rec,fm)

"""
  calculate precision, recall and f-measure for predicted predset values
"""
def evaluateSets(goldsets,predsets):
    totPred=0
    totGold=0
    corPred=0
    for (goldset,predset) in zip(goldsets,predsets):
        totPred += len(predset)
        totGold += len(goldset)
        corPred += len(predset.intersection(goldset))
    prec = corPred/float(totPred) if totPred>0 else 1.0
    rec = corPred/float(totGold) if totGold>0 else 1.0
    try:
        fm = 2*prec*rec / (prec+rec)
    except:
        fm = 0.0
    return (prec,rec,fm)

def evaluate(goldstrings,predstrings):
    goldwtypes = set()
    predwtypes = set()
    goldstypes = set()
    predstypes = set()
    for (g,p) in zip(goldstrings,predstrings):
#        goldwtypes.update(g.replace(".","").split(" "))
#        predwtypes.update(p.replace(".","").split(" "))
        goldwtypes.update(g.split(" "))
        predwtypes.update(p.split(" "))
        goldstypes.update(g.replace("."," ").split(" "))
        predstypes.update(p.replace("."," ").split(" "))

    goldwbs = [wbs(x) for x in goldstrings]
    predwbs = [wbs(x) for x in predstrings]
    goldwords = [words(x) for x in goldstrings]
    predwords = [words(x) for x in predstrings]
    goldsbs = [sbs(x) for x in goldstrings]
    predsbs = [sbs(x) for x in predstrings]
    goldsylls = [syllables(x) for x in goldstrings]
    predsylls = [syllables(x) for x in predstrings]
    evaluateSets(goldwbs,predwbs)
    evaluateSets(goldwords,predwords)
    evaluateSets(goldsbs,predsbs)
    evaluateSets(goldsylls,predsylls)
    evaluate_ind(goldwtypes,predwtypes)
    evaluate_ind(goldstypes,predstypes)
    sys.stdout.write("\n")

def types(s):
    res = set()
    for u in s:
        res.update(u.split(" "))
    return res

if __name__=="__main__":
    sys.stdout.write("# BP BR BF TP TR TF SBP SBR SBF STP STF STR LP LR LF SLP SLR SLF\n")
    goldstrings = [x.strip() for x in open(sys.argv[1])]
    predstrings = []
    printed = False
    for l in sys.stdin:
        printed = False
        l = l.strip()
        if l != "":
            predstrings.append(l)
            continue
        evaluate(goldstrings,predstrings)
        predstrings = []
        printed = True
        sys.stdout.flush()
    if not printed:
        evaluate(goldstrings,predstrings)
        sys.stdout.flush()
    
    
