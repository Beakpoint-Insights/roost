#!/usr/bin/env bash
# Prints the eval cases a change should run, one name per line.
#
# Usage: scripts/eval-cases.sh --all
#        scripts/eval-cases.sh <base-sha> <head-sha>
#
# A change to roost-config, the example config or the plugin manifest can change
# every skill's behaviour, so it runs every case. A change to skills/<name>/ runs
# the cases tagged <name>. A change to evals/<case>/ runs that case.
set -euo pipefail

cd "$(dirname "$0")/.."

all_cases() {
  for f in evals/*/prompt.md; do basename "$(dirname "$f")"; done
}

# The cases whose front-matter tags include $1.
cases_tagged() {
  for f in evals/*/prompt.md; do
    if awk 'NR == 1 { next } /^---$/ { exit } /^tags:/ { print }' "$f" | grep -q -E "[[, ]$1[], ]"; then
      basename "$(dirname "$f")"
    fi
  done
}

if [[ "${1:-}" == "--all" ]]; then
  all_cases
  exit 0
fi

base=$1
head=$2

git diff --name-only "$base...$head" | while IFS= read -r path; do
  case "$path" in
    skills/roost-config/*|examples/config.example.yml|.claude-plugin/*)
      all_cases ;;
    skills/*/*)
      skill=${path#skills/}
      cases_tagged "${skill%%/*}" ;;
    evals/results/*) ;;
    evals/*/*)
      case_dir=${path#evals/}
      case_dir=${case_dir%%/*}
      # A deleted case has nothing to run.
      if [[ -f "evals/$case_dir/prompt.md" ]]; then echo "$case_dir"; fi ;;
  esac
done | sort -u
