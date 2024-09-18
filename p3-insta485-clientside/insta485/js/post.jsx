import React from "react";
import PropTypes from "prop-types";
import moment from "moment";
import Like from "./like";
import Comment from "./comment";

class Post extends React.Component {
  /* Display image and post owner of a single post
   */
  constructor(props) {
    // Initialize mutable state
    super(props);
    this.state = {
      likes: {
        lognameLikesThis: false,
        numLikes: 0,
        url: "",
      },
      comments: [],
      created: "",
      imgUrl: "",
      owner: "",
      ownerImgUrl: "",
      ownerShowUrl: "",
      postShowUrl: "",
      text: "",
    };
    this.handleChange = this.handleChange.bind(this);
    this.keyPress = this.keyPress.bind(this);
  }

  componentDidMount() {
    // This line automatically assigns this.props.url to the const variable url
    const { url } = this.props;
    // Call REST API to get the post's information
    fetch(url, { credentials: "same-origin" })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        this.setState({
          likes: data.likes,
          comments: data.comments,
          imgUrl: data.imgUrl,
          owner: data.owner,
          ownerImgUrl: data.ownerImgUrl,
          created: moment(data.created, "YYYY-MM-DD HH:mm:ss").fromNow(),
          ownerShowUrl: data.ownerShowUrl,
          postShowUrl: data.postShowUrl,
        });
      })
      .catch((error) => console.log(error));
  }

  handleChange(event) {
    this.setState({ text: event.target.value });
  }

  keyPress(event) {
    if (event.keyCode === 13) {
      const { postid } = this.props;
      const { text } = this.state;
      const { comments } = this.state;
      event.preventDefault();

      // post to API to update database + set state
      fetch(`/api/v1/comments/?postid=${postid}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json; charset=UTF-8",
        },
        body: JSON.stringify({ text }),
      })
        .then((response) => {
          if (!response.ok) throw Error(response.statusText);
          return response.json();
        })
        .then((data) => {
          comments.push({
            commentid: data.commentid,
            owner: data.owner,
            ownerShowUrl: data.ownerShowUrl,
            text: data.text,
            lognameOwnsThis: true,
          });
          this.setState({
            comments,
          });
        })
        .catch((error) => console.log(error));
    }
  }

  likeClick() {
    const { postid } = this.props;
    const { likes } = this.state;
    const { lognameLikesThis, url } = likes;
    if (!lognameLikesThis) {
      fetch(`/api/v1/likes/?postid=${postid}`, {
        method: "POST",
        credentials: "same-origin",
      })
        .then((response) => {
          if (!response.ok) throw Error(response.statusText);
          return response.json();
        })
        .then((data) => {
          this.setState((prevState) => ({
            likes: {
              lognameLikesThis: true,
              numLikes: prevState.likes.numLikes + 1,
              url: data.url,
            },
          }));
        })
        .catch((error) => console.log(error));
    } else {
      fetch(url, {
        method: "DELETE",
        credentials: "same-origin",
      })
        .then((response) => {
          if (!response.ok) throw Error(response.statusText);
          this.setState((prevState) => ({
            likes: {
              lognameLikesThis: false,
              numLikes: prevState.likes.numLikes - 1,
              url: null,
            },
          }));
        })
        .catch((error) => console.log(error));
    }
  }

  postClick(event) {
    const { likes } = this.state;
    if (event.detail === 2 && !likes.lognameLikesThis) {
      this.likeClick();
    }
  }

  commentDeleteClick(commentid) {
    fetch(`/api/v1/comments/${commentid}/`, {
      method: "DELETE",
      credentials: "same-origin",
    })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        const { comments } = this.state;
        const newComments = comments.filter(
          (comment) => comment.commentid !== commentid
        );
        this.setState({
          comments: newComments,
        });
      })
      .catch((error) => console.log(error));
  }

  renderComments() {
    const cmts = [];
    const { comments } = this.state;
    comments.forEach((comment) => {
      cmts.push(
        <Comment
          key={comment.commentid}
          owner={comment.owner}
          ownerShowUrl={comment.ownerShowUrl}
          text={comment.text}
          lognameOwnsThis={comment.lognameOwnsThis}
          onClick={() => this.commentDeleteClick(comment.commentid)}
        />
      );
    });
    return cmts;
  }

  render() {
    const {
      imgUrl,
      owner,
      ownerImgUrl,
      created,
      likes,
      ownerShowUrl,
      postShowUrl,
      text,
    } = this.state;
    return (
      <div className="post">
        <div className="info">
          <a href={ownerShowUrl}>
            <img src={ownerImgUrl} alt="post_image" className="user_photo" />
          </a>
          <p className="user_name">{owner}</p>
          <a href={postShowUrl} className="timestamp">
            <p>{created}</p>
          </a>
        </div>
        <div className="post_img">
          <button type="button" onClick={(e) => this.postClick(e)}>
            <img src={imgUrl} alt="post_image" className="post_image" />
          </button>
        </div>
        <div className="likes">
          <Like
            numLikes={likes.numLikes}
            lognameLikesThis={likes.lognameLikesThis}
            onClick={() => this.likeClick()}
          />
        </div>
        <div className="comment_section">{this.renderComments()}</div>
        <div className="comment_input">
          <form className="comment-form">
            <input
              type="text"
              value={text}
              onKeyDown={this.keyPress}
              onChange={this.handleChange}
            />
          </form>
        </div>
      </div>
    );
  }
}
Post.propTypes = {
  url: PropTypes.string.isRequired,
  postid: PropTypes.number.isRequired,
};
export default Post;
