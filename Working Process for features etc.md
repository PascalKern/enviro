Git usage for PR merge simulation and creation of a local build to be deployed out of it

# Issue with multiple PR's on forked Github Repo
[Waiting on Multiple GitHub PR Merges](https://softwareengineering.stackexchange.com/questions/378151/waiting-on-multiple-github-pr-merges)  
-> [Mybe good/usefull Answer](https://softwareengineering.stackexchange.com/a/378192/452113)



# Prerequisite (before first feature implemented)
- The forked repo is up to date with the original repo
- Checkout the main branch
- Creat the FIRST (and only the first) feature branch from the main branch ie. voltage_level_sensing
- Implement the feature

# Setup (locally testing / final product when PR's will be merged in the future!)
```shell
git clone -b main --single-branch git@github.com:PascalKern/enviro.git
cd enviro
git remote set-url --push origin DISALOWED
```

# Do PR simulation of the newly implemented feature
## Get and merge a feature ie. current_feature_branch
```shell
git fetch origin my_feature/<current_feature_branch>
git checkout FETCH_HEAD -b pr/<current_feature_branch>
git checkout main
```
HERE I need to magic to find the last branch named merged/ (newly done instead of clean up the pr/ branch!! ToBeImplemented!!!)
    -> maybe: git branch --sort=-committerdate | grep -v main | head -n1 | tr -d '[:blank:]'
THEN get the merge base with git merge-base (found) merged/... (branch) pr/.... (branch)
THEN git checkout pr/... (branche)
THEN git rebase --onto main/last branch before current pr (found) commit-ref <- cmmit-ref is the REAL root of the current feature branch ie. excliuding all already merged commits!
THEN git checkout main

Example with 'my_develop/Improve_and_issueprotection':
```shell
incoming_branch=my_develop/Improve_and_issueprotection
git checkout main
git fetch origin "$incoming_branch"
git checkout FETCH_HEAD -b "pr/$incoming_branch"
last_branch="$(git branch --sort=-committerdate | grep -v pr | grep -v main | head -n 1 | tr -d '[:blank:]')"
# last_branch == the "root" / base of the incomming branch i.e. where the incomming branch was created off
# If the incomming branch did NOT originate from the last merged branch this stepp bellow must be done different / by hand.
# And it will potentially break the later rebasing / merging etc.
commit="$(git merge-base $last_branch "pr/$incoming_branch")"
git rebase --onto "$last_branch" "$commit"
git checkout main
git merge --squash "pr/$incoming_branch"
# --> Resolve potential issues!!! In the most cases the incomming part (theirs) should be ok, but it has to be checked thoroughly
echo "Merge (test) Feature PR: $incoming_branch"
git commit # Add 'Merge (test) Feature PR: $incoming_branch\n\n\n' in front of created message
git branch --move "pr/$incoming_branch" "merged/$incoming_branch"  
```


```shell
git merge --squash pr/<current_feature_branch>
git commit
# Prepend existing message with: 'Merge (test) Feature PR: my_develop/Improve_and_issueprotection\n\n'
```

## Check
```shell
git log --oneline --graph --all
git diff origin/HEAD HEAD
```

## Clean up
```shell
git branch -D pr/<current_feature_branch>
git log --oneline --graph --all
```

### A script that does "it all"
```shell
#!/usr/bin/env bash

set -Eeuo pipefail

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
```


# Deploy on device
- The local simulated PR result repo has it's git HEAD (of the main branch) in the state which should be used
  for the deployment. Here also the Version and other infos can be added / improved   
  **But be Carefully** Changes should only be done in additional files (ie. Version etc.) and kept locally. 
**TODO** Figure out a way to handle the version in constants.py ie. to be able to increase it for each added feature?
OR Just add another version (somehow) and (or) even better the git rev to know which state is installed on the devices!

# Continue work on features / next feature
- Go back to forked repo (forked_enviro)
- Checkout the last feature branch
- Create a new feature branch from the LAST (always us the last feature branch ie. stack the feature 
  branches on each other) merged (PR merge simulation locally) feature branch
- When done do simulate the PR again locally ([Do PR simulation of the newly implemented feature](#Do PR simulation of the newly implemented feature))

# When fork get's changes
TO BE EVALUATED / TESTED! 
- Rebase all features on the changes on the updated (from the original) main branch.
  -> Only the first feature to be rebased or all?!

## One solution would be:
1. Have a list of all feature branches ordered by their creation date. The order is important!
2. checkout main, pull incoming changes etc.
3. `git rebase [--committer-date-is-author-date] master branch_list[0]` (hopefully no issues! else resolve them)
4. `git rebase [--committer-date-is-author-date] branch_list[0] branch_list[1]` (hopefully no issues! else resolve them)
   Repeat above step (4.) until end of branch list. If no issues arise in step 3. step 4. may be done in a iteration? 
### Sources with potential solutions and more infos
- [Rebasing a tree (a commit/branch and all its children) \[duplicate\]](https://stackoverflow.com/questions/17315285/rebasing-a-tree-a-commit-branch-and-all-its-children)
  Especially this answer: https://stackoverflow.com/a/45844847/5230043 (even when in the end the checkout, reset/delete part is to be figured out. Most 
  likely checkout the merge commits for each branch and reset the specific branch head from there to the last commit it was before the merge to the pack!?)
  **OR** Check this answer (referenced above) from another question: https://stackoverflow.com/questions/14504029/git-rebase-subtree/69396585#69396585 and the related
  tool [git move](https://github.com/arxanas/git-branchless/wiki/Command:-git-move) from [git-branchless](https://github.com/arxanas/git-branchless) (`brew install git-branchless`) might be the 
  best solution?
- My solution is somehow this here: https://stackoverflow.com/a/5632027/5230043 but more manually! :)