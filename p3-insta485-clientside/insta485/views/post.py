"""
Insta485 views for POST.

URLs include:
/accounts/logout/
/likes/?target=URL
/comments/?target=URL
/posts/?target=URL
/following/?target=URL
/accounts/?target=URL
"""


import os
import pathlib
import uuid
import hashlib
import flask
from flask import request
import insta485


@insta485.app.post('/accounts/logout/')
def perform_logout():
    """Logout and redirect to /accounts/login/."""
    # Clear the session
    flask.session.clear()

    # Redirect to /accounts/login/
    return flask.redirect(flask.url_for('show_login'))


@insta485.app.post('/likes/')
def perform_likes():
    """Like or unlike, and then redirect."""
    # Get operation and postid values
    operation_val = flask.request.form['operation']
    postid_val = flask.request.form['postid']

    # Get logname
    logname = flask.session["username"]

    # Connect to database
    connectdb = insta485.model.get_db()

    if operation_val == 'like':
        # If already liked, abort the operation
        cur = connectdb.execute(
            "SELECT * FROM likes WHERE owner = ? "
            "AND postid = ?",
            (logname, postid_val)
        )
        if cur.fetchone() is not None:
            flask.abort(409)

        # Otherwise, insert a new like to database
        cur = connectdb.execute(
            "INSERT INTO likes(owner, postid) "
            "VALUES (?, ?)",
            (logname, postid_val)
        )

    elif operation_val == 'unlike':
        # If not liked, abort the operation
        cur = connectdb.execute(
            "SELECT * FROM likes WHERE owner = ? "
            "AND postid = ?",
            (logname, postid_val)
        )
        if cur.fetchone() is None:
            flask.abort(409)

        # Otherwise, delete the like from database
        cur = connectdb.execute(
            "DELETE FROM likes WHERE owner = ? "
            "AND postid = ?",
            (logname, postid_val)
        )

    # If URL exists redirect to URL
    # Otherwise, redirect to root
    target_val = request.args.get('target', '/')
    return flask.redirect(target_val)


@insta485.app.post('/comments/')
def perform_comments():
    """Comment or delete comment, and then redirect."""
    # Get all needed pars
    operation_val = flask.request.form['operation']

    # Get logname
    logname = flask.session["username"]

    # Connect to database
    connectdb = insta485.model.get_db()

    # Create
    if operation_val == 'create':
        postid_val = flask.request.form['postid']
        text_val = flask.request.form['text']
        # If comment is empty, return Bad Request
        if text_val is None:
            flask.abort(400)

        # Otherwise, insert a new like to database
        cur = connectdb.execute(
            "INSERT INTO comments"
            "(owner, postid, text)"
            "VALUES(?, ?, ?)",
            (logname, postid_val, text_val)
        )

    # Delete
    elif operation_val == 'delete':
        commentid_val = flask.request.form['commentid']

        # If comment not owned, return abort(403)
        cur = connectdb.execute(
            "SELECT * FROM comments WHERE owner = ? "
            "AND commentid = ?",
            (logname, commentid_val)
        )
        if cur.fetchone() is None:
            flask.abort(403)

        # Otherwise, delete the comment
        cur = connectdb.execute(
            "DELETE FROM comments WHERE owner = ? "
            "AND commentid = ?",
            (logname, commentid_val)
        )

    # If URL exists redirect to URL
    # Otherwise, redirect to root
    target_val = request.args.get('target', '/')
    return flask.redirect(target_val)


@insta485.app.post('/posts/')
def perform_posts():
    """Add or delete post, and then redirect."""
    # Get operation
    operation_val = flask.request.form['operation']

    # Get logname
    logname = flask.session["username"]

    # Connect to database
    connectdb = insta485.model.get_db()

    if operation_val == 'create':
        # Unpack flask object
        fileobj = flask.request.files.get("file", None)
        if fileobj is None:
            flask.abort(400)
        filename = fileobj.filename
        if filename is None:
            flask.abort(400)

        # Compute base name (filename without directory).
        # We use a UUID to avoid clashes with existing files,
        # and ensure that the name is compatible with the filesystem.
        stem = uuid.uuid4().hex
        suffix = pathlib.Path(filename).suffix
        # Filename par we should use
        uuid_basename = f"{stem}{suffix}"

        # Save to disk
        path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
        fileobj.save(path)

        # Otherwise, save the image file to disk and redirect to URL
        cur = connectdb.execute(
            "INSERT INTO posts(filename, owner) "
            "VALUES (?, ?)",
            (uuid_basename, logname)
        )

    elif operation_val == 'delete':
        postid_val = flask.request.form['postid']
        # If not owned, abort(403)
        cur = connectdb.execute(
            "SELECT * FROM posts WHERE owner = ? "
            "AND postid = ?",
            (logname, postid_val)
        )
        if cur.fetchone() is None:
            flask.abort(403)

        # Otherwise, delete image from UPLOAD_FOLDER
        cur = connectdb.execute(
            "SELECT filename FROM posts WHERE owner = ? "
            "AND postid = ?",
            (logname, postid_val)
        )
        filename = cur.fetchall()[0]['filename']
        os.remove(insta485.app.config["UPLOAD_FOLDER"]/filename)

        # Otherwise, delete the post from database
        cur = connectdb.execute(
            "DELETE FROM posts WHERE owner = ? "
            "AND postid = ?",
            (logname, postid_val)
        )

    # If URL exists redirect to URL
    # Otherwise, redirect to /users/<logname>/
    target_val = request.args.get('target', f'/users/{logname}/')
    return flask.redirect(target_val)


@insta485.app.post('/following/')
def perform_following():
    """Follow or unfollow, and then redirect."""
    # Get operation and username values
    operation_val = flask.request.form['operation']
    username_val = flask.request.form['username']

    # Get logname
    logname = flask.session["username"]

    # Connect to database
    connectdb = insta485.model.get_db()

    if operation_val == 'follow':
        # If try to follow sb already follows, abort(409)
        cur = connectdb.execute(
            "SELECT * FROM following WHERE username1 = ? "
            "AND username2 = ?",
            (logname, username_val)
        )
        if cur.fetchone() is not None:
            flask.abort(409)

        # Otherwise, insert the following into db
        cur = connectdb.execute(
            "INSERT INTO following(username1, username2)"
            "VALUES (?,?)",
            (logname, username_val)
        )

    elif operation_val == 'unfollow':
        # If try to unfollow sb unfollows, abort(409)
        cur = connectdb.execute(
            "SELECT * FROM following WHERE username1 = ? "
            "AND username2 = ?",
            (logname, username_val)
        )
        if cur.fetchone() is None:
            flask.abort(409)

        # Otherwise, delete the following into db
        cur = connectdb.execute(
            "DELETE FROM following WHERE username1 = ? "
            "AND username2 = ?",
            (logname, username_val)
        )

    # If URL exists redirect to URL
    # Otherwise, redirect to root
    target_val = request.args.get('target', '/')
    return flask.redirect(target_val)


@insta485.app.post('/accounts/')
def perform_account():
    """Perform various account operations and immediately redirect to URL."""
    # Get operation values
    operation_val = flask.request.form['operation']

    # Connect to database
    connectdb = insta485.model.get_db()

    if operation_val == 'login':
        username_val = flask.request.form['username']
        password_val = flask.request.form['password']
        # Perform password authentication
        cur = connectdb.execute(
            "SELECT * FROM users WHERE username = ? ",
            (username_val, )
        )
        # Username does not exist
        user = cur.fetchone()
        if user is None:
            flask.abort(403)

        # Username does not match password
        algorithm, salt, password_hash_correct = user['password'].split("$")
        hash_obj = hashlib.new(algorithm)
        password_salted = salt + password_val
        hash_obj.update(password_salted.encode('utf-8'))
        password_hash = hash_obj.hexdigest()
        if password_hash != password_hash_correct:
            flask.abort(403)

        # Set the cookies
        flask.session['username'] = username_val

    elif operation_val == 'create':
        create_account(connectdb)

    elif operation_val == 'delete':
        # If the user is not logged in, abort(403).
        if "username" not in flask.session:
            flask.abort(403)
        delete_account(connectdb)

    elif operation_val == 'edit_account':
        # If the user is not logged in, abort(403).
        if "username" not in flask.session:
            flask.abort(403)
        logname = flask.session['username']
        edit_account(logname, connectdb)

    elif operation_val == 'update_password':
        # If the user is not logged in, abort(403).
        if "username" not in flask.session:
            flask.abort(403)
        logname = flask.session["username"]
        update_password(logname, connectdb)

    target_val = request.args.get('target', '/')
    return flask.redirect(target_val)


def create_account(connectdb):
    """Create a new account."""
    # Fetch username, password, fullname and email
    username_val = flask.request.form['username']
    password_val = flask.request.form['password']
    fullname_val = flask.request.form['fullname']
    email_val = flask.request.form['email']

    # Unpack flask object
    fileobj = flask.request.files["file"]
    filename = fileobj.filename
    if filename is None:
        flask.abort(400)

    # Hash the password
    password_db_string = hash_password(password_val)

    # Compute base name (filename without directory).
    # We use a UUID to avoid clashes with existing files,
    # and ensure that the name is compatible with the filesystem.
    stem = uuid.uuid4().hex
    suffix = pathlib.Path(filename).suffix
    # Filename par we should use
    uuid_basename = f"{stem}{suffix}"

    # Save to disk
    path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
    fileobj.save(path)

    # If a user tries to create an account
    # with an existing username in the database, abort(409)
    cur = connectdb.execute(
        "SELECT * FROM users WHERE username = ? ",
        (username_val, )
    )
    # Username does not exist
    if cur.fetchone() is not None:
        flask.abort(409)

    # Otherwise, create a new account
    cur = connectdb.execute(
        "INSERT INTO users(username, fullname, "
        "email, filename, password) "
        "VALUES (?,?,?,?,?)",
        (username_val, fullname_val,
            email_val, uuid_basename, password_db_string)
    )

    # Set the cookies(Log the user in)
    flask.session['username'] = username_val


def delete_account(connectdb):
    """Delete the account."""
    logname = flask.session['username']
    # Find and remove the old photo
    cur = connectdb.execute(
        "SELECT * FROM users WHERE username = ? ",
        (logname, )
    )
    old_uuid_basename = cur.fetchone()['filename']
    os.remove(insta485.app.config["UPLOAD_FOLDER"]/old_uuid_basename)

    # Find and remove the images of posts
    cur = connectdb.execute(
        "SELECT filename FROM posts WHERE owner = ?",
        (logname, )
    )
    posts_file = cur.fetchall()
    for post in posts_file:
        old_uuid_basename = post['filename']
        os.remove(insta485.app.config["UPLOAD_FOLDER"]/old_uuid_basename)

    # Delete the account and related info in the database
    cur = connectdb.execute(
        "DELETE FROM users WHERE username = ? ",
        (logname, )
    )

    # Clear the user’s session upon success
    flask.session.clear()


def edit_account(logname, connectdb):
    """Edit the account."""
    # Fetch fullname, email and file
    fullname_val = flask.request.form['fullname']
    email_val = flask.request.form['email']

    # Unpack flask object
    fileobj = flask.request.files.get("file", None)

    if fileobj is None:
        cur = connectdb.execute(
            "UPDATE users "
            "SET fullname = ?, email = ? "
            "WHERE username = ?",
            (fullname_val, email_val, logname)
        )

    else:
        filename = fileobj.filename
        # Find and remove the old photo
        cur = connectdb.execute(
            "SELECT * FROM users WHERE username = ? ",
            (logname, )
        )
        old_uuid_basename = cur.fetchone()['filename']
        os.remove(insta485.app.config["UPLOAD_FOLDER"]/old_uuid_basename)

        # Compute base name (filename without directory).
        # We use a UUID to avoid clashes with existing files,
        # and ensure that the name is compatible with the filesystem.
        stem = uuid.uuid4().hex
        suffix = pathlib.Path(filename).suffix
        uuid_basename = f"{stem}{suffix}"
        # Save to disk
        path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
        fileobj.save(path)
        cur = connectdb.execute(
            "UPDATE users "
            "SET fullname = ?, email = ?, filename = ? "
            "WHERE username = ?",
            (fullname_val, email_val, uuid_basename, logname)
        )


def update_password(logname, connectdb):
    """Update password."""
    # Fetch password, new_password1 and new_password2
    password_val = flask.request.form['password']
    password1_val = flask.request.form['new_password1']
    password2_val = flask.request.form['new_password2']

    # Fetch current right password
    cur = connectdb.execute(
        "SELECT * FROM users WHERE username = ? ",
        (logname, )
    )

    # Verify password
    password_db_string = cur.fetchone()["password"]
    password_db_string = verify_hash_update_password(
        password_val, password1_val, password_db_string)

    # Check whether two new password match
    if password1_val != password2_val:
        flask.abort(401)

    # Update password
    cur = connectdb.execute(
        "UPDATE users "
        "SET password = ? "
        "WHERE username = ?",
        (password_db_string, logname)
    )


def hash_password(password_val):
    """Hash password."""
    algorithm = 'sha512'
    salt = uuid.uuid4().hex
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password_val
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    return password_db_string


def verify_hash_update_password(password_val,
                                password1_val, password_db_string):
    """Verify and hash password."""
    # Continue to verify
    algorithm, salt, password_hash_correct = password_db_string.split("$")
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password_val
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    if password_hash != password_hash_correct:
        flask.abort(403)

    # Hash the password
    salt = uuid.uuid4().hex
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password1_val
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    return password_db_string
