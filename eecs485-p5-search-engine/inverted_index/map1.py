#!/usr/bin/env python3
"""Map 1."""
import sys
import csv
import re

csv.field_size_limit(sys.maxsize)
for line in csv.reader(sys.stdin):
    doc_id, doc_title, doc_content = line
    doc_content = re.sub(r"[^a-zA-Z0-9 ]+", "", doc_title + " " + doc_content)
    doc_content = doc_content.casefold()
    doc_content = doc_content.split()

    stop_words = []
    with open("stopwords.txt", "r", encoding='utf-8') as stop_file:
        stop_words = [line.rstrip("\n").casefold() for line in stop_file]

    for word in doc_content:
        if word != "" and word not in stop_words:
            print(f"{doc_id}\t{word}")
