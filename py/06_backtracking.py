# 06 — Call a continuation MORE THAN ONCE = backtracking search
# Run: python3 06_backtracking.py
#
# A normal function returns once. A continuation is just a function,
# so nothing stops you calling it several times — "continue the rest of
# the program with THIS value... now with THAT value..."

def choose(options, k):          # run the rest of the program once per option
    for x in options:
        k(x)

# Find all Pythagorean triples a <= b <= c <= 20.
# Read it top to bottom like straight-line code that "picks" values.
def with_a(a):
    def with_b(b):
        def with_c(c):
            if a * a + b * b == c * c:
                print((a, b, c))
        choose(range(b, 21), with_c)
    choose(range(a, 21), with_b)

print("--- nested defs ---")
choose(range(1, 21), with_a)

# ---------- the same search, flat: choose + require ----------
# Python lambdas can't contain an `if`, which is why the version above needs
# nested defs. One helper fixes that — and it's a real CPS idea, not a hack:
#
#   require(cond, k): continue with k only if cond holds.
#   If it doesn't hold, k is simply NEVER CALLED — this branch dies, control
#   falls back to the nearest `choose` loop, and it tries the next value.
#   "Not calling the continuation" = backtracking (like `exit` skipping
#   work in lesson 03).

def require(cond, k):
    if cond:
        k()

print("--- choose + require ---")
choose(range(1, 21), lambda a:
    choose(range(a, 21), lambda b:
        choose(range(b, 21), lambda c:
            require(a * a + b * b == c * c, lambda: print((a, b, c))))))

# Read it as straight-line code:
#   pick a, pick b, pick c, require a² + b² = c², print.
# Logic languages call this pair `amb` (choose) and `require`/`guard`.

# Each `choose` is a fork in the road. When a branch finishes, control
# falls back to the loop in the enclosing `choose`, which tries the next
# value — backtracking, for free. Prolog, parser combinators, and
# constraint solvers are built on this.
# (Python's nested generator comprehensions are this same idea, sugared.)

# EXERCISE: solve 4-queens (or SEND + MORE = MONEY) using `choose` and `require`.
# Add an `exit` continuation (from 03) so you can stop at the first solution.
#
# Write these two functions ABOVE the tests (the tests cover n-queens only):
#
#   queens_k(n, k)
#       Call k(solution) once for EVERY solution, in any order.
#       solution = tuple of length n, solution[row] = column of that row's queen.
#       e.g. for n=4: k((1, 3, 0, 2)) and k((2, 0, 3, 1))
#
#   first_queens_k(n, found, not_found)
#       Call found(solution) exactly once with the first solution you find,
#       or not_found() exactly once if there is none, and STOP searching
#       as soon as one is found.
#
# Tip: `require` the queen is safe right after choosing each row's column,
# not only at the end — otherwise n=8 tries 8^8 = 16 million boards.


def is_answer(sol : tuple[int]) -> bool:
    assert isinstance(sol, tuple)
    n = len(sol)
    for i in range(n):
        for j in range(i + 1, n):
            if sol[i] == sol[j]:
                return False
            if abs(sol[i] - sol[j]) == abs(i - j):
                return False
    return True


def queens_k(n, k):
    def place(placed):
        if len(placed) == n:
            return require(is_answer(placed), lambda: k(placed))
        require(is_answer(placed),
            lambda: choose(range(n), lambda c: place(placed + (c,))))
    place(())


def choose_k(options, k, found, not_found):
    if not options:
        return not_found()
    x, *rest = options

    def choose_rest():
        return lambda: choose_k(rest, k, found, not_found)
    return lambda: k(x, found, choose_rest)


def cond_k(cond, ok, fail):
    if cond:
        return ok()
    else:
        return fail()


def first_queens_k(n, found, not_found):
    def place(placed, found, not_found):
        if len(placed) == n:
            return cond_k(
                is_answer(placed),
                lambda: found(placed),
                not_found
            )
        return cond_k(
            is_answer(placed),
            lambda: choose_k(
                range(n),
                lambda c, found, not_found: place(placed + (c,), found, not_found),
                found,
                not_found,
            ),
            not_found,
        )
    step = place((), found, not_found)
    while callable(step):
        step = step()
    return step


print("--- first_queen_k ---")
found = lambda sol: print(sol)
not_found = lambda : print("Not found")
first_queens_k(4, found, not_found)


# ---------------------------------------------------------------------------
# Tests for the exercise — every line should say PASS.
import sys
# sys.setrecursionlimit(1_000_000)

def report(label, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {label:44} {detail}")

def is_solution(sol, n):
    return (isinstance(sol, tuple) and len(sol) == n and
            all(0 <= c < n for c in sol) and
            all(sol[i] != sol[j] and abs(sol[i] - sol[j]) != j - i
                for i in range(n) for j in range(i + 1, n)))

def attempt(thunk):
    try:
        return thunk()
    except Exception as e:
        return f"!! {type(e).__name__}: {e}"

def all_solutions(n):
    sols = []
    queens_k(n, sols.append)
    return sols

def first_solution(n):
    calls = []
    first_queens_k(n, lambda s: calls.append(("found", s)), lambda: calls.append(("not_found",)))
    return calls

def count_calls(thunk):
    """How many Python function calls thunk() makes (a measure of search work)."""
    calls = 0
    def prof(frame, event, arg):
        nonlocal calls
        if event == "call":
            calls += 1
    sys.setprofile(prof)
    try:
        thunk()
    finally:
        sys.setprofile(None)
    return calls

print("\n--- exercise tests ---")

# 1-3. queens_k finds exactly the known solutions.
got = attempt(lambda: sorted(all_solutions(4)))
report("queens_k(4): both solutions", got == [(1, 3, 0, 2), (2, 0, 3, 1)], f"{got}")

KNOWN = {1: 1, 2: 0, 3: 0, 4: 2, 5: 10, 6: 4, 8: 92}
got = {n: attempt(lambda n=n: all_solutions(n)) for n in KNOWN}
counts = {n: len(s) if isinstance(s, list) else s for n, s in got.items()}
report("queens_k(n): solution counts", counts == KNOWN, f"{counts}")

valid = all(isinstance(s, list) and all(is_solution(x, n) for x in s) and len(set(s)) == len(s)
            for n, s in got.items())
report("queens_k(n): all valid, no duplicates", valid)

# 4-5. first_queens_k calls exactly one of its continuations, exactly once.
got = attempt(lambda: first_solution(8))
report("first_queens_k(8): found once, valid",
       isinstance(got, list) and len(got) == 1 and got[0][0] == "found" and is_solution(got[0][1], 8),
       f"{got}")

got = {n: attempt(lambda n=n: first_solution(n)) for n in (2, 3)}
report("first_queens_k(2), (3): not_found once",
       all(g == [("not_found",)] for g in got.values()), f"{got}")

# 6. ...and it really STOPS: far less work than searching everything.
full = count_calls(lambda: attempt(lambda: all_solutions(8)))
first = count_calls(lambda: attempt(lambda: first_solution(8)))
first_ok = attempt(lambda: first_solution(8))
first_ok = isinstance(first_ok, list) and len(first_ok) == 1 and first_ok[0][0] == "found"
report("first_queens_k(8) stops early", first_ok and first * 5 < full,
       f"(function calls: first={first}, full search={full})")
