# modified to read lexicon from stream

import argparse
import sys
import math
import bisect, random

parser = argparse.ArgumentParser(description = 'Generate a corpus from the output of a maxent grammar and with a specified frequency distribution')
#parser.add_argument('scoreFile', help='Tab-delimited file with word string first and disharmony last')
parser.add_argument('freqFile', help='List of word frequencies, line-separated')
parser.add_argument('-o', '--outputFile', default='corpus.txt', help='Name of output corpus file')
parser.add_argument('-l', '--lexFile', help='Name of lexicon file to output (optional)')
parser.add_argument('-m', '--minHarmony', type=float, default = -25.0, help='Do not consider words with disharmony <= m')
parser.add_argument('-p', '--probUttBound', type=float, default = 0.333, help='Probability of utterance boundary')
args = parser.parse_args()

## Read in frequency distribution
sys.stderr.write('Reading in frequency distribution\n')
freqDist = []
with open(args.freqFile) as fin:
    for line in fin:
        parse = line.strip().split()
        if parse: freqDist.append(int(parse[0]))
nTypes = len(freqDist)

## Read in score file and set up sampler
sys.stderr.write('Reading in scores from stdin and setting up sampler\n')
words, fmass = [], [0]
for line in sys.stdin:
    parse = line.strip().split('\t')
    word, disharmony = parse[0], float(parse[-1])
    if disharmony <= args.minHarmony: continue
    words.append(word)
    fmass.append(fmass[-1]+math.exp(disharmony))

## Generate/sample words
sys.stderr.write('Generating/sampling words\n')
newwords = []
while len(newwords) < nTypes:
    r = random.random()*fmass[-1]
    i = bisect.bisect_right(fmass, r)-1
    newword = words[i]
    if newword not in newwords: newwords.append(newword)
if args.lexFile:
    with open(args.lexFile,'w') as fout:
        for i in range(nTypes): fout.write('%s\t%d\n' %(newwords[i],freqDist[i]))

## Generate corpus by permuting words
sys.stderr.write('Generating corpus by permuting words\n')
corpus = []
# sort words by length
newwords.sort(lambda x,y: cmp(len(x.split()),len(y.split())))
# now shake a bit through "random" sort
newwords.sort(lambda x,y: cmp(len(x.split()),len(y.split())) if random.random()<0.9 else -cmp(len(x.split()),len(y.split())))

for i in range(nTypes): corpus.extend(freqDist[i]*[newwords[i]])
random.shuffle(corpus)

## Output corpus
sys.stderr.write('Outputting corpus')
with open(args.outputFile,'w') as fout:
    while corpus:
        buf = []
        while random.random() >= args.probUttBound:
            try: buf.append(corpus.pop())
            except IndexError: pass
        if buf: fout.write(' # '.join(buf)+'\n')


