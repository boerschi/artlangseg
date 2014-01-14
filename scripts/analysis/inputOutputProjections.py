"""input / output projections as defined in Daland and Zuraw (2013)

author: benjamin boerschinger

an output-projection is 
  "the minimal sequence of segmented words containing the entire input word. For example, 
   if 'the#kitty' were segmented as 'thekitty', then 'thekitty' would be the output pro-
   jection for both 'the' and 'kitty'"

an input-projection is defined analogously as the minimal sequence of gold words containing
the entire output (predicted) word. That is, if
  "'the#kitty' were segmented as 'theki#tty', then the 'the#kitty' would be the input pro-
    jection of both 'theki' and 'tty'."

"""


import doctest,segUtils,sys


def outputprojections(goldseg,predseg):
    """calculate outputprojections for all the words in goldseg given predseg
    
    @goldseg  the goldsegmentation, a white-space separated string, e.g. "the kitty"
    @predseg  the predicted segmentation, a white-space separated string, e.g. "th e kitty"

    >>> outputprojections("the kitty","thekitty")
    [("the","thekitty"),("kitty","thekitty")]

    >>> outputprojections("the kitty","thek itty")
    [("the","thek"),("kitty","thek itty")]
    """
    inWords = segUtils.words(goldseg)
    goldtext = goldseg.replace(" ","").replace(".","")
    predVector = segUtils.getBVec(predseg)
    res = []
    for (l,r) in sorted(inWords,lambda x,y:cmp(x[0],y[0])):
        inpP = goldtext[l:r]
        # find the left-most boundary that includes l
        if l==0:
            lp = -1
        else:
            lp = l-1
            while lp>-1 and predVector[lp]!="b":
                lp-=1
        rp = r-1
        while rp<len(goldtext)-1 and predVector[rp]!="b":
            rp+=1
        outP = segUtils.segment(goldtext[lp+1:rp+1],predVector[lp+1:rp])
        res.append((inpP,outP))
    return res


    

def inputprojections(goldseg,predseg):
    """calculate inputprojections for all the words in predseg given goldseg
    
    @goldseg  the goldsegmentation, a white-space separated string, e.g. "the kitty"
    @predseg  the predicted segmentation, a white-space separated string, e.g. "th e kitty"

    >>> inputprojections("the kitty","thekitty")
    [("thekitty","the kitty")]

    >>> inputputprojections("the kitty","thek itty")
    [("thek","the kitty"),("itty","kitty")]
    """
    outWords = segUtils.words(predseg)
    predtext = predseg.replace(" ","").replace(".","")
    goldVector = segUtils.getBVec(goldseg)
    res = []
#    print goldseg,predseg
    if len(goldVector)==0: #special case onesegment utterances
        return [(goldseg,predseg)]
    else:
#        print goldVector,outWords
        for (l,r) in sorted(outWords,lambda x,y:cmp(x[0],y[0])):
            outP = predtext[l:r]
            lp = l-1 if l>0 else -1
            while lp>-1 and goldVector[lp]!="b":
                lp-=1
            rp = r-1
            while rp<len(predtext)-1 and goldVector[rp]!="b":
                rp+=1
#            print lp,rp
            inpP = segUtils.segment(predtext[lp+1:rp+1],goldVector[lp+1:rp])
            res.append((outP,inpP))
        return res

def inc(hm,k1,k2):
    try:
        hm.setdefault(k1,{})[k2]+=1
    except KeyError:
        hm.setdefault(k1,{})[k2]=1

def inc1(hm,k):
    try:
        hm[k]+=1
    except KeyError:
        hm[k]=1

if __name__=="__main__":
    pred = open(sys.argv[1])
    gold = open(sys.argv[2])
    inps = {}
    outps = {}
    goldtypes = {}
    predtypes = {}
    for (p,g) in zip(pred,gold):
        p = p.strip()
        g = g.strip()
        ins = inputprojections(g,p)
        outs = outputprojections(g,p)
        for (a,b) in ins:
            inc1(predtypes,a)
            inc(inps,a,b)
        for (a,b) in outs:
            inc1(goldtypes,a)
            if len(b.split())>1 and a in b.split():
                print a,b
                print p
                print g
                sys.exit(1)
            inc(outps,a,b)

    print "gold-types: %d"%len(outps)
    for g in sorted(outps.keys(),lambda x,y:-cmp(len(outps[x]),len(outps[y]))):
        print g,"(%d)"%goldtypes[g]
        for o in sorted(outps[g],lambda x,y:-cmp(outps[g][x],outps[g][y])):
            if o==g:
                print "-> %d\t%s"%(outps[g][o],o)
            else:
                print "   %d\t%s"%(outps[g][o],o)

    print
    print "INPUTPROJECTIONS"
    print
        
    for g in sorted(inps.keys(),lambda x,y:-cmp(len(inps[x]),len(inps[y]))):
        print g
        for o in sorted(inps[g],lambda x,y:-cmp(inps[g][x],inps[g][y])):
            print "  %d\t%s"%(inps[g][o],o)

