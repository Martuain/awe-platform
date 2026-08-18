#!/usr/bin/env bash
# Interactive wrapper for merge_and_push_agent.sh
# Prompts for parameters (with useful defaults) and invokes the merge script.

set -euo pipefail
IFS=$'\n\t'

DEFAULT_INCOMING="/Users/mfmora/Documents/GitHub/awe-platform-genesis-v0.1.0"
DEFAULT_TARGET="Martuain/awe-platform"
DEFAULT_BRANCH="main"
DEFAULT_REMOTE_NAME="incoming-awe"
DEFAULT_SSH_KEY="$HOME/.ssh/id_ed25519"

print_usage() {
  cat <<EOF
Usage: $0 [options]

Options (any provided here will skip interactive prompts):
  --incoming PATH       Path to incoming repo (default: $DEFAULT_INCOMING)
  --target PATH|REPO    Target local repo path, GitHub slug (owner/repo), or GitHub URL (default: $DEFAULT_TARGET)
  --branch BRANCH       Branch to merge (default: $DEFAULT_BRANCH)
  --remote-name NAME    Remote name for incoming repo (default: $DEFAULT_REMOTE_NAME)
  --ssh-key PATH        SSH private key path to use when pushing (default: $DEFAULT_SSH_KEY)
  --keep-remote         Keep the incoming remote after the run
  --no-push             Don't attempt to push the resulting branch (dry run)
  --no-auto-theirs      Keep target versions for conflicts (default: take incoming)
  --help                Show this help

If the environment variable MERGE_AGENT_PASSPHRASE is set, it will be used non-interactively
as the passphrase for your private key when an SSH push requires it. Otherwise the merge script
will prompt for the passphrase interactively when needed.
EOF
}

# Defaults
INCOMING_PATH=""
TARGET_PATH=""
BRANCH=""
REMOTE_NAME=""
SSH_KEY=""
KEEP_REMOTE=false
NO_PUSH=false
NO_AUTO_THEIRS=false

# Parse CLI options
while [ $# -gt 0 ]; do
  case "$1" in
    --incoming) INCOMING_PATH="$2"; shift 2;;
    --target) TARGET_PATH="$2"; shift 2;;
    --branch) BRANCH="$2"; shift 2;;
    --remote-name) REMOTE_NAME="$2"; shift 2;;
    --ssh-key) SSH_KEY="$2"; shift 2;;
    --keep-remote) KEEP_REMOTE=true; shift;;
    --no-push) NO_PUSH=true; shift;;
    --no-auto-theirs) NO_AUTO_THEIRS=true; shift;;
    --help) print_usage; exit 0;;
    *) echo "Unknown option: $1"; print_usage; exit 1;;
  esac
done

# Use defaults when values not provided via CLI
INCOMING_PATH="${INCOMING_PATH:-$DEFAULT_INCOMING}"
TARGET_PATH="${TARGET_PATH:-$DEFAULT_TARGET}"
BRANCH="${BRANCH:-$DEFAULT_BRANCH}"
REMOTE_NAME="${REMOTE_NAME:-$DEFAULT_REMOTE_NAME}"
SSH_KEY="${SSH_KEY:-$DEFAULT_SSH_KEY}"

# If still empty, prompt interactively
if [ -z "$INCOMING_PATH" ]; then
  read -p "Incoming repo path [$DEFAULT_INCOMING]: " v
  INCOMING_PATH="${v:-$DEFAULT_INCOMING}"
fi
if [ -z "$TARGET_PATH" ]; then
  read -p "Target repo path or GitHub slug [$DEFAULT_TARGET]: " v
  TARGET_PATH="${v:-$DEFAULT_TARGET}"
fi
if [ -z "$BRANCH" ]; then
  read -p "Branch to merge [$DEFAULT_BRANCH]: " v
  BRANCH="${v:-$DEFAULT_BRANCH}"
fi
if [ -z "$REMOTE_NAME" ]; then
  read -p "Remote name for incoming repo [$DEFAULT_REMOTE_NAME]: " v
  REMOTE_NAME="${v:-$DEFAULT_REMOTE_NAME}"
fi
if [ -z "$SSH_KEY" ]; then
  read -p "SSH private key path [$DEFAULT_SSH_KEY]: " v
  SSH_KEY="${v:-$DEFAULT_SSH_KEY}"
fi

# If MERGE_AGENT_PASSPHRASE is not set, ask the user whether to provide it now (only if push will run)
if [ "$NO_PUSH" = false ] && [ -z "${MERGE_AGENT_PASSPHRASE:-}" ]; then
  echo "Note: push will attempt SSH authentication. If your key is passphrase-protected you can"
  echo "set MERGE_AGENT_PASSPHRASE environment variable before running this wrapper to run non-interactively."
  read -p "Provide passphrase now for non-interactive push? (y/N): " yn
  case "$yn" in
    [Yy]*)
      read -s -p "Enter passphrase (will not be echoed): " input_pass
      echo
      export MERGE_AGENT_PASSPHRASE="$input_pass";
      ;;
    *)
      echo "Will proceed; the merge script will prompt for passphrase if push needs it."
      ;;
  esac
fi

# Build args for the merge script
ARGS=(--incoming "$INCOMING_PATH" --target "$TARGET_PATH" --branch "$BRANCH" --remote-name "$REMOTE_NAME" --ssh-key "$SSH_KEY")
if [ "$KEEP_REMOTE" = true ]; then
  ARGS+=(--keep-remote)
fi
if [ "$NO_PUSH" = true ]; then
  ARGS+=(--no-push)
fi
if [ "$NO_AUTO_THEIRS" = true ]; then
  ARGS+=(--no-auto-theirs)
fi

# Run the merge script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
MERGE_SCRIPT="$SCRIPT_DIR/merge_and_push_agent.sh"
if [ ! -x "$MERGE_SCRIPT" ]; then
  if [ -f "$MERGE_SCRIPT" ]; then
    chmod +x "$MERGE_SCRIPT" || true
  else
    echo "Merge script not found at $MERGE_SCRIPT" >&2
    exit 1
  fi
fi

echo "Running merge script with the following parameters:"
echo "  incoming: $INCOMING_PATH"
echo "  target:   $TARGET_PATH"
echo "  branch:   $BRANCH"
echo "  remote:   $REMOTE_NAME"
echo "  ssh key:  $SSH_KEY"
echo "  keep remote: $KEEP_REMOTE"
echo "  no-push: $NO_PUSH"
echo "  no-auto-theirs: $NO_AUTO_THEIRS"

echo
# Invoke merge script
# Note: MERGE_AGENT_PASSPHRASE may be set in the environment (for non-interactive use)
"$MERGE_SCRIPT" "${ARGS[@]}"

EXIT=$?
if [ $EXIT -eq 0 ]; then
  echo "Wrapper finished successfully."
else
  echo "Wrapper failed with exit code $EXIT" >&2
fi

exit $EXIT
