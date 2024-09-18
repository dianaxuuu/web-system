"""
search views for GET.

URLS include:
/
"""
import re
import threading
import heapq
import requests
import flask
import search

responses = []


def request_index(url, args):
    """Make HTTP requests to the Index servers."""
    response = requests.get(url, params=args, timeout=5)
    responses.append(response.json()["hits"])


@search.app.get('/')
def show_index():
    """Display / rout."""
    # Make concurrent requests to index server
    responses.clear()
    threads = []
    for api_url in search.app.config["SEARCH_INDEX_SEGMENT_API_URLS"]:
        thread = threading.Thread(target=request_index,
                                  args=(api_url, flask.request.args))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    # Merge the results from the responses
    hits = list(heapq.merge(*responses,
                            key=lambda doc: doc["score"], reverse=True))

    # Connect to database
    connectdb = search.model.get_db()
    docs = []
    for i in range(min(10, len(hits))):
        cur = connectdb.execute(
            "SELECT * FROM Documents WHERE docid = ?", (hits[i]["docid"], )
        )
        doc = cur.fetchone()
        summary = doc.get("summary", "")
        url = doc.get("url", "")
        if summary is None or summary == "":
            doc["summary"] = "No summary available"
        if url is None or url == "":
            doc["url"] = "No url available"
        docs.append(doc)

    # Add database info to context
    context = {
        "docs": docs,
        "query": re.sub(r"\+", " ", flask.request.args.get("q", "")),
        "weight": flask.request.args.get("w", 0.5)
    }
    return flask.render_template("index.html", **context)
