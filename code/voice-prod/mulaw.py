"""Phone audio in 60 lines: G.711 mu-law to PCM16 and back, plus re-framing.

Run:  python mulaw.py

Carriers send 8 kHz mu-law in 20 ms frames (160 bytes). Media SDKs often hand
you 10 ms frames of PCM16. This file shows both conversions with stdlib only.
"""
import math
import struct

BIAS, CLIP = 0x84, 32635


def encode_sample(s):
    """One signed 16-bit sample -> one mu-law byte (the G.711 algorithm)."""
    sign = 0x80 if s < 0 else 0
    s = min(abs(s), CLIP) + BIAS
    exp = max(0, s.bit_length() - 8)          # which of 8 segments
    mant = (s >> (exp + 3)) & 0x0F
    return ~(sign | (exp << 4) | mant) & 0xFF


def decode_byte(b):
    b = ~b & 0xFF
    sign, exp, mant = b & 0x80, (b >> 4) & 0x07, b & 0x0F
    s = ((mant << 3) + BIAS) << exp
    return -(s - BIAS) if sign else s - BIAS


# Lookup table: decode is a hot path (50 frames/s per call), so precompute all 256.
DECODE = [decode_byte(b) for b in range(256)]


def ulaw_to_pcm16(data: bytes) -> bytes:
    return struct.pack(f"<{len(data)}h", *(DECODE[b] for b in data))


def pcm16_to_ulaw(pcm: bytes) -> bytes:
    return bytes(encode_sample(s) for s in struct.unpack(f"<{len(pcm)//2}h", pcm))


class FrameChunker:
    """Collects bytes of any size and hands out fixed-size frames."""
    def __init__(self, frame_bytes):
        self.size, self.buf = frame_bytes, bytearray()

    def push(self, data):
        self.buf += data
        while len(self.buf) >= self.size:
            yield bytes(self.buf[:self.size])
            del self.buf[:self.size]


if __name__ == "__main__":
    rate = 8000
    tone = [int(8000 * math.sin(2 * math.pi * 440 * n / rate)) for n in range(rate // 50)]  # 20 ms of 440 Hz
    pcm = struct.pack(f"<{len(tone)}h", *tone)
    ulaw = pcm16_to_ulaw(pcm)
    back = struct.unpack(f"<{len(tone)}h", ulaw_to_pcm16(ulaw))
    worst = max(abs(a - b) for a, b in zip(tone, back))
    print(f"20 ms at 8 kHz: {len(tone)} samples, PCM16 {len(pcm)} bytes, mu-law {len(ulaw)} bytes")
    print(f"round trip worst error: {worst} (of peak 8000) -> lossy, but fine for speech")
    print(f"one minute of call audio: mu-law {rate*60//1000} KB, PCM16 {rate*2*60//1000} KB")

    # SDK gives 10 ms PCM16 frames (160 bytes); carrier wants 20 ms mu-law frames (160 bytes).
    chunker = FrameChunker(160)
    sent = []
    for i in range(5):                                  # five 10 ms frames arrive
        ten_ms = pcm[(i % 2) * 160:(i % 2) * 160 + 160]
        for frame in chunker.push(pcm16_to_ulaw(ten_ms)):  # 80 mu-law bytes each
            sent.append(len(frame))
    print(f"5 x 10 ms in -> frames out: {sent}, left in buffer: {len(chunker.buf)} bytes")
    # shortcut: no resampling here. 8 kHz <-> 48 kHz is the media SDK's job in our platform.
