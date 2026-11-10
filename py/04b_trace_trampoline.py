# 04b — What do the thunks look like? Trace the trampoline step by step.
# Run: python3 04b_trace_trampoline.py [n]
#
# This is your v2 fib_t, but each lambda is replaced by a tiny class that
# does the same thing AND can print itself. One class per lambda:
#
#   def fib_t(n, k):
#       if n < 2: return lambda: k(n)                         -> Apply(k, n)
#       return lambda: fib_t(n - 1,                           -> CallFib(n - 1, ...)
#                      lambda lhs: fib_t(n - 2,               -> AfterLhs(n, k)
#                      lambda rhs: lambda: k(lhs + rhs)))     -> AfterRhs(lhs, k) -> Apply(...)
#
# Continuations print as "the expression waiting for a value", with □ marking
# the hole the value goes into. E.g. "□ + fib(2)" = "give me fib(3), then I'll
# compute fib(2) and add them".
import sys

# ---------- continuations (the "lambda result: ..." functions) ----------
class Done:                       # lambda r: r
    def __call__(self, v): return v
    def chain(self): return ["done"]

class AfterLhs:                   # lambda lhs: fib_t(n - 2, lambda rhs: ...)
    def __init__(self, n, k): self.n, self.k = n, k
    def __call__(self, lhs): return fib_t(self.n - 2, AfterRhs(lhs, self.k))
    def chain(self): return [f"□ + fib({self.n - 2})"] + self.k.chain()

class AfterRhs:                   # lambda rhs: lambda: k(lhs + rhs)
    def __init__(self, lhs, k): self.lhs, self.k = lhs, k
    def __call__(self, rhs): return Apply(self.k, self.lhs + rhs)
    def chain(self): return [f"{self.lhs} + □"] + self.k.chain()

# ---------- thunks (the zero-argument "lambda: ..." steps) ----------
class CallFib:                    # lambda: fib_t(n, k)
    def __init__(self, n, k): self.n, self.k = n, k
    def __call__(self): return fib_t(self.n, self.k)
    def __str__(self): return f"compute fib({self.n})"

class Apply:                      # lambda: k(v)
    def __init__(self, k, v): self.k, self.v = k, v
    def __call__(self): return self.k(self.v)
    def __str__(self): return f"deliver {self.v}"

def fib_t(n, k):
    if n < 2:
        return Apply(k, n)
    return CallFib(n - 1, AfterLhs(n, k))

# ---------- a trampoline that prints every step ----------
def traced_trampoline(step):
    i = 0
    while callable(step):
        stack = " → ".join(step.k.chain())
        print(f"{i:>3}  {str(step):<16} then: {stack}")
        step = step()
        i += 1
    print(f"{i:>3}  result = {step}")
    return step

n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
print(f"fib({n}), one line per trampoline step\n")
print(f"{'step':>4} {'thunk':<16} continuation chain (innermost first)")
traced_trampoline(CallFib(n, Done()))
