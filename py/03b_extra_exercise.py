# 03b — Extra exercise: sum a nested tree, fail fast on bad data
# Run: python3 03b_extra_exercise.py
#
# Combines the two ideas from 03:
#   - product_k:  continuations that CARRY A VALUE (the partial result)
#   - find_k:     walking a NESTED tree, with an early-exit continuation
#
# Write sum_tree_k(tree, ok, fail):
#   - tree is a list that may contain numbers and nested lists
#   - when everything is a number, call ok(total)
#   - as soon as you meet something that is not a number or a list,
#     call fail(f"not a number: {item!r}") — and do NO further work
#
# Rules (same spirit as lesson 03):
#   - do every addition with add_k (it counts them)
#   - nothing after a call: whatever comes "next" goes into a continuation
#   - ok or fail must be called EXACTLY ONCE per sum_tree_k call from the outside

additions = 0

def add_k(a, b, k):
    global additions
    additions += 1
    k(a + b)


def sum_tree_k(tree, ok, fail):
    assert isinstance(tree, list)
    if not tree:
        return ok(0)

    x, *rest = tree

    def then_add_rest(v):
        sum_tree_k(rest, lambda r: add_k(v, r, ok), fail)
    if isinstance(x, list):
        return sum_tree_k(x, then_add_rest, fail)
    if isinstance(x, int):
        then_add_rest(x)
    else:
        return fail(f"not a number: {x!r}")


# ---------------------------------------------------------------------------
# Tests — don't edit below. Every line should say PASS.

def check(tree, expect, max_additions=None):
    global additions
    additions = 0
    calls = []
    sum_tree_k(tree, lambda v: calls.append(("ok", v)), lambda e: calls.append(("fail", e)))
    status = "PASS" if calls == [expect] else "FAIL"
    if status == "PASS" and max_additions is not None and additions > max_additions:
        status = "FAIL"
    print(f"{status}  {tree!r:32} -> {calls}  ({additions} additions)")

check([1, 2, 3],                     ("ok", 6))
check([1, [2, 3]],                     ("ok", 6))
check([],                            ("ok", 0))
check([[[]]],                        ("ok", 0))
check([1, [2, [3, 4], 5], [6, 7]],   ("ok", 28))
check(["x"],                         ("fail", "not a number: 'x'"))
check([1, [2, ["x", 4], 5], [6, 7]], ("fail", "not a number: 'x'"), max_additions=0)
check([1, 2, 3, "y", "z"],           ("fail", "not a number: 'y'"), max_additions=0)

# The max_additions=0 tests are the interesting ones: when the bad item is
# found, the pending "add me to the rest" steps must simply never run.
#
# BONUS: make the error report WHERE the bad item is, e.g.
#   "not a number: 'x' at path [1, 1, 0]"   (index at each nesting level)
