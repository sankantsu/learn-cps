# Recap exercises (optional): one per concept, before the CPS interpreter
# Run: python3 ex_recap.py
#
#   Ex 1  ANF → CPS conversion, two recursive calls    (lessons 01, 03c, 04)
#   Ex 2  two continuations: ok / fail                 (lesson 03)
#   Ex 3  trampoline for mutual recursion              (lesson 04)
#   Ex 4  parking continuations in a scheduler         (lesson 05)
#   Ex 5  backtracking with choose / require           (lesson 06)
#   Ex 6  escape continuation out of a callback        (lesson 07)
#   Ex 7  (bonus) continuation → explicit stack loop   (lesson 04, v2/v3)
#
# Each exercise is independent. Replace `raise NotImplementedError` with your
# code; the tests at the bottom say PASS/FAIL per exercise.
from collections import deque


# ---------------- provided helpers (from earlier lessons) ----------------

def trampoline(step):
    while callable(step):
        step = step()
    return step

ready = deque()
def pause(k):
    ready.append(k)
def run():
    while ready:
        ready.popleft()()

def choose(options, k):
    for x in options:
        k(x)
def require(cond, k):
    if cond:
        k()

class _Escape(Exception):
    def __init__(self, tag, value):
        self.tag, self.value = tag, value
def call_ec(f):
    tag = object()
    def escape(v):
        raise _Escape(tag, v)
    try:
        return f(escape)
    except _Escape as e:
        if e.tag is not tag:
            raise
        return e.value


# ======================= Ex 1: tree depth =======================
# A binary tree is either a leaf (any non-tuple, e.g. an int) or a pair
# (left, right). depth(leaf) = 0, depth((l, r)) = 1 + max(depth(l), depth(r)).
#   tree_depth(((1, 2), 3)) == 2
# Step A: write tree_depth in ANF (every call result named, no nested calls).
# Step B: convert to tree_depth_k(tree, k) with the recipe from 03c.

def tree_depth(tree):
    if not isinstance(tree, tuple):
        return 0
    assert isinstance(tree, tuple)
    assert len(tree) == 2
    dl = tree_depth(tree[0])
    dr = tree_depth(tree[1])
    mx = max(dl, dr)
    res = 1 + mx
    return res

def tree_depth_k(tree, k):
    if not isinstance(tree, tuple):
        return k(0)
    assert isinstance(tree, tuple)
    assert len(tree) == 2

    tree_depth_k(tree[0], lambda dl:
        tree_depth_k(tree[1], lambda dr:
             k(1 + max(dl, dr))))


# ======================= Ex 2: nested lookup, ok / fail =======================
# get_path_k(data, path, ok, fail): follow `path` (a list of keys) through
# nested dicts. Call ok(value) at the end, or fail(f"missing key: {key!r}")
# at the FIRST missing key.
#   get_path_k({"a": {"b": 1}}, ["a", "b"], ok, fail)  -> ok(1)
#   get_path_k({"a": {"b": 1}}, ["a", "x"], ok, fail)  -> fail("missing key: 'x'")
# Write it in CPS: no loops, and recursion only in tail position.

def get_path(data, path):
    if not path:
        return data
    if path[0] in data:
        return get_path(data[path[0]], path[1:])
    else:
        raise KeyError

def get_path_k(data, path, ok, fail):
    if not path:
        return ok(data)
    if path[0] in data:
        get_path_k(data[path[0]], path[1:], ok, fail)
    else:
        fail(f"missing key: {path[0]!r}")


# ======================= Ex 3: mutual recursion on a trampoline =======================
# Direct style (tail calls, but Python still overflows for big n):
#   def is_even(n): return True if n == 0 else is_odd(n - 1)
#   def is_odd(n):  return False if n == 0 else is_even(n - 1)
# Write is_even_t(n, k) and is_odd_t(n, k) so that
#   trampoline(is_even_t(100_001, lambda r: r)) == False
# works with a constant stack depth.
# Question to think about: do you need to build NEW continuations here?

def is_even_k(n, k):
    if n == 0:
        return k(True)
    return is_odd_k(n - 1, k)

def is_odd_k(n, k):
    if n == 0:
        return k(False)
    return is_even_k(n - 1, k)

def is_even_t(n, k):
    if n == 0:
        return k(True)
    return lambda: is_odd_t(n - 1, k)

def is_odd_t(n, k):
    if n == 0:
        return k(False)
    return lambda: is_even_t(n - 1, k)


# ======================= Ex 4: wait_until in the scheduler =======================
# wait_until(pred, k): continue with k() once pred() is true.
#   - if pred() is already true, call k() right away
#   - otherwise, park a continuation with `pause` that checks again later
# The tests use it for a consumer task that waits for a producer to put items
# in a shared buffer (it must never try to take from an empty buffer).

def wait_until(pred, k):
    if pred():
        k()
    else:
        pause(lambda: wait_until(pred, k))


# ======================= Ex 5: subset sum by backtracking =======================
# subset_sums_k(xs, target, k): call k(subset) once for EVERY subset of xs
# whose sum is target. subset = tuple, keeping the original order of xs.
#   subset_sums_k([1, 2, 3, 4, 5], 5, k)  -> k((1, 4)), k((2, 3)), k((5,))  (any order)
# Use `choose` (include this element: True / False?) and `require`.
# Bonus: all xs are positive, so prune as soon as the partial sum exceeds target.

def subset_sums_k(xs, target, k):
    def f(rest, cur):
        if not rest:
            return require(sum(cur) == target, lambda: k(cur))
        choose(range(len(rest)), lambda i: f(rest[i + 1:], cur + (rest[i],)))
        f([], cur)  # Skip all remaining elements
    f(xs, ())


# ======================= Ex 6: escape from a callback =======================
# A "library" function you can't change: it calls visit(x) on every int in a
# nested list, depth-first, left to right.

_visited = []                    # (the tests use this to see how far it walked)

def for_each_int(tree, visit):
    for x in tree:
        if isinstance(x, list):
            for_each_int(x, visit)
        else:
            _visited.append(x)
            visit(x)

# first_over(tree, limit): return the first int > limit, or None.
# Use for_each_int + call_ec. It must STOP walking as soon as it finds one.

def first_over(tree, limit):
    def f(escape):
        def visit(x):
            if x > limit:
                escape(x)
        for_each_int(tree, visit)
    return call_ec(f)


# ======================= Ex 7 (bonus): explicit stack =======================
# tree_depth_loop(tree): same result as tree_depth, but with NO recursion and
# NO trampoline: a while loop and a Python list as the stack (lesson 04 v2/v3).
# The tests run it on a tree 100_000 levels deep.
# Hint: start from your tree_depth_k. What does each continuation remember?
#       Turn each kind of continuation into a tagged tuple on the stack.

# def tree_depth_k(tree, k):
#     if not isinstance(tree, tuple):
#         return k(0)
#     assert isinstance(tree, tuple)
#     assert len(tree) == 2
# 
#     tree_depth_k(tree[0], lambda dl:
#         tree_depth_k(tree[1], lambda dr:
#              k(1 + max(dl, dr))))

def tree_depth_loop(tree):
    stack = []
    mode = "eval"
    value = None
    while True:
        if mode == "eval":
            if not isinstance(tree, tuple):
                mode = "apply"
                value = 0
            else:
                stack.append(("left", tree[1]))
                tree = tree[0]
        elif mode == "apply":
            if not stack:
                return value
            tag, v = stack.pop()
            if tag == "left":
                # v is the right side tree here
                mode = "eval"
                dl = value
                stack.append(("right", dl))
                tree = v
            elif tag == "right":
                # v is the saved dl value here
                assert isinstance(v, int)
                dl = v
                dr = value
                value = 1 + max(dl, dr)
            else:
                assert False
        else:
            assert False


# ---------------------------------------------------------------------------
# Tests — every line should say PASS.
import sys

def report(label, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {label:46} {detail}")

def attempt(thunk):
    try:
        return thunk()
    except Exception as e:
        return f"!! {type(e).__name__}: {e}"

def max_depth(run_it):
    depth = best = 0
    def prof(frame, event, arg):
        nonlocal depth, best
        if event == "call":
            depth += 1
            best = max(best, depth)
        elif event == "return":
            depth -= 1
    sys.setprofile(prof)
    try:
        run_it()
    finally:
        sys.setprofile(None)
    return best

def once(call):
    """Run call(k) with a recording k; return the list of values k received."""
    got = []
    call(lambda *v: got.append(v[0] if len(v) == 1 else v))
    return got

# ---- Ex 1
print("Ex 1: tree depth")
TREES = [(7, 0), ((1, 2), 1), (((1, 2), 3), 2), ((1, (2, (3, 4))), 3), ((((1, 2), (3, 4)), 5), 3)]
for t, want in TREES:
    report(f"tree_depth({t})", attempt(lambda: tree_depth(t)) == want,
           f"(got {attempt(lambda: tree_depth(t))})")
for t, want in TREES:
    got = attempt(lambda: once(lambda k: tree_depth_k(t, k)))
    report(f"tree_depth_k({t})", got == [want], f"(got {got})")

# ---- Ex 2
print("Ex 2: get_path_k")
DATA = {"a": {"b": {"c": 42}}, "x": 1}
def path_result(path):
    got = []
    get_path_k(DATA, path, lambda v: got.append(("ok", v)), lambda e: got.append(("fail", e)))
    return got
for path, want in [(["x"], ("ok", 1)), (["a", "b", "c"], ("ok", 42)), ([], ("ok", DATA)),
                   (["a", "q", "c"], ("fail", "missing key: 'q'")), (["nope"], ("fail", "missing key: 'nope'"))]:
    got = attempt(lambda: path_result(path))
    report(f"get_path_k(DATA, {path})", got == [want], f"(got {got})")

# ---- Ex 3
print("Ex 3: trampolined even/odd")
for n, want in [(0, True), (1, False), (10, True), (7, False), (100_001, False), (100_000, True)]:
    got = attempt(lambda: trampoline(is_even_t(n, lambda r: r)))
    report(f"is_even_t({n})", got == want, f"(got {got})")
depths = [max_depth(lambda n=n: attempt(lambda: trampoline(is_even_t(n, lambda r: r)))) for n in (10, 1000)]
report("is_even_t stack depth constant in n",
       len(set(depths)) == 1 and attempt(lambda: trampoline(is_even_t(1000, lambda r: r))) is True,
       f"(max depth for n=10,1000: {depths})")

# ---- Ex 4
print("Ex 4: wait_until")
def producer_consumer():
    ready.clear()
    buffer, log = [], []
    def produce(items, delay):
        if not items:
            return
        def step(d):
            if d > 0:
                return pause(lambda: step(d - 1))
            buffer.append(items[0])
            log.append(f"put {items[0]}")
            pause(lambda: produce(items[1:], delay))
        step(delay)
    def consume(n):
        if n == 0:
            log.append("consumer done")
            return
        def take():
            log.append(f"take {buffer.pop(0)}")
            pause(lambda: consume(n - 1))
        wait_until(lambda: len(buffer) > 0, take)
    consume(3)
    produce([1, 2, 3], 2)
    run()
    return log
got = attempt(producer_consumer)
want = ["put 1", "take 1", "put 2", "take 2", "put 3", "take 3", "consumer done"]
report("consumer waits for producer", got == want, f"(got {got})")
calls = []
got = attempt(lambda: (ready.clear(), wait_until(lambda: True, lambda: calls.append("now")), calls)[2])
report("already true: continues immediately", got == ["now"] and not ready, f"(got {got})")

# ---- Ex 5
print("Ex 5: subset sums")
for xs, target, want in [([1, 2, 3, 4, 5], 5, [(1, 4), (2, 3), (5,)]),
                         ([2, 4, 6], 5, []),
                         ([3, 3, 3], 6, [(3, 3), (3, 3), (3, 3)]),
                         ([1, 2, 3], 0, [()])]:
    got = attempt(lambda: sorted(once(lambda k: subset_sums_k(xs, target, k))))
    report(f"subset_sums_k({xs}, {target})", got == sorted(want), f"(got {got})")

# ---- Ex 6
print("Ex 6: escape from a callback")
for tree, limit, want, max_seen in [([1, [2, [30, 4]], 50], 10, 30, 3),
                                    ([1, 2, 3], 10, None, 3),
                                    ([[[[99]]]], 10, 99, 1),
                                    ([], 0, None, 0)]:
    _visited.clear()
    got = attempt(lambda: first_over(tree, limit))
    report(f"first_over({tree}, {limit})", got == want and len(_visited) <= max_seen,
           f"(got {got}, visited {_visited})")

# ---- Ex 7
print("Ex 7 (bonus): explicit stack")
for t, want in TREES:
    report(f"tree_depth_loop({t})", attempt(lambda: tree_depth_loop(t)) == want,
           f"(got {attempt(lambda: tree_depth_loop(t))})")
deep = 0
for _ in range(100_000):
    deep = (deep, 0)
got = attempt(lambda: tree_depth_loop(deep))
report("tree_depth_loop(100_000 levels deep)", got == 100_000, f"(got {got})")
