# CPS, hands-on

Learning continuation-passing style by writing code, not by reading theory.
Each lesson is a single runnable file that explains one idea and ends with
exercises, most of them with tests (every line should say `PASS`).

The exercises are already solved in place: these are my solutions. To do them
yourself, replace a solution with `raise NotImplementedError` and make the tests pass again.

## Python (`py/`): run with `cd py && python3 <file>`

| File | Idea |
|------|------|
| `01_basics.py` | A function takes an extra argument `k` and calls it instead of returning |
| `02_you_already_use_it.py` | Callbacks → futures → async/await are all CPS |
| `03_control_flow.py` | Two continuations = exceptions; skipping one = early exit |
| `03b_extra_exercise.py`, `03c_recipe_drills.py` | Practice: converting direct style to CPS, step by step |
| `04_the_stack_is_a_continuation.py` | Trampolines; the continuation chain is the call stack |
| `04b_trace_trampoline.py` | Watch a trampoline run, one step at a time |
| `04c_closures_to_loop.py` | Continuations → classes → an explicit stack → a plain loop |
| `05_pause_and_resume.py` | Store a continuation to pause and resume later = coroutines, generators |
| `06_backtracking.py` | Call a continuation many times = backtracking search (n-queens) |
| `07_callcc.py` | call/cc: escape continuations and re-entering a saved continuation |
| `ex_recap.py`, `ex_final.py` | Optional recap exercises covering all of the above |
| `interpreter/` | Project: a CPS interpreter for a tiny language, built in stages (`python3 test_stage1.py`) |

## JavaScript (`js/`): run with `node js/<file>`

Lessons 01–06 in JavaScript (`01-basics.js` … `06-backtracking.js`), same ideas as above.
