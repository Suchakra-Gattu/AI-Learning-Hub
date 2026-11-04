"""How much memory does the KV cache use? Run: python kv_cache.py

Per token the model stores one key and one value for every layer and every attention head.
bytes = 2 (key and value) * layers * heads * head_size * bytes_per_number * tokens * batch
"""


def kv_cache_gib(layers, heads, head_size, tokens, batch=1, bytes_per_number=2):
    return 2 * layers * heads * head_size * bytes_per_number * tokens * batch / 2**30


if __name__ == "__main__":
    # Llama 2 7B shape: 32 layers, 32 heads, head size 128, 16-bit numbers (2 bytes).
    one = kv_cache_gib(32, 32, 128, tokens=4096)
    print(f"1 request,  4096 tokens: {one:.1f} GiB")
    print(f"16 requests, 4096 tokens: {kv_cache_gib(32, 32, 128, 4096, batch=16):.1f} GiB")
    assert round(one, 1) == 2.0  # NVIDIA's inference blog gives about 2 GB for this case
