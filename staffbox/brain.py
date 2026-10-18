"""Read, check and search a Staffbox brain: a folder of Markdown notes with frontmatter and [[links]].

Standard library only, so it runs on a fresh Mac mini with the system Python.
"""
import datetime, math, pathlib, re, subprocess
from dataclasses import dataclass, field

TYPES = {"index", "company", "sop", "policy", "reference", "person", "log", "note"}
REQUIRED = ("type", "owner", "updated", "source")
LINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
WORD = re.compile(r"[a-z0-9$%.]+")
STOP = set("a an and are as at be by can do does for from how i in is it me my of on or our the this to we what when where which who why will with you your".split())


@dataclass
class Note:
    path: pathlib.Path
    name: str
    meta: dict
    body: str
    links: list = field(default_factory=list)

    def text(self, root):
        return f"=== note: {self.path.relative_to(root)} ===\n{self.body.strip()}\n"


def parse_frontmatter(raw):
    """Small YAML subset: `key: value`, `key: [a, b]` and the block list Obsidian writes
    (`key:` then `  - a` lines). Returns (meta, body, error)."""
    if not raw.startswith("---\n"):
        return {}, raw, "no frontmatter"
    end = raw.find("\n---", 4)
    if end < 0:
        return {}, raw, "frontmatter not closed"
    meta, block = {}, None  # block = key whose value is a `  - item` list
    for line in raw[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if block and line.lstrip().startswith("- "):
            meta[block] = (meta[block] or []) + [line.lstrip()[2:].strip()]
            continue
        if ":" not in line:
            return meta, raw[end + 4:], f"bad frontmatter line: {line!r}"
        k, v = line.split(":", 1)
        v = v.strip()
        block = k.strip() if not v else None
        meta[k.strip()] = [x.strip() for x in v[1:-1].split(",") if x.strip()] if v.startswith("[") and v.endswith("]") else v
    return meta, raw[end + 4:].lstrip("\n"), None


def load(root):
    root = pathlib.Path(root)
    notes, errors = {}, []
    for p in sorted(root.rglob("*.md")):
        if any(part.startswith(".") for part in p.relative_to(root).parts):
            continue
        meta, body, err = parse_frontmatter(p.read_text(encoding="utf-8"))
        if err:
            errors.append(f"{p.relative_to(root)}: {err}")
        n = Note(p, p.stem, meta, body, [l.strip() for l in LINK.findall(body)])
        if n.name.lower() in notes:
            errors.append(f"{p.relative_to(root)}: duplicate note name {n.name!r} (links would be ambiguous)")
        notes[n.name.lower()] = n
    return notes, errors


def check(root, today=None):
    """Return a list of problems. Empty list = the brain is healthy."""
    root = pathlib.Path(root)
    today = today or datetime.date.today()
    notes, problems = load(root)
    if "company" not in notes:
        problems.append("missing company.md (the worker reads it before every task)")
    if "log" not in notes:
        problems.append("missing log.md (the worker appends one line per task)")
    for n in notes.values():
        rel = n.path.relative_to(root)
        if not n.meta:
            continue
        for k in REQUIRED:
            if not n.meta.get(k):
                problems.append(f"{rel}: frontmatter missing '{k}'")
        t = n.meta.get("type")
        if t and t not in TYPES:
            problems.append(f"{rel}: type '{t}' is not one of {sorted(TYPES)}")
        u = n.meta.get("updated")
        if u:
            try:
                if datetime.date.fromisoformat(u) > today:
                    problems.append(f"{rel}: updated {u} is in the future")
            except ValueError:
                problems.append(f"{rel}: updated '{u}' is not YYYY-MM-DD")
        for l in n.links:
            if l.lower() not in notes:
                problems.append(f"{rel}: broken link [[{l}]]")
    problems += check_log_append_only(root)
    return problems


def check_log_append_only(root):
    """If the vault is in git, log.md may only grow: the committed text must be a prefix of the current text."""
    log = pathlib.Path(root) / "log.md"
    if not log.exists():
        return []
    try:
        top = subprocess.run(["git", "-C", str(log.parent), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip()
        rel = log.resolve().relative_to(pathlib.Path(top).resolve())
        old = subprocess.run(["git", "-C", top, "show", f"HEAD:{rel}"], capture_output=True, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return []
    if old.returncode != 0:
        return []  # not committed yet
    if not log.read_text(encoding="utf-8").startswith(old.stdout):
        return [f"log.md: an existing line was changed or removed (the log is append-only; restore with `git checkout HEAD -- {rel}` and append instead)"]
    return []


def append_log(root, asked, did, could_not="nothing", now=None):
    now = now or datetime.datetime.now()
    clean = lambda s: " ".join(str(s).split()).replace("·", "-")
    line = f"- {now:%Y-%m-%d %H:%M} · {clean(asked)} · {clean(did)} · {clean(could_not)}\n"
    log = pathlib.Path(root) / "log.md"
    text = log.read_text(encoding="utf-8")
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(("" if text.endswith("\n") else "\n") + line)
    return line


def words(s):
    return [w.strip(".") for w in WORD.findall(s.lower()) if w.strip(".") and w.strip(".") not in STOP]


def search(notes, question, k=4):
    """BM25 over body, with title, aliases and tags weighted x3. Returns notes ranked, best first."""
    q = set(words(question))
    docs = {}
    for key, n in notes.items():
        head = " ".join([n.name.replace("-", " ")] + list(_aslist(n.meta.get("aliases"))) + list(_aslist(n.meta.get("tags"))))
        docs[key] = words(head) * 3 + words(n.body)
    N = len(docs) or 1
    avg = sum(len(d) for d in docs.values()) / N or 1
    df = {w: sum(1 for d in docs.values() if w in d) for w in q}
    scores = {}
    for key, d in docs.items():
        s = 0.0
        for w in q:
            tf = d.count(w)
            if tf:
                idf = math.log(1 + (N - df[w] + 0.5) / (df[w] + 0.5))
                s += idf * tf * 2.2 / (tf + 1.2 * (0.25 + 0.75 * len(d) / avg))
        if s > 0:
            scores[key] = s
    return [notes[key] for key in sorted(scores, key=scores.get, reverse=True)[:k]]


def context(root, question, k=4, budget=12000):
    """The text the worker reads before it answers: company.md, the top-k notes, and notes the best hit links to."""
    root = pathlib.Path(root)
    notes, _ = load(root)
    picked = []
    if "company" in notes:
        picked.append(notes["company"])
    hits = [n for n in search(notes, question, k) if n.meta.get("type") not in ("log", "index")]
    for n in hits:
        if n not in picked:
            picked.append(n)
    if hits:
        for l in hits[0].links:
            n = notes.get(l.lower())
            if n and n not in picked and n.meta.get("type") not in ("log", "index"):
                picked.append(n)
    out, used = [], 0
    for n in picked:
        t = n.text(root)
        if used + len(t) > budget:
            break
        out.append(t)
        used += len(t)
    return "\n".join(out), [str(n.path.relative_to(root)) for n in picked[: len(out)]]


def _aslist(v):
    return v if isinstance(v, list) else ([v] if v else [])
