# A CPS interpreter for a tiny language

A project after lessons 01–07. We build an interpreter in stages. Each stage adds one feature.
The point: once the evaluator is in CPS, features like exceptions,
generators, `amb` and call/cc each take a few lines in the evaluator. Programs
written *in* the language never need to be rewritten in CPS by hand.

| Stage | Feature | Tests |
|-------|---------|-------|
| 1 | The core language: direct-style evaluator, then CPS evaluator | `test_stage1.py` |
| 2 | Trampoline: deep recursion in the language, proper tail calls | |
| 3 | `raise` / `try` | |
| 4 | Generators (`yield`) | |
| 5 | `amb` / `require` | |
| 6 | call/cc | |

## Files

- `interp.py`: the CPS evaluator. It grows with every stage. Tests only use its
  `run(expr, env)` function, so its internals can change freely.
- `direct.py`: the direct-style evaluator from stage 1, frozen, kept for comparison.
- `test_stage<N>.py`: the tests for each stage. All stages are re-run every time,
  so a new feature can't silently break an old one.

Run the tests from the repository root with `uv run pytest`, or with plain `pytest`
if you have it installed. Add `-k stage1` to run one stage.
Each finished stage is tagged in git (`stage1`, `stage2`, ...), so
`git diff stage1 stage2 -- py/interpreter/interp.py` shows what a feature cost.

## The language

There's no parser: a program is a Python value, an AST written as nested tuples.

| Syntax | Meaning |
|--------|---------|
| `5`, `True` | literal (int or bool) |
| `"x"` | variable reference |
| `("+", a, b)` | also `"-"`, `"*"`, `"<"`, `"=="`; both sides evaluated, left first |
| `("if", c, t, e)` | evaluate `c`, then evaluate *only* `t` or *only* `e` |
| `("let", "x", e, body)` | evaluate `e` (in the outer env), bind it to `x`, evaluate `body` |
| `("letrec", "f", fn_expr, body)` | like `let`, but `fn_expr` can refer to `f` itself (recursion) |
| `("fn", ["x", "y"], body)` | a function (closure) with parameters `x`, `y` |
| `("call", f, a1, a2, ...)` | evaluate `f`, then the arguments left to right; call it |

Example, factorial:

```python
("letrec", "fact", ("fn", ["n"],
                     ("if", ("<", "n", 1),
                            1,
                            ("*", "n", ("call", "fact", ("-", "n", 1))))),
 ("call", "fact", 5))                                     # => 120
```

An environment maps names to values. Extend it without mutating it, e.g. `{**env, name: value}`,
so an outer env never sees inner bindings. Functions use *lexical* scope: a
closure remembers the env where its `fn` was evaluated, not the env where it's called.

## Stage 1: the core language

- **Step A:** `evaluate(expr, env)` in direct style (`direct.py`). It's one big if/elif
  on the kind of expression. Write it in ANF (name every recursive result) so
  step B is mechanical.
- **Step B:** `eval_k(expr, env, k)` in CPS (`interp.py`): the same cases, converted with the
  recipe from lesson 03c. The interesting cases are `call` (evaluating a *list* of arguments in
  CPS) and applying a closure. `eval_k` must never fall back to the direct-style evaluator.

Without a trampoline, every step of the CPS evaluator is a nested Python call,
so even `fib(8)` overflows Python's stack. The stage 1 CPS tests therefore use small inputs, and stage 2 fixes this.
