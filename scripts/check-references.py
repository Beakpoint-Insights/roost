#!/usr/bin/env python3
"""Checks that what the skills and docs refer to exists, with no model needed:

- skills named as "the `x` skill" (or "`x` skill"), and in eval graders' input_match;
- files named in backticks: references/*.md, and paths under scripts/, skills/,
  evals/, examples/ and .github/;
- config keys in backticks (`stack.database.local`), against config-schema.md;
- relative Markdown links.

Prints one line per broken reference, as file:line, and exits 1 if there are any.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SKILLS = {os.path.basename(os.path.dirname(p)) for p in glob.glob("skills/*/SKILL.md")}
REFERENCE_FILES = {os.path.basename(p) for p in glob.glob("skills/*/references/*.md")}
SECTIONS = ["team", "tracker", "tests", "repos", "stack", "vcs", "planning", "deploy", "design", "qa", "roadmap"]


def schema_keys():
    """Every key config-schema.md documents, as full dotted paths."""
    keys = set()
    section = None
    for line in open("skills/roost-config/references/config-schema.md"):
        heading = re.match(r"^## `(\w+)`", line)
        if heading:
            section = heading.group(1)
            keys.add(section)
            continue
        if line.startswith("## "):
            section = None
        if section and line.startswith("| `"):
            first_cell = line.split("|")[1]
            names = re.findall(r"`([\w.]+)`", first_cell)
            parent = ""
            for i, name in enumerate(names):
                if i == 0:
                    parent = name.rsplit(".", 1)[0] + "." if "." in name else ""
                    keys.add(f"{section}.{name}")
                else:
                    keys.add(f"{section}.{parent}{name}" if "." not in name else f"{section}.{name}")
    return keys


KEYS = schema_keys()


def key_known(ref):
    ref = ref.replace("[]", "")
    if ref in KEYS:
        return True
    # A sub-key the schema describes in words (e2e.run_tags) under a documented key,
    # never just under a section name, or a parent of documented keys.
    return any((ref.startswith(k + ".") and "." in k) or k.startswith(ref + ".") for k in KEYS)


def documents():
    files = glob.glob("skills/**/*.md", recursive=True) + ["README.md", "CONTRIBUTING.md"]
    files += glob.glob("evals/*/prompt.md") + glob.glob("evals/*/graders/*.md")
    return [f for f in files if os.path.exists(f) and "/results/" not in f]


problems = []


def report(path, lineno, message):
    problems.append(f"{path}:{lineno}: {message}")


for path in documents():
    for lineno, line in enumerate(open(path, encoding="utf-8"), 1):
        # Skills named as skills.
        for name in re.findall(r"`([a-z][a-z0-9-]+)` skill\b", line) + re.findall(r"\bskill `([a-z][a-z0-9-]+)`", line):
            if name not in SKILLS:
                report(path, lineno, f"names a skill that doesn't exist: {name}")
        # Skills an eval grader expects to be called.
        if path.startswith("evals/") and "input_match" in line:
            for name in re.findall(r'\(\?:\[\\w-\]\+:\)\?([a-z][a-z0-9-]+)', line):
                if name not in SKILLS:
                    report(path, lineno, f"grader expects a skill that doesn't exist: {name}")

        for token in re.findall(r"`([^`\s]+)`", line):
            if "<" in token or "*" in token or "{" in token:
                continue
            # Reference files.
            if re.fullmatch(r"(?:[\w-]+/)*references/[\w.-]+\.md", token) or re.fullmatch(r"[\w-]+\.md", token) and token.startswith("phase-"):
                if os.path.basename(token) not in REFERENCE_FILES:
                    report(path, lineno, f"names a reference file that doesn't exist: {token}")
            # Repo paths.
            elif re.match(r"(scripts|skills|evals|examples|\.github)/", token):
                clean = token.rstrip("/.,:;")
                if not os.path.exists(clean) and "results" not in clean:
                    report(path, lineno, f"names a path that doesn't exist: {clean}")
            # Config keys.
            else:
                m = re.fullmatch(r"((?:%s)(?:\[\])?(?:\.[a-z_]+(?:\[\])?)+)" % "|".join(SECTIONS), token)
                if m and not key_known(m.group(1)):
                    report(path, lineno, f"names a config key that isn't in config-schema.md: {m.group(1)}")

        # Relative Markdown links.
        for target in re.findall(r"\]\(([^)\s#]+)(?:#[^)]*)?\)", line):
            if re.match(r"[a-z]+:", target):
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(path), target))
            if not os.path.exists(resolved):
                report(path, lineno, f"links to a file that doesn't exist: {target}")

for p in problems:
    print(p)
if problems:
    print(f"{len(problems)} broken reference(s).")
    sys.exit(1)
print(f"All references resolve ({len(documents())} files, {len(SKILLS)} skills, {len(KEYS)} config keys).")
