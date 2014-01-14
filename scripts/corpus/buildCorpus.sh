#assuming that pakna_test has already been built
#this generates a random corpus for a random language
#does not rebuild the lexicon if already has been built

lang=$1
version=$2
# checking for existence of lexicon
if ! [ -e scored_${lang}.txt ]
then
  echo Generating the base distribution by executing the following:
  echo python phoment.py pakna_feats.txt -w ./ -g grammar_${lang}.txt -T pakna_test.txt -o scored_${lang}.txt
python phoment.py pakna_feats.txt -w ./ -g grammar_${lang}.txt -T pakna_test.txt -o scored_${lang}.txt
fi

echo Generating a pseudo-${lang} corpus by executing the following:
echo python makeCorpFromScoresAndFreqs.py scored_${lang}.txt freq-dist_brent.txt -o corpus_${lang}_${version}.txt -m -25.0 -p 0.25
python makeCorpFromScoresAndFreqs.py scored_${lang}.txt freq-dist_brent.txt -o corpus_${lang}_${version}.txt -m -25.0 -p 0.25

echo Now you can inspect the output file corpus_${lang}_${version}.txt
