// 02 — You already write CPS: callbacks, promises, async/await
// Run: node 02-you-already-use-it.js
//
// Why would anyone write code this way? Because when the result isn't
// available YET (network, disk, timer), you can't "return" it.
// You can only say "when you have it, do THIS" — that's a continuation.

function fetchUserK(id, k)    { setTimeout(() => k({ id, name: "Ada" }), 1000); }
function fetchPostsK(user, k) { setTimeout(() => k([`${user.name}'s post 1`, `${user.name}'s post 2`]), 1000); }

// ---------- 1. raw CPS (a.k.a. Node-style callbacks / "callback hell") ----------
fetchUserK(1, (user) =>
  fetchPostsK(user, (posts) =>
    console.log("callbacks:  ", posts)));

// Compare with 01-basics.js: it's the *same shape* as pythK.
// "Callback hell" is just CPS written by hand.

// ---------- 2. promises: the continuation becomes an object you pass around ----------
const fetchUser  = (id)   => new Promise((k) => fetchUserK(id, k));
const fetchPosts = (user) => new Promise((k) => fetchPostsK(user, k));

fetchUser(1)
  .then((user) => fetchPosts(user))      // .then(k) == "here is my continuation"
  .then((posts) => console.log("promises:   ", posts));

// ---------- 3. async/await: the compiler does the CPS transform for you ----------
async function main() {
  const user  = await fetchUser(1);      // everything BELOW this line is the continuation
  const posts = await fetchPosts(user);  // ...and everything below THIS line is the next one
  console.log("async/await:", posts);
}
main();

// Mental model worth keeping:
//   `await x` = "take the rest of this function, wrap it in a closure,
//                and give it to x as its continuation."
// The JS engine literally does this (it suspends the function and resumes
// it later). You write direct style; it runs as CPS.

// EXERCISE: add fetchCommentsK(post, k) and fetch comments for the first
// post in all three styles. Feel how the nesting grows in style 1.
function firstK(list, k) {
  k(list[0])
}

function fetchCommentsK(post, k) {
  setTimeout(() => k(`A comment for the post ${post}`), 1000)
}
function fetchComments(post) {
  return new Promise((k) => fetchCommentsK(post, k))
}

fetchUserK(1, (user) => {
  fetchPostsK(user, (posts) => {
    firstK(posts, (post) => {
      fetchCommentsK(post, (comment) =>
        console.log(comment)
      );
    })
  })
})

fetchUser(1)
  .then((user) => fetchPosts(user))
  .then((posts) => posts[0])
  .then((post) => fetchComments(post))
  .then((comment) => console.log(comment))

async function ex() {
  const user = await fetchUser(1);
  const posts = await fetchPosts(user);
  const post = posts[0];
  const comment = await fetchComments(post);
  console.log(comment);
}
ex();
