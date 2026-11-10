// 01 — Direct style vs. CPS
// Run: node 01-basics.js
//
// Direct style: a function RETURNS its result to whoever called it.
// CPS:          a function never returns. It receives an extra argument `k`
//               (the "continuation" = "what to do next with my result")
//               and CALLS k with the result.

// ---------- direct style ----------
function add(a, b) { return a + b; }
function square(x) { return x * x; }
function pyth(a, b) { return add(square(a), square(b)); }

console.log("direct:", pyth(3, 4));

// ---------- CPS ----------
function addK(a, b, k) { k(a + b); }
function squareK(x, k) { k(x * x); }

function pythK(a, b, k) {
  squareK(a, (a2) =>          // "square a, then call the result a2, and..."
    squareK(b, (b2) =>        // "square b, then call the result b2, and..."
      addK(a2, b2, k)));      // "add them, and hand the sum to MY continuation"
}

pythK(3, 4, (result) => console.log("cps:   ", result));

// Things to notice:
//  1. Every intermediate value got a NAME (a2, b2). Nothing is implicit.
//  2. The ORDER of evaluation is spelled out: square a, then b, then add.
//     In `add(square(a), square(b))` the language decides; here, you do.
//  3. No function returns anything useful. "Returning" has been replaced by
//     "calling the next thing". The rest of the program is just a function.

// ---------- make the continuation visible ----------
function squareTraced(x, k) {
  console.log(`  squareTraced(${x}) will continue with:  ${k.toString().replace(/\s+/g, " ")}`);
  k(x * x);
}
console.log("\ntracing:");
squareTraced(3, (a2) => squareTraced(4, (b2) => console.log("  sum =", a2 + b2)));

// EXERCISE: write `mulK(a, b, k)` and use it to compute (2 + 3) * (4 + 5)
// entirely in CPS. Then try evaluating the right side first — only the
// nesting changes.
