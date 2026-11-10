# 07 — call/cc: "give me the rest of the program as a value"
# Run: python3 07_callcc.py
#
# Scheme's call/cc (call-with-current-continuation) calls a function f and
# passes it k = "the rest of the program from the point where call/cc was
# called". Calling k(v) ABANDONS whatever is running and makes that call/cc
# expression produce v instead, then the program carries on from there.
#
# Python has no real call/cc. We'll look at it two ways:
#   Part 1: escape-only call/cc in normal Python (built from exceptions)
#   Part 2: full call/cc in CPS (it's 2 lines, because CPS already HAS k)


# ======================= Part 1: escape-only call/cc =======================
# call_ec(f): call f(escape). If f calls escape(v), call_ec returns v right away,
# no matter how deep inside loops and calls it is. Otherwise it returns f's result.

class _Escape(Exception):
    def __init__(self, tag, value):
        self.tag, self.value = tag, value

def call_ec(f):
    tag = object()                       # unique id, so nested call_ec's don't mix up
    def escape(v):
        raise _Escape(tag, v)
    try:
        return f(escape)
    except _Escape as e:
        if e.tag is not tag:
            raise
        return e.value

# Where does escape beat a plain `return`? When the place you want to leave
# from is in a DIFFERENT function than the one you want to return from.
# `return` only exits the function it's written in. Here `key` is a callback
# that sorted() calls; `return` inside key can't stop sorted():

def first_long_word(words):
    calls = []
    def search(escape):
        def key(w):
            calls.append(w)
            if len(w) > 10:
                escape(w)            # exits key AND sorted() AND search, at once
            return len(w)
        sorted(words, key=key)       # code we don't control
        return None                  # normal return: nothing found
    return call_ec(search), calls

print("--- part 1: escape ---")
words = ["cat", "continuation", "dog", "trampoline", "backtracking"]
found, looked_at = first_long_word(words)
print(f"found {found!r} after looking at {looked_at}")   # stops at the 2nd word
print(first_long_word(["a", "b"]))                          # (None, ['a', 'b'])

# This is a "non-local return": return from an OUTER function, from inside an
# inner one. Ruby/Kotlin/Smalltalk have it built in (`return` inside a block).

# This is the "exception" approach from lesson 06, B, given a name. It's ONE-SHOT and
# OUTWARD-ONLY: after call_ec returns, `escape` is useless, because the frames
# it would jump into are gone. Calling it later just raises an error.


# ======================= Part 2: full call/cc in CPS =======================
# In CPS every function already receives k. call/cc just HANDS k to f as a value:

def call_cc_k(f_k, k):
    escape = lambda v, _ignored_k: k(v)   # a continuation, packaged as a CPS function
    return f_k(escape, k)

# The `_ignored_k` is the whole trick: whoever calls escape(v, their_k) passes
# their own "what to do next", and escape THROWS IT AWAY and jumps to k instead.
# That's the "abandon what's running" part.

def add_k(a, b, k): return k(a + b)

# The classic demo. In Scheme:
#   (define saved #f)
#   (display (+ 1 (call/cc (lambda (c) (set! saved c) 1))))    ; prints 2
#   (saved 10)                                                 ; prints 11 (!)
saved = None

def demo(k_done):
    def f_k(c, k):
        global saved
        saved = c          # keep "the rest of the program" for later
        return k(1)        # ...and continue normally with 1
    return call_cc_k(f_k, lambda v:
           add_k(1, v, lambda x:
           (print("  1 + call/cc(...) =", x), k_done())[1]))

print("\n--- part 2: re-entering a saved continuation ---")
demo(lambda: None)
print("  now calling saved(10, ...) — this jumps BACK into the middle of demo:")
saved(10, None)
print("  and again with 100:")
saved(100, None)

# "But that's just a saved function!" Yes — IN CPS. Here call_cc_k is trivial
# because we already rewrote the program in CPS by hand, so k exists as a
# function. In normal (direct-style) code, "the rest of the program" is only
# implicit: Python's stack frames + where execution resumes. Inside
# `print(1 + f())`, f has NO way to get "add 1, print, run the rest" as a value.
# Real call/cc turns that implicit state into a function value WITHOUT you
# rewriting anything. That's what lets Scheme build exceptions, generators and
# coroutines as library functions, while Python needed new syntax for each
# (yield: PEP 255, async/await: PEP 492).
#
# The same saved continuation ran THREE times: once normally, twice re-entered.
# A Python exception can't do this (part 1), and neither can a generator (one-shot).
# This is the "multi-shot" power that choose() in lesson 06 relied on.


# ======================= Exercises =======================
#
# EXERCISE 1 (part 1, warm-up): using call_ec, write first_negative(tree) that
# returns the first negative number in a nested list, or None. Write it as a
# normal recursive function; use `escape` to get out of the recursion at once.
#
# EXERCISE 2 (part 2): a loop made only of a saved continuation.
# Write count_up_k(limit, k) in CPS that calls k([0, 1, ..., limit]), WITHOUT
# any for/while loop and WITHOUT calling count_up_k recursively. Instead:
#   - use call_cc_k to capture `again` at the start, with initial value 0,
#   - after recording x, if x < limit, call `again` with x + 1 to jump back,
#   - otherwise call k with the recorded list.
# In direct style with a real call/cc, it would read:
#     out = []
#     x, again = call/cc(lambda c: (0, c))
#     out.append(x)
#     if x < limit: again((x + 1, again))
#     return out
# Hint: the value passed through call/cc can be a pair (x, again), since `again`
#       must be available again after every jump back.

def first_negative(tree):
    def walk(tree, escape):
        for item in tree:
            if isinstance(item, list):
                walk(item, escape)
            else:
                assert isinstance(item, int)
                if item < 0:
                    escape(item)
    return call_ec(lambda escape: walk(tree, escape))


def count_up_k(limit, k):
    def f_k(c, k):
        return k((0, c))
    out = []

    def g(v):
        x, again = v
        out.append(x)
        if x < limit:
            return again((x + 1, again), lambda _: k(out))
        return k(out)
    return call_cc_k(f_k, g)


# ---------------------------------------------------------------------------
# Tests — every line should say PASS.

def report(label, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {label:40} {detail}")

def attempt(thunk):
    try:
        return thunk()
    except Exception as e:
        return f"!! {type(e).__name__}: {e}"

print("\n--- exercise tests ---")

cases = [([1, [2, [-3, 4]], -5], -3), ([1, 2, 3], None), ([], None), ([[[-1]]], -1), ([0, [5, [6, -7]]], -7)]
for tree, want in cases:
    got = attempt(lambda: first_negative(tree))
    report(f"first_negative({tree})", got == want, f"(got {got!r})")

for limit, want in [(0, [0]), (3, [0, 1, 2, 3]), (10, list(range(11)))]:
    calls = []
    got = attempt(lambda: (count_up_k(limit, calls.append), calls)[1])
    report(f"count_up_k({limit})", got == [want], f"(got {got})")
