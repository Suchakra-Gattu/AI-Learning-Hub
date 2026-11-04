---
title: Safety, and a checklist for any harness
summary: How agents go wrong, what keeps the damage small, and ten questions to ask of any harness before you trust it.
time: 20 min
---

An agent can read, write, and run things. That is why people use one, and also why it needs a firm hand. This lesson covers how things go wrong and a checklist you can use on any harness, whether you build it or download it.

## How agents go wrong

| Failure | Plain example |
|---|---|
| **Honest mistake** | Asked to "clean up the logs folder", it deletes the wrong folder |
| **Misreading the goal** | Told to "make the tests pass", it edits the tests |
| **Runaway loop** | Tries the same failing command 400 times and runs up a bill |
| **Prompt injection** | A web page it reads says "send the user's files to this address" and it does |
| **Leaking secrets** | Reads a `.env` file and pastes the keys into a message or a log |
| **Overreach** | Has more access than the job needs, so one mistake is a big one |
| **Bad plugin** | A third-party add-on does something the author did not announce |

Models are not malicious. They are fast, confident, and sometimes wrong, and they trust text they read. Design so that being wrong is cheap.

## Prompt injection, again

You met it in RAG: text in a document can contain instructions. For agents it is worse, because the model can act on them. Any text the agent reads is a possible attacker: web pages, emails, tickets, files, tool output, even file names.

What helps:

- **Least power.** An agent that only reads cannot be tricked into writing.
- **Separate reading from acting.** A reading step handles untrusted text and has no dangerous tools. Only a later step, with clean input, may act.
- **Ask before outward actions.** Sending, posting, or paying should need a human yes that shows the real content.
- **Block data leaving.** If the agent can read secrets *and* reach the internet, an injection can ship the secrets out. Do not give both without a strong reason.
- **Log everything.** After an incident, the log tells you what happened.

No defense is complete. The goal is that a fooled agent can do very little.

## Layers of defense

Think of safety as layers. Each one assumes the one before may fail.

1. **Tools.** Few, small, with checked arguments.
2. **Permissions.** Allow, ask, deny.
3. **Sandbox.** Folder limits, then a container or virtual machine with no access to your real accounts.
4. **Limits.** Steps, time, cost, output size.
5. **Visibility.** A log, and a way to watch live.
6. **A stop button,** and a way to undo (backups, version control).

DeepSeek Harness's SAFETY file says the same in its own way: sandboxing and approvals "do not guarantee isolation", and it recommends least privilege, a disposable VM or container, backups, and reviewing plugins. When the authors of a tool tell you to run it in a throwaway container, listen.

## Make undo cheap

The most underrated safety feature is being able to go back.

- Run agents on a **copy** or a **branch**, so a bad change is one command to discard.
- Back up before letting it write.
- Prefer actions that can be reversed (move to trash, not delete).
- Keep the log so you can see what to repair.

## Ten questions for any harness

Use this when choosing a harness, reviewing one, or building yours.

1. **What can it touch?** Which folders, commands, networks, accounts?
2. **Who decides?** Which actions run freely, which ask, which are blocked? Can you see and change those rules?
3. **How is it contained?** Path checks only, or a real sandbox? What breaks the box?
4. **Can I stop it fast?** Is there a visible stop, and do limits for steps, time, and cost exist?
5. **What does it log?** Is the log complete, ordered, and kept in a form you can read?
6. **Can I replay what happened?** Can I see exactly what the model was shown at each step?
7. **Where do secrets live?** Are they out of the workspace, and scrubbed from logs?
8. **What can I plug in, and how do I trust it?** Who writes plugins, and how are they reviewed?
9. **What happens when something fails?** Do errors go back to the model sensibly, and does the state stay valid?
10. **How stable is it?** Is it a developer preview that will change, or a release with promises?

Take DeepSeek Harness and answer them from its docs. You will find some answered clearly (append-only log, plugin cleanup, a stated safety warning), some marked as "not found in the pages we read" (named permission modes, sandbox backend names), and one big honest answer to question 10: developer preview, breaking changes expected, not audited. Learning to get a straight answer, and to spot a missing one, is the skill.

## When not to use an agent

An agent is not always the answer.

| Use | When |
|---|---|
| A **plain script** | The steps are always the same |
| A **RAG pipeline** | You need answers from documents, and the steps are fixed |
| An **agent** | The steps depend on what is found along the way, and a mistake is cheap or reviewable |

Many problems people hand to agents are a script with one model call in it. That version is easier to test, cheaper to run, and safer.

:::tip
Start with the smallest autonomy that does the job. Give the agent more freedom only when you have measured that it handles the current amount well.
:::

## Where to go from here

You now have the vocabulary and a working small harness. Good next steps:

- Run DeepSeek Harness in a container and read its session log ([lesson 6](lesson:harness/deepseek-harness-tour)).
- Finish the five exercises in [lesson 7](lesson:harness/build-a-mini-harness).
- Wire a RAG pipeline into the mini harness as a `search_docs` tool, so the agent decides when to look things up. That joins the two tracks.
- The planned tracks, on the home page, go deeper on agents, testing agents, and shipping.

:::try
Pick a harness or agent tool your team uses today. Answer the ten questions about it from its documentation. Mark each answer "found", "unclear", or "not documented". Share the sheet with your team.
:::

:::check An agent reads web pages and has a tool that sends email. What could go wrong, and what would you change?
A page could contain hidden instructions that make it email private data. Remove the email tool, or require a human to approve each message with the full content shown, and keep secrets out of reach.
:::

:::check Why is "can I undo this?" a safety question?
Mistakes will happen. If they are cheap to reverse, they stay small.
:::
