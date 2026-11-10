# 04 — The call stack is just a continuation. Move it to the heap.
# Run: python3 04_the_stack_is_a_continuation.py
import sys

N = 100_000
print("recursion limit:", sys.getrecursionlimit())

# ---------- direct recursion: the stack remembers "what's left to do" ----------
def total(n):
    return 0 if n == 0 else n + total(n - 1)

try:
    print("direct:        ", total(N))
except RecursionError as e:
    print("direct:         RecursionError -", e)
# Each pending `n + ___` sits in a stack frame. 100k of them don't fit.

# ---------- naive CPS: still overflows in Python! ----------
def total_k(n, k):
    return k(0) if n == 0 else total_k(n - 1, lambda r: k(n + r))

try:
    print("naive cps:     ", total_k(N, lambda r: r))
except RecursionError as e:
    print("naive cps:      RecursionError -", e)
# Every call in CPS is a tail call, but Python (and Node) don't optimize
# tail calls, so k(...) calling k(...) calling k(...) still stacks up.

# ---------- CPS + trampoline ----------
# Instead of CALLING the next step, RETURN it as a thunk (a zero-arg lambda),
# and let a flat loop call it. Now the Python stack never grows.
def total_t(n, k):
    if n == 0:
        return lambda: k(0)
    return lambda: total_t(n - 1, lambda r: lambda: k(n + r))


def trampoline(step):
    while callable(step):
        step = step()
    return step


print("cps+trampoline:", trampoline(total_t(N, lambda r: r)))

# What moved where:
#   direct: pending "n + ___"  lives in   stack frames   (limited)
#   CPS:    pending "n + ___"  lives in   closures k     (heap, as big as RAM)
# The continuation is literally a reified call stack.
#
# This is how Scheme implementations, SML/NJ, Kotlin coroutines, etc. get deep
# recursion and suspendable functions: transform to CPS, then run on a loop.

# EXERCISE: convert fib(n) = fib(n-1) + fib(n-2) to CPS + trampoline.
# It has TWO recursive calls — the first continuation must start the second.
def fib(n):
    if n <= 1:
        return n
    lhs = fib(n - 1)
    rhs = fib(n - 2)
    return lhs + rhs

def fib_k(n, k):
    if n <= 1:
        return k(n)
    fib_k(n - 1, lambda lhs: fib_k(n - 2, lambda rhs: k(lhs + rhs)))

def fib_t(n, k):
    if n <= 1:
        return lambda: k(n)
    return lambda: fib_t(n - 1, lambda lhs: fib_t(n - 2, lambda rhs: lambda: k(lhs + rhs)))


# ---------------------------------------------------------------------------
# Tests for the exercise — every line should say PASS.
# Convention: fib(0) = 0, fib(1) = 1, fib(2) = 1, fib(3) = 2, ...

FIBS = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610]

def report(label, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {label:38} {detail}")

def attempt(thunk):
    """Run thunk(); return ("ok", value) or ("error", ExceptionName)."""
    try:
        return ("ok", thunk())
    except Exception as e:
        return ("error", type(e).__name__)

print("\n--- exercise tests ---")

# 1. Direct version: correct values.
got = [attempt(lambda n=n: fib(n)) for n in range(len(FIBS))]
report("fib(0..15)", got == [("ok", v) for v in FIBS],
       "" if got == [("ok", v) for v in FIBS] else f"got {got[:4]}...")

# 2. Plain CPS: k must be called exactly once, with the right value.
#    Only up to n=10: plain CPS in Python already overflows the default
#    recursion limit (1000) around n=13. Nothing ever returns until the very
#    end, so EVERY call so far is still on the stack. That's what step 5 fixes.
def cps_result(n):
    calls = []
    fib_k(n, calls.append)
    return calls
got = [attempt(lambda n=n: cps_result(n)) for n in range(11)]
want = [("ok", [v]) for v in FIBS[:11]]
report("fib_k(0..10) calls k once", got == want,
       "" if got == want else f"got {got[:4]}...")

# 3. Trampolined CPS: correct values via the trampoline.
got = [attempt(lambda n=n: trampoline(fib_t(n, lambda r: r))) for n in range(len(FIBS))]
want = [("ok", v) for v in FIBS]
report("trampoline(fib_t(0..15))", got == want,
       "" if got == want else f"got {got[:4]}...")

# 4. fib_t must not do the work itself: it should hand back a step (a thunk)
#    for the trampoline to run, not a finished number.
first = attempt(lambda: fib_t(10, lambda r: r))
report("fib_t(10, k) returns a thunk", first[0] == "ok" and callable(first[1]),
       f"(returned {first[1]!r})" if not callable(first[1]) else "")

# 5. Stack safety: the max stack depth while running must NOT grow with n.
#    (A recursion-limit test is too weak here: a half-trampolined version only
#    reaches ~n frames, which fits under any reasonable limit for small n.)
import sys

def max_depth(run):
    """Run run() and return the deepest Python call stack seen (via a profiler)."""
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
        run()
    finally:
        sys.setprofile(None)
    return best

depths = [max_depth(lambda n=n: attempt(lambda: trampoline(fib_t(n, lambda r: r))))
          for n in (5, 10, 20)]
report("fib_t stack depth constant in n", len(set(depths)) == 1,
       f"(max depth for n=5,10,20: {depths})")
naive = [max_depth(lambda n=n: attempt(lambda: cps_result(n))) for n in (5, 10)]
print(f"      (for comparison, plain fib_k max depth for n=5,10: {naive})")
