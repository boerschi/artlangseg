with open("pakna_feats.txt") as fin:
    header = fin.readline()
    segs = []
    for line in fin:
        segs.append(line.rstrip().split('\t')[0])
nSegs = len(segs)

with open('pakna_test.txt','w') as fout:
    for wordLen in range(1,7):
        continueFlag, curPos = True, wordLen*[0]
        while continueFlag:
            ## output string
            print >> fout, ' '.join([segs[i] for i in curPos])
            ## increment counter, including carry
            curPos[-1] += 1
            for iPos in range(wordLen-1,-1,-1):
                if curPos[iPos] == nSegs:
                    curPos[iPos] = 0
                    if iPos == 0: continueFlag = False
                    else: curPos[iPos-1] += 1

