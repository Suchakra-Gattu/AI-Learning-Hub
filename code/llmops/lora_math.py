"""Why LoRA is small. Run: python lora_math.py

A weight matrix with d rows and k columns has d*k numbers. LoRA freezes it and trains two thin
matrices instead: one d x r and one r x k. That is r * (d + k) numbers, where r is the "rank".
"""


def full_params(d, k):
    return d * k


def lora_params(d, k, r):
    return r * (d + k)


if __name__ == "__main__":
    d = k = 4096  # one attention matrix in a 7B-class model
    for r in (4, 8, 16):
        share = lora_params(d, k, r) / full_params(d, k)
        print(f"rank {r:>2}: {lora_params(d, k, r):>9,} trainable vs {full_params(d, k):,} ({share:.2%})")
    assert lora_params(4096, 4096, 8) == 65_536
