#!/usr/bin/python

#|___ you may need to change the python path, depending on your system configurations

# the syll-grammars don't generalize over entire syllables but do adapt for onsets, nuclei and codas
# the Syll-grammars (capital S) in addition generalize over entire syllables

usage = """input2grammar.py
  (c) Ben Boerschinger, 24/01/2013

  starting from on
  (c) Mark Johnson, 7th August, 2012

Reads a py-cfg input file, extracts the tokens [=segments] from it, and writes a
grammar based on those tokens to stdout.
"""

import optparse, re, sys

# top-node for all grammars

ROOT="ROOT"

# easy pattern for vowels, everything not matching is a consonant
global vowel_rex

global vowels, consonants


vowel_rex = None
vowels = None
consonants = None


def makeRule(lhs,rhs,adapt=False):
    if adapt:
        return "%s --> %s"%(lhs,rhs)
    else:
        return "1 1 %s --> %s"%(lhs,rhs) #and uniform Dirichlet Prior

#format required - segments separated by whitespace
def tokens(inf):
    """Returns set of tokens that appear in inf."""
    return set(inf.read().split())
    #return set([x for x in inf.read().split() if x!="lexentry"])

def colloc_header(n):
    """
       generates a collocation header of arbitrary depth and returns it as a string
       that can be written to stdout
    """
    res = []
    res.append(makeRule(ROOT,"Collocations%s"%n))
    #res.append(makeRule(ROOT,"LexEntry Word")) #dummy rule for words
    #res.append(makeRule("LexEntry","lexentry")) #dummy rule for words
    res.append(makeRule("Collocations1","Collocation1"))
    res.append(makeRule("Collocations1","Collocation1 Collocations1"))
    res.append(makeRule("Collocation1","Words",True))
    #res.append(makeRule("Words","Word"))
    #res.append(makeRule("Words","Word Words"))
    for i in range(2,n+1):
        res.append(makeRule("Collocations%d"%i,"Collocation%d"%i))
        res.append(makeRule("Collocations%d"%i,"Collocation%d Collocations%d"%(i,i)))
        res.append(makeRule("Collocation%d"%i,"Collocations%d"%(i-1),True))
    return "\n".join(res)+"\n"



def collocN(n):
    def closure(toks,outf):
        outf.write(colloc_header(n))
        unigram(toks, outf)
    return closure

unigram_header = """1 1 Words --> Word
1 1 Words --> Words Word
Word --> Segs
1 1 Segs --> Seg
1 1 Segs --> Segs Seg
"""

unigram_header_2 = """10 1 Words --> Word
20 1 Words --> Words Word
Word --> Segs
1 1 Segs --> Seg
1 1 Segs --> Segs Seg
"""


def unigram(toks, outf):
    outf.write(unigram_header)
    for tok in toks:
        outf.write("1 1 Seg --> {0}\n".format(tok))

def unigram_2(toks, outf):
    outf.write(unigram_header_2)
    for tok in toks:
        outf.write("1 1 Seg --> {0}\n".format(tok))

    
unigrammorph_header = """1 1 Words --> Word
1 1 Words --> Words Word
Word --> Stem
Word --> Stem Suffix
Stem --> Segs
Suffix --> Segs
1 1 Segs --> Seg
1 1 Segs --> Segs Seg
"""

def unigrammorph(toks, outf):
    outf.write(unigrammorph_header)
    for tok in toks:
        outf.write("1 1 Seg --> {0}\n".format(tok))
 
def collocNmorph(n):
    def closure(toks,outf):
        outf.write(colloc_header(n))
        unigrammorph(toks, outf)
    return closure


# note: this implicitly encodes some kind of performance-constraint, i.e. maximally 4-syllables/word
# for a fully-recursive grammar, use a recursion such as
# Word --> Syllables
# Syllables --> Syl
# Syllables --> Syllables Syl
syll_header = """1 1 Words --> Word
1 1 Words --> Words Word
Word --> Syll
Word --> Syll Syll
Word --> Syll Syll Syll
Word --> Syll Syll Syll Syll
1e-10 Word --> Consonants
1 1 Syll --> Onset Rhyme
1 1 Syll --> Rhyme
1 1 Rhyme --> Nucleus Coda
1 1 Rhyme --> Nucleus
Onset --> Consonants
Nucleus --> Vowels
Coda --> Consonants
1 1 Consonants --> Consonant
1 1 Consonants --> Consonants Consonant
1 1 Vowels --> Vowel
1 1 Vowels --> Vowels Vowel
"""

def syll(toks, outf):
    outf.write(syll_header)
    for v in vowels:
        outf.write('1 1 Vowel --> {}\n'.format(v))
    for c in consonants:
        outf.write('1 1 Consonant --> {}\n'.format(c))

def collocNsyll(n):
    def closure(toks,outf):
        outf.write(colloc_header(n))
        syll(toks, outf)
    return closure

#also contains an implicit constraint, see above
syllIF_header = """1 1 Words --> Word
1 1 Words --> Words Word
Word --> SyllIF
Word --> SyllI SyllF
Word --> SyllI Syll SyllF
Word --> SyllI Syll Syll SyllF
1e-10 Word --> Consonants
1 1 Syll --> Onset Rhyme
1 1 Syll --> Rhyme
1 1 Rhyme --> Nucleus Coda
1 1 Rhyme --> Nucleus
Onset --> Consonants
Nucleus --> Vowels
Coda --> Consonants
1 1 Consonants --> Consonant
1 1 Consonants --> Consonants Consonant
1 1 Vowels --> Vowel
1 1 Vowels --> Vowels Vowel
1 1 SyllIF --> OnsetI RhymeF
1 1 SyllIF --> RhymeF
1 1 SyllI --> OnsetI Rhyme
1 1 SyllI --> Rhyme
1 1 SyllF --> Onset RhymeF
1 1 SyllF --> RhymeF
1 1 RhymeF --> Nucleus CodaF
1 1 RhymeF --> Nucleus
OnsetI --> Consonants
CodaF --> Consonants
"""

def syllIF(toks, outf):
    outf.write(syllIF_header)
    for v in vowels:
        outf.write('1 1 Vowel --> {}\n'.format(v))
    for c in consonants:
        outf.write('1 1 Consonant --> {}\n'.format(c))

def collocNsyllIF(n):
    def closure(toks,outf):
        outf.write(colloc_header(n))
        syllIF(toks, outf)
    return closure


#learns entire syllables
SyllIF_header = """1 1 Words --> Word
1 1 Words --> Words Word
Word --> SyllIF
Word --> SyllI SyllF
Word --> SyllI Syll SyllF
Word --> SyllI Syll Syll SyllF
1e-10 Word --> Consonants
Syll --> Onset Rhyme
Syll --> Rhyme
1 1 Rhyme --> Nucleus Coda
1 1 Rhyme --> Nucleus
Onset --> Consonants
Nucleus --> Vowels
Coda --> Consonants
1 1 Consonants --> Consonant
1 1 Consonants --> Consonants Consonant
1 1 Vowels --> Vowel
1 1 Vowels --> Vowels Vowel
SyllIF --> OnsetI RhymeF
SyllIF --> RhymeF
SyllI --> OnsetI Rhyme
SyllI --> Rhyme
SyllF --> Onset RhymeF
SyllF --> RhymeF
1 1 RhymeF --> Nucleus CodaF
1 1 RhymeF --> Nucleus
OnsetI --> Consonants
CodaF --> Consonants
"""

def SyllIF(toks, outf):
    outf.write(SyllIF_header)
    for v in vowels:
        outf.write('1 1 Vowel --> {}\n'.format(v))
    for c in consonants:
        outf.write('1 1 Consonant --> {}\n'.format(c))

def collocNSyllIF(n):
    def closure(toks,outf):
        outf.write(colloc_header(n))
        SyllIF(toks, outf)
    return closure

#learns entire syllables
Syll_header = """1 1 Words --> Word
1 1 Words --> Words Word
Word --> Syll
Word --> Syll Syll
Word --> Syll Syll Syll
Word --> Syll Syll Syll Syll
1e-10 Word --> Consonants
Syll --> Onset Rhyme
Syll --> Rhyme
1 1 Rhyme --> Nucleus Coda
1 1 Rhyme --> Nucleus
Onset --> Consonants
Nucleus --> Vowels
Coda --> Consonants
1 1 Consonants --> Consonant
1 1 Consonants --> Consonants Consonant
1 1 Vowels --> Vowel
1 1 Vowels --> Vowels Vowel
"""

#Abdellah 31 jan 2013: learn entire syllables but without the sub-syllabic structure
Syll_header_bis = """1 1 Words --> Word
1 1 Words --> Words Word
Word --> Syll
Word --> Syll Syll
Word --> Syll Syll Syll
Word --> Syll Syll Syll Syll
Word --> Syll Syll Syll Syll Syll
Word --> Syll Syll Syll Syll Syll Syll
Syll --> Onset Rhyme
Syll --> Rhyme
1 1 Rhyme --> Nucleus Coda
1 1 Rhyme --> Nucleus
1 1 Onset --> Consonants
1 1 Nucleus --> Vowels
1 1 Coda --> Consonants
1 1 Consonants --> Consonant
1 1 Consonants --> Consonants Consonant
1 1 Vowels --> Vowel
1 1 Vowels --> Vowels Vowel
"""
levels_header = """1 1 ROOT --> Collocations
1 1 Collocations --> Collocation
1 1 Collocations --> Collocations Collocation
Collocation --> Words
1 1 Words --> Word
1 1 Words --> Words Word
Word --> Sylls
1 1 Sylls --> Syll
1 1 Sylls --> Sylls Syll
Syll --> Segs
1 1 Segs --> Seg
1 1 Segs --> Segs Seg
"""
def levels(toks, outf):
    outf.write(levels_header)
    for tok in toks:
	outf.write("1 1 Seg --> {0}\n".format(tok))

def Syllnew(toks, outf):
    outf.write(Syll_header_bis)
    for tok in toks:
        outf.write('1 1 Vowel --> {0}\n'.format(tok))
        outf.write('1 1 Consonant --> {0}\n'.format(tok))

def Syllsup(toks, outf):
    outf.write(Syll_header_bis)
    for v in vowels:
        outf.write('80000 1 Vowel --> {0}\n'.format(v))
        outf.write('20000 1 Consonant --> {0}\n'.format(v))
    for c in consonants:
        outf.write('20000 1 Vowel --> {0}\n'.format(c))
        outf.write('80000 1 Consonant --> {0}\n'.format(c))

def Syll(toks, outf):
    outf.write(Syll_header)
    for v in vowels:
        outf.write('1 1 Vowel --> {0}\n'.format(v))
    for c in consonants:
        outf.write('1 1 Consonant --> {0}\n'.format(c))

def collocNSyllnew(n):
    def closure(toks,outf):
        outf.write(colloc_header(n))
        Syllnew(toks, outf)
    return closure

def collocNSyllsup(n):
    def closure(toks,outf):
        outf.write(colloc_header(n))
        Syllsup(toks, outf)
    return closure

def collocNSyll(n):
    def closure(toks,outf):
        outf.write(colloc_header(n))
        Syll(toks, outf)
    return closure
        
# grammar_writer maps the grammar's name to
# the program that writes that grammar

grammar_writer = { 'colloc':collocN(1), 
                   'colloc2':collocN(2),
                   'colloc3':collocN(3),
                   'colloc4':collocN(4),
                   'colloc5':collocN(5),
                   'collocmorph':collocNmorph(1),
                   'colloc2morph':collocNmorph(2),
                   'colloc3morph':collocNmorph(3),
                   'colloc4morph':collocNmorph(4),
                   'colloc5morph':collocNmorph(5),
                   'collocsyll':collocNsyll(1),
                   'colloc2syll':collocNsyll(2),
                   'colloc3syll':collocNsyll(3),
                   'colloc4syll':collocNsyll(4),
                   'colloc5syll':collocNsyll(5),
                   'collocSyll':collocNSyll(1),
                   'colloc2Syll':collocNSyll(2),
                   'colloc3Syll':collocNSyll(3),
                   'colloc4Syll':collocNSyll(4),
                   'colloc5Syll':collocNSyll(5),
		   'collocSyllnew':collocNSyllnew(1),
		   'collocSyllsup':collocNSyllsup(1),
                   'syll':syll,
                   'Syll':Syll,
		   'Syllnew':Syllnew,
		   'Syllsup':Syllsup,
                   'unigram':unigram,
                   'unigram2':unigram_2,
		   'levels':levels,
                   'unigrammorph':unigrammorph,
		   'unigram':unigram,
                   'syllIF':syllIF,
                   'collocsyllIF':collocNsyllIF(1),
                   'colloc2syllIF':collocNsyllIF(2),
                   'colloc3syllIF':collocNsyllIF(3),
                   'colloc4syllIF':collocNsyllIF(4),
                   'colloc5syllIF':collocNsyllIF(5),
                   'SyllIF':SyllIF,
                   'collocSyllIF':collocNSyllIF(1),
                   'colloc2SyllIF':collocNSyllIF(2),
                   'colloc3SyllIF':collocNSyllIF(3),
                   'colloc4SyllIF':collocNSyllIF(4),
                   'colloc5SyllIF':collocNSyllIF(5),
                   }

if __name__ == '__main__':
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-g", "--grammar", dest="grammar", default="unigram",
                      help="type of grammar to produce")
    parser.add_option("-l", "--list-grammars", dest='list_grammars', action='store_true',
                      help="print out names of grammars that we can generate")
    parser.add_option("-v", "--vowel-re", dest="vowel_re",
                      #default=r"^.*[aeiou]:?.*$",
		      #default=r"^.*-[aeiou]:?\+.*$",
		      #default=r"^.*[aeiou][maeywohyrnl]?.*$",
		      default=r"^.*-[aeiou][maeywohyrnl]?\+.*$",
                      help="regex identifying vowel segments")
    options, args = parser.parse_args()

    if options.list_grammars:
        sys.stdout.write(' '.join(sorted(grammar_writer.keys())))
        sys.stdout.write('\n')
        sys.exit(0)

    writer = grammar_writer.get(options.grammar)
    if not writer:
        sys.exit("Unknown grammar: {0}\nAvailable grammars: {1}\n".format(
                options.grammar, ' '.join(sorted(grammar_writer.keys()))))

    if len(args) == 0:
        inf = sys.stdin
    else:
        assert(len(args) == 1)
        inf = open(args[0], "rU")

    toks = tokens(inf)

    vowel_rex = re.compile(options.vowel_re)
    vowels = [tok for tok in toks if vowel_rex.match(tok)]
    consonants = [tok for tok in toks if not vowel_rex.match(tok)]

    writer(toks, sys.stdout)
