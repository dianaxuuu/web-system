"""
Insta485 api for DELETE.

URLs include:
/api/v1/likes/<likeid>/
/api/v1/comments/<commentid>/
"""

import flask
import insta485


@insta485.app.delete('/api/v1/likes/<int:likeid>/')
def delete_like(likeid):
    """Delete a like."""
    logname = insta485.model.authentication()
    if not isinstance(logname, str):
        return logname

    like_owner = insta485.model.get_like_owner(likeid)
    if like_owner is None:
        context = {
                "message": "Not Found",
                "status_code": 404
            }
        return flask.jsonify(**context), 404
    if like_owner["owner"] != logname:
        context = {
                "message": "Forbidden",
                "status_code": 403
            }
        return flask.jsonify(**context), 403
    insta485.model.delete_one_like(likeid)
    context = {
            "message": "No Content",
            "status_code": 204
        }
    return flask.jsonify(**context), 204


@insta485.app.delete('/api/v1/comments/<int:commentid>/')
def delete_comment(commentid):
    """Delete a comment."""
    logname = insta485.model.authentication()
    if not isinstance(logname, str):
        return logname

    comment_owner = insta485.model.get_comment_owner(commentid)
    if comment_owner is None:
        context = {
            "message": "Not Found",
            "status_code": 404
        }
        return flask.jsonify(**context), 404
    if comment_owner["owner"] != logname:
        context = {
            "message": "Forbidden",
            "status_code": 403
        }
        return flask.jsonify(**context), 403
    insta485.model.delete_one_comment(commentid)
    context = {
        "message": "No Content",
        "status_code": 204
    }
    return flask.jsonify(**context), 204
