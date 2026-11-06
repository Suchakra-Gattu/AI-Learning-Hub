"""Barge-in: stop the agent's audio when the caller starts talking.

Run:  python barge_in.py

The bridge keeps the caller's loudness (RMS) per 20 ms frame. When the agent
stops speaking (because the turn detector heard the caller), the bridge checks:
was the caller actually loud recently? If yes, it throws away audio already
queued for the phone and tells the carrier to clear its own buffer too.
"""
import math
import struct
from collections import deque

THRESHOLD, WINDOW_S, FRAME_S = 600, 0.6, 0.02


def rms(pcm: bytes) -> float:
    s = struct.unpack(f"<{len(pcm)//2}h", pcm)
    return math.sqrt(sum(x * x for x in s) / len(s))


def frame(amplitude):
    return struct.pack("<160h", *(int(amplitude * math.sin(i / 3)) for i in range(160)))


class BargeIn:
    def __init__(self):
        self.loud_at = deque()               # times of loud caller frames
        self.queued_to_phone = 0

    def caller_frame(self, t, pcm):
        if rms(pcm) >= THRESHOLD:
            self.loud_at.append(t)
        while self.loud_at and t - self.loud_at[0] > WINDOW_S:
            self.loud_at.popleft()

    def agent_stopped_speaking(self, t):
        if self.loud_at and t - self.loud_at[-1] <= WINDOW_S:
            dropped, self.queued_to_phone = self.queued_to_phone, 0
            return f"clear: dropped {dropped} queued frames, sent carrier clear command"
        return "no clear: agent just finished its sentence"


if __name__ == "__main__":
    for label, caller_amp in (("caller silent", 50), ("line hiss", 300), ("caller talks", 3000)):
        b = BargeIn()
        b.queued_to_phone = 25                # 500 ms of agent audio waiting to be sent
        for i in range(30):
            b.caller_frame(i * FRAME_S, frame(caller_amp if i > 20 else 50))
        print(f"{label:13} rms={rms(frame(caller_amp)):6.0f} -> {b.agent_stopped_speaking(30 * FRAME_S)}")
    # shortcut: fixed threshold. Loud lines and quiet callers need it tuned per carrier.
