# 02 — You already know CPS: callbacks, futures, async/await
# Run: python3 02_you_already_use_it.py
#
# Why write code this way? Because when the result isn't available YET
# (network, disk, timer), you can't "return" it. You can only say
# "when you have it, do THIS" — that's a continuation.
import asyncio

def fetch_user_k(uid, k):
    asyncio.get_running_loop().call_later(0.1, k, {"id": uid, "name": "Ada"})

def fetch_posts_k(user, k):
    name = user["name"]
    asyncio.get_running_loop().call_later(0.1, k, [f"{name}'s post 1", f"{name}'s post 2"])

# Wrap a CPS function into a Future: the future's set_result IS the continuation.
def fetch_user(uid):
    fut = asyncio.get_running_loop().create_future()
    fetch_user_k(uid, fut.set_result)
    return fut

def fetch_posts(user):
    fut = asyncio.get_running_loop().create_future()
    fetch_posts_k(user, fut.set_result)
    return fut

async def main():
    # ---------- 1. raw CPS (callbacks) ----------
    fetch_user_k(1, lambda user:
        fetch_posts_k(user, lambda posts:
            print("callbacks:  ", posts)))
    # Same shape as pyth_k in 01. "Callback hell" is CPS written by hand.

    # ---------- 2. futures: the continuation is registered on an object ----------
    fetch_user(1).add_done_callback(lambda f:
        fetch_posts(f.result()).add_done_callback(lambda f2:
            print("futures:    ", f2.result())))
    # (JS promises' .then(k) is the same idea with nicer chaining.)

    # ---------- 3. async/await: the language does the CPS transform for you ----------
    user = await fetch_user(1)        # everything BELOW this line is the continuation
    posts = await fetch_posts(user)   # ...and everything below THIS line is the next one
    print("async/await:", posts)

    await asyncio.sleep(0.05)         # let the other two styles finish printing

asyncio.run(main())

# Mental model worth keeping:
#   `await x` = "take the rest of this function, freeze it, and give it
#                to x as its continuation."
# Python implements that freezing with coroutine objects (built on generators):
# you write direct style; it runs as CPS.

# EXERCISE: add fetch_comments_k(post, k) and fetch comments for the first
# post in all three styles. Feel how the nesting grows in style 1.
