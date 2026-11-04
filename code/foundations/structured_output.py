"""Ask for JSON, check it, retry once. Run: python structured_output.py
Without an API key it checks canned replies, so you can see the checking logic work."""
import json
from llm import ask

PROMPT = ('Read the message and answer ONLY with JSON like '
          '{"topic": "returns" | "shipping" | "other", "urgent": true | false}.\nMessage: ')
TOPICS = {"returns", "shipping", "other"}


def parse(text):
    """Return a dict if the reply is valid, else raise ValueError with a reason."""
    try:
        data = json.loads(text.strip().removeprefix("```json").removesuffix("```").strip())
    except json.JSONDecodeError:
        raise ValueError("not JSON")
    if data.get("topic") not in TOPICS or not isinstance(data.get("urgent"), bool):
        raise ValueError(f"wrong fields: {data}")
    return data


def classify(message):
    prompt = PROMPT + message
    for _ in range(2):  # shortcut: one retry only. Log failures and alert if they climb.
        reply = ask(prompt)
        try:
            return parse(reply)
        except ValueError as why:
            prompt += f"\nYour last reply was invalid ({why}). Reply with the JSON only."
    raise ValueError("model never returned valid JSON")


if __name__ == "__main__":
    assert parse('{"topic": "returns", "urgent": false}') == {"topic": "returns", "urgent": False}
    for bad in ["Sure! Here you go", '{"topic": "billing", "urgent": false}', '{"topic": "other"}']:
        try:
            parse(bad)
            raise SystemExit("should have failed: " + bad)
        except ValueError as why:
            print("rejected:", bad[:40], "->", why)
    print("checks passed")
    print(classify("My order never arrived and I need it Friday") if ask("ping", max_tokens=5) else "(no key: skipping live call)")
