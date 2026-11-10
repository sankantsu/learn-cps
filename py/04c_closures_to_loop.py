# 04c — From closures to a loop: the trampolined total_t, three ways
# Run: python3 04c_closures_to_loop.py
#
# The same computation as total_t in lesson 04, rewritten step by step:
#   v1: every lambda becomes a small class (so each step can print itself)
#   v2: the continuation becomes a Python list of frames (an explicit stack)
#   v3: the frames only hold a number, so the classes go away: a plain loop
# Turning lambdas into data like this is called defunctionalization.


# --- v1: one class per lambda in total_t
class Apply:
    def __init__(self, k, v):
        self._k = k
        self._v = v

    def __call__(self):
        print(f"{self}()")
        return self._k(self._v)

    def __str__(self):
        return f"Apply<{self._k}, {self._v}>"


class Total:
    def __init__(self, n, k):
        self._n = n
        self._k = k

    def __call__(self):
        print(f"{self}()")
        if self._n == 0:
            return Apply(self._k, 0)
        else:
            return Total(self._n - 1, AfterTotal(self._n, self._k))

    def __str__(self):
        return f"Total<{self._n}, {self._k}>"


class AfterTotal:
    def __init__(self, n, k):
        self._n = n
        self._k = k

    def __call__(self, r):
        print(f"{self}({r})")
        return Apply(self._k, r + self._n)

    def __str__(self):
        return f"AfterTotal<{self._n}, {self._k}>"


class Id:
    def __call__(self, r):
        return r

    def __str__(self):
        return "Id"


def trampoline_trace(step):
    i = 0
    while callable(step):
        print("-" * 40)
        print(f"step {i}: {step}")
        step = step()
        i += 1
    print("-" * 40)
    print(f"step {i}: {step}")
    return step


N = 5
print("cps+trampoline:", trampoline_trace(Total(N, Id())))


# --- Tracing v2: continuation = a Python list of frames (top = last element)
#
# Compared with v1, only three things change:
#   - AfterTotal no longer stores `k`: "the next continuation" is now just
#     the frame BELOW it in the list.
#   - wrapping   AfterTotal(n, k)   becomes   stack.append(AfterTotal(n))   (push)
#   - calling    k(v)               becomes   stack.pop()(v, stack)         (pop)

class Apply:                      # v1: lambda: k(v)
    def __init__(self, stack, v):
        self._stack = stack
        self._v = v

    def __call__(self):
        frame = self._stack.pop()           # the innermost continuation...
        return frame(self._v, self._stack)  # ...gets the value (and the rest of the stack)

    def __str__(self):
        return f"Apply<{self._v}>"


class Total:                      # v1: lambda: total_t(n, k)
    def __init__(self, n, stack):
        self._n = n
        self._stack = stack

    def __call__(self):
        if self._n == 0:
            return Apply(self._stack, 0)
        self._stack.append(AfterTotal(self._n))   # push instead of wrapping k
        return Total(self._n - 1, self._stack)

    def __str__(self):
        return f"Total<{self._n}>"


class AfterTotal:                 # v1: lambda r: lambda: k(n + r)  -- but no k!
    def __init__(self, n):
        self._n = n

    def __call__(self, r, stack):
        print(f"    AfterTotal<{self._n}>({r})")
        return Apply(stack, r + self._n)

    def __str__(self):
        return f"AfterTotal<{self._n}>"


class Id:                         # v1: lambda r: r
    def __call__(self, r, stack):
        return r

    def __str__(self):
        return "Id"


def trampoline_trace_v2(step, stack):
    i = 0
    while callable(step):
        print("-" * 40)
        print(f"step {i}: {str(step):<12} stack: [{', '.join(map(str, stack))}]")
        step = step()
        i += 1
    print("-" * 40)
    print(f"step {i}: {step}")
    return step


N = 5
stack = [Id()]
print("cps+trampoline (list stack):", trampoline_trace_v2(Total(N, stack), stack))


# --- v3: the frames only hold a number, so drop the classes entirely.
#
# Every AfterTotal frame is just "n, waiting to be added". So the stack can be
# a list of ints, and the two thunk kinds become two phases of a plain loop:
#   Total  (compute) phase: push n, go to n - 1         -> going DOWN
#   Apply  (deliver) phase: pop a frame, add it to v    -> coming back UP
# Id at the bottom == "stack is empty, v is the answer".

def total_loop(n):
    stack = []
    while n > 0:              # Total: push a frame, recurse on n - 1
        stack.append(n)
        n -= 1
    v = 0                     # Total<0>: base case -> Apply(stack, 0)
    while stack:              # Apply: pop frame, run AfterTotal (v + n)
        v = v + stack.pop()
    return v                  # stack empty == reached Id

print("explicit stack loop:", total_loop(N), " and for 100_000:", total_loop(100_000))
