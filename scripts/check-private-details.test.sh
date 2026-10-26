#!/usr/bin/env bash
# Tests scripts/check-private-details.sh against a throwaway git repo, with a
# made-up private value, so the test itself publishes nothing real.
set -euo pipefail

script="$(cd "$(dirname "$0")" && pwd)/check-private-details.sh"
repo=$(mktemp -d)
trap 'rm -rf "$repo"' EXIT
cd "$repo"

git init -q
git -c user.name=test -c user.email=test@example.com commit -q --allow-empty -m "base"
base=$(git rev-parse HEAD)

secret="zz-not-a-real-site.example"
printf 'line one\nline two\n' > clean.md
git add clean.md
git -c user.name=test -c user.email=test@example.com commit -q -m "docs: a clean change"
clean=$(git rev-parse HEAD)

printf 'first\nsecond\nsee https://%s/browse\n' "$secret" > leak.md
git add leak.md
git -c user.name=test -c user.email=test@example.com commit -q -m "docs: mention ZZ-NOT-A-REAL-SITE.example"
leak=$(git rev-parse HEAD)

# An added line that starts with "++" looks like a file header in the diff.
printf '++ %s\n' "$secret" > plusplus.md
git add plusplus.md
git -c user.name=test -c user.email=test@example.com commit -q -m "docs: plus plus"
plusplus=$(git rev-parse HEAD)

# A clean file whose path holds the value, added and then renamed.
git checkout -q "$clean"
printf 'nothing here\n' > "docs-$secret.md"
git add "docs-$secret.md"
git -c user.name=test -c user.email=test@example.com commit -q -m "docs: add a page"
pathadd=$(git rev-parse HEAD)
git mv "docs-$secret.md" "renamed-ZZ-NOT-A-REAL-SITE.example.md"
git -c user.name=test -c user.email=test@example.com commit -q -m "docs: rename a page"
pathrename=$(git rev-parse HEAD)

# A match inside a file whose path also holds the value.
printf 'see %s\n' "$secret" > "renamed-ZZ-NOT-A-REAL-SITE.example.md"
git add -A
git -c user.name=test -c user.email=test@example.com commit -q -m "docs: link"
pathandcontent=$(git rev-parse HEAD)

printf '%s\n\nanother-unused-entry\n' "$secret" > patterns
fail=0

# A clean change passes.
if ! out=$(PR_TITLE="docs: a clean change" PR_BODY="" "$script" patterns "$base" "$clean" 2>&1); then
  echo "FAIL: a clean change was rejected:"; echo "$out"; fail=1
fi

# A change that adds the value fails, and says where.
if out=$(PR_TITLE="docs: fine" PR_BODY="links to $secret" "$script" patterns "$base" "$leak" 2>&1); then
  echo "FAIL: a change adding a private value passed"; fail=1
fi
for want in "leak.md:3" "entry #1" "message has private entry #1" "PR body has private entry #1"; do
  if ! grep -q -F "$want" <<<"$out"; then echo "FAIL: expected '$want' in:"; echo "$out"; fail=1; fi
done
if grep -q -i -F "$secret" <<<"$out"; then
  echo "FAIL: the output prints the private value"; fail=1
fi
if grep -q -F "PR title" <<<"$out"; then
  echo "FAIL: a clean PR title was reported"; fail=1
fi

# Each of these adds the value somewhere a line-by-line scan of file contents misses,
# and none of the output may show it, in any case.
check_fails() {  # <name> <base> <head> <expected text>
  local out
  if out=$(PR_TITLE="docs: fine" PR_BODY="" "$script" patterns "$2" "$3" 2>&1); then
    echo "FAIL ($1): passed"; fail=1
  fi
  if ! grep -q -F "$4" <<<"$out"; then echo "FAIL ($1): expected '$4' in:"; echo "$out"; fail=1; fi
  if grep -q -i -F "$secret" <<<"$out"; then echo "FAIL ($1): the output shows the value"; fail=1; fi
}
check_fails "line starting ++" "$clean" "$plusplus" "plusplus.md:1"
check_fails "added path" "$clean" "$pathadd" "file path added or renamed by this PR"
check_fails "renamed path" "$pathadd" "$pathrename" "file path added or renamed by this PR"
check_fails "match in a file with a forbidden path" "$pathrename" "$pathandcontent" "path withheld"

[[ $fail -eq 0 ]] && echo "check-private-details: all tests pass"
exit $fail
