# Final exercises (optional): the two hardest ideas, one more time
# Run: python3 ex_final.py
#
#   Ex A  recursive data + ok/fail continuations + rebuilding (lessons 03, 03b, 03c)
#   Ex B  full-CPS search with "ask for the next answer" + trampoline (lessons 04, 06)
#
# Replace each `raise NotImplementedError` with your code. As before, write the
# direct-style version first, then the CPS one.


def trampoline(step):
    while callable(step):
        step = step()
    return step


# ======================= Ex A: replace the first match =======================
# A tree is a (possibly nested) Python list of ints, e.g. [1, [2, [3, 4]], 5].
# Find the FIRST leaf (left to right) where pred(leaf) is true, and return a NEW
# tree where only that leaf is replaced by f(leaf). Don't mutate the input.
# Stop as soon as you've found it: pred must not be called on later leaves.
#
#   replace_first([1, [2, [3, 4]], 5], is_even, times10)
#       == (True, [1, [20, [3, 4]], 5])      # 4 is NOT replaced: only the first
#   replace_first([1, 3], is_even, times10)
#       == (False, [1, 3])
#
# Step A: replace_first(tree, pred, f) in direct style (ANF), returning a pair
#         (found?, tree). (Notice how much of the code is about the flag.)
# Step B: replace_first_k(tree, pred, f, found, not_found) in CPS:
#         call found(new_tree) or not_found(), exactly one of them, exactly once.
#         No flag: which continuation you call IS the flag.
#
# Hint: if you get stuck on the shape, think "head, then rest". The head can be a leaf or
#       a sublist. If it's a sublist and nothing matches inside it, the search
#       must carry on into the rest.

# def replace_first(tree, pred, f):
#     def helper(found, tree):
#         # print("helper", found, tree)
#         assert isinstance(tree, (int, list))
#         if found:
#             return found, tree
#         if isinstance(tree, int):
#             if pred(tree):
#                 return True, f(tree)
#             return found, tree
#         assert isinstance(tree, list)
#         if not tree:
#             return found, tree
#         x, *rest = tree
#         found, x = helper(found, x)
#         found, rest = helper(found, rest)
#         return found, [x] + rest
#     return helper(False, tree)

def replace_first(tree, pred, f):
    assert isinstance(tree, (int, list))
    if isinstance(tree, int):
        if pred(tree):
            return True, f(tree)
        return False, tree
    assert isinstance(tree, list)
    if not tree:
        return False, []
    x, *rest = tree
    ok, x = replace_first(x, pred, f)
    if ok:
        return True, [x] + rest
    ok, rest = replace_first(rest, pred, f)
    if ok:
        return True, [x] + rest
    return False, [x] + rest


def replace_first_k(tree, pred, f, found, not_found):
    assert isinstance(tree, (int, list))
    if isinstance(tree, int):
        if pred(tree):
            return found(f(tree))
        return not_found()
    assert isinstance(tree, list)
    if not tree:
        return not_found()
    x, *rest = tree
    return replace_first_k(x, pred, f,
        lambda x: found([x] + rest),
        lambda: replace_first_k(rest, pred, f,
            lambda rest: found([x] + rest),
            lambda: not_found(),
        )
    )

# Example:
#
# [1, [3, 2], 4]
# found0 = lambda r: print(r)
# found1 = lambda r: found0([1] + r)
# found2 = lambda x: found1([x] + [4])
# found3 = lambda r: found2([3] + r)
# found4 = lambda x: found3([x] + [])
# found4(f(2)) = found4(20)
#              = found3([20])
#              = found2([3, 20])
#              = found1([[3, 20], 4])
#              = found0([1, [3, 20], 4])
#              = print([1, [3, 20], 4])

is_even = lambda x: x % 2 == 0
print(replace_first([1, 2, 3, 4], is_even, lambda x: x*10))
print(replace_first([1, [2, 3], 4], is_even, lambda x: x*10))
print(replace_first([1, 3, 5], is_even, lambda x: x*10))
print_found = lambda x: print(f"Found {x}")
print_not_found = lambda: print("Not found")
print(replace_first_k([1, 2, 3, 4], is_even, lambda x: x*10, print_found, print_not_found))
print(replace_first_k([1, [2, 3], 4], is_even, lambda x: x*10, print_found, print_not_found))
print(replace_first_k([1, 3, 5], is_even, lambda x: x*10, print_found, print_not_found))
print(replace_first_k([1, [3, 2], 4], is_even, lambda x: x*10, print_found, print_not_found))

# ======================= Ex B: all paths, one at a time =======================
# A graph is a dict: node -> list of neighbours (every node is a key).
# Find SIMPLE paths (no node twice) from start to goal, depth-first, trying
# neighbours in list order. A path is a tuple of nodes, start and goal included.
# Once you reach the goal, that path ends: don't look at the goal's neighbours.
#
#   G = {"a": ["b", "c"], "b": ["d"], "c": ["d"], "d": []}
#   paths from "a" to "d", in order:  ("a", "b", "d"), ("a", "c", "d")
#
# Step A: paths_gen(graph, start, goal): a generator yielding the paths in order.
#         (Python saves the "where was I in the search" continuation for you.)
#
# Step B: paths_k(graph, start, goal, found, not_found), full CPS. No
#         generators, no for/while loops, no exceptions:
#           - for each path, call found(path, retry). `retry` is a zero-argument
#             function: calling it resumes the search for the NEXT path.
#           - when there are no more paths, call not_found().
#         It's the caller who decides whether to continue, so stopping early
#         comes for free. E.g. "give me the first path":
#             found = lambda path, retry: path       # just don't call retry
#         and "give me all paths":
#             found = lambda path, retry: (out.append(path), retry)[1]
#
#         The tests run trampoline(paths_k(...)), so:
#           - EVERY call must `return` its result (found's result, not_found's
#             result, ...), so the return values travel back to the trampoline.
#           - found may return `retry` itself, meaning "trampoline, please call
#             it". So retry must work as a thunk.
#         Get the small tests passing first. The deep tests (a 3000-node chain)
#         then need thunks in the right places (lesson 04's rule: every cycle
#         in the call graph must pass through a thunk).
#
# paths_gen can't pass the deep tests (Python's stack), so they only run paths_k.

# v1: for loop
# def paths_gen(graph, start, goal):
#     def dfs(cur, path):
#         path.append(cur)
#         if cur == goal:
#             yield tuple(path)
#         else:
#             for nxt in graph[cur]:
#                 if nxt in path:
#                     continue
#                 yield from dfs(nxt, path)
#         path.pop() # remove current state
#     yield from dfs(start, [])

# v2: recursion, list -> tuple
def paths_gen(graph, start, goal):
    def dfs(cur, nxts, path):
        if cur == goal:
            yield path
        else:
            if nxts:
                nxt, *rest = nxts
                if nxt not in path:
                    yield from dfs(nxt, graph[nxt], path + (nxt,))
                yield from dfs(cur, rest, path)
    yield from dfs(start, graph[start], (start,))


def paths_k(graph, start, goal, found, not_found):
    def dfs_k(cur, nxts, path, found, resume):
        if cur == goal:
            return found(path, resume)
        if not nxts:
            return resume
        nxt, *rest = nxts

        def dfs_rest():
            return lambda: dfs_k(cur, rest, path, found, resume)
        if nxt in path:
            return dfs_rest
        else:
            return lambda: dfs_k(nxt, graph[nxt], path + (nxt,), found, dfs_rest)

    return dfs_k(start, graph[start], (start,), found, not_found)

    

print("--- paths_gen examples ---")
print(list(paths_gen({"a": ["b", "c"], "b": ["d"], "c": ["d"], "d": []}, "a", "d")))

# ---------------------------------------------------------------------------
# Tests — every line should say PASS.

def report(label, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {label:50} {detail}")

def attempt(thunk):
    try:
        return thunk()
    except Exception as e:
        return f"!! {type(e).__name__}: {e}"

import copy

# ---------- Ex A ----------
print("Ex A: replace the first match")
is_even = lambda x: x % 2 == 0
times10 = lambda x: x * 10

A_CASES = [
    ([1, [2, [3, 4]], 5],    [1, [20, [3, 4]], 5]),
    ([1, 3, 5],              None),
    ([],                     None),
    ([[], [[], [3, 4]]],     [[], [[], [3, 40]]]),
    ([[[[6]]], 8],           [[[[60]]], 8]),
    ([1, [3, [5]], 7, 8],    [1, [3, [5]], 7, 80]),
    ([[1, [3]], [[5], 2]],   [[1, [3]], [[5], 20]]),
]

def leaves(tree):
    return [y for x in tree for y in (leaves(x) if isinstance(x, list) else [x])]

def first_match_prefix(tree):
    ls = leaves(tree)
    for i, x in enumerate(ls):
        if is_even(x):
            return ls[:i + 1]
    return ls

def spy_pred(seen):
    return lambda x: (seen.append(x), is_even(x))[1]

# Step A (direct)
for tree, want in A_CASES:
    original = copy.deepcopy(tree)
    seen = []
    got = attempt(lambda: replace_first(tree, spy_pred(seen), times10))
    expect = (True, want) if want is not None else (False, original)
    ok = got == expect and tree == original and seen == first_match_prefix(original)
    report(f"replace_first({original})", ok,
           "" if ok else f"(got {got}, pred saw {seen}, input now {tree})")

# Step B (CPS)
def run_replace_k(tree, pred):
    calls = []
    replace_first_k(tree, pred, times10,
                    lambda t: calls.append(("found", t)),
                    lambda: calls.append(("not_found",)))
    return calls

for tree, want in A_CASES:
    original = copy.deepcopy(tree)
    seen = []
    got = attempt(lambda: run_replace_k(tree, spy_pred(seen)))
    expect = [("found", want)] if want is not None else [("not_found",)]
    ok = got == expect and tree == original and seen == first_match_prefix(original)
    report(f"replace_first_k({original})", ok,
           "" if ok else f"(got {got}, pred saw {seen}, input now {tree})")

# ---------- Ex B ----------
print("\nEx B: all paths, one at a time")

class LoggingGraph(dict):
    """A dict that records every node whose neighbours were looked up."""
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.log = []
    def __getitem__(self, node):
        self.log.append(node)
        return super().__getitem__(node)
    def get(self, node, default=None):
        self.log.append(node)
        return super().get(node, default)

def take(n, graph, start, goal):
    """Run paths_k, asking for up to n paths. Returns (paths, how it ended)."""
    out = []
    def found(path, retry):
        out.append(path)
        return retry if len(out) < n else "stopped"
    end = trampoline(paths_k(graph, start, goal, found, lambda: "exhausted"))
    return out, end

INF = float("inf")
G_DIAMOND = {"a": ["b", "c"], "b": ["d"], "c": ["d"], "d": []}
G_CYCLE   = {"a": ["b"], "b": ["a", "c"], "c": ["b", "d"], "d": []}
G_TANGLE  = {1: [2, 3], 2: [3, 4], 3: [2, 4], 4: [1]}
G_NONE    = {"a": ["b"], "b": ["a"], "c": []}

B_CASES = [
    ("diamond", G_DIAMOND, "a", "d", [("a", "b", "d"), ("a", "c", "d")]),
    ("cycle",   G_CYCLE,   "a", "d", [("a", "b", "c", "d")]),
    ("tangle",  G_TANGLE,  1, 4,     [(1, 2, 3, 4), (1, 2, 4), (1, 3, 2, 4), (1, 3, 4)]),
    ("no path", G_NONE,    "a", "c", []),
    ("start is goal", G_TANGLE, 1, 1, [(1,)]),
]

# Step A (generator)
for name, g, s, t, want in B_CASES:
    got = attempt(lambda: list(paths_gen(g, s, t)))
    report(f"paths_gen: {name}", got == want, "" if got == want else f"(got {got})")

# Step B (CPS): all paths, then "exhausted"
for name, g, s, t, want in B_CASES:
    got = attempt(lambda: take(INF, g, s, t))
    report(f"paths_k all: {name}", got == (want, "exhausted"),
           "" if got == (want, "exhausted") else f"(got {got})")

# Stopping early: the caller just doesn't call retry
got = attempt(lambda: take(1, G_TANGLE, 1, 4))
report("paths_k: first only", got == ([(1, 2, 3, 4)], "stopped"), f"(got {got})")
got = attempt(lambda: take(2, G_TANGLE, 1, 4))
report("paths_k: first two", got == ([(1, 2, 3, 4), (1, 2, 4)], "stopped"), f"(got {got})")

# ...and stopping really stops: a 6x6 grid (right/down moves) has 252 paths,
# but finding the first one should only look at ~10 nodes.
def grid(n):
    g = LoggingGraph()
    for r in range(n):
        for c in range(n):
            g[(r, c)] = [(r + dr, c + dc) for dr, dc in ((0, 1), (1, 0))
                         if r + dr < n and c + dc < n]
    return g

g1 = grid(6)
got1 = attempt(lambda: take(1, g1, (0, 0), (5, 5)))
gall = grid(6)
gotall = attempt(lambda: take(INF, gall, (0, 0), (5, 5)))
ok = (isinstance(got1, tuple) and len(got1[0]) == 1 and got1[1] == "stopped" and
      isinstance(gotall, tuple) and len(gotall[0]) == 252 and
      len(g1.log) <= 11 and len(g1.log) * 10 < len(gall.log))
report("paths_k: stopping early does little work", ok,
       f"(nodes looked up: first={len(g1.log)}, all={len(gall.log)})")

# Deep: 3000-node chain. Every node also has a dead end tried FIRST, so the
# search must back out of 3000 dead ends (deep retry chains, too).
N = 3000
deep = {i: [("dead", i), i + 1] for i in range(N - 1)}
deep[N - 1] = []
for i in range(N - 1):
    deep[("dead", i)] = []
got = attempt(lambda: take(INF, deep, 0, N - 1))
ok = isinstance(got, tuple) and got[0] == [tuple(range(N))] and got[1] == "exhausted"
report("paths_k: 3000-node chain with dead ends", ok,
       "" if ok else f"(got {str(got)[:120]})")
