# 01 — Direct style vs. CPS
# Run: python3 01_basics.py
#
# Direct style: a function RETURNS its result to whoever called it.
# CPS:          a function never returns. It receives an extra argument `k`
#               (the "continuation" = "what to do next with my result")
#               and CALLS k with the result.

# ---------- direct style ----------
def add(a, b): return a + b
def square(x): return x * x
def pyth(a, b): return add(square(a), square(b))

print("direct:", pyth(3, 4))

# ---------- CPS ----------
def add_k(a, b, k): k(a + b)
def square_k(x, k): k(x * x)

def pyth_k(a, b, k):
    square_k(a, lambda a2:          # "square a, call the result a2, and..."
        square_k(b, lambda b2:      # "square b, call the result b2, and..."
            add_k(a2, b2, k)))      # "add them, and hand the sum to MY continuation"

pyth_k(3, 4, lambda result: print("cps:   ", result))

# Things to notice:
#  1. Every intermediate value got a NAME (a2, b2). Nothing is implicit.
#  2. The ORDER of evaluation is spelled out: square a, then b, then add.
#  3. No function returns anything useful. "Returning" has been replaced by
#     "calling the next thing". The rest of the program is just a function.

# ---------- make the continuation visible ----------
# Same thing with named continuations (nested defs instead of lambdas),
# so we can print which continuation each step hands its result to.
def square_traced(x, k):
    print(f"  square_traced({x}) will continue with: {k.__qualname__}")
    k(x * x)

def pyth_traced(a, b, k):
    def after_a2(a2):
        def after_b2(b2):
            k(a2 + b2)
        square_traced(b, after_b2)
    square_traced(a, after_a2)

print("\ntracing:")
pyth_traced(3, 4, lambda s: print("  sum =", s))

# EXERCISE: write mul_k(a, b, k) and use it to compute (2 + 3) * (4 + 5)
# entirely in CPS. Then try evaluating the right side first — only the
# nesting changes.
def add_k(a, b, k):
    # with tracing
    print("Adding", a, b)
    k(a + b)

def mul_k(a, b, k):
    k(a * b)

def ex1(a, b, c, d, k):
    add_k(a, b, lambda lhs: add_k(c, d, lambda rhs: mul_k(lhs, rhs, k)))

ex1(2, 3, 4, 5, lambda res: print(res))

def ex2(a, b, c, d, k):
    add_k(c, d, lambda rhs: add_k(a, b, lambda lhs: mul_k(lhs, rhs, k)))

ex2(2, 3, 4, 5, lambda res: print(res))
