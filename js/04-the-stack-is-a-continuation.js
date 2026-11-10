// 04 — The call stack is just a continuation. Move it to the heap.
// Run: node 04-the-stack-is-a-continuation.js

const N = 1_000_000;

// ---------- direct recursion: the stack remembers "what's left to do" ----------
function sum(n) { return n === 0 ? 0 : n + sum(n - 1); }
try { console.log("direct:", sum(N)); }
catch (e) { console.log("direct:", e.constructor.name, "-", e.message); }

// Each pending `n + ___` sits in a stack frame. A million of them don't fit.

// ---------- CPS: "what's left to do" becomes a chain of closures ----------
// Plain CPS still nests JS calls (k calls k calls k...), so we use a
// TRAMPOLINE: instead of calling the next step, RETURN it as a thunk,
// and let a flat loop call it. Now the stack never grows.

function sumK(n, k) {
  if (n === 0) return () => k(0);
  return () => sumK(n - 1, (r) => () => k(n + r));
}

function trampoline(step) {
  while (typeof step === "function") step = step();
  return step;
}

console.log("cps:   ", trampoline(sumK(N, (r) => r)));

// What moved where:
//   direct: pending "n + ___"  lives in   stack frames   (small, fixed size)
//   CPS:    pending "n + ___"  lives in   closures k     (heap, as big as RAM)
// The continuation is literally a reified call stack.
//
// This is how many interpreters/compilers (Scheme, SML/NJ, some JS-to-X
// compilers, Kotlin coroutines) get deep recursion, tail calls, and
// suspendable functions: transform to CPS, then run on a loop.

// EXERCISE: convert fib(n) = fib(n-1) + fib(n-2) to CPS + trampoline.
// It has TWO recursive calls — the first continuation must start the second.
