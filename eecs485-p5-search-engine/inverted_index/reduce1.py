#!/usr/bin/env python3
"""Reduce 1."""

import sys
import itertools


def main():
    """Divide sorted lines into groups that share a key."""
    for key, group in itertools.groupby(sys.stdin, keyfunc):
        reduce_one_group(key, group)


def keyfunc(line):
    """Return the key from a TAB-delimited key-value pair."""
    return line.partition("\t")[0]


def reduce_one_group(key, group):
    """Reduce one group."""
    term_freq = {}
    for line in group:
        word = line.partition("\t")[2][:-1]
        if word in term_freq:
            term_freq[word] += 1
        else:
            term_freq[word] = 1

    for word, freq in term_freq.items():
        print(f"{word}\t{key} {freq}")


if __name__ == "__main__":
    main()
