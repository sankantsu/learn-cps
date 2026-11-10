// 06 — Call a continuation MORE THAN ONCE = backtracking search
// Run: node 06-backtracking.js
//
// A normal function returns once. A continuation is just a function,
// so nothing stops you calling it several times — "continue the rest of
// the program with THIS value... now with THAT value..."

// choose(options, k): run the rest of the program once per option
function choose(options, k) { for (const x of options) k(x); }

const range = (a, b) => Array.from({ length: b - a + 1 }, (_, i) => a + i);

// Find all Pythagorean triples a <= b <= c <= 20.
// Read it top to bottom like straight-line code that "picks" values.
choose(range(1, 20), (a) =>
  choose(range(a, 20), (b) =>
    choose(range(b, 20), (c) => {
      if (a * a + b * b === c * c) console.log([a, b, c]);
    })));

// Each `choose` is a fork in the road. When a branch finishes, control
// falls back to the loop in the enclosing `choose`, which tries the next
// value — that's backtracking, for free. Prolog, parser combinators,
// and logic/constraint solvers are built on this.

// EXERCISE: solve SEND + MORE = MONEY, or 4-queens, using `choose`.
// Add a `fail` continuation (from 03) so you can stop at the first solution.
