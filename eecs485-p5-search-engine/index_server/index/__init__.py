"""index package initializer."""
import os
import flask
# app is a single object used by all the code modules in this package
app = flask.Flask(__name__)  # pylint: disable=invalid-name
app.config["INDEX_PATH"] = os.getenv("INDEX_PATH", "inverted_index_1.txt")
import index.api    # noqa: E402  pylint: disable=wrong-import-position
import index.api.get    # noqa: E402  pylint: disable=wrong-import-position

index.api.get.load_index(app.config["INDEX_PATH"])
