#!/usr/bin/env python3
"""
Atomic PR merge and cleanup.

This script exists because bash rules prohibit && and ; operators,
forcing merge and cleanup to be separate commands. Agents forget
to run cleanup after merge, leaving orphaned branches.

This script does BOTH atomically - no gaps, no forgetting.

Usage:
    poetry run python tools/merge_pr.py --pr 123
    poetry run python tools/merge_pr.py --pr 123 --no-squash
"""

import argparse
import json
import subprocess
import sys

# Base path for git operations (Unix-style for Git Bash on Windows)
REPO_PATH = "/c/Users/mcwiz/Projects/Aletheia"


def run(cmd: list[str], check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    """Run a command via bash shell for Windows/Git Bash compatibility."""
    cmd_str = " ".join(cmd)
    print(f"  $ {cmd_str}")
    # S602: shell=True is safe here - all inputs are hardcoded, not from users
    return subprocess.run(
        cmd_str,
        shell=True,  # noqa: S602 - Required for Git Bash path compatibility on Windows
        check=check,
        capture_output=capture,
        text=True,
    )


def get_pr_info(pr_number: int) -> dict:
    """Get PR information from GitHub."""
    result = run(
        [
            "gh", "pr", "view", str(pr_number),
            "--repo", "martymcenroe/Aletheia",
            "--json", "headRefName,state,title,number"
        ],
        capture=True,
    )
    return json.loads(result.stdout)


def get_issue_id_from_branch(branch_name: str) -> str | None:
    """Extract issue ID from branch name (format: {ID}-description)."""
    parts = branch_name.split("-")
    if parts and parts[0].isdigit():
        return parts[0]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Atomic PR merge and cleanup")
    parser.add_argument("--pr", type=int, required=True, help="PR number to merge")
    parser.add_argument("--no-squash", action="store_true", help="Don't squash commits")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without doing it")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"ATOMIC MERGE: PR #{args.pr}")
    print(f"{'='*60}\n")

    # Step 1: Get PR info
    print("[1/6] Getting PR info...")
    try:
        pr_info = get_pr_info(args.pr)
    except subprocess.CalledProcessError:
        print(f"ERROR: Could not fetch PR #{args.pr}")
        return 1

    branch_name = pr_info["headRefName"]
    state = pr_info["state"]
    title = pr_info["title"]

    print(f"  Title: {title}")
    print(f"  Branch: {branch_name}")
    print(f"  State: {state}")

    if state == "MERGED":
        print(f"\nPR #{args.pr} is already merged. Running cleanup only...")
    elif state == "CLOSED":
        print(f"\nERROR: PR #{args.pr} is closed (not merged). Cannot proceed.")
        return 1
    elif state != "OPEN":
        print(f"\nERROR: PR #{args.pr} has unexpected state: {state}")
        return 1

    # Step 2: Determine worktree path
    print("\n[2/6] Determining worktree path...")
    issue_id = get_issue_id_from_branch(branch_name)
    if issue_id:
        # Use Unix-style path string for Git Bash compatibility
        worktree_path = f"/c/Users/mcwiz/Projects/Aletheia-{issue_id}"
        print(f"  Worktree: {worktree_path}")
    else:
        worktree_path = None
        print("  No issue ID in branch name, skipping worktree cleanup")

    if args.dry_run:
        print("\n[DRY RUN] Would execute:")
        if state == "OPEN":
            print(f"  - gh pr merge {args.pr} --squash --delete-branch")
        if worktree_path:
            print(f"  - git worktree remove {worktree_path} --force")
        print(f"  - git branch -D {branch_name}")
        return 0

    # Step 3: Merge PR (if not already merged)
    if state == "OPEN":
        print("\n[3/6] Merging PR...")
        merge_cmd = [
            "gh", "pr", "merge", str(args.pr),
            "--repo", "martymcenroe/Aletheia",
            "--delete-branch",  # Delete remote branch
        ]
        if not args.no_squash:
            merge_cmd.append("--squash")

        try:
            run(merge_cmd)
            print("  Merge successful!")
        except subprocess.CalledProcessError as e:
            print(f"  ERROR: Merge failed: {e}")
            return 1
    else:
        print("\n[3/6] Skipping merge (already merged)")

    # Step 4: Remove worktree (if exists)
    print("\n[4/6] Removing worktree...")
    if worktree_path:
        result = run(
            ["git", "-C", REPO_PATH, "worktree", "remove", worktree_path, "--force"],
            check=False,
        )
        if result.returncode == 0:
            print("  Worktree removed!")
        else:
            print("  Worktree not found or already removed")
    else:
        print("  No worktree to remove")

    # Step 5: Delete local branch
    print("\n[5/6] Deleting local branch...")
    result = run(
        ["git", "-C", REPO_PATH, "branch", "-D", branch_name],
        check=False,
    )
    if result.returncode == 0:
        print("  Branch deleted!")
    else:
        print("  Branch not found or already deleted")

    # Step 6: Verify cleanup
    print("\n[6/6] Verifying cleanup...")

    # Check branch
    result = run(
        ["git", "-C", REPO_PATH, "branch", "--list", branch_name],
        capture=True,
        check=False,
    )
    branch_exists = branch_name in result.stdout

    # Check worktree
    result = run(
        ["git", "-C", REPO_PATH, "worktree", "list"],
        capture=True,
        check=False,
    )
    worktree_exists = worktree_path and worktree_path in result.stdout

    print(f"\n{'='*60}")
    if branch_exists or worktree_exists:
        print("CLEANUP INCOMPLETE:")
        if branch_exists:
            print(f"  WARNING: Branch '{branch_name}' still exists!")
        if worktree_exists:
            print(f"  WARNING: Worktree '{worktree_path}' still exists!")
        print(f"{'='*60}\n")
        return 1
    else:
        print(f"SUCCESS: PR #{args.pr} merged and fully cleaned up!")
        print(f"{'='*60}\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
