import doctest,sys

SBSYMBOL=""
WBSYMBOL=" "

def getBVec(t,ignoreSyll=True):
    """get a vector-representation of a segmentation, 's' indicates syllable, 'b' a word-boundary, 'n' absence of a boundary

    >>> getBVec("the kit.ty")
    ["n","n","b","n","n","n","n"]

    >>> getBVec("the kit.ty",False)
    ["n","n","b","n","n","s","n"]
    """
    res = []
    pos = 1
    if ignoreSyll:
        t = t.replace(SBSYMBOL,"")
    while pos<len(t):
        if t[pos]==SBSYMBOL:
            res.append("s")
            pos+=2
        elif t[pos]==WBSYMBOL:
            res.append("b")
            pos+=2
        else:
            res.append("n")
            pos+=1
    return res

def segment(text,vec):
    """given a vectorial segmentation of text, generate the segmented string
    
    @text  an unsegmented string, e.g. "thekitty"
    @vec   a list indicating the segmentation, using "n" for indicating absence of any boundary, a "s" for presence of syllable and "b" for presence of word boundary

    >>> segment("thekitty",["n","n","b","n","n","s","n"])
    "the kit.ty"
    """
    text = text.replace(SBSYMBOL,"").replace(WBSYMBOL,"")
#    print text,vec
    res = []
    buf = [text[0]]
    spos=1
    try:
        for b in vec:
            if b=="n":
                buf.append(text[spos])
                spos+=1
            elif b=="s":
                buf.append(SBSYMBOL)
                buf.append(text[spos])
                spos+=1
            elif b=="b":
                res.append(''.join(buf))
                buf=[text[spos]]
                spos+=1
            else:
                raise ValueError("Invalid boundary indicator: %s"%b)
        res.append(''.join(buf))
    except:
        sys.stderr.write("%s %s\n"%(text,vec))
        sys.exit(1)
    return WBSYMBOL.join(res)


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
        if s[sPos]==WBSYMBOL:
            res.add((start,i))
            sPos+=1
            start=i
        else: 
            sPos+=1
            i+=1
    res.add((start,i))
    return res
