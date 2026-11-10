# Shared helpers for the test_stage<N>.py files.


def report(label, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {label:44} {detail}")


def attempt(thunk):
    try:
        return thunk()
    except Exception as e:
        return f"!! {type(e).__name__}: {e}"
