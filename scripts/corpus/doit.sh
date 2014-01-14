echo Making the test file by executing the following:
echo python make_pakna.py
python make_pakna.py

echo Generating the base distribution by executing the following:
echo python phoment.py pakna_feats.txt -w ./ -g grammar_hawaiian.txt -T pakna_test.txt -o scored_hawaiian.txt
python phoment.py pakna_feats.txt -w ./ -g grammar_hawaiian.txt -T pakna_test.txt -o scored_hawaiian.txt

echo Generating a pseudo-Hawaiian corpus by executing the following:
echo python makeCorpFromScoresAndFreqs.py scored_hawaiian.txt freq-dist_brent.txt -o corpus_hawaiian.txt -m -25.0 -p 0.25
python makeCorpFromScoresAndFreqs.py scored_hawaiian.txt freq-dist_brent.txt -o corpus_hawaiian.txt -m -25.0 -p 0.25

echo Now you can inspect the output file corpus_hawaiian.txt
