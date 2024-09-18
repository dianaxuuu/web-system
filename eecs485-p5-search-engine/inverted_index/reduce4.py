#!/usr/bin/env python3
"""Word count reducer."""
import sys
import itertools


def main():
    """Divide sorted lines into groups that share a key."""
    for _, group in itertools.groupby(sys.stdin, keyfunc):
        reduce_one_group(group)


def keyfunc(line):
    """Return the key from a TAB-delimited key-value pair."""
    return line.partition("\t")[0]


def reduce_one_group(group):
    """Reduce one group."""
    word_doc = {}
    for line in group:
        item = line.partition("\t")[2]
        doc_id, word, idf, term_freq, d_norm = item.split(" ")[:5]
        if word in word_doc:
            word_doc[word].append((doc_id, idf, term_freq, d_norm))
        else:
            word_doc[word] = [(doc_id, idf, term_freq, d_norm), ]

    for word in sorted(word_doc):
        output_line = f"{word} {word_doc[word][0][1]}"
        for doc_id, _, term_freq, d_norm in sorted(word_doc[word]):
            output_line += f" {doc_id} {term_freq} {d_norm[:-1]}"
        print(output_line)


if __name__ == "__main__":
    main()
