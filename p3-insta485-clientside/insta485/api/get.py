"""
Insta485 api for GET.

URLs include:
/api/v1/
/api/v1/posts/
/api/v1/posts/<postid>/
"""

import flask
from flask import request
import insta485


@insta485.app.get('/api/v1/')
def get_resources():
    """Get resources."""
    context = {
        "comments": "/api/v1/comments/",
        "likes": "/api/v1/likes/",
        "posts": "/api/v1/posts/",
        "url": "/api/v1/"
    }
    return flask.jsonify(**context), 200


@insta485.app.get('/api/v1/posts/')
def get_10_new_posts():
    """Get 10 new posts."""
    logname = insta485.model.authentication()
    if not isinstance(logname, str):
        return logname

    postid_lte = request.args.get('postid_lte', None)
    size = request.args.get('size', 10, int)
    page = request.args.get('page', 0, int)

    # Bad request of negative val for size/page
    if size < 0 or page < 0:
        context = {
            "message": "Bad Request",
            "status_code": 400
        }
        return flask.jsonify(**context), 400

    postids = (insta485.
               model.get_10_newest_posts)(logname, postid_lte, size, page)

    # postid_lts = max postid, if not specific in args
    posts_list = []
    for row in postids:
        post_dict = {}
        post_dict["postid"] = row["postid"]
        post_dict["url"] = f"/api/v1/posts/{row['postid']}/"
        posts_list.append(post_dict)

    next0 = ""
    if len(posts_list) >= size:
        if postid_lte is None:
            postid_lte = postids[0]["postid"]
        next0 = "/api/v1/posts/"\
            f"?size={size}&page={page+1}&postid_lte={postid_lte}"
    if ((request.args.get('postid_lte') is None) and
            (request.args.get('size') is None) and
            (request.args.get('page') is None)):
        context = {
            "next": next0,
            "results": posts_list,
            "url": flask.request.path
        }
    else:
        context = {
            "next": next0,
            "results": posts_list,
            "url": flask.request.full_path
        }
    return flask.jsonify(**context), 200


@insta485.app.get('/api/v1/posts/<int:postid_url_slug>/')
def get_one_post(postid_url_slug):
    """Get a single post."""
    logname = insta485.model.authentication()
    if not isinstance(logname, str):
        return logname

    # Post IDs that are out of range should return a 404 error.
    if postid_url_slug > insta485.model.get_max_postid()["max_postid"]:
        context = {
            "message": "Not Found",
            "status_code": 404
        }
        return flask.jsonify(**context), 404

    # return commentid, owner, text
    comments = insta485.model.get_post_comments(postid_url_slug)
    comments_list = []
    for row in comments:
        comment_dict = {}
        comment_dict["commentid"] = row["commentid"]
        comment_dict["lognameOwnsThis"] = False
        if logname == row["owner"]:
            comment_dict["lognameOwnsThis"] = True
        comment_dict["owner"] = row["owner"]
        comment_dict["ownerShowUrl"] = f"/users/{row['owner']}/"
        comment_dict["text"] = row["text"]
        comment_dict["url"] = f"/api/v1/comments/{row['commentid']}/"
        comments_list.append(comment_dict)

    # return p.postid, p.filename, p.owner, p.created
    post_details = insta485.model.get_post_details(postid_url_slug)
    postid = post_details["postid"]
    post_owner = post_details["owner"]
    filename = post_details["filename"]
    owner_imgurl = insta485.model.get_owner_img(post_owner)["filename"]

    # check likeid of logname to the post OR null
    logname_likeid = insta485.model.get_logname_likeid(
        postid_url_slug, logname)
    likes_url = None
    if logname_likeid is not None:
        likes_url = f"/api/v1/likes/{logname_likeid['likeid']}/"

    # count likes
    likes_count = insta485.model.get_likes_count(postid_url_slug)

    context = {
        "comments": comments_list,
        "comments_url": f"/api/v1/comments/?postid={postid_url_slug}",
        "created": post_details["created"],
        "imgUrl": f"/uploads/{filename}",
        "likes": {
            "lognameLikesThis": logname_likeid is not None,
            "numLikes": likes_count["count"],
            "url": likes_url
        },
        "owner": post_owner,
        "ownerImgUrl": f"/uploads/{owner_imgurl}",
        "ownerShowUrl": f"/users/{post_owner}/",
        "postShowUrl": f"/posts/{postid}/",
        "postid": postid,
        "url": flask.request.path
    }
    return flask.jsonify(**context), 200
