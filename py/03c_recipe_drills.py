# 03c — The recipe: converting direct style to CPS mechanically
# Run: python3 03c_recipe_drills.py
#
# CPS feels like a brain teaser when you try to write it from scratch.
# Don't. Write the normal (direct) version first, then convert it with
# these steps — no cleverness needed:
#
#   1. Add a `k` parameter (and `fail` if the function can fail).
#   2. `return value`            -> `return k(value)`
#      `raise ...`               -> `return fail(...)`
#   3. For each call to a CPS function that is NOT the last thing:
#        result = f(args)          f(args, lambda result:
#        <rest of the code>   ->       <rest of the code>)
#      i.e. "everything after the call" moves INTO the lambda.
#   4. If a call is the last thing (`return f(args)`), just pass your own k:
#        f(args, k)                   (the tail call from lesson 01)
#   5. Pass `fail` through unchanged to every call.
#
# When "the rest of the code" is more than one expression, use a nested
# `def` instead of a lambda.
#
# ---------------- worked example: sum_tree from 03b ----------------
#
# Direct style (with exceptions):
#
#   def sum_tree(tree):
#       if not tree:
#           return 0
#       x, *rest = tree
#       if isinstance(x, list):
#           v = sum_tree(x)                    # call, not last  -> step 3
#       elif isinstance(x, int):
#           v = x
#       else:
#           raise ValueError(f"not a number: {x!r}")
#       r = sum_tree(rest)                     # call, not last  -> step 3
#       return v + r
#
# Notice: two branches assign `v`, then SHARED code runs. In CPS that shared
# code becomes one named continuation that both branches feed into:
#
#   def sum_tree_k(tree, ok, fail):
#       if not tree:
#           return ok(0)                                       # step 2
#       x, *rest = tree
#       def after_v(v):                                        # step 3: "rest of the code"
#           sum_tree_k(rest, lambda r: ok(v + r), fail)        # step 3 again
#       if isinstance(x, list):
#           sum_tree_k(x, after_v, fail)
#       elif isinstance(x, int):
#           after_v(x)
#       else:
#           fail(f"not a number: {x!r}")                       # step 2
#
# Each drill below gives you the direct version. Convert it using the recipe.
# Don't write the CPS version from scratch. Translate the direct one line by line.


# ======================= Drill 1 (warm-up) =======================

def length(xs):
    if not xs:
        return 0
    _, *rest = xs
    n = length(rest)
    return 1 + n

def length_k(xs, k):
    if not xs:
        return k(0)
    _, *rest = xs
    length_k(rest, lambda n: k(1 + n))


# ======================= Drill 2 =======================

# flatten([1, [2, [3, 4], 5], [6, 7]]) == [1, 2, 3, 4, 5, 6, 7]
#
# Step A: write the direct version in "CPS-ready" shape (A-normal form):
#   - every call's result is stored in a named variable (no nested calls
#     like `f(g(x))` and no calls inside an expression like `f(a) + f(b)`)
#   - if branches differ, make them all assign the SAME variable,
#     then let one piece of shared code continue from there
#   - use recursion and plain `x, *rest = tree` (no loops / list comprehensions)
#
# Step B: convert it to CPS with the recipe.

def flatten(tree):
    if not tree:
        return []
    x, *rest = tree
    if isinstance(x, int):
        v = [x]
    elif isinstance(x, list):
        v = flatten(x)
    else:
        assert False
    r = flatten(rest)
    return v + r

def flatten_k(tree, k):
    if not tree:
        return k([])
    x, *rest = tree

    def flatten_rest(v):
        flatten_k(rest, lambda r: k(v + r))
    if isinstance(x, int):
        flatten_rest([x])
    elif isinstance(x, list):
        flatten_k(x, flatten_rest)
    else:
        assert False


# ======================= Drill 3 =======================
# Now the function you apply is ITSELF a CPS function that can fail.
# half_k halves even numbers and fails on odd ones.

half_calls = 0

def half_k(n, ok, fail):
    global half_calls
    half_calls += 1
    if n % 2:
        return fail(f"odd: {n}")
    ok(n // 2)

# The direct-style twin: raises instead of calling fail.
def half(n):
    if n % 2:
        raise ValueError(f"odd: {n}")
    return n // 2

# map_tree(half, [2, [4, [6]], 8]) == [1, [2, [3]], 4]   (same nesting, f applied to numbers)
# map_tree(half, [2, [3, 4], 6])   raises ValueError("odd: 3")
#
# Step A: write map_tree in CPS-ready shape (same rules as drill 2).
#         Calling f is a call too: treat it like any other call.
# Step B: convert to map_tree_k. f_k has the signature f_k(x, ok, fail).

def map_tree(f, tree):
    if not tree:
        return []
    x, *rest = tree
    if isinstance(x, int):
        v = [f(x)]
    elif isinstance(x, list):
        v = [map_tree(f, x)]
    else:
        assert False
    r = map_tree(f, rest)
    return v + r

def map_tree_k(f_k, tree, ok, fail):
    if not tree:
        return ok([])
    x, *rest = tree

    def map_rest(v):
        map_tree_k(f_k, rest, lambda r: ok([v] + r), fail)
    if isinstance(x, int):
        f_k(x, lambda r: map_rest(r), fail)
    elif isinstance(x, list):
        map_tree_k(f_k, x, map_rest, fail)
    else:
        assert False


# ---------------------------------------------------------------------------
# Tests — every line should say PASS.

def run(label, call, expect, extra_check=None):
    calls = []
    call(calls)
    status = "PASS" if calls == [expect] else "FAIL"
    note = ""
    if status == "PASS" and extra_check:
        ok_, note = extra_check()
        status = "PASS" if ok_ else "FAIL"
    print(f"{status}  {label:40} -> {calls} {note}")

print("Drill 1")
for xs in [[], [7], [1, 2, 3, 4]]:
    run(f"length_k({xs})", lambda c, xs=xs: length_k(xs, c.append), length(xs))

FLATTEN_CASES = [
    ([], []),
    ([1, 2], [1, 2]),
    ([1, [2, [3, 4], 5], [6, 7]], [1, 2, 3, 4, 5, 6, 7]),
    ([[[]], [[1]]], [1]),
]

print("Drill 2A (direct)")
for t, want in FLATTEN_CASES:
    run(f"flatten({t})", lambda c, t=t: c.append(flatten(t)), want)

print("Drill 2B (CPS)")
for t, want in FLATTEN_CASES:
    run(f"flatten_k({t})", lambda c, t=t: flatten_k(t, c.append), want)

def direct_map(t):
    def call(c):
        try:
            c.append(("ok", map_tree(half, t)))
        except ValueError as e:
            c.append(("fail", str(e)))
    return call

print("Drill 3A (direct)")
run("map_tree(half, [])",               direct_map([]),               ("ok", []))
run("map_tree(half, [2, [4, [6]], 8])", direct_map([2, [4, [6]], 8]), ("ok", [1, [2, [3]], 4]))
run("map_tree(half, [2, [3, 4], 6])",   direct_map([2, [3, 4], 6]),   ("fail", "odd: 3"))

print("Drill 3B (CPS)")
def m(t):
    def call(c):
        global half_calls
        half_calls = 0
        map_tree_k(half_k, t, lambda v: c.append(("ok", v)), lambda e: c.append(("fail", e)))
    return call
run("map_tree_k(half_k, [])",             m([]),             ("ok", []))
run("map_tree_k(half_k, [2, [4, [6]], 8])", m([2, [4, [6]], 8]), ("ok", [1, [2, [3]], 4]))
run("map_tree_k(half_k, [2, [3, 4], 6])",   m([2, [3, 4], 6]),   ("fail", "odd: 3"),
    extra_check=lambda: (half_calls == 2, f"(half_k called {half_calls}x, expected 2: stop at 3)"))
