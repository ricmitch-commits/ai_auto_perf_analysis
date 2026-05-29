"""CLI tool to check whether a fix is present across curl branches.

Usage:
    python -m auto_bug_fix.check_fix <source_branch> <target_branch> [<target_branch> ...]

Examples:
    # Check if fix from 8.20 is present in 8.19 and 8.18
    python -m auto_bug_fix.check_fix curl-8_20_0 curl-8_19_0 curl-8_18_0

    # Short-form aliases also work
    python -m auto_bug_fix.check_fix 8.20 8.19 8.18

The fix signatures are read from bug_fix_config.fix_signatures.
The source branch is used only for display — the signatures are what's checked.
"""

import sys


def _normalize_branch(name: str) -> str:
    """Allow shorthand like '8.20' in addition to 'curl-8_20_0'."""
    if name.startswith("curl-"):
        return name
    parts = name.split(".")
    if len(parts) == 2:
        return f"curl-{parts[0]}_{parts[1]}_0"
    return name


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python -m auto_bug_fix.check_fix <source> <target> [<target> ...]")
        print("  e.g. python -m auto_bug_fix.check_fix 8.20 8.19 8.18")
        sys.exit(1)

    from auto_bug_fix.bug_fix_config import bug_fix_config
    from auto_bug_fix.gateway import check_fix_needed

    source = _normalize_branch(sys.argv[1])
    targets = [_normalize_branch(t) for t in sys.argv[2:]]

    if not bug_fix_config.fix_signatures:
        print("ERROR: fix_signatures is empty in bug_fix_config.py")
        print("  Add at least one signature string so the gateway knows what to look for.")
        sys.exit(1)

    print(f"Fix commit : {bug_fix_config.source_fix_commit}")
    print(f"Issue      : #{bug_fix_config.issue_id}")
    print(f"Source     : {source}  (fix lives here)")
    print()

    needs_fix = check_fix_needed(
        repo_path=bug_fix_config.repo_path,
        fix_signatures=bug_fix_config.fix_signatures,
        target_branches=targets,
    )

    print()
    if not needs_fix:
        print("✓ All target branches already have the fix. No backport needed.")
        sys.exit(0)
    else:
        print(f"✗ {len(needs_fix)} branch(es) need the fix: {needs_fix}")
        sys.exit(2)


if __name__ == "__main__":
    main()
