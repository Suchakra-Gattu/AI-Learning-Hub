"""Rough token and cost estimate. Run: python token_count.py "some text" """
import sys

# shortcut: 4 characters per token is an English rule of thumb, not a real tokenizer. Use your provider's token counter for billing.
def rough_tokens(text):
    return max(1, round(len(text) / 4))

if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) or "How long do I have to return a tent?"
    print(f"{len(text)} characters is about {rough_tokens(text)} tokens")
    assert rough_tokens("a" * 400) == 100
