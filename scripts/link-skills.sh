#!/usr/bin/env bash
# Links each roost skill into another tool's skills folder, so tools that read
# SKILL.md folders (Cursor, Codex and others) can use them. Links follow this
# clone, so `git pull` here updates the skills everywhere.
#
# Usage: scripts/link-skills.sh [target-dir]    (default: ~/.cursor/skills)
#        scripts/link-skills.sh --remove [target-dir]
set -euo pipefail

remove=false
if [[ "${1:-}" == "--remove" ]]; then
  remove=true
  shift
fi
target="${1:-$HOME/.cursor/skills}"
repo="$(cd "$(dirname "$0")/.." && pwd)"

mkdir -p "$target"
for dir in "$repo"/skills/*/; do
  skill=$(basename "$dir")
  link="$target/$skill"
  if $remove; then
    if [[ -L "$link" && "$(readlink "$link")" == "$repo/skills/$skill" ]]; then
      rm "$link"
      echo "Removed $link"
    fi
    continue
  fi
  if [[ -L "$link" ]]; then
    ln -sfn "$repo/skills/$skill" "$link"
    echo "Updated $link"
  elif [[ -e "$link" ]]; then
    echo "Skipped $link: something that isn't a link is already there. Move it, then run this again." >&2
  else
    ln -s "$repo/skills/$skill" "$link"
    echo "Linked $link"
  fi
done
