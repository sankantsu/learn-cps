# Stage 2 tests: trampoline + proper tail calls. Run from the repo root: uv run pytest -k stage2
import sys
import tracemalloc

import pytest

from interp import run


def SUM(n):
    """Non-tail recursion: the pending `n + ...` must be remembered at every level."""
    return (
        "letrec",
        "sum",
        (
            "fn",
            ["n"],
            ("if", ("<", "n", 1), 0, ("+", "n", ("call", "sum", ("-", "n", 1)))),
        ),
        ("call", "sum", n),
    )


def LOOP(n):
    """Tail recursion: the recursive call is the last thing the function does."""
    return (
        "letrec",
        "loop",
        (
            "fn",
            ["n", "acc"],
            (
                "if",
                ("<", "n", 1),
                "acc",
                ("call", "loop", ("-", "n", 1), ("+", "acc", "n")),
            ),
        ),
        ("call", "loop", n, 0),
    )


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


STAGE2 = [
    # The inputs stage 1 had to leave out of its CPS tests.
    ("fact(10)", FACT(10), 3628800),
    ("fib(15)", FIB(15), 610),
    # Far deeper than Python's recursion limit (1000).
    ("non-tail recursion: sum(100_000)", SUM(100_000), 5000050000),
    ("tail recursion: loop(100_000)", LOOP(100_000), 5000050000),
]


@pytest.mark.parametrize("case", STAGE2, ids=lambda case: case[0])
def test_deep(case):
    _, expr, want = case
    assert run(expr) == want


def max_depth(thunk):
    """Run thunk() and return the deepest Python call stack seen (via a profiler)."""
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
        thunk()
    finally:
        sys.setprofile(None)
    return best


def test_python_stack_depth_constant():
    """The trampoline keeps Python's stack flat: depth must not grow with n.
    (Passing the deep tests alone isn't proof: a half-trampolined evaluator can
    get through some programs and still overflow on others.)"""
    depths = {n: max_depth(lambda n=n: run(SUM(n))) for n in (10, 100, 300)}
    assert len(set(depths.values())) == 1, f"max Python stack depth by n: {depths}"


def peak_memory(expr):
    tracemalloc.start()
    try:
        run(expr)
        return tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


def test_proper_tail_calls():
    """A tail call must not grow the continuation, so a tail-recursive loop
    runs in constant memory, however many times it goes round.
    (sum, which is NOT tail recursive, is shown for comparison: its continuation
    really has to grow, one pending `n + ...` per level.)"""
    small, big = peak_memory(LOOP(2_000)), peak_memory(LOOP(20_000))
    assert big < 2 * small + 20_000, (
        f"loop: peak memory {small} bytes for n=2_000 but {big} for n=20_000 "
        f"(sum, for comparison: {peak_memory(SUM(2_000))} -> {peak_memory(SUM(20_000))})"
    )


def test_function_value_survives_trampoline():
    """A program's value can be a function. The trampoline must hand it back
    rather than mistake it for a step to run, and it must still work when
    passed back in."""
    inc = run(("fn", ["x"], ("+", "x", 1)))
    assert run(("call", "inc", 41), {"inc": inc}) == 42
