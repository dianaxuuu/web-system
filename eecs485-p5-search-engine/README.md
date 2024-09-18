### Inverted Index Pipeline Design:

* job1: calculate __term frequency (tf)__ for each term in each document
    * map1.py:      clean the input text, output format: __{doc_id}\t{word}__
    * reduce1.py:   output format: __{word}\t{doc_id} {tf}__
* job2: calculate __inverse document frequency (idf)__ for each term
    * map2.py:      identity mapper, echo the input as output
    * reduce2.py:   output format: __{doc_id}\t{word} {tf} {idf}__
* job3: calculate __normalization factor (|d|)__ for each document
    * map3.py:      identity mapper, echo the input as output
    * reduce3.py:   output format: __{doc_id % 3}\t{doc_id} {word} {idf} {tf} {|d|}__
* job4: output the final format
    * map4.py:      identity mapper, echo the input as output
    * reduce4.py:   output the final format __{word} {idf} ({doc_id} {tf} {|d|})+__
 to 3 different files
