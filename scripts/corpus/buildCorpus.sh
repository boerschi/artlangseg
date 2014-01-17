#assuming that pakna_test has already been built
#this generates a random corpus for a random language
#does not rebuild the lexicon if already has been built

lang=$1
struct=$2
version=$3
if ! [ -e pakna_test.txt ]
then
  echo Generating pakna_test
  echo python make_pakna.py
  python make_pakna.py
fi

# checking for existence of lexicon
if ! [ -e scored_${lang}_${struct}.gz ]
then
  echo Generating the base distribution by executing the following:
  echo python phomentCompress.py pakna_feats.txt -w ./ -g grammar_${lang}_${struct}.txt -T pakna_test.txt | gzip > scored_${lang}_${struct}.txt
python phomentCompress.py pakna_feats.txt -w ./ -g grammar_${lang}_${struct}.txt -T pakna_test.txt | gzip > scored_${lang}_${struct}.gz
fi

echo Generating a pseudo-${lang} corpus by executing the following:
echo python makeCorpFromScoresAndFreqs.py scored_${lang}.txt freq-dist_brent.txt -o corpus_${lang}_${version}.txt -m -25.0 -p 0.25
zcat scored_${lang}_${struct}.gz | python makeCorpFromScoresAndFreqs.py freq-dist_brent.txt -o corpus_${lang}_${struct}_${version}.txt -m -25.0 -p 0.25

echo Now you can inspect the output file corpus_${lang}_${version}.txt
