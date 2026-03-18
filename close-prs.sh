#!/bin/bash
# Script to close unnecessary/old Dependabot PRs
# Run this with a GitHub token: GITHUB_TOKEN=<token> ./close-prs.sh

set -e

REPO="RafflesiaKhan/quick-short-generator"
COMMENT="Closing this PR as part of routine PR cleanup. This dependency update is either \
outdated (superseded by newer versions), a routine/low-priority update, or the security \
patch it addressed was reverted. Security-critical updates are being handled separately."

if [ -z "$GITHUB_TOKEN" ]; then
  echo "Error: Set GITHUB_TOKEN environment variable first"
  echo "Usage: GITHUB_TOKEN=<token> ./close-prs.sh"
  exit 1
fi

# PRs to close (old/unnecessary/low-priority Dependabot updates)
PRS_TO_CLOSE=(14 16 17 21)

# PRs to keep (security-relevant)
# PR #23 - pyjwt security fix (GHSA-752w-5fwx-jx9f)
# PR #22 - minimatch ReDoS fix
# PR #18 - ajv CVE-2025 security fix
# PR #15 - axios DoS fix
# PR #24 - flatted (recent, minor)

for PR in "${PRS_TO_CLOSE[@]}"; do
  echo "Commenting on PR #$PR..."
  curl -s -X POST \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/$REPO/issues/$PR/comments" \
    -d "{\"body\": \"$COMMENT\"}" > /dev/null

  echo "Closing PR #$PR..."
  curl -s -X PATCH \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/$REPO/pulls/$PR" \
    -d '{"state": "closed"}' | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'PR #{PR}: {d.get(\"state\", d.get(\"message\", \"unknown\"))}')"
done

echo "Done!"
