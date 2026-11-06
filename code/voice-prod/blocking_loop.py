"""One sync call inside async code stalls every call on that event loop.

Run:  python blocking_loop.py

An audio pump must handle a frame every 20 ms. Next to it, a handler publishes
an event. If the publish is a normal blocking call (like a sync Redis client),
the whole loop waits. Then we run the same publish in a thread.
"""
import asyncio
import time


def slow_publish():
    time.sleep(0.05)           # shortcut: stands in for a sync network call taking 50 ms


async def audio_pump(n=50):
    gaps, last = [], time.perf_counter()
    for _ in range(n):
        await asyncio.sleep(0.02)
        now = time.perf_counter()
        gaps.append((now - last) * 1000)
        last = now
    return gaps


async def on_transcript(mode, n=10):
    for _ in range(n):         # one event per partial transcript
        await asyncio.sleep(0.08)
        if mode == "blocking":
            slow_publish()                       # blocks the loop
        else:
            await asyncio.to_thread(slow_publish)  # loop keeps running


async def run(mode):
    gaps, _ = await asyncio.gather(audio_pump(), on_transcript(mode))
    late = sum(g > 30 for g in gaps)
    print(f"{mode:9} worst gap {max(gaps):5.1f} ms, frames later than 30 ms: {late}/{len(gaps)}")


if __name__ == "__main__":
    asyncio.run(run("blocking"))
    asyncio.run(run("to_thread"))
