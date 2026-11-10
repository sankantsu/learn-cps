# Stage 1 tests: the core language. Run from the repo root: uv run pytest -k stage1
import re
from dataclasses import dataclass

import pytest

import direct
import interp


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


@dataclass
class Raises:
    """Expected result: evaluating must raise an exception whose message mentions
    `name` (e.g. KeyError('secret') or NameError('unbound variable: secret')).
    Any Python exception type is fine for now; stage 3 adds the language's own errors."""

    name: str


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


ENV = {"y": 7}


def check(evaluate, expr, want):
    if isinstance(want, Raises):
        with pytest.raises(Exception, match=re.escape(want.name)):
            evaluate(expr, dict(ENV))
    else:
        got = evaluate(expr, dict(ENV))
        assert got == want and type(got) is type(want)


def label(case):
    return case[0]


@pytest.mark.parametrize("case", STAGE1, ids=label)
def test_direct(case):
    _, expr, want = case
    check(direct.evaluate, expr, want)


@pytest.mark.parametrize("case", STAGE1_K, ids=label)
def test_cps(case):
    _, expr, want = case
    check(interp.run, expr, want)


def test_cps_does_not_use_direct():
    """A CPS evaluator must not hand any part of the program (e.g. a function
    body) to the direct-style one."""
    assert not hasattr(interp, "evaluate")
    borrowed = [
        name
        for name, v in vars(interp).items()
        if v is direct or getattr(v, "__module__", None) == "direct"
    ]
    assert borrowed == [], f"interp.py uses direct.py: {borrowed}"
