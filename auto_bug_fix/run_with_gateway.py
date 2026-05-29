"""Gateway-aware orchestrator for the auto_bug_fix pipeline.

Usage:
    python -m auto_bug_fix.run_with_gateway

Flow:
    1. Run the zero-token gateway check across all target branches.
    2. Skip branches that already have the fix.
    3. Run the full Claude pipeline for each branch that needs the fix — in PARALLEL.
       Each branch gets its own repo clone and output folder so runs don't interfere.

Per-branch repo clones and output dirs are configured in BRANCH_CONFIGS below.
"""

import sys
import time
import asyncio
import dataclasses

from common.utils import Tee
from common.claude_utils import ClaudeConfig, claude_run

from auto_bug_fix.bug_fix_config import claude_config, bug_fix_config, MULTI_TARGET_CONFIGS
from auto_bug_fix.gateway import check_fix_needed
from auto_bug_fix.run_bug_fix import gen_prompts

LOG_FILE = "__run_log_bug_fix_series.txt"


def make_branch_config(branch: str):
    """Return a (BugFixConfig, ClaudeConfig) pair customised for this branch."""
    overrides = MULTI_TARGET_CONFIGS[branch]
    build_cmd = (
        f"cmake --build {overrides['build_dir']} "
        f"-j$(sysctl -n hw.logicalcpu)"
    )
    test_cmd = (
        f"ctest --test-dir {overrides['build_dir']} "
        f"-j$(sysctl -n hw.logicalcpu)"
    )
    config = dataclasses.replace(
        bug_fix_config,
        target_branch=branch,
        repo_path=overrides["repo_path"],
        build_dir=overrides["build_dir"],
        output_dir=overrides["output_dir"],
        build_command=build_cmd,
        test_command=test_cmd,
    )
    branch_claude_config = dataclasses.replace(
        claude_config,
        cwd=overrides["output_dir"],
    )
    return config, branch_claude_config


async def run_for_branch(branch: str) -> None:
    """Run the full Claude pipeline for a single target branch."""
    config, branch_claude_config = make_branch_config(branch)
    prompts = gen_prompts(branch_claude_config, config)
    start = time.time()
    print(f"\n[{branch}] Starting pipeline → output: {config.output_dir}")
    await claude_run(branch_claude_config, prompts)
    elapsed = time.time() - start
    print(f"\n[{branch}] FINISHED: duration={elapsed:.1f}s")


async def main() -> None:
    if not bug_fix_config.fix_signatures:
        print(
            "WARNING: fix_signatures is empty in bug_fix_config.\n"
            "Set fix_signatures in bug_fix_config.py and re-run."
        )
        sys.exit(1)

    # Gateway check — use the original repo (read-only grep, no modification)
    branches_needing_fix = check_fix_needed(
        repo_path=bug_fix_config.repo_path,
        fix_signatures=bug_fix_config.fix_signatures,
        target_branches=list(MULTI_TARGET_CONFIGS.keys()),
    )

    if not branches_needing_fix:
        print("Gateway: all branches already have the fix. Exiting.")
        return

    print(f"\nRunning pipelines in SERIES for: {branches_needing_fix}\n")

    for branch in branches_needing_fix:
        await run_for_branch(branch)


if __name__ == "__main__":
    log_file = open(LOG_FILE, "w")
    original_stdout = sys.stdout
    sys.stdout = Tee(original_stdout, log_file)

    total_start = time.time()
    asyncio.run(main())
    total_elapsed = time.time() - total_start
    print(f"FINISHED ALL: total_duration={total_elapsed:.1f}s")
