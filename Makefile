# AdaptorGrammar/Makefile
#  modified by ben boerschinger, 10/12/13 
#
#  (c) Mark Johnson, 20th July 2012
#
#
# Makefile for Adaptor Grammar word segmentation

# set default shell
#
SHELL=/bin/bash

# DIR is the base directory in which we work (all files produced are
# relative to this directory)
#
DIR:=runs

# OUTPUTPREFIX is a prefix prepended to all temporary and output run
# files (change this for a new run)
#
OUTPUTPREFIX=r00

# the model we use
GRAMMAR=unigram

LANGUAGE=geo
# #which language is used
# GOLDB=200
# #which concentration parameter was used in generating the data
# SET=01
# #which random set
# SOURCE=data/$(LANGUAGE)/$(LANGUAGE)_$(GOLDB)_$(SET).txt
# EVALDIR:=$(DIR)/$(LANGUAGE)_$(GOLDB)_$(GRAMMAR)Eval
# TMPDIR:=$(DIR)/$(LANGUAGE)_$(GOLDB)_$(GRAMMAR)Tmp

SOURCE=data/corpus_$(LANGUAGE).txt
EVALDIR:=$(DIR)/$(LANGUAGE)_$(GRAMMAR)Eval
TMPDIR:=$(DIR)/$(LANGUAGE)_$(GRAMMAR)Tmp

# BURNINSKIP is the fraction of the sample to be discarded before collecting 
# samples for evaluation
BURNINSKIP=0.8

# PYFLAGS specify flags to be given to py-cfg, e.g., -P (predictive filter)
PYFLAGS=-d 10 -P

# OUTS is a list of types of output files we're going to produce
OUTS=trscore

# Each fold is a different run; to do 8 runs set FOLDS=0 1 2 3 4 5 6 7
#FOLDS=01 02
FOLDS=1

# PYCFG is the py-cfg program (including its path)
#
PYCFG=./py-cfg/py-cfg


# see PYCFG help for explanation
# no discount
PYAS=0 #disable discount, set to 0

PYBS=1 #if no hyper-parameter sampling, set to gold

PYGS=100 #if no hyper-parameter sampling, set to -1, otherwise 100
PYHS=0.01 #if no hyper-parameter sampling, set to -1, otherwise 0.01

PYWS=1   #uniform dirichlet prior, but we do not estimate the rule probabilities

# PYNS is the number of iterations, 1000 ought to be plenty
PYNS=1000

# PYRS controls how long we do table label resampling for (-1 = forever), shouldn't matter here
PYRS=-1

# rate at which model's output is evaluated
TRACEEVERY=10

# EXEC is the prefix used to execute the py-cfg command
EXEC=time
# EXEC=valgrind

# EVALREGEX is the regular expression given to eval.py in the evaluation script (may depend on grammar)
# EVALREGEX=Colloc\\b
# basically, which Non-Terminal symbol is supposed to correspond to a word
EVALREGEX=^Word

# IGNORETERMINALREGEX is the regular expression given to eval.py in the evaluation script
IGNORETERMINALREGEX=^[$$]{3}$$

# WORDSPLITREGEX is the regular expression given to eval.py in the evaluation script
WORDSPLITREGEX=[ ]+

################################################################################
#                                                                              #
#                     everything below this should be generic                  #
#                                                                              #
################################################################################

# INPUTFILE is the file that contains the adaptor grammar input
#
INPUTFILE:=$(TMPDIR)/AGinput.txt

# GOLDFILE is the file that contains word boundaries that will be used to
# evaluate the adaptor grammar word segmentation
#
GOLDFILE:=$(TMPDIR)/AGgold.txt


# The list of files we will make
OUTPUTS=$(foreach GRAMMAR,$(GRAMMAR), \
	$(foreach g,$(PYGS), \
	$(foreach h,$(PYHS), \
	$(foreach b,$(PYBS), \
	$(foreach w,$(PYWS), \
	$(foreach n,$(PYNS), \
	$(foreach R,$(PYRS), \
	$(foreach out,$(OUTS), \
	$(EVALDIR)/$(OUTPUTPREFIX)_G$(GRAMMAR)_E_n$(n)_w$(w)_b$(b)_g$(g)_h$(h)_R$(R)_s$(SET).$(out)))))))))

TARGETS=$(OUTPUTS)

.PHONY: top
top: $(TARGETS)

.SECONDARY:
.DELETE_ON_ERROR:

getarg=$(patsubst $(1)%,%,$(filter $(1)%,$(subst _, ,$(2))))

keyword=$(patsubst $(1),-$(1),$(filter $(1),$(subst _, ,$(2))))

GRAMMARFILES=$(foreach g,$(GRAMMAR),$(TMPDIR)/$(g).gr)

#calculate scores from the average parses, i.e. from doing MBR decoding across multiple samples
$(EVALDIR)/$(OUTPUTPREFIX)_%.trscore: $(TMPDIR)/$(OUTPUTPREFIX)_%.travprs prog_seg/eval.py
	mkdir -p $(EVALDIR)
	prog_seg/eval.py --gold $(GOLDFILE) --train $< --score-cat-re="$(EVALREGEX)" --ignore-terminal-re="$(IGNORETERMINALREGEX)" --word-split-re=" " > $@	

#generate the MBR solution from multiple samples
$(TMPDIR)/$(OUTPUTPREFIX)_%.travprs: prog_seg/mbr.py $(foreach fold,$(FOLDS),$(TMPDIR)/$(OUTPUTPREFIX)_%_$(fold).trsws)
	$^ > $@

#produce samples from a single run = run the actual experiments
$(TMPDIR)/$(OUTPUTPREFIX)_%.trsws: $(PYCFG) $(GRAMMARFILES) $(GOLDFILE) $(INPUTFILE)
	mkdir -p $(TMPDIR)
	echo "Starting $@"
	date
	$(EXEC) $(PYCFG) $(PYFLAGS) \
		-A $(basename $@).prs \
		-F $(basename $@).trace \
		-G $(basename $@).wlt \
		-C \
		-d 101 \
		-D \
		-E \
		-r $$RANDOM$$RANDOM \
		-a $(PYAS) \
		-b $(call getarg,b,$(*F)) \
		-g $(call getarg,g,$(*F)) \
		-h $(call getarg,h,$(*F)) \
		-w $(call getarg,w,$(*F)) \
		-n $(call getarg,n,$(*F)) \
		-R $(call getarg,R,$(*F)) \
		-x $(TRACEEVERY) \
		-X "prog_seg/eval.py --gold $(GOLDFILE) --train-trees --score-cat-re=\"$(EVALREGEX)\" --ignore-terminal-re=\"$(IGNORETERMINALREGEX)\" --word-split-re=\" \" > $(basename $@).trweval" \
		-X "prog_seg/trees-words.py --ignore-terminal-re=\"$(IGNORETERMINALREGEX)\" --score-cat-re=\"$(EVALREGEX)\" --nepochs $(call getarg,n,$(*F)) --rate $(TRACEEVERY) --skip $(BURNINSKIP) > $(basename $@).trsws" \
		$(TMPDIR)/$(call getarg,G,_$(*F)).gr \
		< $(INPUTFILE)

# produce the input grammar
$(TMPDIR)/%.gr: prog_seg/input2grammar.py $(INPUTFILE)
	$^ --grammar $(*F) > $@

# produce the input file, i.e. make format suitable for adaptor grammar
$(INPUTFILE): prog_seg/source2AGinput.py $(SOURCE)
	mkdir -p $(TMPDIR)
	cat $(SOURCE) | prog_seg/source2AGinput.py -w " # " > $@ 

# produce a gold file, 
$(GOLDFILE): prog_seg/source2AGinput.py $(SOURCE)
	mkdir -p $(TMPDIR)
	cat $(SOURCE) | prog_seg/source2AGinput.py --gold -w " # " > $@

.PHONY: clean
clean: 
	rm -fr $(TMP)

.PHONY: real-clean
real-clean: clean
	rm -fr $(OUTPUTDIR)
