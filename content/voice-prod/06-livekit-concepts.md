---
title: LiveKit concepts, one call at a time
summary: Rooms, participants, tracks, tokens, webhooks, and the agent worker that joins each call. Learn the nouns LiveKit uses, and how one phone call maps onto them.
time: 25 min
---

You have a phone call and an agent. The last two lessons showed how [an SFU](lesson:voice-prod/mesh-mcu-sfu) forwards packets between them. Now you have to set it up. Who is allowed into the call? How does the agent know a call started? Who writes the database row, and who records the audio? LiveKit answers each question with a different part, and every part uses the same few nouns. Learn the nouns first and the rest of the platform reads easily.

## The object model

A **LiveKit server** is the SFU process. It holds rooms and forwards media between participants ([source](https://docs.livekit.io/intro/basics/rooms-participants-tracks.md)).

A **room** is a named space where a session happens. A room is created by the server API (`CreateRoom`) or on the fly when the first participant joins. `DeleteRoom` disconnects everyone in it ([source](https://docs.livekit.io/intro/basics/rooms-participants-tracks/rooms.md)).

A **participant** is anything that joins a room: a browser user, an agent, a SIP caller, a recorder. The participants page lists the fields that matter ([source](https://docs.livekit.io/intro/basics/rooms-participants-tracks/participants.md)):

- **identity**: a string you choose. It is unique per room. If a second participant joins with the same identity, the server disconnects the first.
- **kind**: what sort of participant it is. Values include `STANDARD` (an end user), `AGENT`, `SIP`, `EGRESS` (a recorder) and `INGRESS`.
- **metadata**: one free-form string, often JSON.
- **attributes**: a map of string keys to string values. Other participants can read them, and they get an event when one changes.

A **track** is one media stream a participant sends, such as a microphone. A **track publication** is the server's record that the track exists. You can see a publication without receiving its media. Each track has a **source**: camera, microphone, screen share, or screen share audio. To **subscribe** is to ask the server to forward a track to you. `autoSubscribe` is on by default, so a participant gets every existing and future track in the room ([source](https://docs.livekit.io/intro/basics/rooms-participants-tracks/tracks.md)).

<figure>
<svg viewBox="0 0 760 300" role="img" aria-labelledby="t-lkmodel d-lkmodel">
  <title id="t-lkmodel">The LiveKit object model for one call</title>
  <desc id="d-lkmodel">A room holds two participants. The phone participant publishes a caller-audio track and the agent publishes an agent-audio track. The SFU in the middle forwards each track to the other participant, who subscribes to it.</desc>
  <defs><marker id="ah-lkmodel" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="ah" d="M0 0 L10 5 L0 10 z"/></marker></defs>
  <rect class="box" x="16" y="30" width="728" height="236" rx="12" stroke-dasharray="6 4"/>
  <text x="32" y="54" font-size="15" font-weight="700">Room call-42 (one per call)</text>
  <g text-anchor="middle">
    <rect class="box" x="48" y="70" width="220" height="170" rx="10"/>
    <text x="158" y="94" font-size="15">Participant pstn-42</text>
    <text x="158" y="114" font-size="13" class="small">kind STANDARD</text>
    <rect class="box hot" x="68" y="130" width="180" height="50" rx="8"/>
    <text x="158" y="152" font-size="14">Track: caller-audio</text>
    <text x="158" y="170" font-size="12" class="small">source: microphone</text>
    <text x="158" y="222" font-size="13" class="small">receives agent-audio</text>
    <rect class="box" x="300" y="110" width="160" height="120" rx="10"/>
    <text x="380" y="150" font-size="15">SFU</text>
    <text x="380" y="176" font-size="12" class="small">forwards packets,</text>
    <text x="380" y="192" font-size="12" class="small">never decodes them</text>
    <rect class="box" x="492" y="70" width="220" height="170" rx="10"/>
    <text x="602" y="94" font-size="15">Participant agent</text>
    <text x="602" y="114" font-size="13" class="small">kind AGENT</text>
    <rect class="box hot" x="512" y="130" width="180" height="50" rx="8"/>
    <text x="602" y="152" font-size="14">Track: agent-audio</text>
    <text x="602" y="170" font-size="12" class="small">source: microphone</text>
    <text x="602" y="222" font-size="13" class="small">receives caller-audio</text>
  </g>
  <path class="arrow" d="M248 155 H296" marker-end="url(#ah-lkmodel)"/>
  <path class="arrow" d="M460 210 H488" marker-end="url(#ah-lkmodel)"/>
  <path class="arrow" d="M512 155 H464" marker-end="url(#ah-lkmodel)"/>
  <path class="arrow" d="M300 210 H272" marker-end="url(#ah-lkmodel)"/>
  <text x="380" y="290" font-size="13" class="small" text-anchor="middle">Publish goes up to the SFU. Subscribe brings a copy down to each other participant.</text>
</svg>
<figcaption>One call as LiveKit sees it. Each side publishes one audio track and subscribes to the other's.</figcaption>
</figure>

On the client side the SDK raises events as this happens. The Python `rtc.Room` documents `participant_connected`, `track_published`, `track_subscribed`, `participant_attributes_changed` and `participant_disconnected`, among others ([source](https://docs.livekit.io/reference/python/livekit/rtc/room.html)). `track_published` means "a track exists". `track_subscribed` means "its media is now coming to you". Code that wants audio waits for the second one.

## Who may join: access tokens

Nobody joins a room without an **access token**. It is a JWT signed with your **API secret**. The `iss` claim is the **API key**, and `sub` is the participant's identity. The **video grant** inside says what the holder may do ([source](https://docs.livekit.io/frontends/reference/tokens-grants.md)):

| Grant | Means |
|---|---|
| `roomJoin` + `room` | May join this one named room |
| `canPublish` | May send tracks |
| `canSubscribe` | May receive other participants' tracks |
| `canPublishData` | May send data messages |
| `roomCreate`, `roomAdmin` | May create, delete or moderate rooms |

The token can also carry the participant's metadata and attributes. If you set no expiry, most server SDKs default to 6 hours, and expiry only checks the first connect, not reconnects. Signing needs the secret, so you mint tokens on a server, never in the browser or app ([source](https://docs.livekit.io/frontends/build/authentication.md)).

## Two kinds of SDK

The **server API** is plain HTTP calls signed with the key and secret. It creates and deletes rooms, lists participants, starts recordings, and places SIP calls. Nothing in it sends or receives audio. The **realtime SDK** (`rtc` in Python) joins a room as a participant, publishes tracks, and gets audio frames. Our platform uses both. The services that manage calls only use the server API. The media bridge and the agent use the realtime SDK.

## The companions

LiveKit server only moves media. Four separate programs do the rest. When you host LiveKit yourself, each is its own deployment that shares the server's API key and Redis.

- **livekit-sip** speaks SIP to phone carriers. An **inbound trunk** accepts calls. An **outbound trunk** places them, through the `CreateSIPParticipant` API. A **dispatch rule** says which room an inbound caller lands in: one room per caller (individual), one fixed room (direct), or a room named after the dialed number (callee) ([source](https://docs.livekit.io/telephony.md), [dispatch rules](https://docs.livekit.io/telephony/accepting-calls/dispatch-rule.md)).
- **Egress** exports media. A **room composite** mixes the whole room into one output; with `audio_only` you get one mixed audio file. **Track egress** exports a single track and ends when that track is unpublished. Outputs can upload to S3 or any S3-compatible store ([source](https://docs.livekit.io/transport/media/ingress-egress/egress.md), [outputs](https://docs.livekit.io/transport/media/ingress-egress/egress/outputs.md)). The current docs replace the older `StartRoomCompositeEgress` call with one `StartEgress` call that takes a source. Our platform still calls the older one.
- **Ingress** brings in non-WebRTC media such as RTMP, WHIP or a file URL ([source](https://docs.livekit.io/transport/media/ingress-egress/ingress.md)). Phone calls do not use it.
- **Webhooks** tell your backend what happened. You add a `webhook:` block with an `api_key` and a list of `urls` to the server config. Each POST carries an `Authorization` JWT that includes a sha256 of the body, so you can check it came from your server. Events include `room_started`, `participant_joined`, `track_published`, `participant_left`, `room_finished`, `egress_started`, `egress_updated` and `egress_ended`. Delivery is retried but not guaranteed, and queued events go out in sequence ([source](https://docs.livekit.io/intro/basics/rooms-participants-tracks/webhooks-events.md)). `participant_joined` fires once the participant's media connection is up.

## The whole flow in a toy

`code/voice-prod/room_model.py` fakes a room in about 80 lines. It skips the audio and keeps the shape: tokens that name one room, publish and subscribe, and the webhooks a call produces. A real token is a JWT; here an HMAC over a small dict stands in for it.

```python
def make_token(identity, room, can_publish=True, can_subscribe=True):
    grant = {"sub": identity, "room": room, "pub": can_publish, "subs": can_subscribe}
    body = json.dumps(grant, sort_keys=True).encode()
    return body, hmac.new(SECRET, body, hashlib.sha256).hexdigest()

# in Room.join: a late joiner is subscribed to tracks that already exist
for owner, names in self.tracks.items():
    for t in names:
        self._subscribe(grant["sub"], owner, t)
```

Run `python3 code/voice-prod/room_model.py`:

```text
webhook -> room_started        {'room': 'call-42'}
webhook -> participant_joined  {'identity': 'pstn-42'}
webhook -> track_published     {'identity': 'pstn-42', 'track': 'caller-audio'}
webhook -> participant_joined  {'identity': 'agent'}
    [sfu] agent now receives pstn-42/caller-audio (packets forwarded, not decoded)
webhook -> track_published     {'identity': 'agent', 'track': 'agent-audio'}
    [sfu] pstn-42 now receives agent/agent-audio (packets forwarded, not decoded)
rejected: token is for room call-7
webhook -> participant_left    {'identity': 'pstn-42'}
webhook -> participant_left    {'identity': 'agent'}
webhook -> room_finished       {'room': 'call-42'}
           call rows: {'42': 'in-progress'} -> mark ended, start recording upload
```

The agent joins after the caller's track exists, and it still receives it. That is auto-subscribe. The `snoop` token is valid but names another room, so the join fails.

:::try
Copy the script and give the agent's token `can_subscribe=False`. Predict which line disappears before you run it. We ran it: the `[sfu] agent now receives pstn-42/caller-audio` line goes away. Every webhook still fires, and the caller still hears the agent. A room that looks healthy from the webhooks can still have an agent that hears nothing.
:::

## The Agents framework

An agent is just another participant. The **Agents framework** runs it for you. You start a long-lived **worker** process (the current docs call it an **agent server**). It registers with the LiveKit server and waits. When a room needs an agent, the server sends a **job** to a worker with spare capacity, and the worker runs that job in its own process, so one crash does not take down other calls ([source](https://docs.livekit.io/agents/server/lifecycle.md)).

**Dispatch** decides which rooms get a job. If the worker sets no `agent_name`, it gets **automatic dispatch**: a job for every new room. The docs advise against this for most apps. Set an `agent_name` and you get **explicit dispatch**: the agent only joins when something asks for it by name, through the dispatch API, a token's room config, or a SIP dispatch rule ([source](https://docs.livekit.io/agents/server/agent-dispatch.md)).

Inside the worker:

- **Idle processes** are started ahead of time and wait for jobs. `num_idle_processes` sets how many; production defaults to the CPU count ([source](https://docs.livekit.io/agents/server/options.md)).
- **Prewarm** runs once in each new process, before any job. Load slow things here, such as Silero VAD weights, and keep them in `proc.userdata` ([source](https://docs.livekit.io/agents/logic/turns/vad.md)).
- The **entrypoint** runs once per job. It gets a **JobContext**: `ctx.room`, `ctx.job` (the dispatch data, including the room name), `ctx.connect()` to join the room, `ctx.wait_for_participant()`, and `ctx.delete_room()` ([source](https://docs.livekit.io/agents/server/job.md)).
- An **AgentSession** is the voice loop. You give it `stt`, `llm` and `tts` plugins for a **cascaded** pipeline, or a **realtime model** (speech-to-speech) instead ([source](https://docs.livekit.io/agents/models.md)). The platform passes its realtime model in the `llm` argument. A **VAD** plugin (Silero) hears speech start and stop. A **turn detector** model guesses whether the caller has finished ([source](https://docs.livekit.io/agents/logic/turns/turn-detector.md)).
- The job ends when every standard and SIP participant has left, or when you shut it down.

<figure>
<svg viewBox="0 0 770 260" role="img" aria-labelledby="t-lkworker d-lkworker">
  <title id="t-lkworker">Agent worker lifecycle</title>
  <desc id="d-lkworker">Top row: the worker registers, a room is created, a job is dispatched, an idle process takes it. Bottom row: prewarm was already done, the entrypoint runs and connects, the AgentSession runs the conversation, the job ends when the room closes.</desc>
  <defs><marker id="ah-lkworker" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="ah" d="M0 0 L10 5 L0 10 z"/></marker></defs>
  <g text-anchor="middle">
    <rect class="box" x="16" y="40" width="170" height="56" rx="10"/><text x="101" y="64" font-size="14">1. Worker registers</text><text x="101" y="84" font-size="12" class="small">once, at startup</text>
    <rect class="box" x="204" y="40" width="170" height="56" rx="10"/><text x="289" y="64" font-size="14">2. Room created</text><text x="289" y="84" font-size="12" class="small">first join or API call</text>
    <rect class="box" x="392" y="40" width="170" height="56" rx="10"/><text x="477" y="64" font-size="14">3. Job dispatched</text><text x="477" y="84" font-size="12" class="small">automatic, or by name</text>
    <rect class="box" x="580" y="40" width="170" height="56" rx="10"/><text x="665" y="64" font-size="14">4. Idle process</text><text x="665" y="84" font-size="12" class="small">takes the job</text>
    <rect class="box hot" x="16" y="150" width="170" height="56" rx="10"/><text x="101" y="174" font-size="14">5. Prewarm done</text><text x="101" y="194" font-size="12" class="small">VAD, turn model loaded</text>
    <rect class="box" x="204" y="150" width="170" height="56" rx="10"/><text x="289" y="174" font-size="14">6. entrypoint(ctx)</text><text x="289" y="194" font-size="12" class="small">ctx.connect()</text>
    <rect class="box" x="392" y="150" width="170" height="56" rx="10"/><text x="477" y="174" font-size="14">7. AgentSession</text><text x="477" y="194" font-size="12" class="small">STT, LLM, TTS turns</text>
    <rect class="box" x="580" y="150" width="170" height="56" rx="10"/><text x="665" y="174" font-size="14">8. Job ends</text><text x="665" y="194" font-size="12" class="small">callers left, room closes</text>
  </g>
  <path class="arrow" d="M186 68 H200" marker-end="url(#ah-lkworker)"/>
  <path class="arrow" d="M374 68 H388" marker-end="url(#ah-lkworker)"/>
  <path class="arrow" d="M562 68 H576" marker-end="url(#ah-lkworker)"/>
  <path class="arrow" d="M665 96 V122 H101 V146" marker-end="url(#ah-lkworker)"/>
  <path class="arrow" d="M186 178 H200" marker-end="url(#ah-lkworker)"/>
  <path class="arrow" d="M374 178 H388" marker-end="url(#ah-lkworker)"/>
  <path class="arrow" d="M562 178 H576" marker-end="url(#ah-lkworker)"/>
  <text x="385" y="238" font-size="13" class="small" text-anchor="middle">Step 1 happens once. Prewarm ran when the process started, before this call existed. Steps 2 to 8 repeat per call.</text>
</svg>
<figcaption>The worker does the slow loading before the phone rings, so a call only pays for steps 6 and 7.</figcaption>
</figure>

## What the platform did

The platform runs self-hosted, unmodified LiveKit: server, sip, egress and ingress, all sharing one key pair. The worker runs from the call orchestration image as a second process. It pins livekit-agents 1.6.x, which still uses the older names: `WorkerOptions(entrypoint_fnc=..., prewarm_fnc=..., num_idle_processes=...)` and `cli.run_app`. The current docs call the same pieces `AgentServer`, `setup_fnc` and `@server.rtc_session()`.

- It keeps two idle processes, set explicitly rather than per CPU, so a shared host does not over-provision.
- Prewarm loads Silero VAD and the turn-detector model. If the turn model fails to load, the worker logs it and those assistants fall back to VAD-only turns.
- The entrypoint reads the room name from `ctx.job`, then connects and looks up the call row at the same time. It loads the assistant config and fetches the three provider secrets in parallel. It builds a cascaded session, or a realtime one if the assistant has a realtime config.
- Trunks and dispatch rules are created at runtime through the SIP API by the telephony service. No config file holds them.
- Egress records each call as an audio-only room composite to S3 or MinIO.

:::warn Gotcha from the platform
The first local test call connected, and the agent left at once with "no call row for room". The server config had no `webhook:` block. LiveKit never sent `room_started` or `participant_joined`, so call orchestration never wrote the call row the agent looks up. The media path was fine; only the bookkeeping was missing. A second gap is still open: the worker sets no `agent_name`, so it uses automatic dispatch and gets a job for every room on the server, including rooms that never need an agent.
:::

:::note What we did not test
Every LiveKit fact here comes from the docs pages linked above. The platform details come from reading its config and worker code. We did not run a LiveKit server for this lesson. `room_model.py` is a toy. It has no real JWTs, no media and no network, and its webhooks fire inline instead of being retried.
:::

:::say
A call is a room, the caller and the agent are participants, their voices are tracks, and a webhook tells your backend each time one of those changes.
:::

:::check What is the difference between `track_published` and `track_subscribed`?
`track_published` says a participant has a track in the room. `track_subscribed` says the server is now sending that track's media to you. You can see a publication you never subscribe to, and an agent that waits on the first event may start before any audio arrives.
:::

:::check The worker has no `agent_name`. What happens when someone creates a room for a recording test with no caller in it?
Automatic dispatch sends a job to every new room, so an agent process starts, connects, finds no call row and exits. It wastes a process and logs an error each time. Setting an `agent_name` and dispatching explicitly fixes it.
:::

Next: [How the platform rides LiveKit](lesson:voice-prod/how-the-platform-rides-livekit)
