// 03 — Continuations ARE control flow: build your own `throw` and early `return`
// Run: node 03-control-flow.js
//
// If "what happens next" is just a function, you can pass MORE THAN ONE.
// Pick which one to call, and you've invented branching / exceptions.

// ---------- exceptions without try/catch ----------
function divK(a, b, ok, fail) {
  if (b === 0) fail(`cannot divide ${a} by zero`);
  else ok(a / b);
}

// (x / y) / z
function calcK(x, y, z, ok, fail) {
  divK(x, y, (r) => divK(r, z, ok, fail), fail);
}

const ok   = (v) => console.log("ok:  ", v);
const fail = (e) => console.log("fail:", e);
calcK(100, 5, 2, ok, fail);   // ok: 10
calcK(100, 0, 2, ok, fail);   // fail: ... (second division never runs)

// `fail` is exactly what a `catch` block is: a continuation you jump to,
// skipping everything the normal continuation would have done.
// Promises have the same two: .then(ok, fail).

// ---------- early exit that skips pending work ----------
// Multiply a list. If we meet a 0, the answer is 0 — so skip ALL the
// multiplications that are still waiting on the stack.

let mults = 0;
function productDirect(list) {
  if (list.length === 0) return 1;
  const [x, ...rest] = list;
  const r = productDirect(rest);       // even after finding 0 deep inside,
  mults++; return x * r;               // every frame still multiplies on the way out
}

function productK(list, k, exit) {
  if (list.length === 0) return k(1);
  const [x, ...rest] = list;
  if (x === 0) return exit(0);         // jump straight to the OUTERMOST continuation
  productK(rest, (r) => { mults++; k(x * r); }, exit);
}

const nums = [1, 2, 3, 4, 0, 5, 6, 7];

mults = 0; const d = productDirect(nums);
console.log(`\ndirect: ${d} after ${mults} multiplications`);

mults = 0;
const done = (v) => console.log(`cps:    ${v} after ${mults} multiplications`);
productK(nums, done, done);            // normal continuation and exit are the same final `done`

// What happened: the chain of pending `(r) => k(x * r)` closures IS the
// "stack of work left to do". By calling `exit` we simply never call them.
// That's what `throw`, `return` from a nested loop, and `break` do.

// EXERCISE: write findK(tree, pred, found, notFound) that searches a nested
// array like [1, [2, [3, 4]], 5] and calls `found` the instant it sees a
// match, without unwinding through the recursion.
