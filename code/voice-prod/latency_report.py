"""p50 and p95 per turn, from metric events a call emits.

Run:  python latency_report.py

Each agent turn emits one event: how long from the caller going quiet to the
first audio of the reply, split by stage. Averages hide bad turns, so report
percentiles. The data is generated, with one slow LLM provider mixed in.
"""
import random
import statistics


def fake_events(n=400, seed=3):
    rnd = random.Random(seed)
    for i in range(n):
        eot = rnd.uniform(200, 500)                      # end-of-turn detection wait
        llm = rnd.lognormvariate(5.8, 0.35)              # time to first sentence, ~330 ms median
        if rnd.random() < 0.06:
            llm += rnd.uniform(1500, 3000)               # a slow response now and then
        tts = rnd.uniform(90, 220)                       # time to first audio byte
        yield {"turn": i, "eot_ms": eot, "llm_ttfs_ms": llm, "tts_ttfb_ms": tts}


def pct(xs, p):
    return statistics.quantiles(xs, n=100)[p - 1]


if __name__ == "__main__":
    ev = list(fake_events())
    for e in ev:
        e["total_ms"] = e["eot_ms"] + e["llm_ttfs_ms"] + e["tts_ttfb_ms"]
    print(f"{'stage':12} {'mean':>6} {'p50':>6} {'p95':>6} {'p99':>6}")
    for k in ("eot_ms", "llm_ttfs_ms", "tts_ttfb_ms", "total_ms"):
        xs = [e[k] for e in ev]
        print(f"{k:12} {statistics.mean(xs):6.0f} {pct(xs, 50):6.0f} {pct(xs, 95):6.0f} {pct(xs, 99):6.0f}")
    slow = [e for e in ev if e["total_ms"] > 1500]
    print(f"\nturns over 1.5 s: {len(slow)}/{len(ev)}; LLM was the biggest stage in {sum(e['llm_ttfs_ms'] > e['eot_ms'] + e['tts_ttfb_ms'] for e in slow)} of them")
    # shortcut: events come from a list. On the platform they are read back from the event stream.
