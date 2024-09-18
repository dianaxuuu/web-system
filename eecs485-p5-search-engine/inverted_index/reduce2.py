#!/usr/bin/env python3
"""Reduce 1."""

import sys
import itertools
import math


def main():
    """Divide sorted lines into groups that share a key."""
    for key, group in itertools.groupby(sys.stdin, keyfunc):
        reduce_one_group(key, list(group))


def keyfunc(line):
    """Return the key from a TAB-delimited key-value pair."""
    return line.partition("\t")[0]


def reduce_one_group(key, group):
    """Reduce one group."""
    num_docs = 0
    with open("total_document_count.txt", "r",
              encoding='utf-8') as num_docs_file:
        num_docs = int(num_docs_file.read())

    idf = math.log(num_docs / len(group), 10)

    for line in group:
        partial = line.partition("\t")[2]
        doc_id, term_freq = partial.split(" ")[:2]
        print(f"{doc_id}\t{key} {term_freq[:-1]} {idf}")


if __name__ == "__main__":
    main()
