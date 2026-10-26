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

[[ $fail -eq 0 ]] && echo "check-private-details: all tests pass"
exit $fail
