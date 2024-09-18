"""
Index api for GET.

URLS include:
/api/v1/
/api/v1/hits/
"""

import re
from math import sqrt
import flask
import index

inverted_index = {}
stop_words = []
page_rank = {}


def load_index(index_path):
    """Load inverted_index, stopwords.txt and pagerank.out."""
    # load inverted_index
    with open(f"index_server/index/inverted_index/{index_path}",
              encoding='utf-8') as ii_file:
        for line in ii_file:
            items = line.rstrip("\n").split(" ")
            word = items[0]
            inverted_index[word] = {
                "idf": float(items[1]),
                "docs": [],
            }
            for i in range(2, len(items), 3):
                doc = {
                    "id": int(items[i]),
                    "tf": int(items[i + 1]),
                    "d": sqrt(float(items[i + 2]))
                }
                inverted_index[word]["docs"].append(doc)
    # load stopwords.txt
    with open("index_server/index/stopwords.txt",
              encoding='utf-8') as stop_file:
        for line in stop_file:
            stop_words.append(line.rstrip("\n").casefold())
    # load pagerank.out
    with open("index_server/index/pagerank.out",
              encoding='utf-8') as pr_file:
        for line in pr_file:
            key, val = line.rstrip("\n").split(",")
            page_rank[int(key)] = float(val)


@index.app.get('/api/v1/')
def get_services():
    """Get a list of services available."""
    context = {
        "hits": "/api/v1/hits/",
        "url": "/api/v1/"
    }
    return flask.jsonify(**context), 200


@index.app.get('/api/v1/hits/')
def get_hits():
    """Get a list of ordered hits of the query."""
    query = flask.request.args.get('q', "")
    weight = flask.request.args.get('w', 0.5, float)
    context = {"hits": []}

    # clean the query and calculate tf for the query
    query = re.sub(r"\+", " ", query)
    query = re.sub(r"[^a-zA-Z0-9 ]+", "", query)
    query = query.casefold()
    vec_q = {}
    for word in query.split():
        if word != "" and word not in stop_words:
            if word not in inverted_index:
                return flask.jsonify(**context), 200
            if word in vec_q:
                vec_q[word] += 1
            else:
                vec_q[word] = 1
    if not vec_q:
        return flask.jsonify(**context), 200

    # find the hits
    word = list(vec_q.keys())[0]
    hits = {doc["id"] for doc in inverted_index[word]["docs"]}
    for word in vec_q:
        hits = hits.intersection({doc["id"] for doc in
                                  inverted_index[word]["docs"]})

    # calculate vec_q and norm_q
    norm_q = 0.0
    for word in vec_q:
        vec_q[word] *= inverted_index[word]["idf"]
        norm_q += vec_q[word] ** 2
    norm_q = sqrt(norm_q)

    for hit in hits:
        # calculate tfidf for each document
        vec_d = {}
        tfidf = 0.0
        norm_d = 0.0
        for word, val_q in vec_q.items():
            # calculate vec_d
            for doc in inverted_index[word]["docs"]:
                if doc["id"] == hit:
                    vec_d[word] = doc["tf"] * inverted_index[word]["idf"]
                    norm_d = doc["d"]
                    break
            tfidf += val_q * vec_d[word]
        tfidf /= norm_q * norm_d

        # calculate score for each hit
        score = weight * page_rank[hit] + (1 - weight) * tfidf
        context["hits"].append({
            "docid": hit,
            "score": score
        })

    # sort the hits by their scores
    context["hits"].sort(key=lambda hit: hit["score"], reverse=True)
    return flask.jsonify(**context), 200
