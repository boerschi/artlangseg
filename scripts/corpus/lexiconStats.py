# calculate colission probabilities, unweighted, for fixed-size lexicons
# do several simulations and average

import argparse
import sys
import math
import bisect, random

parser = argparse.ArgumentParser(description = 'Generate a corpus from the output of a maxent grammar and with a specified frequency distribution')
#parser.add_argument('scoreFile', help='Tab-delimited file with word string first and disharmony last')
#parser.add_argument('freqFile', help='List of word frequencies, line-separated')
parser.add_argument('-n',help='Number of word types', type=int)
parser.add_argument('-o', '--outputFile', default='corpus.txt', help='Name of output corpus file')
parser.add_argument('-m', '--minHarmony', type=float, default = -25.0, help='Do not consider words with disharmony <= m')
args = parser.parse_args()

# ## Read in frequency distribution
# sys.stderr.write('Reading in frequency distribution\n')
# freqDist = []
# with open(args.freqFile) as fin:
#     for line in fin:
#         parse = line.strip().split()
#         if parse: freqDist.append(int(parse[0]))
# nTypes = len(freqDist)
nTypes = args.n

## Read in score file and set up sampler
sys.stderr.write('Reading in scores from stdin and setting up sampler\n')
words, fmass = [], [0]
for line in sys.stdin:
    parse = line.strip().split('\t')
    word, disharmony = parse[0], float(parse[-1])
    if disharmony <= args.minHarmony: continue
    words.append(word)
    fmass.append(fmass[-1]+math.exp(disharmony))


def sample(words,fmass,lexicon={}):
    while True:
        r = random.random()*fmass[-1]
        i = bisect.bisect_right(fmass, r)-1
        newword = words[i]
        if not lexicon.has_key(newword):
            return newword

def collission(word, lexicon):
    return lexicon.has_key(word)
#     for w in lexicon:
#         if len(w)<len(word):
#             if word.find(w)!=-1:
# #                print "%s collides with %s"%(word,w)
#                 return True
#         else:
#             if w.find(word)!=-1:
# #                print "%s collides with %s"%(word,w)
#                 return True
#     return False

nExperiments = 100
colissions = []
## Generate a lexicon of size
for nEx in range(nExperiments):
    sys.stderr.write("simulating %d\n"%nEx)
    lexicon = {}
    j = 0
    while j < nTypes:
        newword = sample(words,fmass,lexicon)
        lexicon[newword] = 0
        j+=1
    tColissions = 0
    for i in range(10000):
        if collission(sample(words,fmass),lexicon):
            tColissions+=1
    colissions.append(tColissions)

mean = sum(colissions)/float(len(colissions))
sys.stdout.write("average:\t%d\t%f\n"%(mean,mean/10000.0))
sys.stdout.write("max:\t%d\t%f\n"%(max(colissions),max(colissions)/10000.0))
sys.stdout.write("min:\t%d\t%f\n"%(min(colissions),min(colissions)/10000.0))
sys.stdout.write("# %s\n"%" ".join([str(x) for x in colissions]))
