# Stage 1, step A: the direct-style evaluator. Frozen: later stages only
# change the CPS evaluator in interp.py. Kept self-contained (its own copy of
# OPS, Closure, ...) so changes in interp.py can't break it.
# See README.md for the language.
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
