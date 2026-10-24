#!/usr/bin/env python3
"""Backlog tool for the Citi Bike Fabric project. Standard library only.

Usage:
  python3 tools/backlog.py check
  python3 tools/backlog.py next [--all]
  python3 tools/backlog.py show T013
  python3 tools/backlog.py set T013 doing
  python3 tools/backlog.py set T013 done --result "one line"
  python3 tools/backlog.py summary
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKLOG = ROOT / "backlog"

EPIC_RE = re.compile(r"^# (EP\d{2}) · (.+)$")
FEATURE_RE = re.compile(r"^## (FT\d{2}) · (.+)$")
STORY_RE = re.compile(r"^### (US\d{3}) · (.+)$")
TASK_RE = re.compile(r"^#### (T\d{3}) · (.+)$")
FIELD_RE = re.compile(r"^- \*\*([A-Za-z0-9 -]+):\*\* ?(.*)$")
RESULT_RE = re.compile(r"^\*\*Result:\*\* ?(.*)$")

REQUIRED = ["Story", "ADO", "Owner", "Model", "Estimate", "Sprint", "Depends on", "DP-700", "Status", "Read first"]
STATUSES = {"todo", "doing", "done", "blocked"}
MODELS = {"Sonnet", "Haiku", "Opus"}
OWNERS = ("Bharat builds", "Claude builds", "Claude writes, Bharat runs")


@dataclass
class Task:
    id: str
    title: str
    file: Path
    start: int  # line index of the heading
    end: int  # line index after the card
    epic: str
    feature: str
    story: str
    fields: dict = field(default_factory=dict)
    result: str = ""

    @property
    def deps(self) -> list[str]:
        raw = self.fields.get("Depends on", "").strip()
        if raw in ("", "—", "-"):
            return []
        return [d.strip() for d in raw.split(",") if d.strip()]

    @property
    def minutes(self) -> int:
        m = re.match(r"(\d+)\s*min", self.fields.get("Estimate", ""))
        return int(m.group(1)) if m else 0

    @property
    def sprint(self) -> int:
        try:
            return int(self.fields.get("Sprint", "99"))
        except ValueError:
            return 99


def load():
    epics, features, stories, tasks = {}, {}, {}, {}
    problems = []
    for path in sorted(BACKLOG.glob("EP*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        epic = feature = story = None
        current = None
        for i, line in enumerate(lines):
            if m := EPIC_RE.match(line):
                epic = m.group(1)
                if epic in epics:
                    problems.append(f"duplicate epic {epic}")
                epics[epic] = {"title": m.group(2), "file": path}
                if not path.name.startswith(epic):
                    problems.append(f"{path.name}: file name does not start with {epic}")
                continue
            if m := FEATURE_RE.match(line):
                feature = m.group(1)
                if feature in features:
                    problems.append(f"duplicate feature {feature}")
                features[feature] = {"title": m.group(2), "epic": epic}
                continue
            if m := STORY_RE.match(line):
                story = m.group(1)
                if story in stories:
                    problems.append(f"duplicate story {story}")
                stories[story] = {"title": m.group(2), "feature": feature, "epic": epic}
                continue
            if m := TASK_RE.match(line):
                if current:
                    current.end = i
                tid = m.group(1)
                if tid in tasks:
                    problems.append(f"duplicate task {tid}")
                current = Task(tid, m.group(2), path, i, len(lines), epic, feature, story)
                tasks[tid] = current
                continue
            if current is not None:
                if line.startswith("## ") or line.startswith("### ") or line.startswith("# "):
                    current.end = i
                    current = None
                    continue
                if m := FIELD_RE.match(line):
                    current.fields.setdefault(m.group(1), m.group(2).strip())
                elif m := RESULT_RE.match(line):
                    current.result = m.group(1).strip()
        if current:
            current.end = len(lines)
    return epics, features, stories, tasks, problems


def card_lines(t: Task) -> list[str]:
    return t.file.read_text(encoding="utf-8").splitlines()[t.start:t.end]


def cmd_check(_args) -> int:
    epics, features, stories, tasks, problems = load()
    for tid, t in tasks.items():
        for f in REQUIRED:
            if f not in t.fields:
                problems.append(f"{tid}: missing field '{f}'")
        if t.fields.get("Story") != t.story:
            problems.append(f"{tid}: Story field '{t.fields.get('Story')}' but card sits under {t.story}")
        if t.fields.get("Status") not in STATUSES:
            problems.append(f"{tid}: bad status '{t.fields.get('Status')}'")
        if t.fields.get("Model") not in MODELS:
            problems.append(f"{tid}: bad model '{t.fields.get('Model')}'")
        if not t.fields.get("Owner", "").startswith(OWNERS):
            problems.append(f"{tid}: bad owner '{t.fields.get('Owner')}'")
        if not re.fullmatch(r"#\d+", t.fields.get("ADO", "")):
            problems.append(f"{tid}: ADO must look like '#9' (the Azure Boards work item id)")
        if t.minutes <= 0:
            problems.append(f"{tid}: estimate must look like '45 min'")
        if t.sprint == 99:
            problems.append(f"{tid}: sprint must be a number")
        for d in t.deps:
            if d not in tasks:
                problems.append(f"{tid}: depends on unknown {d}")
            elif tasks[d].sprint > t.sprint:
                problems.append(f"{tid} (sprint {t.sprint}) depends on {d} in a later sprint ({tasks[d].sprint})")
        text = "\n".join(card_lines(t))
        if "**Do**" not in text or "**Acceptance**" not in text:
            problems.append(f"{tid}: needs **Do** and **Acceptance** sections")
        if "**Result:**" not in text:
            problems.append(f"{tid}: needs a **Result:** line")
        if t.fields.get("Status") == "done":
            if "- [ ]" in text:
                problems.append(f"{tid}: done but has unticked acceptance boxes")
            if t.result in ("", "—"):
                problems.append(f"{tid}: done but Result line is empty")
    seen_ado = {}
    for tid, t in tasks.items():
        a = t.fields.get("ADO")
        if a and a in seen_ado:
            problems.append(f"{tid}: ADO {a} already used by {seen_ado[a]}")
        seen_ado.setdefault(a, tid)
    for sid, s in stories.items():
        if not any(t.story == sid for t in tasks.values()):
            problems.append(f"{sid}: story has no tasks")
    for fid in features:
        if not any(s["feature"] == fid for s in stories.values()):
            problems.append(f"{fid}: feature has no stories")
    # cycles
    state = {}

    def visit(n, stack):
        if state.get(n) == 1:
            problems.append("dependency cycle: " + " -> ".join(stack + [n]))
            return
        if state.get(n) == 2 or n not in tasks:
            return
        state[n] = 1
        for d in tasks[n].deps:
            visit(d, stack + [n])
        state[n] = 2

    for n in tasks:
        visit(n, [])
    if problems:
        print("FAIL")
        for p in problems:
            print(" -", p)
        return 1
    print(f"PASS: {len(epics)} epics, {len(features)} features, {len(stories)} stories, {len(tasks)} tasks")
    return 0


def cmd_next(args) -> int:
    _, _, _, tasks, _ = load()
    ready = []
    for t in tasks.values():
        if t.fields.get("Status") not in ("todo", "doing"):
            continue
        if all(tasks[d].fields.get("Status") == "done" for d in t.deps if d in tasks):
            ready.append(t)
    ready.sort(key=lambda t: (t.sprint, t.id))
    if not ready:
        print("Nothing is ready.")
        return 0
    shown = ready if args.all else ready[:8]
    for t in shown:
        mark = " (in progress)" if t.fields.get("Status") == "doing" else ""
        print(f"{t.id}  {t.fields.get('ADO', ''):5}  sprint {t.sprint}  {t.fields.get('Model'):6}  {t.minutes:>3} min  {t.title}{mark}")
    if len(ready) > len(shown):
        print(f"... {len(ready) - len(shown)} more ready (use --all)")
    return 0


def cmd_show(args) -> int:
    epics, features, stories, tasks, _ = load()
    t = tasks.get(args.id)
    if not t:
        print(f"No task {args.id}")
        return 1
    print(f"{t.epic} · {epics[t.epic]['title']}")
    print(f"  {t.feature} · {features[t.feature]['title']}")
    print(f"    {t.story} · {stories[t.story]['title']}")
    print(f"File: {t.file.relative_to(ROOT)}")
    print(f"Commit message: {t.id}: <summary> AB{t.fields.get('ADO', '#?')}  (then close the item in Azure Boards: protocol step 11)\n")
    print("\n".join(card_lines(t)))
    open_deps = [d for d in t.deps if tasks.get(d) and tasks[d].fields.get("Status") != "done"]
    if open_deps:
        print("\nWARNING: not ready. Unfinished dependencies: " +
              ", ".join(f"{d} ({tasks[d].fields.get('Status')})" for d in open_deps))
    return 0


def cmd_set(args) -> int:
    if args.status not in STATUSES:
        print(f"Status must be one of {sorted(STATUSES)}")
        return 1
    _, _, _, tasks, _ = load()
    t = tasks.get(args.id)
    if not t:
        print(f"No task {args.id}")
        return 1
    lines = t.file.read_text(encoding="utf-8").splitlines()
    changed_status = changed_result = False
    for i in range(t.start, t.end):
        if lines[i].startswith("- **Status:**"):
            lines[i] = f"- **Status:** {args.status}"
            changed_status = True
        elif args.result is not None and RESULT_RE.match(lines[i]):
            lines[i] = f"**Result:** {args.result}"
            changed_result = True
    if args.status == "done":
        for i in range(t.start, t.end):
            if lines[i].startswith("- [ ]") and args.tick:
                lines[i] = "- [x]" + lines[i][5:]
    t.file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{t.id}: status -> {args.status}" + (" ; result written" if changed_result else ""))
    if not changed_status:
        print("warning: no Status line found")
    return 0


def cmd_summary(_args) -> int:
    epics, _, _, tasks, _ = load()
    print(f"{'Epic':6} {'Tasks':>5} {'Done':>5} {'Hours':>6} {'Bharat h':>8}  Title")
    for eid, e in epics.items():
        ts = [t for t in tasks.values() if t.epic == eid]
        done = sum(1 for t in ts if t.fields.get("Status") == "done")
        hrs = sum(t.minutes for t in ts) / 60
        bh = sum(t.minutes for t in ts if not t.fields.get("Owner", "").startswith("Claude builds")) / 60
        print(f"{eid:6} {len(ts):>5} {done:>5} {hrs:>6.1f} {bh:>8.1f}  {e['title']}")
    print()
    print(f"{'Sprint':6} {'Tasks':>5} {'Done':>5} {'Hours':>6} {'Bharat h':>8}")
    for sp in sorted({t.sprint for t in tasks.values()}):
        ts = [t for t in tasks.values() if t.sprint == sp]
        done = sum(1 for t in ts if t.fields.get("Status") == "done")
        hrs = sum(t.minutes for t in ts) / 60
        bh = sum(t.minutes for t in ts if not t.fields.get("Owner", "").startswith("Claude builds")) / 60
        print(f"{sp:<6} {len(ts):>5} {done:>5} {hrs:>6.1f} {bh:>8.1f}")
    total = sum(t.minutes for t in tasks.values()) / 60
    print(f"\nTotal: {len(tasks)} tasks, {total:.1f} hours")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    n = sub.add_parser("next")
    n.add_argument("--all", action="store_true")
    s = sub.add_parser("show")
    s.add_argument("id")
    st = sub.add_parser("set")
    st.add_argument("id")
    st.add_argument("status")
    st.add_argument("--result")
    st.add_argument("--tick", action="store_true", help="tick every acceptance box (only after checking each one)")
    sub.add_parser("summary")
    args = p.parse_args()
    return {"check": cmd_check, "next": cmd_next, "show": cmd_show, "set": cmd_set, "summary": cmd_summary}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
