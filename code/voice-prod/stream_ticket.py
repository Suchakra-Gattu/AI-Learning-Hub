"""Who is on this socket? One-time tickets and signed URLs.

Run:  python stream_ticket.py

A carrier webhook says "call coming". We answer with a stream URL holding a
ticket. The carrier then opens a WebSocket and sends the ticket back. The
ticket works once, and only for a short time.
"""
import hashlib
import hmac
import secrets
import time

store = {}   # shortcut: a dict stands in for Redis. Real code: SET key val EX ttl, then GETDEL.


def issue_ticket(call_id, ttl=60):
    t = secrets.token_urlsafe(24)
    store[t] = (call_id, time.monotonic() + ttl)
    return t


def redeem(ticket):
    entry = store.pop(ticket, None)          # GETDEL: read and delete in one step
    if entry is None or time.monotonic() > entry[1]:
        return None
    return entry[0]


KEY = b"url-signing-key"


def url_token(org_id):
    return hmac.new(KEY, org_id.encode(), hashlib.sha256).hexdigest()[:32]


def check_url_token(org_id, given):
    return hmac.compare_digest(url_token(org_id), given)


def naive_check(expected, given):           # what `!=` does, made visible
    steps = 0
    for a, b in zip(expected, given):
        steps += 1
        if a != b:
            break
    return steps


if __name__ == "__main__":
    t = issue_ticket("call-42")
    print("first use :", redeem(t))
    print("replay    :", redeem(t), "-> close socket with 1008 (policy violation)")
    old = issue_ticket("call-43", ttl=0)
    time.sleep(0.01)
    print("expired   :", redeem(old))

    good = url_token("org-1")
    print("url token ok :", check_url_token("org-1", good), "| wrong org:", check_url_token("org-2", good))
    # Why compare_digest: a plain compare stops at the first wrong char.
    # More right chars = more work = a tiny time difference an attacker can measure.
    for right in (0, 8, 24):
        guess = good[:right] + "z" * (32 - right)          # 'z' is never in a hex digest
        print(f"guess with {right:>2} right chars: plain compare did {naive_check(good, guess):>2} steps")
