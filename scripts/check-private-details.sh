#!/usr/bin/env bash
# Fails if a PR adds any string from a private list: a team's tracker site, IDs,
# hostnames and other details that belong in its own config, never in roost.
# It says where each one is (file and line, commit, PR title or body) and which
# entry of the list matched, by number, but never prints the string itself.
#
# Usage: scripts/check-private-details.sh <patterns-file> <base-sha> <head-sha>
#   <patterns-file>  one string per line (fixed strings, matched case-insensitively)
#   PR_TITLE, PR_BODY (environment, optional) are checked too.
set -euo pipefail

patterns_file=$1
base=$2
head=$3

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# Each added line of the diff, as "file:line" in one file and its text in another,
# so a match can be reported by place without its text.
git diff -U0 --no-color "$base...$head" | awk -v loc="$work/where" -v txt="$work/added" '
  /^\+\+\+ / { file = substr($0, 7); next }
  /^@@ / {
    split($3, a, ",")
    line = substr(a[1], 2) + 0
    next
  }
  /^\+/ { print file ":" line > loc; print substr($0, 2) > txt; line++ }
'
touch "$work/where" "$work/added"

git log --format='%h' "$base..$head" > "$work/commits"
printf '%s\n' "${PR_TITLE:-}" > "$work/title"
printf '%s\n' "${PR_BODY:-}" > "$work/body"

found=0
n=0
while IFS= read -r pattern || [[ -n "$pattern" ]]; do
  [[ -z "$pattern" ]] && continue
  n=$((n + 1))

  while IFS= read -r hit; do
    echo "::error file=${hit%%:*},line=${hit##*:}::Adds private entry #$n from the forbidden list at $hit"
    found=1
  done < <(grep -n -i -F -e "$pattern" "$work/added" | cut -d: -f1 | while read -r i; do sed -n "${i}p" "$work/where"; done)

  while IFS= read -r commit; do
    if git log -1 --format='%B' "$commit" | grep -q -i -F -e "$pattern"; then
      echo "::error::Commit $commit's message has private entry #$n from the forbidden list"
      found=1
    fi
  done < "$work/commits"

  for part in title body; do
    if grep -q -i -F -e "$pattern" "$work/$part"; then
      echo "::error::The PR $part has private entry #$n from the forbidden list"
      found=1
    fi
  done
done < "$patterns_file"

if [[ $found -eq 1 ]]; then
  echo "This PR adds details that belong in a team's own config, not in roost. Remove them; the entry numbers say which list line matched."
  exit 1
fi
echo "No private details found ($n entries checked)."
