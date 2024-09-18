import React from "react";
import PropTypes from "prop-types";
import InfiniteScroll from "react-infinite-scroll-component";
import Post from "./post";

class Board extends React.Component {
  constructor(props) {
    // Initialize mutable state
    super(props);
    this.state = { results: [], next: "" };
    this.getNextTenPosts = this.getNextTenPosts.bind(this);
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
          results: data.results,
          next: data.next,
        });
      })
      .catch((error) => console.log(error));
  }

  getNextTenPosts() {
    // Get the next ten posts.
    const { next } = this.state;
    // Call REST API to get the next ten posts
    fetch(next, { credentials: "same-origin" })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        this.setState((prevState) => ({
          results: prevState.results.concat(data.results),
          next: data.next,
        }));
      })
      .catch((error) => console.log(error));
  }

  render() {
    const { results, next } = this.state;
    return (
      <div className="board">
        <InfiniteScroll
          dataLength={results.length}
          next={this.getNextTenPosts}
          hasMore={next !== ""}
          loader={<h4>Loading...</h4>}
          endMessage={
            <p style={{ textAlign: "center" }}>
              <b>Yay! You have seen it all</b>
            </p>
          }
        >
          {results.map((post) => (
            <Post key={post.postid} url={post.url} postid={post.postid} />
          ))}
        </InfiniteScroll>
      </div>
    );
  }
}
Board.propTypes = {
  url: PropTypes.string.isRequired,
};
export default Board;
