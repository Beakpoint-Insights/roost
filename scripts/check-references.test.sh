#!/usr/bin/env bash
# Tests scripts/check-references.py: a copy of the repo passes as it is, and each
# kind of broken reference planted in it is reported.
set -euo pipefail

repo="$(cd "$(dirname "$0")/.." && pwd)"
copy=$(mktemp -d)
trap 'rm -rf "$copy"' EXIT
git -C "$repo" ls-files -z | (cd "$repo" && xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$copy"
cp "$repo/scripts/check-references.py" "$copy/scripts/"
fail=0

if ! out=$(python3 "$copy/scripts/check-references.py" 2>&1); then
  echo "FAIL: the repo as it is was reported:"; echo "$out"; fail=1
fi

cat >> "$copy/skills/run-bug/SKILL.md" <<'MD'

Planted: see `references/phase-3-prototype.md`, use the `run-slices` skill, read
`stack.databse.local`, run `scripts/no-such-script.sh`, and see [the guide](no-such-guide.md).
Also `repos[].apply_gate.plna`, `team.name.typo`, `repos[].e2f` and
`skills/no-such-skill/references/config-schema.md`.
Also `repos[].production.workflw`, next to a correct `repos[].production.workflow`.
Also `release_notes.publshed_url`, next to a correct `release_notes.published_url`.
Also `release_notes.voic`, next to a correct `release_notes.voice`.
MD
cat > "$copy/evals/update-moving/graders/planted.md" <<'MD'
---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?no-such-skill"'
---
MD

out=$(python3 "$copy/scripts/check-references.py" 2>&1) && { echo "FAIL: planted references passed"; fail=1; }
for want in "reference file that doesn't exist: references/phase-3-prototype.md" \
            "skill that doesn't exist: run-slices" \
            "config key that isn't in config-schema.md: stack.databse.local" \
            "path that doesn't exist: scripts/no-such-script.sh" \
            "links to a file that doesn't exist: no-such-guide.md" \
            "grader expects a skill that doesn't exist: no-such-skill" \
            "config key that isn't in config-schema.md: repos[].apply_gate.plna" \
            "config key that isn't in config-schema.md: team.name.typo" \
            "config key that isn't in config-schema.md: repos[].e2f" \
            "reference file that doesn't exist: skills/no-such-skill/references/config-schema.md" \
            "config key that isn't in config-schema.md: repos[].production.workflw" \
            "config key that isn't in config-schema.md: release_notes.publshed_url" \
            "config key that isn't in config-schema.md: release_notes.voic"; do
  if ! grep -q -F "$want" <<<"$out"; then echo "FAIL: expected '$want' in:"; echo "$out"; fail=1; fi
done
if grep -q -F ": repos[].production.workflow" <<<"$out"; then
  echo "FAIL: a documented key was reported: repos[].production.workflow"; echo "$out"; fail=1
fi
if grep -q -F ": release_notes.published_url" <<<"$out"; then
  echo "FAIL: a documented key was reported: release_notes.published_url"; echo "$out"; fail=1
fi
if grep -q -F ": release_notes.voice" <<<"$out"; then
  echo "FAIL: a documented key was reported: release_notes.voice"; echo "$out"; fail=1
fi

[[ $fail -eq 0 ]] && echo "check-references: all tests pass"
exit $fail
