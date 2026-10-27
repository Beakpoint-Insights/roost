#!/usr/bin/env bash
# Tests scripts/eval-cases.sh against a throwaway git repo with three made-up
# cases: a change to each kind of file selects the cases it can affect.
set -euo pipefail

script="$(cd "$(dirname "$0")" && pwd)/eval-cases.sh"
repo=$(mktemp -d)
trap 'rm -rf "$repo"' EXIT
cd "$repo"
mkdir -p scripts examples skills/close-out-epic
cp "$script" scripts/
fail=0

case_with() { # <name> <tags> <prompt text>
  mkdir -p "evals/$1"
  printf -- '---\ndescription: A test case.\ntags: [%s]\n---\n\n%s\n' "$2" "$3" > "evals/$1/prompt.md"
}
case_with names-github-only roost-config 'Our config is `examples/config.github-only.yml`.'
case_with names-example roost-config 'Our config is `examples/config.example.yml`.'
case_with closes-out close-out-epic 'Our config is `examples/config.example.yml`. Close out PROJ-1.'
case_with writes-notes release-notes 'Draft the release note for PROJ-1.'
echo 'version: 1' > examples/config.example.yml
echo 'version: 1' > examples/config.github-only.yml
echo '# Our voice' > examples/release-notes-voice.md
echo '# Close Out Epic' > skills/close-out-epic/SKILL.md

git init -q
commit() { git add -A; git -c user.name=test -c user.email=test@example.com commit -q -m "$1"; git rev-parse HEAD; }
base=$(commit "base")

expect() { # <what changed> <base> <head> <expected cases, one per line>
  local got
  got=$(scripts/eval-cases.sh "$2" "$3")
  if [[ "$got" != "$4" ]]; then
    echo "FAIL: a change to $1 selected:"; echo "${got:-<nothing>}"; echo "expected:"; echo "$4"; fail=1
  fi
}

echo 'team: { name: Acme }' >> examples/config.github-only.yml
github_only=$(commit "change the GitHub-only example")
expect examples/config.github-only.yml "$base" "$github_only" "names-github-only"

echo 'More.' >> skills/close-out-epic/SKILL.md
skill=$(commit "change a skill")
expect skills/close-out-epic/SKILL.md "$github_only" "$skill" "closes-out"

echo 'team: { name: Acme }' >> examples/config.example.yml
example=$(commit "change the example config")
expect examples/config.example.yml "$skill" "$example" "$(printf 'closes-out\nnames-example\nnames-github-only\nwrites-notes')"

echo 'Sentence case.' >> examples/release-notes-voice.md
voice=$(commit "change the example voice")
expect examples/release-notes-voice.md "$example" "$voice" "writes-notes"

[[ $fail -eq 0 ]] && echo "eval-cases: all tests pass"
exit $fail
