#!/usr/bin/env python3
"""Word count reducer."""
import sys
import itertools


def main():
    """Divide sorted lines into groups that share a key."""
    for key, group in itertools.groupby(sys.stdin, keyfunc):
        reduce_one_group(key, list(group))


def keyfunc(line):
    """Return the key from a TAB-delimited key-value pair."""
    return line.partition("\t")[0]


def reduce_one_group(key, group):
    """Reduce one group."""
    # first pass: caculate normalization factor
    sum_sq = 0.0
    for line in group:
        _, term_freq, idf = line.partition("\t")[2].split(" ")
        tf_idf = float(term_freq) * float(idf[:-1])
        sum_sq += tf_idf * tf_idf

    # print the corresponding output format
    for line in group:
        word, term_freq, idf = line.partition("\t")[2].split(" ")
        print(f"{int(key) % 3}\t{key} {word} {idf[:-1]} {term_freq} {sum_sq}")


if __name__ == "__main__":
    main()
