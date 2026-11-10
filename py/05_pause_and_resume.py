# 05 — A continuation is a value: store it, call it later = pause/resume
# Run: python3 05_pause_and_resume.py
#
# If "the rest of my program" is a function, I can put it in a queue
# instead of calling it. That's a paused thread.
from collections import deque

ready = deque()

def pause(k):            # "yield": don't continue now; park my continuation
    ready.append(k)

def run():
    while ready:
        ready.popleft()()

# A "thread" written in CPS: count to n, pausing between steps.
def counter(name, n, i=1, k=None):
    k = k or (lambda: print(f"{name} done"))
    if i > n:
        return k()
    print(f"{name}: {i}")
    pause(lambda: counter(name, n, i + 1, k))

print("--- CPS threads ---")
counter("A", 3)
counter("B", 5)
run()

# ---------- the same thing with Python generators ----------
# A generator is a function whose continuation Python saves for you at
# every `yield`. Calling next(g) = "resume the saved continuation".
def counter_gen(name, n):
    for i in range(1, n + 1):
        print(f"{name}: {i}")
        yield                    # <- Python captures "the rest of this function" here
    print(f"{name} done")

print("\n--- generator threads ---")
threads = deque([counter_gen("A", 3), counter_gen("B", 5)])
while threads:
    g = threads.popleft()
    try:
        next(g)                  # resume it
        threads.append(g)        # it paused again: back of the queue
    except StopIteration:
        pass                     # it finished

# Same output. asyncio is exactly this: an event loop holding parked
# continuations (coroutines), resuming each when its I/O is ready.

# EXERCISE: add a `sleep(ticks, k)` and make B sleep 2 ticks per step
# (instead of a plain pause). A "tick" = one trip through the ready queue,
# i.e. the other tasks get that many extra turns before k runs.
#   Part 1: write sleep using only `pause` (no scheduler changes needed).
#           B should then advance about once per three steps of A.
#   Part 2 (optional): real event loops don't busy-wait. Change the scheduler
#           so sleepers wait OUTSIDE the ready queue with a wake-up time,
#           and run() keeps going while anything is ready OR sleeping.


def sleep(ticks, k):
    assert ticks >= 0
    if ticks == 0:
        return pause(k)
    pause(lambda: sleep(ticks - 1, k))


def counter_with_sleep(name, n, sleep_ticks=0, i=1, k=None):
    k = k or (lambda: print(f"{name} done"))
    if i > n:
        return k()
    print(f"{name}: {i}")
    sleep(sleep_ticks, lambda: counter_with_sleep(name, n, sleep_ticks, i + 1, k))


print("--- CPS threads (with sleep) ---")
counter_with_sleep("A", 9)
counter_with_sleep("B", 5, sleep_ticks=3)
run()

# ---------------------------------------------------------------------------
# Tests for the exercise. They use your `pause`, `sleep` and `run`, with their
# own tiny tasks that write to a log instead of printing.
# Set PART2 = True once you've done part 2 (with part 1's busy-waiting sleep,
# the PART2 test takes several seconds and fails, which is expected).
import time

PART2 = False

def task(name, n, wait, log, i=1):
    """Like counter(), but logs "A1", "A2", ... "A done" and waits with `wait`."""
    if i > n:
        log.append(f"{name} done")
        return
    log.append(f"{name}{i}")
    wait(lambda: task(name, n, wait, log, i + 1))

def sleeper(ticks):
    return lambda k: sleep(ticks, k)

def report(label, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {label:44} {detail}")

def scenario(*tasks):
    log = []
    try:
        for name, n, wait in tasks:
            task(name, n, wait, log)
        run()
    except Exception as e:
        log.append(f"!! {type(e).__name__}: {e}")
    return log

print("\n--- exercise tests ---")

# 1. sleep(0, k) is the same as pause(k).
log = scenario(("A", 3, pause), ("B", 3, sleeper(0)))
report("sleep(0) behaves like pause",
       log == ["A1", "B1", "A2", "B2", "A3", "B3", "A done", "B done"], f"{log}")

# 2. A task that is the ONLY one, and sleeps, must still finish
#    (the scheduler must not exit while something is asleep).
log = scenario(("B", 3, sleeper(2)))
report("lone sleeper still finishes", log == ["B1", "B2", "B3", "B done"], f"{log}")

# 3. Every task finishes, each step exactly once, in order.
log = scenario(("A", 9, pause), ("B", 3, sleeper(2)))
want_a = [f"A{i}" for i in range(1, 10)] + ["A done"]
want_b = [f"B{i}" for i in range(1, 4)] + ["B done"]
report("all steps run once, in order",
       [e for e in log if e.startswith("A")] == want_a and
       [e for e in log if e.startswith("B")] == want_b, f"{log}")

# 4. While B sleeps, A keeps making progress: at least one A step between B steps.
if all(f"B{i}" in log for i in (1, 2, 3)):
    b_pos = [log.index(f"B{i}") for i in (1, 2, 3)]
    gaps = [sum(1 for e in log[p + 1:q] if e.startswith("A")) for p, q in zip(b_pos, b_pos[1:])]
    report("A runs while B sleeps", all(g >= 1 for g in gaps), f"(A steps between B steps: {gaps})")
else:
    report("A runs while B sleeps", False, "(B didn't reach B3)")

# 5. Part 1 exact schedule: a tick = one trip through the ready queue,
#    so with A and B both running, sleep(2) lets A take 3 steps per B step.
#    (Skipped for part 2: with a real clock, the exact schedule depends on how
#    you define a tick, so only the general checks above apply.)
if not PART2:
    want = ["A1", "B1", "A2", "A3", "A4", "B2", "A5", "A6", "A7", "B3", "A8", "A9",
            "A done", "B done"]
    report("part 1: exactly 3 A steps per B step", log == want, "" if log == want else f"{log}")

# 6. Part 2: a long sleep must not cost one scheduler turn per tick.
if PART2:
    t0 = time.perf_counter()
    log = scenario(("B", 2, sleeper(5_000_000)))
    dt = time.perf_counter() - t0
    report("part 2: sleep(5_000_000) is instant (no busy wait)",
           log == ["B1", "B2", "B done"] and dt < 0.1, f"({dt:.3f}s, {log})")
