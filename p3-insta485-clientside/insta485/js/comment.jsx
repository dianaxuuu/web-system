import React from "react";
import PropTypes from "prop-types";

function Comment({ owner, ownerShowUrl, text, lognameOwnsThis, onClick }) {
  /* Display comment owner and text of a single comment
   */
  const deleteButton = (
    <button type="button" className="delete-comment-button" onClick={onClick}>
      Delete comment
    </button>
  );
  return (
    <div className="comment">
      <p>
        <a href={ownerShowUrl}>
          <span>{owner}</span>
        </a>
        {text}
        &nbsp;&nbsp;
        {lognameOwnsThis ? deleteButton : null}
      </p>
    </div>
  );
}

Comment.propTypes = {
  owner: PropTypes.string.isRequired,
  ownerShowUrl: PropTypes.string.isRequired,
  text: PropTypes.string.isRequired,
  lognameOwnsThis: PropTypes.bool.isRequired,
  onClick: PropTypes.func.isRequired,
};

export default Comment;
