"""Retry schedules and graceful drain.

Run:  python retry_backoff.py

Part 1: a customer's webhook endpoint is down. Compare a fixed schedule with
jittered exponential backoff when 1,000 calls end at the same moment.
Part 2: a deploy sends SIGTERM to a media server with live calls on it.
"""
import random

FIXED = [30, 120, 600, 1800, 7200]          # seconds: 30 s, 2 m, 10 m, 30 m, 2 h


def jittered(attempt, base=30, cap=7200, rnd=random.Random(1)):
    return rnd.uniform(0, min(cap, base * 4 ** attempt))   # "full jitter"


def busiest_second(delays):
    buckets = {}
    for d in delays:
        buckets[int(d)] = buckets.get(int(d), 0) + 1
    return max(buckets.values())


def drain(calls_left_s, grace_s):
    """Stop taking new calls, let live ones finish, kill whatever is left at the deadline."""
    finished = sum(1 for c in calls_left_s if c <= grace_s)
    return finished, len(calls_left_s) - finished


if __name__ == "__main__":
    n = 1000
    print("first retry of 1,000 failed webhooks:")
    print(f"  fixed 30 s   -> {busiest_second([FIXED[0]] * n):>4} requests in the busiest second")
    print(f"  full jitter  -> {busiest_second([jittered(0) for _ in range(n)]):>4} requests in the busiest second")
    print(f"  give-up time with the fixed schedule: {sum(FIXED) / 60:.0f} min after the first failure")

    rnd = random.Random(2)
    live = [rnd.uniform(0, 600) for _ in range(40)]      # seconds each live call still needs
    print("\nSIGTERM with 40 live calls (health check now returns 503, new streams get close code 1013):")
    for grace in (30, 120, 300):
        ok, cut = drain(live, grace)
        print(f"  grace {grace:>3} s -> {ok:>2} calls end normally, {cut:>2} cut off")
    # shortcut: no real signals or sockets; the numbers are the lesson.
