# writes to stdout, allowing us to compress the output directly using gzip
# python <args> | gzip > output.gz

##############################################################################
##  Import statements and helper functions                                  ##
##############################################################################

import argparse
import os, sys, time, random
import re
import scipy, scipy.sparse, scipy.optimize
from maxent import *

starttime = time.clock()
def status(s):
    print >> sys.stderr, '%4.2f\t%s' %(time.clock(), s)
    sys.stderr.flush()

##############################################################################
##  Core data structures and filenames                                      ##
##############################################################################

## FeatureSet -- relates segments to feature descriptors using natural classes
feats = None

## Registry -- the interface between constraint strings and corresponding fn's
registry = None

## Canonical order for forms: [ training (lexicographic) ] + [ contrast (lex) ]
##    and corresponding counts (e.g. [1 1 1 ... 0 0 0 ... ])
wordOrder = []
wordCts = []

## conOrder is a list of constraint strings, e.g. 'Ngram:^[+syllabic]' 
##    This is a canonical ordering used in calculating violations
##    and weight-setting.
## discrimDic is a dictionary whose keys are constraint indices (wrt conOrder)
##    and whose values are the corresponding discriminativity scores
## activeCons is a list of 'active' constraints, i.e. ones whose violation
##    vector is entered into the violation matrix and which receive a weight.
##    The *values* in the list are constraint indices with respect to conOrder,
##    while the *indices* of activeCons represent the constraint indices
##    with respect to the violation matrix (and the weight vector).
## An example may make it clear. Suppose ONSET happens to be constraint 100.
##    Further suppose ONSET assigns 0.3 violations/form in the contrast set,
##    and 0.1 violations/form in the training set, so its discriminativity
##    is 0.3-0.1 = 0.2, and that this is the most discriminative constraint.
##    Then we would see the following:
##        conOrder[99]='Ngram:^[+syllabic]'
##        discrimDic[99] = 0.2
##        activeCons[0] = 99
conOrder = []
discrimDic = {}
activeCons = []

## violMat is a sparse matrix holding the violations for 'active' constraints
## conWts is a scipy array holding the corresponding constraint weights
violMat = None
conWts = None

##############################################################################
##  Parse command-line arguments                                            ##
##############################################################################

parser = argparse.ArgumentParser(description = 'Phonotactic learning with maximum entropy harmonic grammar')
parser.add_argument('featureFilename', help='Feature file')
parser.add_argument('-w', '--workingDir', default='output/', help='Working directory')

## one of the following must be supplied to fill wordOrder and wordCts
parser.add_argument('-a', '--allForms', help='File listing training items and contrast set, with counts')
parser.add_argument('-t', '--trainCounts', help='File listing training items only, with optional counts')

## one of the following must be supplied to fill conOrder
parser.add_argument('-c', '--constraints', help='File listing constraints to consider')
parser.add_argument('-e', '--enumerate', action='store_true', help='Enumerate constraints from scratch (see docs)')

## one of the following must be supplied to get violation counts
parser.add_argument('-v', '--violations', help='File listing nonzero constraint violations in COO format')
parser.add_argument('-E', '--evaluate', action='store_true', help='Evaluate constraints on training and contrast set')

## to fill activeCons, need either -d or -s
parser.add_argument('-d', '--discriminativity', help='File listing discriminativity scores for each constraint')
parser.add_argument('-s', '--score', action='store_true', help='Calculate discriminativity scores')

## the following control how many constraints are put into activeCons
parser.add_argument('-M', '--maxCons', type=int, help='Maximum number of constraints (recommended: 100)')
parser.add_argument('--discrimThresh', type=float, default=0.0, help='Ignore constraints below this discriminativity')

## the following are parameters for the weight-setting step
parser.add_argument('-l', '--L1', type=float, default=1.0, help='Multiplier for L1 regularizer')
parser.add_argument('-L', '--L2', type=float, default=None, help='Multiplier for L1 regularizer')
parser.add_argument('-p', '--precision', type=float, default=10000000, help='Precision for gradient search (see docs)')

## alternatively, one can just load a grammar directly
parser.add_argument('-g', '--grammar', help='File listing active constraints and weights to load directly')

## and finally, the test file
parser.add_argument('-T', '--test', help='File listing test items')
#parser.add_argument('-o', '--output', help='Testing output')

args = parser.parse_args()
##args = parser.parse_args([ \
##    'pakna_feats.txt', \
##    '--workingDir', 'pakna/', \
##    '--trainCounts', 'lex_gold.txt', \
##    '--allForms', 'pakna/hawaiian_sparseContrast.txt', \
##    '--enumerate', \
##    '--constraints', 'hawaiian.txt', \
##    '--violations', 'output/violations.txt', \
##    '--evaluate', \
##    '--score', \
##    '--discriminativity', 'output/discriminativity.txt', \
##    '--maxCons', '100', \
##    '--discrimThresh', '-100', \
##    '--precision', '1000000000000', \
##    '--grammar', 'hawaiian.txt', \
##    '--L1', '0.01', \
##    '--test', 'pakna_test.txt' \
##    ])
    
conFile = args.constraints or os.path.join(args.workingDir, 'constraints.txt')
violFile = args.violations or os.path.join(args.workingDir, 'violations.txt')
discrimFile = args.discriminativity or os.path.join(args.workingDir, 'discriminativity.txt')
gramFile = args.grammar or os.path.join(args.workingDir, 'grammar.txt')
#testOutputFile = args.output or os.path.join(args.workingDir,'test_output.txt')

##############################################################################
## Setting up working directory                                             ##
##############################################################################

if not os.path.isdir(args.workingDir):
    try: os.makedirs(args.workingDir)
    except OSError:
        print >> sys.stderr, 'Specified working directory does not exist '+\
                             'and make directory failed.'
        print >> sys.stderr, 'Please check the directory name, set '+\
                             'permissions, or create it manually.'
        sys.exit(1)

##############################################################################
## Initialize the FeatureSet and Registry                                   ##
##############################################################################
##                                                                          ##
##  feats <FeatureSet> -- relates features to segments and natural classes  ##
##  registry <Registry> -- converts constraint strings to actual functions  ##
##                                                                          ##
##############################################################################

print >> sys.stderr, '**** Initializing FeatureSet and Registry ****'
feats = FeatureSet(args.featureFilename)
registry = Registry(feats)
print >> sys.stderr, ''

##############################################################################
## Getting the training data                                                ##
##############################################################################
##                                                                          ##
##  wordOrder <list> -- the observed forms and the contrast set             ##
##  wordCts <ndarray> -- counts for same (0 for contrast set obv)           ##
##  nTypes <int> -- number of (observed) types with freq > 0                ##
##  nForms <int> -- number of total forms in wordOrder                      ##
##                                                                          ##
##############################################################################

print >> sys.stderr, '**** Getting training and contrast set ****'

if args.allForms:
    status('Reading training/contrast forms/counts from %s' %args.allForms)
    nTypes = 0
    with open(args.allForms,'r') as fin:
        for line in fin:
            form, ct = line.rstrip().split('\t')
            wordOrder.append(form)
            wordCts.append(int(ct))
            if wordCts[-1] > 0: nTypes += 1
    wordCts = scipy.array(wordCts)
    nForms = len(wordCts)
    
elif args.trainCounts:
    status('Reading training forms from %s' %args.trainCounts)
    trainCts = {}
    with open(args.trainCounts, 'r') as fin:
        for line in fin:
            parse = line.rstrip().split('\t')
            word, ct = parse[0], 1
            try: ct = int(parse[1])
            except IndexError: pass
            trainCts[word] = ct
    nTypes = len(trainCts)
            
    status('Generating unobserved string edit neighbors as contrast set')
    wordOrder = sorted(trainCts.keys())
    badNbs = badNeighbors(trainCts, feats.segments)
    randVec = scipy.rand(len(badNbs))
    for iNb, randNum in enumerate(randVec):
        if randNum < 0.5:
            badNb = badNbs[iNb]
            if badNb not in trainCts: wordOrder.append(badNb)
    wordCts = scipy.array([trainCts.get(word,0) for word in wordOrder])
    nForms = len(wordOrder)

    wordFile = os.path.join(args.workingDir, 'allForms.txt')
    status('Writing train and contrast forms to %s' %wordFile)
    with open(wordFile,'w') as fout:
        for iWord,word in enumerate(wordOrder):
            fout.write('%s\t%d\n' %(word,wordCts[iWord]))
else:
    status('No lexicon file passed. Cannot evaluate constraints or set weights')

print >> sys.stderr, ''

############################################################################
##                            GETTING A GRAMMAR IN                        ##
############################################################################
##                                                                        ##
##  conOrder <list> -- canonical order for constraint strings             ##
##  discrimDic <dict> -- key: conOrder index; value: contextual           ##
##  activeCons = <list> -- conOrder indices of constraints in final gram  ##
##  conWts <scipy.ndarray> -- weights associated with cons in activeCons  ##
##                                                                        ##
############################################################################

############################################################################
## STEP 1: Get constraint strings                                         ##
############################################################################
print >> sys.stderr, '**** Obtaining constraint strings ****'

## Option A: stored in a file
if args.constraints:
    status('Loading constraint names from %s' %conFile)
    conOrder = []
    with open(conFile, 'r') as fin:
        for line in fin:
            conOrder.append(line.rstrip().split('\t')[0])

## Option B: make 'em up from scratch
elif args.enumerate:
    status('Separating natural classes by featural complexity')
    complexityDic, featStr2segTuple = {}, {}
    for segTuple in feats.natclasses:
        featStr = feats.featspec2str(feats.natclasses[segTuple])
        featStr2segTuple[featStr] = segTuple
        if featStr == '': nFeats = 0
        else: nFeats = len(featStr.split(','))
        complexityDic[nFeats] = complexityDic.get(nFeats,[]) + [featStr]
    print >> sys.stderr, 'To constrain the running time, this code will only'+\
                         ' enumerate constraints over'
    print >> sys.stderr, 'natural classes that can be stated with 1-2' + \
                         ' features. Therefore, it is'
    print >> sys.stderr, 'strongly recommended that you choose a feature set'+\
                         ' in which classes that are'
    print >> sys.stderr, 'likely to be phonotactically active can be stated' +\
                         ' in 1-2 features.'

    status('Enumerating constraints with 0-2 feature values total')
    conOrder = ['Ngram:[]']
    for featStr in featStr2segTuple:
        conOrder.append('Ngram:[%s]' %featStr)
        conOrder.append('Ngram:^[%s]' %featStr)
        conOrder.append('Ngram:[%s]$' %featStr)
    for lFeatStr in featStr2segTuple:
        for rFeatStr in featStr2segTuple:
            conOrder.append('Ngram:[%s] [%s]' %(lFeatStr,rFeatStr))
            conOrder.append('Ngram:^[%s] [%s]' %(lFeatStr,rFeatStr))
            conOrder.append('Ngram:[%s] [%s]$' %(lFeatStr,rFeatStr))
    
    conFile = os.path.join(args.workingDir, 'constraints.txt')    
    status('Enumerating constraints to %s' %conFile)
    with open(conFile, 'w') as fout:
        for conStr in conOrder:
            print >> fout, conStr

## Option C: Load 'em from a stored grammar file
elif args.grammar:
    conOrder, conWts = [], []
    with open(args.grammar, 'r') as fin:
        for line in fin:
            conStr, wt = line.rstrip().split('\t')
            conOrder.append(conStr)
            conWts.append(float(wt))
    conWts = scipy.array(conWts)
    activeCons = range(len(conOrder))   ## identity mapping
    for conIndex in activeCons: discrimDic[conIndex] = 0.0

## There is no Option D:
else:
    print >> sys.stderr, 'You have not specified any way to get constraints'+\
                         ' into memory.'
    print >> sys.stderr, 'All downstream processes require constraints.' +\
                         ' Exiting.'
    sys.exit(0)

status('Constraint strings loaded: %d' %len(conOrder))
print >> sys.stderr, ''

############################################################################
## STEP 2: Get constraint violations                                      ##
############################################################################
print >> sys.stderr, '**** Ensuring that violations file is accessible ****'

## in the worst case, have to evaluate constraints
if args.evaluate:
    violFile = os.path.join(args.workingDir, 'violations.txt')
    status('No violations file supplied, evaluating and storing to %s' \
           %violFile)
    print >> sys.stderr, 'This step may take a lot of time. Constraint stats'+\
                         ' shown to report progress.'
##    status('discriminativity\tconstraint string')
    with open(violFile, 'w') as fViol:
        for jCon,conStr in enumerate(conOrder):
            trnViols, altViols = 0, 0
            con = registry.interpret(conStr)
            for iWord,word in enumerate(wordOrder):
                nViols = con(word)
                if nViols:
                    fViol.write('%d\t%d\t%d\n' %(iWord,jCon,nViols))
                    if iWord >= nTypes: altViols += nViols
                    else: trnViols += nViols
            ## discriminativity = avg. violations per contrast item, minus
            ##      avg. violations per training item
            discrim = float(altViols)/(nForms-nTypes) - float(trnViols)/nTypes
            discrimDic[jCon] = discrim
            
##            status('%1.6f\t%s' %(discrim, conStr))
    status('done evaluating!!')
    
    discrimFile = os.path.join(args.workingDir, 'discriminativity.txt')
    status('Writing constraint discriminativities to %s' %discrimFile)
    with open(discrimFile,'w') as fDiscrim:
        for jCon,conStr in enumerate(conOrder):
            print >> fDiscrim, '%s\t%f' %(conStr, discrimDic[jCon])

##  but if the were compiled already, use the stored file
elif args.violations:
    violFile = args.violations
    status('You have indicated violations are stored in %s' %violFile)

## and issue a warning if no violations included
else:
    status('WARNING: You have not indicated a way to get the violations')

print >> sys.stderr, ''

############################################################################
## STEP 3: Get constraint discriminativities
############################################################################
print >> sys.stderr, '**** Getting constraint discriminativities ****'

if discrimDic:
    status('Discriminativities were calculated during constraint evaluation')

elif args.discriminativity:
    status('Reading constraint discriminativities from %s' %discrimFile)
    with open(discrimFile,'r') as fin:
        for line in fin:
            conStr, discrim = line.rstrip().split('\t')
            discrimDic[conOrder.index(conStr)] = float(discrim)

elif args.score:
    status('Calculating constraint discriminativity from violations file')
    print >> sys.stderr, 'Since the violations file may not be stored' + \
                                                'in any particular'
    print >> sys.stderr, 'order, the code cannot know when a violation has ' +\
                                                'been fully processed.'
    print >> sys.stderr, 'Thus, running progress cannot really be shown.'
    print >> sys.stderr, 'Instead, a status update will be shown when done.'
    
    trnViols, altViols = {}, {}
    with open(violFile, 'r') as fin:
        for line in fin:
            iWord, jCon, nViols = [int(x) for x in line.split()]
            discrimDic[jCon] = 0.0
            if iWord >= nObserved:
                altViols[jCon] = altViols.get(jCon,0) + nViols
            else:
                trnViols[jCon] = trnViols.get(jCon,0) + nViols
    for jCon in discrimDic:
        altViolsPerWord = float(altViols.get(jCon,0))/(nForms-nTypes)
        trnViolsPerWord = float(trnViols.get(jCon,0))/nTypes
        discrimDic[jCon] = altViolsPerWord - trnViolsPerWord

    discrimFile = os.path.join(args.workingDir, 'discriminativity.txt')
    status('Writing constraint discriminativities to %s')
    with open(discrimFile,'w') as fDiscrim:
        for jCon,conStr in enumerate(conOrder):
            print >> fDiscrim, '%s\t%f' %(conStr, discrimDic[jCon])
else:
    print >> sys.stderr, 'WARNING: No constraint discriminativities to get'
print >> sys.stderr, ''

############################################################################
## STEP 4: Pick out active constraints based on discriminativity
############################################################################

print >> sys.stderr, '**** Selecting active constraints ****'
if discrimDic:
    discrimThresh = args.discrimThresh or 0.0
    ## filter out all constraint strings below the discrimiinativity threshold
    activeCons = [jCon for jCon in discrimDic \
                    if discrimDic[jCon] > discrimThresh]
    ## arrange constraints in decreasing order of discriminativity
    activeCons.sort(key = discrimDic.get, reverse=True)
    ## dump less-discriminative constraints so as not to exceeed maxCons
    if len(activeCons) > args.maxCons: activeCons = activeCons[:args.maxCons]
    status('Selected %d active constraints' %len(activeCons))
    
    activeConsFile = os.path.join(args.workingDir, 'active_constraints.txt')
    status('Writing active constraints to %s' %activeConsFile)
    with open(activeConsFile, 'w') as fout:
        for jCon in activeCons:
            print >> fout, conOrder[jCon]
else:
    print >> sys.stderr, 'WARNING: No constraints to select'
print >> sys.stderr, ''

############################################################################
## STEP 5: Build sparse matrix
############################################################################

print >> sys.stderr, '**** Reading sparse violation matrix in from file ****'
if activeCons:
    status('Creating sparseIndex dict for fast constraint checking')
    status('(keys = raw index; values = col index in sparse matrix)')
    sparseIndex = {}
    for colIndex,jCon in enumerate(activeCons):
        sparseIndex[jCon] = colIndex
    
    status('Initializing violations matrix')
    nRows, nCols = len(wordOrder), len(sparseIndex)
    violMat = scipy.sparse.csr_matrix((nRows, nCols), dtype=int)
    status('Commencing read-in. A "." will be displayed for every 100,000')
    status('\tviolations added to the violation matrix.')
    
    with open(violFile, 'r') as fin:
        rowVec, colVec, valVec = [], [], []
        for iLine,line in enumerate(fin):
            iWord, jCon, nViols = [int(x) for x in line.rstrip().split('\t')]
            if jCon in sparseIndex:
                rowVec.append(iWord)
                colVec.append(sparseIndex[jCon])
                valVec.append(nViols)
                
                ## every 10,000 appends, COO -> CSR -> violMat
                if (len(rowVec) % 100000 == 0) and len(rowVec):
                    print >> sys.stderr, '.',
                    tempMat = scipy.sparse.coo_matrix((scipy.array(valVec), \
                                (scipy.array(rowVec), scipy.array(colVec))), \
                                shape=(nRows, nCols), dtype=int)
                    violMat = violMat + tempMat.tocsr()
                    rowVec, colVec, valVec, tempMat = [], [], [], None
        ## add any remaining nonzero counts
        tempMat = scipy.sparse.coo_matrix((scipy.array(valVec), \
                    (scipy.array(rowVec), scipy.array(colVec))), \
                    shape=(nRows, nCols), dtype=int)
        violMat = violMat + tempMat.tocsr()
        print >> sys.stderr, ''
    status('Sparse violations matrix added to memory!')
    
else:
    print >> sys.stderr, 'WARNING: No active constraints, skipping'

print >> sys.stderr, ''


############################################################################
## STEP 6: Weight-setting step
############################################################################

print >> sys.stderr, '**** Weight-setting step ****'

if activeCons:
    l1_mult = args.L1
    l2_mult = args.L2
    prec = args.precision
    negReals = [(-25,0) for wt in range(nCols)]

    status('Optimizing objective function with scipy.optimize.fmin_l_bfgs_b')
    status('This may take some time')
    conWts, nfeval, returnCode = scipy.optimize.fmin_l_bfgs_b(objective, \
            -scipy.array([discrimDic[jCon] for jCon in activeCons]), \
            args = (violMat,wordCts,l1_mult,l2_mult), \
            bounds=negReals, factr=args.precision)
    status('done!')

    ## save final grammar
    gramFile = os.path.join(args.workingDir,'grammar.txt')
    status('Writing learned weights to %s' %gramFile)
    with open(gramFile, 'w') as fout:
        for jCol,jCon in enumerate(activeCons):
            print >> fout, '%s\t%f' %(conOrder[jCon], conWts[jCol])

    status('Outputting calculation for trained max')
    print >> sys.stderr, 'Running objective function for trained max'
    fMax, grad = objective(conWts, violMat, wordCts, l1_mult, l2_mult)

print >> sys.stderr, ''

##############################################################################
##  LOADING GRAMMAR
##############################################################################

if args.grammar:
    status('Loading grammar from %s' %gramFile)
    conOrder, conWts = [], []
    with open(gramFile) as fin:
        for line in fin:
            parse = line.rstrip().split('\t')
            conOrder.append(parse[0])
            conWts.append(float(parse[1]))
    conWts = scipy.array(conWts)
    activeCons = range(len(conOrder))

##############################################################################
##  TESTING
##############################################################################

print >> sys.stderr, '**** Testing codeblock ****'

if args.test:
    status('Getting constraints')
    cons = []
    for jCol, jCon in enumerate(activeCons):
        conStr = conOrder[jCon]
        cons.append(registry.interpret(conStr))

    
    status('Writing test results to stdout')
    fout = sys.stdout
    with open(args.test) as fin:
        for line in fin:
            parse = line.rstrip().split('\t')
            testForm = parse[0]
            fout.write(testForm)
            H = 0.0
            for jCol,con in enumerate(cons):
                nViols = con(testForm)
                fout.write('\t%d' %nViols)
                H += conWts[jCol]*nViols
            fout.write('\t%f\n' %H)
    status('Done!')

print >> sys.stderr, ''
status('The code has finished.')
