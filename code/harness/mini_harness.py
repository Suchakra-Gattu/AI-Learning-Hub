"""A tiny agent harness, about 120 lines, to show the parts every harness has.

Run:  python mini_harness.py
No installs, no API key. The "model" here is a script that plays the part of a real model,
so you can watch the harness do its job. Swap in a real model by replacing ScriptedModel
(see lesson 7).

The five parts to look for:
  1. TOOLS        what the model is allowed to ask for
  2. POLICY       which requests run, which need a yes, which are refused
  3. THE LOOP     ask the model -> run the tool -> show the result -> repeat
  4. THE LOG      every event is written down, and the model's memory is rebuilt from it
  5. LIMITS       a step limit so it cannot run forever
"""
import json
import time
from pathlib import Path

WORKSPACE = Path(__file__).parent / "workspace"   # the only folder the agent may touch
LOG = Path(__file__).parent / "session.jsonl"


# ---------- 1. TOOLS ----------
def _safe_path(name):
    """Refuse any path that escapes the workspace (like ../../secrets)."""
    p = (WORKSPACE / name).resolve()
    if WORKSPACE.resolve() not in p.parents and p != WORKSPACE.resolve():
        raise PermissionError(f"path outside workspace: {name}")
    return p


def list_files(args):
    return "\n".join(sorted(p.name for p in WORKSPACE.iterdir()))


def read_file(args):
    return _safe_path(args["name"]).read_text(encoding="utf-8")


def write_file(args):
    _safe_path(args["name"]).write_text(args["content"], encoding="utf-8")
    return f"wrote {len(args['content'])} characters to {args['name']}"


TOOLS = {
    "list_files": {"fn": list_files, "needs_approval": False, "doc": "List files in the workspace."},
    "read_file": {"fn": read_file, "needs_approval": False, "doc": "Read a file. args: name"},
    "write_file": {"fn": write_file, "needs_approval": True, "doc": "Write a file. args: name, content"},
}


# ---------- 2. POLICY ----------
def ask_human(tool, args):
    """In a real harness this is a button in a UI. Here it is a prompt in the terminal."""
    answer = input(f"  APPROVE {tool}({json.dumps(args)[:80]})? [y/N] ").strip().lower()
    return answer == "y"


# ---------- 4. THE LOG ----------
def log_event(kind, **data):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"t": round(time.time(), 2), "kind": kind, **data}) + "\n")


def messages_from_log():
    """The model's memory is rebuilt from the log. If it is not in the log, the model never saw it."""
    msgs = []
    for line in LOG.read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        if e["kind"] in ("user", "assistant", "tool_result"):
            msgs.append(e)
    return msgs


# ---------- A stand-in for a real model ----------
class ScriptedModel:
    """Plays a fixed plan. A real model decides these steps itself."""

    def __init__(self):
        self.plan = [
            {"type": "tool_call", "tool": "list_files", "args": {}},
            {"type": "tool_call", "tool": "read_file", "args": {"name": "notes.txt"}},
            {"type": "tool_call", "tool": "read_file", "args": {"name": "../mini_harness.py"}},  # an escape attempt
            {"type": "tool_call", "tool": "write_file", "args": {"name": "summary.txt", "content": "Notes were read."}},
            {"type": "final", "text": "I read notes.txt and wrote a summary."},
        ]

    def next(self, messages, tools):
        return self.plan.pop(0)


# ---------- 3. THE LOOP ----------
def run(task, model, max_steps=8):
    WORKSPACE.mkdir(exist_ok=True)
    (WORKSPACE / "notes.txt").write_text("Meeting moved to Friday. Bring the Q3 numbers.", encoding="utf-8")
    LOG.write_text("", encoding="utf-8")
    log_event("user", text=task)
    print(f"TASK: {task}\n")

    for step in range(1, max_steps + 1):                       # 5. LIMITS
        action = model.next(messages_from_log(), TOOLS)
        if action["type"] == "final":
            log_event("assistant", text=action["text"])
            print(f"\nDONE after {step} steps: {action['text']}")
            return
        tool, args = action["tool"], action["args"]
        log_event("tool_call", tool=tool, args=args, step=step)
        print(f"step {step}: model asks for {tool}({json.dumps(args)})")

        spec = TOOLS.get(tool)
        if spec is None:
            result = f"ERROR: no such tool '{tool}'"
        elif spec["needs_approval"] and not ask_human(tool, args):
            result = "DENIED: the user did not approve this action"
        else:
            try:
                result = spec["fn"](args)
            except Exception as e:                              # errors go back to the model, not crash the loop
                result = f"ERROR: {e}"
        log_event("tool_result", tool=tool, text=result)
        print(f"        result: {result[:90]}")
    print("\nSTOPPED: step limit reached")
    log_event("stopped", reason="max_steps")


if __name__ == "__main__":
    run("Read my notes and save a one-line summary.", ScriptedModel())
    print(f"\nEvery event is saved in {LOG.name}. Open it and read it.")
