"""A toy LiveKit-style room: tokens, participants, tracks, webhooks.

Run:  python room_model.py

No audio moves here. The point is the shape: who may join, who publishes what,
who subscribes, and which webhook events the server sends while one phone call
goes from ring to hang-up.
"""
import hashlib
import hmac
import json

SECRET = b"dev-secret"   # shortcut: real tokens are JWTs signed with the API secret


def make_token(identity, room, can_publish=True, can_subscribe=True):
    grant = {"sub": identity, "room": room, "pub": can_publish, "subs": can_subscribe}
    body = json.dumps(grant, sort_keys=True).encode()
    return body, hmac.new(SECRET, body, hashlib.sha256).hexdigest()


class Room:
    def __init__(self, name, on_webhook):
        self.name, self.emit = name, on_webhook
        self.participants, self.tracks = {}, {}          # identity -> {track names}
        self.emit("room_started", room=name)

    def join(self, token):
        body, sig = token
        if not hmac.compare_digest(sig, hmac.new(SECRET, body, hashlib.sha256).hexdigest()):
            raise PermissionError("bad token")
        grant = json.loads(body)
        if grant["room"] != self.name:
            raise PermissionError(f"token is for room {grant['room']}")
        self.participants[grant["sub"]] = grant
        self.emit("participant_joined", identity=grant["sub"])
        for owner, names in self.tracks.items():        # late joiner sees existing tracks
            for t in names:
                self._subscribe(grant["sub"], owner, t)

    def publish(self, identity, track):
        if not self.participants[identity]["pub"]:
            raise PermissionError(f"{identity} may not publish")
        self.tracks.setdefault(identity, set()).add(track)
        self.emit("track_published", identity=identity, track=track)
        for other in self.participants:
            if other != identity:
                self._subscribe(other, identity, track)

    def _subscribe(self, who, owner, track):
        if self.participants[who]["subs"]:
            print(f"    [sfu] {who} now receives {owner}/{track} (packets forwarded, not decoded)")

    def leave(self, identity):
        del self.participants[identity]
        self.tracks.pop(identity, None)
        self.emit("participant_left", identity=identity)
        if not self.participants:
            self.emit("room_finished", room=self.name)


if __name__ == "__main__":
    calls = {}

    def webhook(event, **data):                         # what the orchestrator receives
        print(f"webhook -> {event:19} {data}")
        if event == "participant_joined" and data["identity"].startswith("pstn-"):
            calls[data["identity"][5:]] = "in-progress"   # idempotent upsert in real life
        if event == "room_finished":
            print(f"           call rows: {calls} -> mark ended, start recording upload")

    room = Room("call-42", webhook)
    room.join(make_token("pstn-42", "call-42"))         # media bridge, for the phone leg
    room.publish("pstn-42", "caller-audio")
    room.join(make_token("agent", "call-42"))           # agent job dispatched to this room
    room.publish("agent", "agent-audio")
    try:
        room.join(make_token("snoop", "call-7"))
    except PermissionError as e:
        print(f"rejected: {e}")
    room.leave("pstn-42")                               # caller hangs up
    room.leave("agent")
