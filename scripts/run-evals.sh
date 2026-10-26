#!/usr/bin/env bash
# Runs eval cases the way CI does: on Opus, judged by Sonnet, up to four cases at once, each case
# retried once if it fails (the judges get a few verdicts wrong, so a case fails
# only if it fails twice). Results go to eval-json/ (a retried case's first try
# to eval-json/first-try/) and each case's output to eval-logs/.
#
# Usage: scripts/run-evals.sh <runs per case> <case>...
#   MAX_COST_USD (environment, optional) caps each attempt of each case.
set -uo pipefail

export RUNS=$1
shift
mkdir -p eval-json/first-try eval-logs

run_case() {
  local c=$1
  local args=(--no-publish --trust-plugin --model opus --judge-model sonnet --ablation none --runs "$RUNS" --case "$c")
  if [[ -n "${MAX_COST_USD:-}" ]]; then args+=(--max-cost-usd "$MAX_COST_USD"); fi

  if claude plugin eval . "${args[@]}" --json "eval-json/$c.json" > "eval-logs/$c.log" 2>&1; then
    echo "✓ $c"
    return 0
  fi
  echo "::notice::$c failed; running it once more"
  # A run that failed before writing results (at sign-in, say) has none to keep.
  if [[ -f "eval-json/$c.json" ]]; then mv "eval-json/$c.json" "eval-json/first-try/$c.json"; fi
  if claude plugin eval . "${args[@]}" --json "eval-json/$c.json" >> "eval-logs/$c.log" 2>&1; then
    echo "✓ $c (second try)"
    return 0
  fi
  echo "✗ $c"
  return 1
}
export -f run_case

# xargs exits non-zero if any case failed both tries.
printf '%s\n' "$@" | xargs -P 4 -I{} bash -c 'run_case "$1"' _ {}
