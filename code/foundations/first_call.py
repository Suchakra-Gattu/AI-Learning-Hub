"""Your first model call. Run: python first_call.py "Explain a hash map in one sentence."""
import sys
from llm import ask

question = " ".join(sys.argv[1:]) or "Explain a hash map in one sentence."
reply = ask(question)
print(reply if reply else f"(No ANTHROPIC_API_KEY set. This is what would be sent:)\n{question}")
