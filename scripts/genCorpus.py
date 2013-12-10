"""
  Corpus-Generator for Fourtassi, Daland, Boerschinger project
  

  python genCorpus.py [-a[=0.0]] [-b[=200]] [-m[=2]] [-M[=3]] <N> <base>
  
  <base> is either "geo" or "cv",
  <N> is the number of utterances

  -a  the discount parameter
  -b  the concentration parameter
  -m  mean length of a word, in "segments"
  -M  mean length of utterance, in words
"""

import random, sys, argparse

class BaseGeo(object):
    """
      GEO-distribution assumes a geometric distribution over word-lengths,
      uniform distribution over phonemes
    """
    def __init__(self,segs="P T K F S X M N NG L R W J A E I O U".split(),pStop=0.5):
        """
        @segs:   list of segments that can make up words
        @pStop:  parameter of the geometric word-length distribution
        """
        self.segs = segs
        self.pStop = pStop
        self.pPhon = 1/float(len(self.segs))

    def predProb(self,obs):
        return ((1-self.pStop)*self.pPhon)**len(obs) * self.pStop/(1-self.pStop)

    def sample(self):
        res = []
        res.append(self.sampleSegment())
        stop = random.random()
        while stop>self.pStop:
            stop = random.random()
            res.append(self.sampleSegment())
        return ":".join(res)

    def sampleSegment(self):
        cur = 0
        i = -1
        flip = random.random()
        while cur<=flip:
            cur+=self.pPhon
            i+=1
        return self.segs[i]

class BaseGeoCV(object):
    """
      CV-GEO-distribution assumes a geometric distribution over word-lengths,
      uniform distribution over phonemes, but only admits "(CV)+"-words
    """
    def __init__(self,segsC="P T K F S X M N NG L R W J".split(),segsV="A E I O U".split(),pStop=0.5):
        """
        @segsC:  list of consonants
        @segsV:  list of vowels
        @pStop:  parameter of the geometric word-length distribution
        """
        self.segsC = segsC
        self.segsV = segsV
        self.pStop = pStop
        self.pPhonC = 1/float(len(self.segsC))
        self.pPhonV = 1/float(len(self.segsV))

    def predProb(self,obs):
        res = 1
        for i in range(len(obs),step=2):
            pair = obs[i:i+2]
            res = res*(1-self.pStop)*self.pPhonC*self.pPhonV
        return res * self.pStop/(1-self.pStop)

    def sample(self):
        res = []
        res.append(self.sampleSegmentC())
        res.append(self.sampleSegmentV())
        stop = random.random()
        while stop>self.pStop:
            stop = random.random()
            res.append(self.sampleSegmentC())
            res.append(self.sampleSegmentV())
        return ":".join(res)

    def sampleSegmentC(self):
        return self.sampleSegment(self.segsC,self.pPhonC)

    def sampleSegmentV(self):
        return self.sampleSegment(self.segsV,self.pPhonV)

    def sampleSegment(self,segs,p):
        cur = 0
        i = -1
        flip = random.random()
        while cur<=flip:
            cur+=p
            i+=1
        return segs[i]

class BaseDict(object):
    """
      Dict-GEO-distribution assumes a geometric distribution over word-lengths,
      uniform distribution over words at each length
    """
    def __init__(self,dictionary,pStop=0.5):
        """
        @segsC:  list of consonants
        @segsV:  list of vowels
        @pStop:  parameter of the geometric word-length distribution
        """
        self.dictionary = self.initDict(dictionary)
        self.pStop = pStop
        self.maxLength = max(self.dictionary.keys())

    def initDict(self,f):
        res = {}
        for l in open(f):
            l = l.strip()
            length = len(l.split(":"))
            x = res.get(length,[])
            x.append(l)
            res[length] = x
        return res

    def predProb(self,obs):
        length = len(obs.split(":"))
        res = (1-self.pStop)**length * self.pStop/(1-self.pStop)
        counts = self.dictionary.get(length,0)
        if counts == 0:
            return 0
        else:
            return res*1/float(counts)

    def sample(self):
        i = 1
        while random.random()<(1-self.pStop) and i<self.maxLength:
            i+=1
        return random.choice(self.dictionary[i])


class DP(object):
    def __init__(self,base,a=0.0,b=200.0):
        self.base = base
        self.a = a
        self.b = b
        self.counts = {}
        self.obs = 0
        self.tables = 0
    
    def add(self,obs):
        newTable = self.pNewTable(obs)
        oldTable = self.pOldTable(obs)
        self.obs+=1
        if random.random()<=newTable/(newTable+oldTable):
            self.addNewTable(obs)
            self.tables+=1
        else:
            self.addToOldTable(obs)

    def pNewTable(self,obs):
        return (self.b+self.a*self.tables)*self.base.predProb(obs)

    def pOldTable(self,obs):
        try:
            return self.counts[obs][0]-self.a*len(self.counts[obs][1])
        except KeyError:
            0.0

    def pNewTableS(self):
        return (self.b+self.a*self.tables)

    def pOldTableS(self):
        return self.obs - self.tables*self.a

    def addToNewTable(self,obs):
        try:
            oldCounts, tables = self.counts[obs]
            tables.append(1)
            self.counts[obs][0] = oldCounts+1
        except:
            self.counts[obs] = [1,[1]]

    def addToOldTable(self,obs):
        whichTable = random.randint(1,self.counts[obs][0])
        i = -1
        cur = 0
        tables = self.counts[obs][1]
        while whichTable<=cur:
            i+=1
            cur += tables[i]
        tables[i]+=1
        self.counts[obs][0]+=1
    
    def sampleWord(self):
        newWord = self.pNewTableS()
        oldWord = self.pOldTableS()
        if random.random()<=newWord/(newWord+oldWord):
            word = self.base.sample()
            self.addToNewTable(word)
            self.obs+=1
            self.tables+=1
            return word
        else:
            whichTable = random.randint(1,self.obs)
            cur = 0
            for word in self.counts.keys():
                cur += self.counts[word][0]
                if whichTable<=cur:
                    self.addToOldTable(word)
                    self.obs+=1
                    return word

    def sampleSentence(self,stopProb=1/3.0):
        res = [self.sampleWord()]
        while stopProb<random.random():
            res.append(self.sampleWord())
        return " ".join(res)

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("N", help="N is the number of utterances to be generated",type=int)
    parser.add_argument("base", help="base is the language used, either 'geo', 'cv', or 'dict'")
    parser.add_argument("-a",help="discount parameter",type=float,default=0.0)
    parser.add_argument("-b",help="concentration parameter",type=float,default=200.0)
    parser.add_argument("-m",help="mean length of words",type=float,default=3)
    parser.add_argument("-M",help="mean length of utterances",type=float,default=3)
    parser.add_argument("-d",help="dictionary to use")
    args = parser.parse_args()

    N = args.N
    base = args.base
    conc = args.b
    disc = args.a
    meanWord = args.m
    meanUtt = args.M

    if base=="geo":
        baseDist = BaseGeo(pStop=1/float(meanWord))
    elif base=="cv":
        baseDist = BaseGeoCV(pStop=1/(meanWord/2.0))
    elif base=="dict":
        baseDist = BaseDict(args.d,pStop=1/float(meanWord))
    crp = DP(baseDist,disc,conc)
    for i in range(N):
        print crp.sampleSentence(1.0/meanUtt)
