#!/usr/bin/env bash

set -Eeuo pipefail


# TODO Check with workflow. I beleave this is not working / correct anymore!
exit 1

function user_confirm {
  prompt="${1:-Are you sure?}"
  printf "%s [n/Y] " "$prompt"
  read -r reply
  if [[ "$reply" =~ ^[Nn]$ ]]; then
    return 1
  fi
  return 0
}

function print_line {
  printf '=%.0s\n' {1..64}
}

FEATURE_BRANCH="${1:?Must provide a feature branch (except the remote name) as first parameter}"
COMMIT_MESSAGE="${2:-"Merge (test) Feature PR: $FEATURE_BRANCH"}"
FEATURE_REMOTE="${FEATURE_REMOTE:-origin}"
GIT_MAX_LOG_LINES="${GIT_MAX_LOG_LINES:-24}"

pr_branch="pr/$FEATURE_BRANCH"
main_branch="main"

echo "Executing Pull Request merge of: '$FEATURE_BRANCH' into '$main_branch'"
git fetch "$FEATURE_REMOTE" "$FEATURE_BRANCH"
git checkout FETCH_HEAD -b "$pr_branch"
git checkout "$main_branch"
git merge --squash "$pr_branch"
git commit -m "$COMMIT_MESSAGE"
print_line

if user_confirm "Do you wan't to run / see some checks?"; then
  echo "Here the current git logs:" 
  git --no-pager log --oneline --graph --all --max-count "$GIT_MAX_LOG_LINES"
  print_line
  echo "And here the diff of the merged commit to the last comit on main:"
  git --no-pager diff "$FEATURE_REMOTE/HEAD" HEAD
  print_line
fi

git branch -D "$pr_branch"
git log --oneline --graph --all --max-count "$GIT_MAX_LOG_LINES"

