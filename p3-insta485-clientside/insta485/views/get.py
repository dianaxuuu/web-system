"""
Insta485 views for GET.

URLs include:
/
/users/<username>/
/users/<username>/followers/
/users/<username>/following/
/posts/<postid>/
/explore/
/accounts/login/
/accounts/create/
/accounts/delete/
/accounts/edit/
/accounts/password/
"""
# from multiprocessing import connection
# from sqlite3 import connect
import flask
import arrow
from flask import request
from flask import send_from_directory
import insta485


@insta485.app.get('/')
def show_index():
    """Display / route."""
    # If not logged in, redirect to /accounts/login/
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('show_login'))

    # Connect to database
    connectdb = insta485.model.get_db()

    # Query database
    logname = flask.session["username"]
    cur = connectdb.execute(
        "SELECT posts.postid, posts.filename AS img_url, posts.owner, "
        "posts.created AS timestamp, users.filename AS owner_img_url "
        "FROM (posts INNER JOIN users ON posts.owner=users.username)"
        "WHERE posts.owner = ? OR "
        "posts.owner= ( SELECT username2 FROM following WHERE username1 = ? ) "
        "ORDER BY posts.postid DESC",
        (logname, logname, )
    )
    posts = cur.fetchall()
    # humanize timestamp, find comments and likes for each post
    fmt = "YYYY-MM-DD HH:mm:ss"
    for post in posts:
        post["timestamp"] = arrow.get(post["timestamp"], fmt).humanize()
        cur = connectdb.execute(
            "SELECT COUNT(likeid) AS likes FROM likes WHERE postid = ? ",
            (post["postid"], )
        )
        post["likes"] = cur.fetchall()[0]["likes"]
        cur = connectdb.execute(
            "SELECT owner, text FROM comments WHERE postid = ? "
            "ORDER BY commentid",
            (post["postid"], )
        )
        post["comments"] = cur.fetchall()
        # Find likes owners
        # If the logged in user is included,
        # use unlike button; otherwise, use like button
        cur = connectdb.execute(
            "SELECT COUNT(likeid) AS like FROM likes "
            "WHERE postid = ? AND owner = ?",
            (post["postid"], logname, )
        )
        post["like_botton"] = cur.fetchall()[0]["like"]

    # Add database info to context
    context = {"logname": logname, "posts": posts, "curr_path": request.path}
    return flask.render_template("index.html", **context)


@insta485.app.get('/users/<username>/')
def show_user(username):
    """Display /users/<username>/ route."""
    # If not logged in, redirect to /accounts/login/
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('show_login'))
    logname = flask.session["username"]

    # Connect to database
    connectdb = insta485.model.get_db()

    # Query databse
    # check if <username> exists in the databse, if not, abort(404)
    cur = connectdb.execute(
        "SELECT * FROM users WHERE username = ? ",
        (username, )
    )
    if cur.fetchone() is None:
        flask.abort(404)
    # find if <logname> follows <username>
    cur = connectdb.execute(
        "SELECT * FROM following WHERE username1 = ? AND username2 = ?",
        (logname, username, )
    )
    logname_follows_username = not cur.fetchone() is None
    # count the total posts of <username>
    cur = connectdb.execute(
        "SELECT COUNT(postid) AS count FROM posts WHERE owner = ? ",
        (username, )
    )
    total_posts = cur.fetchall()[0]["count"]
    # count followers and following of <username>
    cur = connectdb.execute(
        "SELECT COUNT(username1) AS count FROM following "
        "WHERE username2 = ? ",
        (username, )
    )
    followers = cur.fetchall()[0]["count"]
    cur = connectdb.execute(
        "SELECT COUNT(username2) AS count FROM following "
        "WHERE username1 = ? ",
        (username, )
    )
    following = cur.fetchall()[0]["count"]
    # find the full name of <username>
    cur = connectdb.execute(
        "SELECT fullname FROM users WHERE username = ? ",
        (username, )
    )
    fullname = cur.fetchall()[0]["fullname"]
    # find the posts of <username>
    cur = connectdb.execute(
        "SELECT postid, filename AS img_url FROM posts WHERE owner = ? ",
        (username, )
    )
    posts = cur.fetchall()

    # Add database info to context
    context = {"logname": logname, "username": username, "fullname": fullname,
               "logname_follows_username": logname_follows_username,
               "total_posts": total_posts, "followers": followers,
               "following": following,
               "posts": posts, "curr_path": request.path}
    return flask.render_template("user.html", **context)


@insta485.app.get('/users/<username>/followers/')
def show_followers(username):
    """Display /users/<username>/followers/ route."""
    # If not logged in, redirect to /accounts/login/
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('show_login'))
    logname = flask.session["username"]

    # Connect to database
    connectdb = insta485.model.get_db()

    # Query databse
    # check if <username> exists in the databse, if not, abort(404)
    cur = connectdb.execute(
        "SELECT * FROM users WHERE username = ? ",
        (username, )
    )
    if cur.fetchone() is None:
        flask.abort(404)
    # find followers of <username>
    cur = connectdb.execute(
        "SELECT users.filename AS user_img_url, users.username "
        "FROM (users INNER JOIN following "
        "ON users.username=following.username1 ) "
        "WHERE following.username2 = ? ",
        (username, )
    )
    followers = cur.fetchall()
    # find if <logname> is following each follower
    for follower in followers:
        cur = connectdb.execute(
            "SELECT * FROM following WHERE username1 = ? AND username2 = ? ",
            (logname, follower["username"], )
        )
        follower["logname_follows_username"] = not cur.fetchone() is None

    # Add database info to context
    context = {"logname": logname, "username": username,
               "followers": followers, "curr_path": request.path}
    return flask.render_template("followers.html", **context)


@insta485.app.get('/users/<username>/following/')
def show_following(username):
    """Display /users/<username>/following/ route."""
    # If not logged in, redirect to /accounts/login/
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('show_login'))
    logname = flask.session["username"]

    # Connect to database
    connectdb = insta485.model.get_db()

    # Query databse
    # check if <username> exists in the databse, if not, abort(404)
    cur = connectdb.execute(
        "SELECT * FROM users WHERE username = ? ",
        (username, )
    )
    if cur.fetchone() is None:
        flask.abort(404)
    # find following of <username>
    cur = connectdb.execute(
        "SELECT users.filename AS user_img_url, users.username "
        "FROM (users INNER JOIN following "
        "ON users.username=following.username2 ) "
        "WHERE following.username1 = ? ",
        (username, )
    )
    following = cur.fetchall()
    # find if <logname> is following each follower
    for follow in following:
        cur = connectdb.execute(
            "SELECT * FROM following WHERE username1 = ? AND username2 = ? ",
            (logname, follow["username"], )
        )
        follow["logname_follows_username"] = not cur.fetchone() is None

    # Add database info to context
    context = {"logname": logname, "username": username,
               "following": following, "curr_path": request.path}
    return flask.render_template("following.html", **context)


@insta485.app.get('/posts/<int:postid>/')
def show_post(postid):
    """Display /posts/<postid>/ route."""
    # If not logged in, redirect to /accounts/login/
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('show_login'))
    logname = flask.session["username"]

    # Connect to database
    connectdb = insta485.model.get_db()

    # Query databse
    cur = connectdb.execute(
        "SELECT posts.filename AS img_url, posts.owner, "
        "posts.created AS timestamp, users.filename AS owner_img_url "
        "FROM (posts INNER JOIN users ON posts.owner=users.username)"
        "WHERE posts.postid = ? ",
        (postid, )
    )
    post = cur.fetchall()[0]
    fmt = "YYYY-MM-DD HH:mm:ss"
    post["timestamp"] = arrow.get(post["timestamp"], fmt).humanize()
    # find comments and likes
    cur = connectdb.execute(
        "SELECT COUNT(likeid) AS likes FROM likes WHERE postid = ? ",
        (postid, )
    )
    likes = cur.fetchall()[0]["likes"]
    cur = connectdb.execute(
        "SELECT owner, text, commentid FROM comments WHERE postid = ? "
        "ORDER BY commentid",
        (postid, )
    )
    comments = cur.fetchall()
    # Find likes owners
    # If the logged in user is included,
    # use unlike button; otherwise, use like button
    cur = connectdb.execute(
        "SELECT COUNT(likeid) AS like FROM likes "
        "WHERE postid = ? AND owner = ?",
        (postid, logname, )
    )
    post["like_botton"] = cur.fetchall()[0]["like"]

    # Add database info to context
    context = {"logname": logname, "img_url": post["img_url"],
               "owner": post["owner"], "owner_img_url": post["owner_img_url"],
               "timestamp": post["timestamp"],
               "likes": likes, "comments": comments, "postid": postid,
               "like_botton": post["like_botton"], "curr_path": request.path}
    return flask.render_template("post.html", **context)


@insta485.app.get('/explore/')
def show_explore():
    """Display /explore/ route."""
    # If not logged in, redirect to /accounts/login/
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('show_login'))
    logname = flask.session["username"]

    # Connect to database
    connectdb = insta485.model.get_db()

    # Query database
    cur = connectdb.execute(
        "SELECT username, filename AS user_img_url "
        "FROM users WHERE username <> ? "
        "EXCEPT "
        "SELECT users.username, users.filename AS user_img_url "
        "FROM (users INNER JOIN following "
        "ON users.username=following.username2) "
        "WHERE following.username1 = ?",
        (logname, logname, )

    )
    not_following = cur.fetchall()

    # Add database info to context
    context = {"logname": logname,
               "not_following": not_following, "curr_path": request.path}
    return flask.render_template("explore.html", **context)


@insta485.app.get('/accounts/login/')
def show_login():
    """Display /accounts/login/ route."""
    # If logged in, redirect to /
    if "username" in flask.session:
        return flask.redirect(flask.url_for('show_index'))

    return flask.render_template("login.html")


@insta485.app.get('/accounts/create/')
def show_create():
    """Display /accounts/create/ route."""
    # If logged in, redirect to /accounts/edit/
    if "username" in flask.session:
        return flask.redirect(flask.url_for('show_edit'))

    return flask.render_template("create.html")


@insta485.app.get('/accounts/delete/')
def show_delete():
    """Display /accounts/delete/ route."""
    # If not logged in, redirect to /accounts/login/
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('show_login'))
    logname = flask.session["username"]
    context = {"logname": logname}
    return flask.render_template("delete.html", **context)


@insta485.app.get('/accounts/edit/')
def show_edit():
    """Display /accounts/edit/ route."""
    # If not logged in, redirect to /accounts/login/
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('show_login'))
    logname = flask.session["username"]

    # Connect to database
    connectdb = insta485.model.get_db()

    # Query database
    cur = connectdb.execute(
        "SELECT * FROM users WHERE username = ? ",
        (logname, )
    )
    user = cur.fetchall()[0]

    # Add database info to context
    context = {"logname": logname, "username": logname,
               "photo": user["filename"], "fullname": user["fullname"],
               "email": user["email"], "curr_path": request.path}
    return flask.render_template("edit.html", **context)


@insta485.app.get('/accounts/password/')
def show_password():
    """Display /accounts/password/ route."""
    # If not logged in, redirect to /accounts/login/
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('show_login'))
    logname = flask.session["username"]

    # Add database info to context
    context = {"logname": logname}
    return flask.render_template("password.html", **context)


@insta485.app.get('/uploads/<path:filename>')
def download_file(filename):
    """Download file from the directory."""
    if "username" not in flask.session:
        flask.abort(403)
    filepath = insta485.app.config['UPLOAD_FOLDER'] / filename
    if not filepath.is_file():
        flask.abort(404)
    return send_from_directory(insta485.app.config['UPLOAD_FOLDER'],
                               filename)
