import React from "react";
import PropTypes from "prop-types";

function Like({ numLikes, lognameLikesThis, onClick }) {
  /* Display like/unlike button and the number of likes
   */
  return (
    <div className="like">
      <button type="button" className="like-unlike-button" onClick={onClick}>
        {lognameLikesThis ? "unlike" : "like"}
      </button>
      <p>
        {numLikes} {numLikes === 1 ? "like" : "likes"}
      </p>
    </div>
  );
}

Like.propTypes = {
  numLikes: PropTypes.number.isRequired,
  lognameLikesThis: PropTypes.bool.isRequired,
  onClick: PropTypes.func.isRequired,
};

export default Like;
