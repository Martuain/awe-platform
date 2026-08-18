merge_and_push_agent.sh — README

This script automates merging code from a local git repository into another repository's branch and pushing the result to GitHub over SSH.

What the script does (default behavior)
- Adds the incoming repo as a temporary remote (default name: `incoming-synapxi`).
- Fetches the specified branch from the incoming repo.
- Shows diffs (commits, name-status, diff stat) between the target branch and the incoming branch.
- Creates a backup branch of the target (named `backup-<branch>-pre-merge-incoming-<timestamp>`).
- Merges the incoming branch into the target branch using `--allow-unrelated-histories`.
- If merge conflicts occur it resolves them automatically by taking the incoming repository's versions ("theirs").
- Attempts to push the resulting branch to origin via SSH. If SSH auth fails, it will prompt for your private-key passphrase, create a temporary passphrase-free copy of the key, and retry the push. The temporary key file is removed after use.
- Removes the incoming remote by default; pass `--keep-remote` to retain it.

Usage

From anywhere (the script will cd into the target repo):

  bash scripts/merge_and_push_agent.sh --incoming /path/to/incoming/repo --target /path/to/target/repo

Options

  --branch BRANCH       Branch to merge (default: main)
  --remote-name NAME    Remote name for incoming repo (default: incoming-synapxi)
  --ssh-key PATH        Private SSH key to use if asked (default: ~/.ssh/id_ed25519)
  --keep-remote         Don't remove the incoming remote after the run
  --no-push             Don't attempt to push the resulting branch (dry run)
  --no-auto-theirs      Keep target versions for conflicted files (default: take incoming)
  --help                Show help

Examples

1) Full run (merge incoming main into target main, auto-resolve conflicts by taking incoming):

  bash scripts/merge_and_push_agent.sh --incoming /Users/mfmora/Downloads/synapxi-tech \
    --target /Users/mfmora/Documents/GitHub/synapxi-tech-website

2) Dry-run merge (do everything but push):

  bash scripts/merge_and_push_agent.sh --incoming /path/to/incoming --target /path/to/target --no-push

3) Use a different SSH key and keep the incoming remote:

  bash scripts/merge_and_push_agent.sh --incoming /path/to/incoming --target /path/to/target \
    --ssh-key ~/.ssh/id_rsa_custom --keep-remote

Security notes
- If you are prompted for your private key passphrase the script will only use it to create a temporary passphrase-free copy of the key inside the target repo (the temp file is deleted immediately after the push). Do not paste private keys or passphrases into public chat.
- The script disables GPG signing for automated conflict-resolution commits if the local environment cannot sign commits.

If you want, I can:
- Make this script executable (chmod +x),
- Run it now with your parameters, or
- Add a wrapper that prompts interactively for parameters.
