#!/usr/bin/env bash
# merge_and_push_agent.sh
# Reusable script to fetch from a local repo, show diffs, merge incoming/main into a target
# local repo or GitHub repo slug (resolving conflicts by taking incoming versions), and push to GitHub over SSH.
#
# Usage:
#   ./scripts/merge_and_push_agent.sh --incoming /path/to/incoming-repo --target /path/to/target-repo-or-owner/repo [options]
#
# Example:
#   ./scripts/merge_and_push_agent.sh --incoming /Users/mfmora/Downloads/synapxi-tech \
#       --target /Users/mfmora/Documents/GitHub/synapxi-tech-website --branch main
#
# By default the script:
# - Uses remote name "incoming-synapxi" for the incoming repo (can be changed with --remote-name)
# - Shows diffs (log, name-status, diff stat)
# - Creates a backup branch of the target branch before merging
# - Merges incoming branch into target branch using --allow-unrelated-histories
# - If merge conflicts occur, resolves them automatically by taking the incoming repo's versions
# - Attempts to push to origin; if push fails due to SSH auth it will ask for your private
#   key passphrase and create a temporary passphrase-free copy of the key to perform the push.
#
# Options:
#   --incoming PATH       Path to the incoming (source) git repository (required)
#   --target PATH|REPO    Target local git repo path, GitHub slug (owner/repo), or GitHub URL (required)
#   --branch BRANCH       Branch name to merge (default: main)
#   --remote-name NAME    Remote name to add for incoming repo (default: incoming-synapxi)
#   --ssh-key PATH        Private SSH key path to try when pushing (default: ~/.ssh/id_ed25519)
#   --keep-remote         Keep the incoming remote after the script finishes (default: removed)
#   --no-push             Do everything except push the resulting branch (dry-run push)
#   --no-auto-theirs      If set, keep "ours" (target) versions when resolving conflicts
#   --help                Show this help
#
# Notes:
# - The script will attempt to push to the repository's origin. If origin is an HTTPS URL,
#   the script will translate it into the canonical SSH form (git@github.com:owner/repo.git)
#   and attempt to push via SSH.
# - The temporary passphrase-free key (if created) is removed after use.
# - The script disables GPG signing for automatic conflict-resolution commits (to avoid failures
#   when a signing key is not available).

set -euo pipefail
IFS=$'\n\t'

PROG_NAME=$(basename "$0")

print_usage() {
  cat <<EOF
Usage: $PROG_NAME --incoming /path/to/incoming --target /path/to/target-or-owner/repo [options]

Required:
  --incoming PATH       Path to the incoming git repo (source)
  --target PATH|REPO    Target local git repo path, GitHub slug (owner/repo), or GitHub URL

Options:
  --branch BRANCH       Branch to merge (default: main)
  --remote-name NAME    Remote name for incoming repo (default: incoming-synapxi)
  --ssh-key PATH        Private SSH key to use when asked (default: ~/.ssh/id_ed25519)
  --keep-remote         Don't remove the incoming remote after the run
  --no-push             Don't attempt to push the resulting branch (dry run)
  --no-auto-theirs      Keep target versions for conflicted files (default: take incoming)
  --help                Show this help
EOF
}

# Defaults
BRANCH="main"
REMOTE_NAME="incoming-awe"
SSH_KEY="$HOME/.ssh/id_ed25519"
KEEP_REMOTE=false
DO_PUSH=true
AUTO_THEIRS=true

# Parse args
if [ $# -eq 0 ]; then
  print_usage
  exit 1
fi

while [ $# -gt 0 ]; do
  case "$1" in
    --incoming)
      INCOMING_PATH="$2"; shift 2;;
    --target)
      TARGET_PATH="$2"; shift 2;;
    --branch)
      BRANCH="$2"; shift 2;;
    --remote-name)
      REMOTE_NAME="$2"; shift 2;;
    --ssh-key)
      SSH_KEY="$2"; shift 2;;
    --keep-remote)
      KEEP_REMOTE=true; shift;;
    --no-push)
      DO_PUSH=false; shift;;
    --no-auto-theirs)
      AUTO_THEIRS=false; shift;;
    --help)
      print_usage; exit 0;;
    *)
      echo "Unknown argument: $1" >&2; print_usage; exit 1;;
  esac
done

# Validate required args
if [ -z "${INCOMING_PATH:-}" ] || [ -z "${TARGET_PATH:-}" ]; then
  echo "Error: --incoming and --target are required" >&2
  print_usage
  exit 1
fi

github_target_to_ssh_url() {
  case "$1" in
    git@github.com:*)
      printf '%s\n' "$1"
      ;;
    https://github.com/*)
      local owner_repo
      owner_repo=$(printf '%s' "$1" | sed -E 's#https://github.com/([^/]+/[^/]+)(.git)?/?#\1#')
      printf 'git@github.com:%s.git\n' "$owner_repo"
      ;;
    */*)
      printf 'git@github.com:%s.git\n' "${1%.git}"
      ;;
    *)
      return 1
      ;;
  esac
}

# Normalize incoming path. Target can be a local path or a GitHub repo spec.
INCOMING_PATH=$(cd "$INCOMING_PATH" && pwd -P)
TARGET_SPEC="$TARGET_PATH"
CLONED_TARGET=false
TARGET_CLONE_DIR=""

# Basic incoming validation
if ! git -C "$INCOMING_PATH" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Incoming path is not a git repository: $INCOMING_PATH" >&2
  exit 1
fi

# Include pending incoming repo worktree changes in the merge by committing them first.
if [ -n "$(git -C "$INCOMING_PATH" status --porcelain)" ]; then
  echo "Incoming repo has pending changes. Creating a commit before merge/push."
  git -C "$INCOMING_PATH" add -A
  set +e
  git -C "$INCOMING_PATH" commit -m "chore: prepare merge and push"
  COMMIT_PENDING_EXIT=$?
  set -e
  if [ $COMMIT_PENDING_EXIT -ne 0 ]; then
    echo "Commit failed (likely GPG signing). Retrying with signing disabled."
    git -C "$INCOMING_PATH" -c commit.gpgsign=false commit -m "chore: prepare merge and push"
  fi
fi

if [ -d "$TARGET_SPEC" ]; then
  TARGET_PATH=$(cd "$TARGET_SPEC" && pwd -P)
elif SSH_CLONE_URL=$(github_target_to_ssh_url "$TARGET_SPEC"); then
  TARGET_CLONE_DIR=$(mktemp -d "${TMPDIR:-/tmp}/merge-target.XXXXXX")
  CLONED_TARGET=true
  echo "Target '$TARGET_SPEC' is not a local directory. Cloning $SSH_CLONE_URL into $TARGET_CLONE_DIR"
  git clone "$SSH_CLONE_URL" "$TARGET_CLONE_DIR"
  TARGET_PATH="$TARGET_CLONE_DIR"
else
  echo "Target must be a local git repository path, GitHub slug (owner/repo), or GitHub URL: $TARGET_SPEC" >&2
  exit 1
fi

echo "Incoming repo: $INCOMING_PATH"
echo "Target spec:   $TARGET_SPEC"
echo "Target repo:   $TARGET_PATH"
echo "Branch:        $BRANCH"
echo "Remote name:   $REMOTE_NAME"
echo "SSH key:       $SSH_KEY"
echo "Keep remote:   $KEEP_REMOTE"
echo "Do push:       $DO_PUSH"
echo "Auto take theirs: $AUTO_THEIRS"

if ! git -C "$TARGET_PATH" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Target path is not a git repository: $TARGET_PATH" >&2
  exit 1
fi

cleanup_target_clone() {
  if [ "$CLONED_TARGET" = true ] && [ -n "$TARGET_CLONE_DIR" ]; then
    rm -rf "$TARGET_CLONE_DIR"
  fi
}
trap cleanup_target_clone EXIT

cd "$TARGET_PATH"

# Save origin URL (if any)
ORIGIN_URL=""
if git remote get-url origin >/dev/null 2>&1; then
  ORIGIN_URL=$(git remote get-url origin)
fi

# Create a local backup branch
BACKUP_BRANCH="backup-${BRANCH}-pre-merge-incoming-$(date +%Y%m%d%H%M%S)"
echo "Creating backup branch $BACKUP_BRANCH pointing at current HEAD of $BRANCH"
# create or update the backup branch from current branch HEAD
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
  echo "Checking out target branch $BRANCH"
  git checkout "$BRANCH"
fi

git branch "$BACKUP_BRANCH"

# Add incoming remote if necessary
if git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
  echo "Remote '$REMOTE_NAME' already exists. Using existing remote URL: $(git remote get-url $REMOTE_NAME)"
else
  echo "Adding remote '$REMOTE_NAME' -> $INCOMING_PATH"
  git remote add "$REMOTE_NAME" "$INCOMING_PATH"
fi

# Fetch incoming branch
echo "Fetching $REMOTE_NAME/$BRANCH"
git fetch "$REMOTE_NAME" "$BRANCH"

# Show diffs
echo
echo "===== COMMITS IN $REMOTE_NAME/$BRANCH NOT IN $BRANCH ====="
if git rev-parse --verify "$BRANCH" >/dev/null 2>&1; then
  git --no-pager log --oneline "$BRANCH..$REMOTE_NAME/$BRANCH" || true
else
  echo "Target branch $BRANCH does not exist locally. Showing full incoming log:"
  git --no-pager log --oneline "$REMOTE_NAME/$BRANCH" || true
fi

echo
echo "===== FILE CHANGES (name-status) ====="
git --no-pager diff --name-status "$BRANCH" "$REMOTE_NAME/$BRANCH" || true

echo
echo "===== DIFF STAT ====="
git --no-pager diff --stat "$BRANCH" "$REMOTE_NAME/$BRANCH" || true

echo

# Ensure we are on target branch
git checkout "$BRANCH"

# Try to fast-forward from origin if available
if git rev-parse --verify "origin/$BRANCH" >/dev/null 2>&1; then
  echo "Fetching and attempting fast-forward from origin/$BRANCH"
  git fetch origin "$BRANCH" || true
  if git merge --ff-only origin/$BRANCH >/dev/null 2>&1; then
    echo "Fast-forwarded from origin/$BRANCH"
  else
    echo "Could not fast-forward from origin/$BRANCH (branch may have diverged). Proceeding with merge anyway."
  fi
fi

# Merge incoming into target
MERGE_MSG="Merge $REMOTE_NAME/$BRANCH into $BRANCH: import changes from $INCOMING_PATH"
echo "Merging $REMOTE_NAME/$BRANCH into $BRANCH"
set +e
git -c commit.gpgsign=false merge --no-ff --allow-unrelated-histories -m "$MERGE_MSG" "$REMOTE_NAME/$BRANCH"
MERGE_EXIT=$?
set -e

if [ $MERGE_EXIT -eq 0 ]; then
  echo "Merge completed without conflicts."
else
  echo "Merge had conflicts. Attempting automatic resolution..."
  # List unmerged files
  UNMERGED_FILES=$(git diff --name-only --diff-filter=U || true)
  if [ -z "$UNMERGED_FILES" ]; then
    echo "No unmerged files found but merge reported failure. Aborting merge."
    git merge --abort || true
    exit 1
  fi

  for f in $UNMERGED_FILES; do
    if [ "$AUTO_THEIRS" = true ]; then
      echo "Resolving conflict in $f by taking incoming/$BRANCH (theirs)"
      git checkout --theirs -- "$f"
    else
      echo "Resolving conflict in $f by keeping target/$BRANCH (ours)"
      git checkout --ours -- "$f"
    fi
    git add -- "$f"
  done

  # Commit conflict resolution, disable GPG signing if it fails
  set +e
  git commit -m "Resolve merge conflicts by taking $REMOTE_NAME versions"
  COMMIT_EXIT=$?
  set -e
  if [ $COMMIT_EXIT -ne 0 ]; then
    echo "Commit failed (likely GPG signing). Retrying with signing disabled."
    git -c commit.gpgsign=false commit -m "Resolve merge conflicts by taking $REMOTE_NAME versions"
  fi
fi

echo
echo "Merge finished. Current HEAD:"
git --no-pager log -n 5 --oneline

echo
# Push to origin (by SSH). We'll try several strategies and fall back to asking for passphrase.
if [ "$DO_PUSH" = true ]; then
  echo "Preparing to push $BRANCH to origin..."

  # Determine an SSH URL we can push to
  SSH_URL=""
  if [ -n "$ORIGIN_URL" ]; then
    if printf '%s' "$ORIGIN_URL" | grep -qE '^git@'; then
      SSH_URL="$ORIGIN_URL"
    elif printf '%s' "$ORIGIN_URL" | grep -qE '^https://github.com/'; then
      # convert https://github.com/owner/repo(.git)? -> git@github.com:owner/repo.git
      OWNER_REPO=$(printf '%s' "$ORIGIN_URL" | sed -E 's#https://github.com/([^/]+/[^/]+)(.git)?#\1#')
      SSH_URL="git@github.com:${OWNER_REPO}.git"
    else
      echo "Warning: origin URL '$ORIGIN_URL' is not a recognized GitHub URL. Attempting 'git push origin'."
    fi
  else
    echo "Warning: no origin remote configured on target repo. You must configure origin or pass a push URL. Aborting push."
    exit 1
  fi

  echo "First attempt: git push origin $BRANCH"
  set +e
  git push origin "$BRANCH"
  PUSH_EXIT=$?
  set -e

  if [ $PUSH_EXIT -eq 0 ]; then
    echo "Push to origin succeeded."
  else
    echo "Push to origin failed (exit $PUSH_EXIT)."
    if [ -n "$SSH_URL" ]; then
      echo "Second attempt: push directly to SSH URL: $SSH_URL"
      set +e
      git push "$SSH_URL" "$BRANCH"
      PUSH_EXIT2=$?
      set -e
      if [ $PUSH_EXIT2 -eq 0 ]; then
        echo "Push to $SSH_URL succeeded."
      else
        echo "Push to $SSH_URL failed (exit $PUSH_EXIT2). This may be an SSH auth issue."
        echo "I will ask for your private key passphrase to create a temporary passphrase-free key and try again."

        # Prompt for passphrase and create temporary copy of SSH key without passphrase
        if [ -n "${MERGE_AGENT_PASSPHRASE:-}" ]; then
          PASSPHRASE="$MERGE_AGENT_PASSPHRASE"
          echo "Using passphrase from MERGE_AGENT_PASSPHRASE environment variable."
        else
          read -s -p "Enter passphrase for private key $SSH_KEY (will not be echoed): " PASSPHRASE
          echo
        fi
        if [ ! -f "$SSH_KEY" ]; then
          echo "Private key not found at $SSH_KEY" >&2
          exit 1
        fi

        TMP_KEY=$(mktemp -p "$TARGET_PATH" .tmp_sshkey_XXXXXX)
        cp "$SSH_KEY" "$TMP_KEY"
        chmod 600 "$TMP_KEY"

        # Remove passphrase from the temporary copy (non-interactive)
        if ! ssh-keygen -p -P "$PASSPHRASE" -N "" -f "$TMP_KEY" >/dev/null 2>&1; then
          echo "Failed to remove passphrase from the temporary key. Aborting push." >&2
          rm -f "$TMP_KEY"
          exit 1
        fi

        trap 'rm -f "$TMP_KEY"' EXIT

        echo "Attempting push using temporary key (will be removed after)."
        GIT_SSH_COMMAND="ssh -i $TMP_KEY -o IdentitiesOnly=yes -o StrictHostKeyChecking=no" git push "$SSH_URL" "$BRANCH"
        PUSH_EXIT3=$?
        rm -f "$TMP_KEY"
        trap - EXIT

        if [ $PUSH_EXIT3 -eq 0 ]; then
          echo "Push to $SSH_URL succeeded using temporary key."
        else
          echo "Push failed even after using temporary key (exit $PUSH_EXIT3)." >&2
          exit 1
        fi
      fi
    else
      echo "No SSH URL available to attempt SSH push. Aborting." >&2
      exit 1
    fi
  fi
else
  echo "PUSH disabled (--no-push). Skipping push step."
fi

# Cleanup: remove incoming remote unless user asked to keep it
if [ "$KEEP_REMOTE" = false ]; then
  echo "Removing remote $REMOTE_NAME"
  git remote remove "$REMOTE_NAME" || true
else
  echo "Keeping remote $REMOTE_NAME as requested"
fi

echo "All done. The target branch '$BRANCH' is now updated. Backup branch: $BACKUP_BRANCH"
exit 0
