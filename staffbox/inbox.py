"""The mailbox door, draft-only by construction: read requests from a folder, write draft replies to another.

There is no sending code in this module and no mail credentials anywhere in Staffbox. A person opens the
drafts folder (or the mail client that syncs it), checks each draft, and sends it.

  staffbox inbox VAULT --in requests/ --drafts drafts/ [--model qwen3:8b]

Each request is a .eml or .txt file. Each draft is a .eml file with the same name, which cites the pricing
notes and their `updated` dates. Processed requests move to requests/done/. Every draft is one line in log.md.
"""
import email, email.policy, pathlib, re
from email.message import EmailMessage
from . import brain, evals

FOOTER = ("\n\n--\nDRAFT written by Staffbox for {company}. A person checks this before it is sent.\n"
          "Sources: {sources}")


def read_request(path):
    raw = path.read_bytes()
    if path.suffix.lower() == ".eml":
        msg = email.message_from_bytes(raw, policy=email.policy.default)
        body = msg.get_body(preferencelist=("plain",))
        text = body.get_content() if body else ""
        return msg.get("From", ""), msg.get("Subject", ""), text
    return "", path.stem.replace("-", " "), raw.decode("utf-8", "replace")


def sources(vault, notes, pricing_only=False):
    """'hardware-price-list.md (updated 2026-09-30)' for the notes behind the answer: pricing notes for a priced
    quote, otherwise the notes the answer read."""
    allnotes, _ = brain.load(vault)
    root = pathlib.Path(vault)
    rows = []
    for n in allnotes.values():
        rel = str(n.path.relative_to(root))
        is_pricing = "pricing" in [t.lower() for t in brain._aslist(n.meta.get("tags"))]
        if (is_pricing if pricing_only else rel in notes):
            rows.append(f"{rel} (updated {n.meta.get('updated', '?')})")
    return "; ".join(sorted(rows)) or "none"


def draft_reply(vault, sender, subject, text, answer, notes, company):
    m = EmailMessage()
    m["To"] = sender
    m["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    m["X-Staffbox-Draft"] = "yes"
    final = evals.final_answer(answer)
    name = (sender.split("<")[0].strip().split() or [""])[0]
    hello = f"Hi {name}," if name else "Hello,"
    if "not in vault" in final.lower():
        reason = final.split(":", 1)[-1].strip()
        body = (f"[NOTE FOR THE REVIEWER, delete before sending: Staffbox did not price this. {reason}]\n\n"
                f"{hello}\n\nThanks for the request. We'll confirm the details and come back to you with a price shortly.")
        cite = sources(vault, notes, pricing_only=True)
    elif "Quote action" in answer:
        lines = [l.strip("- ").rstrip(".") for l in answer.split("ANSWER:")[0].replace("Quote action:", "").splitlines() if l.strip()]
        body = f"{hello}\n\nHere is the quote:\n\n" + "\n".join(f"- {l}" for l in lines) + f"\n\nTotal: {final.split(' (')[0]}"
        cite = sources(vault, notes, pricing_only=True)
    else:
        body = f"{hello}\n\n{final}"
        cite = sources(vault, notes)
    m.set_content(body + FOOTER.format(company=company, sources=cite))
    return m


def run(vault, inbox, drafts, host, model, company, ask=evals.ask, num_ctx=None):
    inbox, drafts = pathlib.Path(inbox), pathlib.Path(drafts)
    drafts.mkdir(parents=True, exist_ok=True)
    (inbox / "done").mkdir(exist_ok=True)
    made = []
    for path in sorted(p for p in inbox.iterdir() if p.suffix.lower() in (".eml", ".txt")):
        sender, subject, text = read_request(path)
        question = re.sub(r"(?m)^>.*$", "", text).strip()  # quoted history is context noise
        answer, notes, _, _ = ask(host, model, vault, question, "brain+quote", company, num_ctx)
        out = drafts / (path.stem + ".eml")
        out.write_bytes(bytes(draft_reply(vault, sender, subject, text, answer, notes, company)))
        path.rename(inbox / "done" / path.name)
        brain.append_log(vault, f"request {path.name}", f"draft {out.name}: {evals.final_answer(answer)[:80]}", "not sent: a person sends")
        made.append(out)
    return made
