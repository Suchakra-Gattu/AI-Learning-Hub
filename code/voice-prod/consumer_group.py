"""Events that don't get lost or done twice: a stream with consumer groups.

Run:  python consumer_group.py

Mirrors how Redis Streams work: messages get ids, a group tracks what each
consumer has read, and a message stays "pending" until it is acked. We break it
on purpose, then add the three fixes: reclaim, dead-letter, idempotency.
"""
import itertools

MAX_LEN, MAX_TRIES = 1000, 3


class Stream:
    def __init__(self):
        self.entries, self.ids = [], itertools.count(1)

    def add(self, event):
        self.entries.append((next(self.ids), event))
        del self.entries[:-MAX_LEN]                  # like XADD ... MAXLEN ~ 1000


class Group:
    def __init__(self, stream, start="$"):
        self.stream = stream
        # "$" = only new messages. "0" = replay everything still in the stream.
        self.last = 0 if start == "0" else (stream.entries[-1][0] if stream.entries else 0)
        self.pending = {}                            # id -> (event, tries)
        self.dead = []

    def read(self):
        new = [(i, e) for i, e in self.stream.entries if i > self.last]
        if new:
            self.last = new[-1][0]
        for i, e in new:
            self.pending[i] = (e, 0)
        return new

    def ack(self, i):
        self.pending.pop(i, None)

    def reclaim(self):                                # like XAUTOCLAIM for idle messages
        out = []
        for i, (e, tries) in list(self.pending.items()):
            if tries + 1 >= MAX_TRIES:
                self.dead.append((i, e))              # dead-letter: stop retrying, keep for a human
                del self.pending[i]
            else:
                self.pending[i] = (e, tries + 1)
                out.append((i, e))
        return out


done = set()                                          # shortcut: real code keeps this in the database


def handle(event):
    if event["id"] in done:                           # idempotency key: safe to see twice
        return "skipped (already done)"
    if event.get("bad"):
        raise ValueError("bad payload")
    done.add(event["id"])
    return "sent customer webhook"


def process(group, batch):
    for i, e in batch:
        try:
            print(f"  msg {i} {e['type']:12} -> {handle(e)}")
            group.ack(i)
        except ValueError as err:
            print(f"  msg {i} {e['type']:12} -> FAILED: {err} (stays pending)")


if __name__ == "__main__":
    s = Stream()
    for n, t in enumerate(["call.started", "call.ended", "call.ended"]):
        s.add({"id": f"evt-{n}", "type": t, "bad": n == 2})
    g = Group(s, start="$")
    s.add({"id": "evt-1", "type": "call.ended"})        # duplicate delivery of evt-1
    s.add({"id": "evt-3", "type": "call.started"})
    print("new group from '$' reads only new messages:")
    process(g, g.read())
    replay = Group(s, start="0")
    print(f"a new group from '0' would replay {len(replay.read())} old messages")

    g2 = Group(s, start="0")
    print("group from '0', one bad message:")
    process(g2, g2.read())
    for _ in range(3):
        process(g2, g2.reclaim())
    print(f"pending: {list(g2.pending)}  dead-letter: {[i for i, _ in g2.dead]}")
