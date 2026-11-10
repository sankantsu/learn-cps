// 05 — A continuation is a value: store it, call it later = pause/resume
// Run: node 05-pause-and-resume.js
//
// The big payoff. If "the rest of my program" is a function, I can
// put it in a queue instead of calling it. That's a paused thread.
// Here's a cooperative multitasking scheduler in ~15 lines.

const readyQueue = [];

// "yield" = don't continue now; park my continuation and let others run
function pause(k) { readyQueue.push(k); }

function run() {
  while (readyQueue.length) readyQueue.shift()();
}

// A "thread" written in CPS: count to n, pausing between steps.
function counter(name, n, i = 1, k = () => console.log(`${name} done`)) {
  if (i > n) return k();
  console.log(`${name}: ${i}`);
  pause(() => counter(name, n, i + 1, k));
}

counter("A", 3);
counter("B", 5);
run();

// Output interleaves A and B: two "threads" on one stack, no OS threads.
// This is the same idea behind:
//   - JS generators / async functions (engine saves the continuation at each yield/await)
//   - Python asyncio, Kotlin coroutines, Go-style green threads
//   - the browser event loop: every callback you schedule is a parked continuation

// EXERCISE: add `sleep(ms, k)` that parks k with setTimeout instead of the
// queue, and make thread B sleep 50ms between steps. Watch A finish first.
