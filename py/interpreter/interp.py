# The CPS evaluator. It grows with every stage; see README.md.
# Tests only call run(expr, env), so everything else here can change freely.
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


def eval_list_k(lst, env, k, elst=()):
    if not lst:
        return lambda: k(elst)
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
        return lambda: k(expr)
    # Bool
    if isinstance(expr, bool):
        return lambda: k(expr)
    # Variable
    if isinstance(expr, str):
        var_name = expr
        assert var_name not in OPS
        return lambda: k(env[var_name])
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
                lambda lhs: eval_k(expr[2], env, lambda rhs: lambda: k(op(lhs, rhs))),
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
            return lambda: k(
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


def run(expr, env=None):
    """Evaluate a program and return its value. The stable entry point for tests."""
    step = eval_k(expr, dict(env or {}), lambda v: v)
    while callable(step):
        step = step()
    return step
