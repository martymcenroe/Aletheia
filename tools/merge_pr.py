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
from pathlib import Path

# Base paths for git operations
REPO_PATH_UNIX = "/c/Users/mcwiz/Projects/Aletheia"
REPO_PATH_WIN = Path("C:/Users/mcwiz/Projects/Aletheia")


def run_cmd(
    cmd: list[str],
    check: bool = True,
    capture: bool = False,
    cwd: Path | None = None,
    quiet: bool = False,
) -> subprocess.CompletedProcess:
    """Run a command with proper error handling."""
    if not quiet:
        print(f"  $ {' '.join(cmd)}")

    # S603: All command inputs are hardcoded strings, not user input
    result = subprocess.run(
        cmd,  # noqa: S603
        check=False,  # We'll handle errors ourselves
        capture_output=True,
        text=True,
        cwd=cwd,
    )

    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, cmd, result.stdout, result.stderr
        )

    # If not capturing, print stdout (but not for quiet commands)
    if not capture and not quiet and result.stdout.strip():
        print(f"  {result.stdout.strip()}")

    return result


def get_pr_info(pr_number: int) -> dict:
    """Get PR information from GitHub."""
    result = run_cmd(
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


def branch_exists(branch_name: str) -> bool:
    """Check if a local branch exists."""
    result = run_cmd(
        ["git", "branch", "--list", branch_name],
        capture=True,
        cwd=REPO_PATH_WIN,
        quiet=True,
    )
    return branch_name in result.stdout


def worktree_exists(worktree_path: str) -> bool:
    """Check if a worktree exists."""
    result = run_cmd(
        ["git", "worktree", "list"],
        capture=True,
        cwd=REPO_PATH_WIN,
        quiet=True,
    )
    # Check for both Unix and Windows path formats
    issue_id = worktree_path.split("-")[-1]
    return f"Aletheia-{issue_id}" in result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description="Atomic PR merge and cleanup")
    parser.add_argument("--pr", type=int, required=True, help="PR number to merge")
    parser.add_argument("--no-squash", action="store_true", help="Don't squash commits")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"ATOMIC MERGE: PR #{args.pr}")
    print(f"{'='*60}\n")

    # Step 1: Get PR info
    print("[1/6] Getting PR info...")
    try:
        pr_info = get_pr_info(args.pr)
    except subprocess.CalledProcessError:
        print("  ERROR: Could not fetch PR info")
        return 1

    branch_name = pr_info["headRefName"]
    state = pr_info["state"]
    title = pr_info["title"]

    print(f"  Title: {title}")
    print(f"  Branch: {branch_name}")
    print(f"  State: {state}")

    if state == "MERGED":
        print(f"\n  PR #{args.pr} is already merged. Running cleanup only...")
    elif state == "CLOSED":
        print(f"\n  ERROR: PR #{args.pr} is closed (not merged). Cannot proceed.")
        return 1
    elif state != "OPEN":
        print(f"\n  ERROR: PR #{args.pr} has unexpected state: {state}")
        return 1

    # Step 2: Determine worktree path
    print("\n[2/6] Determining worktree path...")
    issue_id = get_issue_id_from_branch(branch_name)
    if issue_id:
        worktree_path = f"/c/Users/mcwiz/Projects/Aletheia-{issue_id}"
        print(f"  Worktree: {worktree_path}")
    else:
        worktree_path = None
        print("  No issue ID in branch name, skipping worktree cleanup")

    # Check what currently exists
    has_branch = branch_exists(branch_name)
    has_worktree = worktree_path and worktree_exists(worktree_path)

    print(f"  Local branch exists: {'Yes' if has_branch else 'No'}")
    print(f"  Worktree exists: {'Yes' if has_worktree else 'No'}")

    if args.dry_run:
        print("\n[DRY RUN] Would execute:")
        if state == "OPEN":
            print(f"  - Merge PR #{args.pr}")
        if has_worktree:
            print(f"  - Remove worktree {worktree_path}")
        if has_branch:
            print(f"  - Delete branch {branch_name}")
        return 0

    # Step 3: Merge PR (if not already merged)
    if state == "OPEN":
        print("\n[3/6] Merging PR...")
        merge_cmd = [
            "gh", "pr", "merge", str(args.pr),
            "--repo", "martymcenroe/Aletheia",
            "--delete-branch",
        ]
        if not args.no_squash:
            merge_cmd.append("--squash")

        try:
            run_cmd(merge_cmd)
            print("  Merge successful!")
        except subprocess.CalledProcessError as e:
            print(f"  ERROR: Merge failed: {e.stderr}")
            return 1
    else:
        print("\n[3/6] Skipping merge (already merged)")

    # Step 4: Remove worktree (if exists)
    print("\n[4/6] Removing worktree...")
    if not worktree_path:
        print("  Skipped (no worktree path)")
    elif not has_worktree:
        print("  Skipped (worktree already gone)")
    else:
        result = run_cmd(
            ["git", "worktree", "remove", worktree_path, "--force"],
            check=False,
            cwd=REPO_PATH_WIN,
        )
        if result.returncode == 0:
            print("  Worktree removed!")
        else:
            # Try with Windows path as fallback
            win_path = f"C:/Users/mcwiz/Projects/Aletheia-{issue_id}"
            result = run_cmd(
                ["git", "worktree", "remove", win_path, "--force"],
                check=False,
                cwd=REPO_PATH_WIN,
                quiet=True,
            )
            if result.returncode == 0:
                print("  Worktree removed!")
            else:
                print(f"  Warning: Could not remove worktree: {result.stderr.strip()}")

    # Step 5: Delete local branch
    print("\n[5/6] Deleting local branch...")
    if not has_branch:
        print("  Skipped (branch already gone)")
    else:
        result = run_cmd(
            ["git", "branch", "-D", branch_name],
            check=False,
            cwd=REPO_PATH_WIN,
        )
        if result.returncode == 0:
            print("  Branch deleted!")
        else:
            print(f"  Warning: Could not delete branch: {result.stderr.strip()}")

    # Step 6: Verify cleanup
    print("\n[6/6] Verifying cleanup...")

    final_has_branch = branch_exists(branch_name)
    final_has_worktree = worktree_path and worktree_exists(worktree_path)

    print(f"\n{'='*60}")
    if final_has_branch or final_has_worktree:
        print("CLEANUP INCOMPLETE:")
        if final_has_branch:
            print(f"  WARNING: Branch '{branch_name}' still exists!")
        if final_has_worktree:
            print("  WARNING: Worktree still exists!")
        print(f"{'='*60}\n")
        return 1
    else:
        print(f"SUCCESS: PR #{args.pr} merged and fully cleaned up!")
        print(f"{'='*60}\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
