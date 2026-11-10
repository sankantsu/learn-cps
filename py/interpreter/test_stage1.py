# Stage 1 tests: the core language. Run: python3 test_stage1.py
# Every line should say PASS.
import interp
from interp import evaluate, eval_k
from testlib import report, attempt


def FACT(n):
    return (
        "letrec",
        "fact",
        (
            "fn",
            ["n"],
            ("if", ("<", "n", 1), 1, ("*", "n", ("call", "fact", ("-", "n", 1)))),
        ),
        ("call", "fact", n),
    )


def FIB(n):
    return (
        "letrec",
        "fib",
        (
            "fn",
            ["n"],
            (
                "if",
                ("<", "n", 2),
                "n",
                ("+", ("call", "fib", ("-", "n", 1)), ("call", "fib", ("-", "n", 2))),
            ),
        ),
        ("call", "fib", n),
    )


TWICE = (
    "let",
    "twice",
    ("fn", ["f", "x"], ("call", "f", ("call", "f", "x"))),
    ("let", "inc", ("fn", ["n"], ("+", "n", 1)), ("call", "twice", "inc", 5)),
)

ADDER = (
    "let",
    "make_adder",
    ("fn", ["a"], ("fn", ["b"], ("+", "a", "b"))),
    ("let", "add5", ("call", "make_adder", 5), ("call", "add5", 10)),
)

LEXICAL = (
    "let",
    "x",
    1,
    ("let", "f", ("fn", [], "x"), ("let", "x", 2, ("call", "f"))),
)  # lexical scope: 1 (dynamic scope would give 2)

# A closure must NOT see variables bound where it is CALLED. In UNBOUND,
# `secret` only exists at the call site, so looking it up inside f must fail.
UNBOUND = ("let", "f", ("fn", [], "secret"), ("let", "secret", 2, ("call", "f")))


# letrec's name must be visible only in its own fn and body, not to the code
# around it: the ("call", "loop_fn") on the right of + must fail.
LETREC_LEAK = ("+", ("letrec", "loop_fn", ("fn", [], 1), 0), ("call", "loop_fn"))


# let is NOT letrec: the value is evaluated in the OUTER env, so the inner x
# inside the fn is the outer x (1). Evaluating it in the new env would make the
# closure see itself, and the call would return the closure instead.
LET_NOT_REC = ("let", "x", 1, ("let", "x", ("fn", [], "x"), ("call", "x")))


class Raises:
    """Expected result: evaluating must raise an exception whose message mentions
    `name` (e.g. KeyError('secret') or NameError('unbound variable: secret')).
    Any Python exception type is fine for now; stage 3 adds the language's own errors."""

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"<raises, mentioning {self.name!r}>"


STAGE1 = [
    ("literal int", 42, 42),
    ("literal bool", True, True),
    ("variable", "y", 7),  # env = {"y": 7}
    ("arithmetic", ("-", ("*", 6, 7), ("+", 1, 1)), 40),
    ("comparison", ("==", ("+", 1, 2), 3), True),
    ("if: true branch", ("if", ("<", 1, 2), 10, 20), 10),
    ("if: false branch", ("if", ("<", 2, 1), 10, 20), 20),
    ("if: untaken branch unevaluated", ("if", True, 1, "no_such_var"), 1),
    ("let", ("let", "x", 5, ("+", "x", "y")), 12),
    ("let: shadowing", ("let", "x", 1, ("let", "x", 2, "x")), 2),
    ("let: inner doesn't leak", ("let", "x", 1, ("+", ("let", "x", 2, "x"), "x")), 3),
    ("call: zero args", ("call", ("fn", [], 99)), 99),
    (
        "call: arg order",
        ("call", ("fn", ["a", "b", "c"], ("-", ("-", "a", "b"), "c")), 10, 3, 2),
        5,
    ),
    ("higher-order (twice)", TWICE, 7),
    ("closure (make_adder)", ADDER, 15),
    (
        "call: param shadows outer",
        ("let", "x", 1, ("let", "f", ("fn", ["x"], "x"), ("call", "f", 2))),
        2,
    ),
    ("lexical scope", LEXICAL, 1),
    ("lexical scope: unbound at definition", UNBOUND, Raises("secret")),
    ("letrec: name doesn't leak outside", LETREC_LEAK, Raises("loop_fn")),
    ("let: value can't see its own name", LET_NOT_REC, 1),
    ("letrec: fact(10)", FACT(10), 3628800),
    ("letrec: fib(15)", FIB(15), 610),
]

# Without a trampoline, every step of a CPS evaluator is a nested Python call,
# so even fib(8) overflows Python's stack. Stage 1 CPS tests use small inputs;
# stage 2 will make the big ones work.
TOO_DEEP_FOR_K = {"letrec: fact(10)", "letrec: fib(15)"}
STAGE1_K = [case for case in STAGE1 if case[0] not in TOO_DEEP_FOR_K] + [
    ("letrec: fact(6)", FACT(6), 720),
    ("letrec: fib(6)", FIB(6), 8),
]


def run_k(expr, env):
    """Run eval_k, with interp.evaluate disabled: a CPS evaluator must not hand
    any part of the program (e.g. a function body) to the direct-style one."""

    def no_direct(*args):
        raise AssertionError("eval_k called evaluate() (direct style)")

    calls = []
    real, interp.evaluate = interp.evaluate, no_direct
    try:
        eval_k(expr, env, calls.append)
    finally:
        interp.evaluate = real
    return calls


def check(label, run, want):
    """run() evaluates the case; want is the expected value, or a Raises(...)."""
    try:
        got = run()
    except NotImplementedError:
        return report(label, False, "(NotImplementedError)")
    except Exception as e:
        got = f"!! {type(e).__name__}: {e}"
        if isinstance(want, Raises):
            ok = want.name in str(e)
            return report(label, ok, "" if ok else f"(got {got!r}, want {want!r})")
    ok = not isinstance(want, Raises) and got == want and type(got) is type(want)
    report(label, ok, "" if ok else f"(got {got!r}, want {want!r})")


print("--- stage 1, step A: evaluate (direct style) ---")
for label, expr, want in STAGE1:
    check(label, lambda: evaluate(expr, {"y": 7}), want)

print("\n--- stage 1, step B: eval_k (CPS) ---")
for label, expr, want in STAGE1_K:
    check(
        label,
        lambda: run_k(expr, {"y": 7}),
        want if isinstance(want, Raises) else [want],
    )
