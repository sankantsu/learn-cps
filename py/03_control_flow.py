# 03 — Continuations ARE control flow: build your own `raise` and early `return`
# Run: python3 03_control_flow.py
#
# If "what happens next" is just a function, you can pass MORE THAN ONE.
# Pick which one to call, and you've invented branching / exceptions.

# ---------- exceptions without try/except ----------
def div_k(a, b, ok, fail):
    if b == 0:
        fail(f"cannot divide {a} by zero")
    else:
        ok(a / b)

# (x / y) / z
def calc_k(x, y, z, ok, fail):
    div_k(x, y, lambda r: div_k(r, z, ok, fail), fail)

ok   = lambda v: print("ok:  ", v)
fail = lambda e: print("fail:", e)
calc_k(100, 5, 2, ok, fail)   # ok: 10.0
calc_k(100, 0, 2, ok, fail)   # fail: ... (second division never runs)

# `fail` is exactly what an `except` block is: a continuation you jump to,
# skipping everything the normal continuation would have done.

# ---------- early exit that skips pending work ----------
# Multiply a list. If we meet a 0, the answer is 0 — so skip ALL the
# multiplications that are still waiting.

mults = 0

def product_direct(xs):
    global mults
    if not xs:
        return 1
    x, *rest = xs
    r = product_direct(rest)    # even after finding 0 deep inside,
    mults += 1                  # every frame still multiplies on the way out
    return x * r

def product_k(xs, k, exit):
    if not xs:
        return k(1)
    x, *rest = xs
    if x == 0:
        return exit(0)          # jump straight to the OUTERMOST continuation
    def after_rest(r):
        global mults
        mults += 1
        k(x * r)
    product_k(rest, after_rest, exit)

nums = [1, 2, 3, 4, 0, 5, 6, 7]

mults = 0
d = product_direct(nums)
print(f"\ndirect: {d} after {mults} multiplications")

mults = 0
done = lambda v: print(f"cps:    {v} after {mults} multiplications")
product_k(nums, done, done)     # normal continuation and exit are the same final `done`

# What happened: the chain of pending `after_rest` closures IS the
# "stack of work left to do". By calling `exit` we simply never call them.
# That's what `raise`, `return` from nested loops, and `break` do.

# EXERCISE: write find_k(tree, pred, found, not_found) that searches a nested
# list like [1, [2, [3, 4]], 5] and calls `found` the instant it sees a
# match, without unwinding through the recursion.
def find_k(tree, pred, found, not_found):
    assert isinstance(tree, list)
    print(f"(Trace) find_k tree={tree}")
    if not tree:
        return not_found()

    item, *rest = tree
    if pred(item):
        return found(item)

    def find_rest():
        find_k(rest, pred, found, not_found)

    if isinstance(item, list):
        find_k(item, pred, found, find_rest)
    else:
        find_rest()

tree = [1, [2, [3, 4], 5], [6, 7]]
found = lambda x: print(f"Found {x}")
not_found = lambda : print("Not found")
find_k(tree, lambda x: x == 4, found, not_found)
find_k(tree, lambda x: x == -1, found, not_found)
