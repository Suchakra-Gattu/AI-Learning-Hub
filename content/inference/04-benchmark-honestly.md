---
title: Benchmark honestly
summary: Two numbers matter, how long until the first word and how fast the rest arrives. Measure them the same way every time.
time: 15 min
---

"Which server is faster?" is not a question until you say faster at what, with which model, prompt, and load.

## Two numbers

- **Time to first token (TTFT).** How long the user waits before any output appears. Mostly prefill.
- **Tokens per second.** How fast the rest of the answer streams. Mostly decode.

llama.cpp's `llama-bench` reports **pp** (prompt processing) and **tg** (text generation) as average tokens per second, with a standard deviation over repeated runs, five by default. It leaves tokenization and sampling out of the timing ([README](https://github.com/ggml-org/llama.cpp/blob/master/tools/llama-bench/README.md)). Its example command from the docs:

```bash
./llama-bench -n 0 -p 1024 -b 128,256,512,1024
```

vLLM's `vllm bench serve` reports TTFT, TPOT and ITL by default ([docs](https://docs.vllm.ai/en/latest/cli/bench/serve/)). The page we read lists those names without defining them, so check the definitions before you quote them.

## Rules for a fair test

1. **Same model, same quantization, same prompts** on every setup.
2. **Warm up first.** Throw away the first run.
3. **Repeat and report spread.** A mean with no spread hides noise. Use the median and the worst case, as in the [voice timer](lesson:voice/where-the-milliseconds-go).
4. **Test with realistic load.** One request at a time says nothing about 50 at once.
5. **Write down the hardware and versions.** A number without them cannot be reproduced.
6. **Treat vendor numbers as claims.** Dynamo's README cites a 2x faster time to first token. That is one benchmark by the project, not your workload.

:::try
Run the same `llama-bench` command on a Q4 file and a Q8 file of the same model. Compare size, pp and tg. Which one would you ship, and what would you check before you did?
:::

:::check Your server shows great average tokens per second, but users complain it feels slow. Which number do you check?
Time to first token and the worst case. Users feel the wait before output starts and the slow requests, which an average can hide.
:::

You now have the map from prompt to hardware. For the whole picture of shipping, see [going to production](lesson:rag/going-to-production).
