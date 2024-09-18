"""Insta485 model (database) API."""
import sqlite3
import hashlib
import flask
import insta485


def dict_factory(cursor, row):
    """Convert database row objects to a dictionary keyed on column name.

    This is useful for building dictionaries which are then used to render a
    template.  Note that this would be inefficient for large queries.
    """
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def get_db():
    """Open a new database connection.

    Flask docs:
    https://flask.palletsprojects.com/en/1.0.x/appcontext/#storing-data
    """
    if 'sqlite_db' not in flask.g:
        db_filename = insta485.app.config['DATABASE_FILENAME']
        flask.g.sqlite_db = sqlite3.connect(str(db_filename))
        flask.g.sqlite_db.row_factory = dict_factory
        # Foreign keys have to be enabled per-connection.  This is an sqlite3
        # backwards compatibility thing.
        flask.g.sqlite_db.execute("PRAGMA foreign_keys = ON")
    return flask.g.sqlite_db


@insta485.app.teardown_appcontext
def close_db(error):
    """Close the database at the end of a request.

    Flask docs:
    https://flask.palletsprojects.com/en/1.0.x/appcontext/#storing-data
    """
    assert error or not error  # Needed to avoid superfluous style error
    sqlite_db = flask.g.pop('sqlite_db', None)
    if sqlite_db is not None:
        sqlite_db.commit()
        sqlite_db.close()


def authentication():
    """Authenticate the user with this helper function."""
    connectdb = insta485.model.get_db()
    logname = ""
    # Authentication with session cookies
    if "username" not in flask.session:
        # HTTP Basic Access Authentication
        auth = flask.request.authorization
        # No authentication input in command line
        if auth is None:
            context = {
                "message": "Forbidden",
                "status_code": 403
            }
            return flask.jsonify(**context), 403
        username = auth['username']
        password = auth['password']
        cur = connectdb.execute(
            "SELECT * FROM users WHERE username = ? ",
            (username, )
        )
        # Username does not exist
        user = cur.fetchone()
        if user is None:
            context = {
                "message": "Forbidden",
                "status_code": 403
            }
            return flask.jsonify(**context), 403
        # Username does not match password
        algorithm, salt, password_hash_correct = user['password'].split("$")
        hash_obj = hashlib.new(algorithm)
        password_salted = salt + password
        hash_obj.update(password_salted.encode('utf-8'))
        password_hash = hash_obj.hexdigest()
        if password_hash != password_hash_correct:
            context = {
                "message": "Forbidden",
                "status_code": 403
            }
            return flask.jsonify(**context), 403
        logname = username
    else:
        logname = flask.session["username"]
    return logname


def get_10_newest_posts(logname, postid_lte, size, page):
    """Get the most recently 10 posts."""
    connection = get_db()
    if postid_lte is not None:
        cur = connection.execute(
            "SELECT DISTINCT p.postid "
            "FROM posts AS p, following AS f "
            "WHERE f.username1 = ? AND (p.owner = ? OR p.owner = f.username2) "
            "AND p.postid <= ?"
            "ORDER BY postid DESC "
            "LIMIT ? OFFSET ?",
            (logname, logname, postid_lte, size, page*size)
        )
    else:
        cur = connection.execute(
            "SELECT DISTINCT p.postid "
            "FROM posts AS p, following AS f "
            "WHERE f.username1 = ? AND (p.owner = ? OR p.owner = f.username2) "
            "ORDER BY postid DESC "
            "LIMIT ? OFFSET ?",
            (logname, logname, size, page*size)
        )
    return cur.fetchall()


def get_max_postid():
    """Get the max postid."""
    connection = get_db()
    cur = connection.execute(
        "SELECT MAX(postid) as max_postid "
        "FROM posts"
    )
    return cur.fetchall()[0]


def get_post_comments(postid_url_slug):
    """Get post comments."""
    connection = get_db()
    cur = connection.execute(
        "SELECT c.commentid, c.owner, c.text "
        "FROM comments as c "
        "WHERE c.postid = ?",
        (postid_url_slug,)
    )
    return cur.fetchall()


def get_post_details(postid_url_slug):
    """Get the details of the post."""
    connection = get_db()
    cur = connection.execute(
        "SELECT p.postid, p.filename, p.owner, p.created "
        "FROM posts as p "
        "WHERE p.postid = ?",
        (postid_url_slug,)
    )
    return cur.fetchone()


def get_owner_img(post_owner):
    """Get the image of the post owner."""
    connection = get_db()
    cur = connection.execute(
        "SELECT filename "
        "FROM users "
        "WHERE username = ?",
        (post_owner,)
    )
    return cur.fetchone()


def get_logname_likeid(postid_url_slug, logname):
    """Get the likeid of the specific logged in owner."""
    connection = get_db()
    cur = connection.execute(
        "SELECT l.likeid "
        "FROM likes as l "
        "WHERE l.postid = ? AND l.owner = ?",
        (postid_url_slug, logname)
    )
    return cur.fetchone()


def get_likes_count(postid_url_slug):
    """Get number of likes for a specific post."""
    connection = get_db()
    cur = connection.execute(
        "SELECT COUNT(likeid) as count "
        "FROM likes "
        "WHERE postid = ?",
        (postid_url_slug,)
    )
    return cur.fetchall()[0]


def create_one_like(logname, postid):
    """Create a new like."""
    connection = get_db()
    connection.execute(
        "INSERT INTO likes(owner, postid) "
        "VALUES (?, ?)",
        (logname, postid)
    )


def check_like_existence(logname, postid):
    """Check whether the like exists."""
    connection = get_db()
    cur = connection.execute(
        "SELECT likeid "
        "FROM likes "
        "WHERE owner = ? AND postid = ?",
        (logname, postid)
    )
    return cur.fetchone()


def get_like_owner(likeid):
    """Get the owner of the like."""
    connection = get_db()
    cur = connection.execute(
        "SELECT owner "
        "FROM likes "
        "WHERE likeid = ?",
        (likeid,)
    )
    return cur.fetchone()


def delete_one_like(likeid):
    """Delete a like."""
    connection = get_db()
    connection.execute(
        "DELETE FROM likes "
        "WHERE likeid = ?",
        (likeid, )
    )


def add_one_comment(logname, postid, text):
    """Add one comment to a post, return new commentid."""
    connection = get_db()
    cur = connection.execute(
        "INSERT INTO comments(owner, postid, text) "
        "VALUES (?, ?, ?)",
        (logname, postid, text)
    )
    cur = connection.execute(
        "SELECT last_insert_rowid()"
    )
    return cur.fetchone()


def get_comment_owner(commentid):
    """Get the comment owner."""
    connection = get_db()
    cur = connection.execute(
        "SELECT owner "
        "FROM comments "
        "WHERE commentid = ?",
        (commentid,)
    )
    return cur.fetchone()


def delete_one_comment(commentid):
    """Delete a comment."""
    connection = get_db()
    connection.execute(
        "DELETE FROM comments "
        "WHERE commentid = ?",
        (commentid, )
    )
