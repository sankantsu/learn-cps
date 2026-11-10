# A CPS interpreter for a tiny language (project, after lessons 01–07)
# Your implementation goes here. Tests live in test_stage<N>.py next to it:
#   cd py/interpreter && python3 test_stage1.py
#
# We'll build an interpreter in stages. Each stage adds one feature, and the
# point of the lesson: once the evaluator is in CPS, features like exceptions,
# generators, amb and call/cc are each a few lines in the evaluator. The programs
# written IN the language never need to be rewritten in CPS by hand.
#
#   Stage 1  the core language: direct-style evaluator, then CPS evaluator   <- now
#   Stage 2  trampoline: deep recursion in the language, proper tail calls
#   Stage 3  raise / try
#   Stage 4  generators (yield)
#   Stage 5  amb / require
#   Stage 6  call/cc
#
# ======================= The language =======================
# No parser: a program is a Python value (an "AST" written as nested tuples).
#
#   5, True                       literal (int or bool)
#   "x"                           variable reference
#   ("+", a, b)                   also "-", "*", "<", "==" (both sides evaluated, left first)
#   ("if", c, t, e)               evaluate c; then evaluate ONLY t or ONLY e
#   ("let", "x", e, body)         evaluate e, bind it to x, evaluate body
#   ("fn", ["x", "y"], body)      a function (closure) with parameters x, y
#   ("call", f, a1, a2, ...)      evaluate f, then the args left to right; call it
#   ("letrec", "f", fn_expr, body)  like let, but fn_expr can refer to f itself
#                                   (for recursive functions)
#
# Example: factorial.
#   ("letrec", "fact", ("fn", ["n"],
#                        ("if", ("<", "n", 1),
#                               1,
#                               ("*", "n", ("call", "fact", ("-", "n", 1))))),
#    ("call", "fact", 5))                                     # => 120
#
# An environment maps names to values. A plain dict is fine; extend it with
# {**env, name: value} so an outer env never sees inner bindings.
# Functions must use LEXICAL scope: a closure remembers the env where its
# "fn" was evaluated, not the env where it is called.
#
# ======================= Stage 1 =======================
# Step A: evaluate(expr, env) in direct style. It's a big if/elif on the kind
#         of expr. Write it in ANF from the start (name every recursive result),
#         so step B is mechanical.
# Step B: eval_k(expr, env, k) in CPS. Same cases, the 03c recipe.
#         The interesting cases: "call" (evaluate a LIST of args in CPS:
#         you'll want a helper for that) and how a closure gets applied.
#
# Decide for yourself how to represent a closure (a small class, a tuple, ...).
# The tests only look at results that are ints/bools.
import operator
from dataclasses import dataclass

OPS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "<": operator.lt,
    "==": operator.eq,
}

KEYWORDS = {"if", "let", "letrec", "fn", "call"}


def check_varname(var_name: str) -> bool:
    return (
        isinstance(var_name, str) and var_name not in OPS and var_name not in KEYWORDS
    )


@dataclass
class Closure:
    params: list
    body: object
    env: dict


def evaluate(expr, env):
    assert isinstance(expr, (int, bool, str, tuple))
    assert isinstance(env, dict)
    # Integer
    if isinstance(expr, int) and not isinstance(expr, bool):
        return expr
    # Bool
    if isinstance(expr, bool):
        return expr
    # Variable
    if isinstance(expr, str):
        var_name = expr
        assert var_name not in OPS
        return env[var_name]
    # Compound
    if isinstance(expr, tuple):
        e0 = expr[0]
        assert isinstance(e0, str)
        # Operator
        if e0 in OPS:
            assert len(expr) == 3
            op_name = e0
            op = OPS[op_name]
            lhs = evaluate(expr[1], env)
            rhs = evaluate(expr[2], env)
            return op(lhs, rhs)
        assert e0 in KEYWORDS
        if e0 == "if":
            cond = evaluate(expr[1], env)
            if cond:
                return evaluate(expr[2], env)
            else:
                return evaluate(expr[3], env)
        if e0 == "let":
            var_name = expr[1]
            assert check_varname(var_name)
            e = evaluate(expr[2], env)
            new_env = env.copy()
            new_env[var_name] = e
            return evaluate(expr[3], new_env)
        if e0 == "letrec":
            fn_name = expr[1]
            assert check_varname(fn_name)
            new_env = env.copy()
            fn = evaluate(expr[2], new_env)
            assert isinstance(fn, Closure)
            new_env[fn_name] = fn
            return evaluate(expr[3], new_env)
        if e0 == "fn":
            params = expr[1]
            body = expr[2]
            return Closure(
                params,
                body,
                env,
            )
        if e0 == "call":
            fn = evaluate(expr[1], env)
            assert isinstance(fn, Closure)

            def eval_arg(e):
                return evaluate(e, env)

            args = tuple(map(eval_arg, expr[2:]))
            new_env = {**fn.env, **dict(zip(fn.params, args))}
            return evaluate(fn.body, new_env)

    assert False


def eval_list_k(lst, env, k, elst=()):
    if not lst:
        return k(elst)
    x, *rest = lst

    def eval_rest_k(x):
        return eval_list_k(rest, env, k, elst + (x,))

    return eval_k(x, env, eval_rest_k)


def eval_k(expr, env, k):
    assert isinstance(expr, (int, bool, str, tuple))
    assert isinstance(env, dict)
    assert callable(k)
    # Integer
    if isinstance(expr, int) and not isinstance(expr, bool):
        return k(expr)
    # Bool
    if isinstance(expr, bool):
        return k(expr)
    # Variable
    if isinstance(expr, str):
        var_name = expr
        assert var_name not in OPS
        return k(env[var_name])
    # Compound
    if isinstance(expr, tuple):
        e0 = expr[0]
        assert isinstance(e0, str)
        # Operator
        if e0 in OPS:
            assert len(expr) == 3
            op_name = e0
            op = OPS[op_name]
            return eval_k(
                expr[1],
                env,
                lambda lhs: eval_k(expr[2], env, lambda rhs: k(op(lhs, rhs))),
            )

        assert e0 in KEYWORDS
        if e0 == "if":

            def cond_k(cond):
                if cond:
                    return eval_k(expr[2], env, k)
                else:
                    return eval_k(expr[3], env, k)

            return eval_k(expr[1], env, cond_k)
        if e0 == "let":
            var_name = expr[1]
            assert check_varname(var_name)

            def resume(e):
                new_env = env.copy()
                new_env[var_name] = e
                return eval_k(expr[3], new_env, k)

            return eval_k(expr[2], env, resume)
        if e0 == "letrec":
            fn_name = expr[1]
            assert check_varname(fn_name)
            new_env = env.copy()

            def resume(fn):
                assert isinstance(fn, Closure)
                new_env[fn_name] = fn
                return eval_k(expr[3], new_env, k)

            return eval_k(expr[2], new_env, resume)
        if e0 == "fn":
            params = expr[1]
            body = expr[2]
            return k(
                Closure(
                    params,
                    body,
                    env,
                )
            )
        if e0 == "call":
            # expr[1]: fn
            # expr[2:]: args

            def resume(fn):
                assert isinstance(fn, Closure)
                return eval_list_k(
                    expr[2:],
                    env,
                    lambda args: eval_k(
                        fn.body, {**fn.env, **dict(zip(fn.params, args))}, k
                    ),
                )

            return eval_k(expr[1], env, resume)
    assert False
