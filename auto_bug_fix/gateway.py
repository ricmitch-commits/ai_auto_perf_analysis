"""Gateway check: determine which target branches are missing a fix.

Zero Claude calls — uses git + grep only.

Usage
-----
    from auto_bug_fix.gateway import check_fix_needed

    needed = check_fix_needed(
        repo_path="/path/to/repo",
        fix_signatures=["http_negotiate_state == GSS_AUTHNONE"],
        target_branches=["curl-8_19_0", "curl-8_18_0"],
    )
    # needed == ["curl-8_18_0"]  (8_19_0 already has the fix)
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GatewayResult:
    branch: str
    has_fix: bool
    matched_signatures: list[str]
    missing_signatures: list[str]

    def __str__(self) -> str:
        status = "HAS FIX" if self.has_fix else "NEEDS FIX"
        return (
            f"[{status}] {self.branch}\n"
            f"  matched : {self.matched_signatures or '(none)'}\n"
            f"  missing : {self.missing_signatures or '(none)'}"
        )


def _branch_contains_signature(
    repo_path: str | Path,
    branch: str,
    signature: str,
) -> bool:
    """Return True if `signature` appears anywhere in `branch`'s tree."""
    result = subprocess.run(
        ["git", "grep", "--quiet", "-F", signature, branch],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def check_branch(
    repo_path: str | Path,
    branch: str,
    fix_signatures: list[str],
) -> GatewayResult:
    """Check a single branch against all fix signatures.

    A branch is considered to have the fix only if ALL signatures are present
    (AND logic — every signature must match).
    """
    matched: list[str] = []
    missing: list[str] = []

    for sig in fix_signatures:
        if _branch_contains_signature(repo_path, branch, sig):
            matched.append(sig)
        else:
            missing.append(sig)

    has_fix = len(missing) == 0
    return GatewayResult(
        branch=branch,
        has_fix=has_fix,
        matched_signatures=matched,
        missing_signatures=missing,
    )


def check_fix_needed(
    repo_path: str | Path,
    fix_signatures: list[str],
    target_branches: list[str],
    *,
    verbose: bool = True,
) -> list[str]:
    """Check each target branch and return only those that need the fix applied.

    Parameters
    ----------
    repo_path:
        Path to the git repository.
    fix_signatures:
        List of strings that must ALL be present in a branch for it to be
        considered already fixed.
    target_branches:
        Ordered list of branches to check (e.g. ["curl-8_19_0", "curl-8_18_0"]).
    verbose:
        Print a summary table to stdout.

    Returns
    -------
    List of branch names that are missing the fix (in input order).
    """
    if not fix_signatures:
        raise ValueError("fix_signatures must not be empty")

    print("=" * 60)
    print("GATEWAY CHECK")
    print(f"  repo      : {repo_path}")
    print(f"  signatures: {fix_signatures}")
    print(f"  branches  : {target_branches}")
    print("=" * 60)

    needs_fix: list[str] = []
    for branch in target_branches:
        result = check_branch(repo_path, branch, fix_signatures)
        if verbose:
            print(result)
        if not result.has_fix:
            needs_fix.append(branch)

    print("-" * 60)
    if needs_fix:
        print(f"Branches that NEED the fix: {needs_fix}")
    else:
        print("All branches already have the fix. Nothing to do.")
    print("=" * 60)

    return needs_fix
