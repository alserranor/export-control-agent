"""Answer a question from the control lists, with citations."""
import os, sys
from dotenv import load_dotenv
import anthropic
from agent.search import search

load_dotenv()
MODEL = os.getenv("MODEL", "claude-haiku-4-5")

SYSTEM = """You answer export-control questions using ONLY the control entries provided.
- Cite every claim as [EU 2B001, 2026-09-21] or [US 2B001, eCFR <version>].
- If the decision depends on a parameter the user didn't give, name the parameter and threshold.
- If no entry clearly fits, say so and recommend review by a human export-control officer.
- US entries include licensing details: do not give licensing or destination advice.
- Use the main entry for an item before related entries (e.g. 2B001 before 2B201 or 2B991), and say which list each comes from.
- Only mention entries that apply. If none apply, say "No matching entry found" without listing unrelated entries.
End with: "Not a classification decision. Confirm with your export-control officer.\""""

def ask(question):
    hits = search(question, limit=4)
    context = "\n\n".join(
        f"<entry regime='{e['regime']}' code='{e['code']}' version='{e['version']}'>\n{e['text'][:12000]}\n</entry>"
        for e in hits) or "No matching entries found."
    msg = anthropic.Anthropic().messages.create(
        model=MODEL, max_tokens=800, system=SYSTEM,
        messages=[{"role": "user", "content": f"{context}\n\nQuestion: {question}"}])
    print(msg.content[0].text)
    print(f"\n[retrieved: {', '.join(e['regime'] + ' ' + e['code'] for e in hits)} | "
          f"tokens in/out: {msg.usage.input_tokens}/{msg.usage.output_tokens}]")

if __name__ == "__main__":
    ask(" ".join(sys.argv[1:]))
