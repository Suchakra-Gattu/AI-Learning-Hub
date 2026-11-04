"""Time each stage of a voice turn and report the median and worst case.

Run:  python latency_timer.py

The three stages are SIMULATED with sleeps so this runs anywhere with no keys.
To measure a real pipeline, replace the three functions with real calls.
The timing code stays the same, and that part is the lesson.
"""
import random
import statistics
import time


# shortcut: fake stage times (in seconds). Replace each body with a real STT, LLM or TTS call.
def stt(audio):
    time.sleep(random.uniform(0.15, 0.30))
    return "how long do I have to return a tent"


def llm(text):
    time.sleep(random.uniform(0.30, 0.70))
    return "You have 60 days for tents."


def tts(text):
    time.sleep(random.uniform(0.10, 0.20))
    return b"audio-bytes"


def one_turn():
    times = {}
    data = b"audio-in"
    for name, step in (("stt", stt), ("llm", llm), ("tts", tts)):
        start = time.perf_counter()
        data = step(data)
        times[name] = (time.perf_counter() - start) * 1000
    times["total"] = sum(times.values())
    return times


if __name__ == "__main__":
    random.seed(1)
    runs = [one_turn() for _ in range(20)]
    print(f"{'stage':<7}{'median ms':>10}{'worst ms':>10}")
    for stage in ("stt", "llm", "tts", "total"):
        values = [r[stage] for r in runs]
        print(f"{stage:<7}{statistics.median(values):>10.0f}{max(values):>10.0f}")
    assert all(r["total"] > 0 for r in runs)
