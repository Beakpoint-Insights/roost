#!/usr/bin/env bash
# Checks what `claude plugin validate` doesn't: every folder under skills/ has a
# SKILL.md (exact case), its frontmatter `name` matches the folder, and it has a description.
set -euo pipefail

cd "$(dirname "$0")/.."
failed=0

fail() {
  echo "::error file=$1::$2"
  failed=1
}

for dir in skills/*/; do
  skill=$(basename "$dir")
  file="${dir}SKILL.md"

  if [[ ! -f "$file" ]] || ! ls "$dir" | grep -qx 'SKILL.md'; then
    fail "$dir" "skills/$skill has no SKILL.md (the name is case-sensitive)"
    continue
  fi

  if [[ "$(head -n 1 "$file")" != "---" ]]; then
    fail "$file" "$file doesn't start with a frontmatter block (---)"
    continue
  fi

  frontmatter=$(awk 'NR == 1 { next } /^---$/ { exit } { print }' "$file")
  name=$(printf '%s\n' "$frontmatter" | sed -n 's/^name:[[:space:]]*//p' | head -n 1 | tr -d "\"'")
  description=$(printf '%s\n' "$frontmatter" | sed -n 's/^description:[[:space:]]*//p' | head -n 1)

  if [[ "$name" != "$skill" ]]; then
    fail "$file" "$file has name '${name:-<missing>}', but its folder is '$skill'"
  fi
  if [[ -z "$description" ]]; then
    fail "$file" "$file has no description"
  elif [[ "$description" != \"* && "$description" != \'* && "$description" == *": "* ]]; then
    fail "$file" "$file's description has ': ' in an unquoted value, which isn't valid YAML; reword it or quote the value"
  fi
done

if [[ $failed -eq 0 ]]; then
  echo "All skills have a SKILL.md with a matching name and a description."
fi
exit $failed
