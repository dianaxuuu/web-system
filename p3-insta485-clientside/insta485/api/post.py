"""
Insta485 api for POST.

URLs include:
/api/v1/likes/?postid=<postid>
/api/v1/comments/?postid=<postid>
"""

import flask
from flask import request
import insta485


@insta485.app.post('/api/v1/likes/')
def post_like():
    """Post a like."""
    logname = insta485.model.authentication()
    if not isinstance(logname, str):
        return logname

    postid = request.args.get('postid')
    likeid = insta485.model.check_like_existence(logname, postid)
    if likeid is not None:
        context = {
            "likeid": likeid["likeid"],
            "url": f"/api/v1/likes/{likeid['likeid']}/"
        }
        return flask.jsonify(**context), 200

    insta485.model.create_one_like(logname, postid)
    likeid = insta485.model.check_like_existence(logname, postid)
    context = {
        "likeid": likeid["likeid"],
        "url": f"/api/v1/likes/{likeid['likeid']}/"
    }
    return flask.jsonify(**context), 201


@insta485.app.post('/api/v1/comments/')
def post_one_comment():
    """Post a comment."""
    logname = insta485.model.authentication()
    if not isinstance(logname, str):
        return logname

    postid = request.args.get('postid')
    text = flask.request.json.get("text", None)
    commentid = (insta485.model.
                 add_one_comment)(logname, postid, text)["last_insert_rowid()"]
    context = {
        "commentid": commentid,
        "lognameOwnsThis": True,
        "owner": logname,
        "ownerShowUrl": f"/users/{logname}/",
        "text": text,
        "url": f"/api/v1/comments/{commentid}/"
    }
    return flask.jsonify(**context), 201
