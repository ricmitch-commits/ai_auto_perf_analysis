"""Configuration dataclass and default instance for the auto_bug_fix pipeline.

Edit the ``bug_fix_config`` instance at the bottom of this file before running
``python -m auto_bug_fix.run_bug_fix``.

For multi-version gateway runs, use ``run_with_gateway.py`` instead.
"""

from dataclasses import dataclass, field
from common.claude_utils import ClaudeConfig


@dataclass
class BugFixConfig:
    # Repository
    repo_path: str
    build_dir: str

    # Branch identity
    source_branch: str
    target_branch: str
    source_fix_commit: str

    # Bug context
    bug_description: str
    issue_id: str

    # Porting constraints
    disallowed_modules: list[str]
    port_tests: bool

    # Build & test
    build_command: str
    test_command: str
    max_build_test_retries: int

    # Output directory for all Claude artifacts (plans, patches, logs).
    # Each run should use a distinct folder so results are preserved for comparison.
    output_dir: str = "./bug-fix-output"

    # Gateway: code signatures that confirm the fix is present on a branch.
    # All signatures must match for the branch to be considered already fixed.
    # Used by run_with_gateway.py before invoking the Claude pipeline.
    fix_signatures: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Edit the instances below before running the pipeline.
#
# For multi-branch / gateway runs, also populate MULTI_TARGET_CONFIGS and
# use run_with_gateway.py instead of run_bug_fix.py directly.
# ---------------------------------------------------------------------------

_BUG_DESCRIPTION = (
    # Describe the bug clearly: what is broken, where the defect lives in the
    # code, what the correct behaviour should be, and the fix commit / PR.
    # Example:
    # "url: improve connection reuse on negotiate. "
    # "The url_match_auth_ntlm() function allowed connection reuse when "
    # "NTLM state was NTLMSTATE_NONE but did not check the Negotiate/SPNEGO "
    # "state. Fix adds a GSS_AUTHNONE check so a connection is only reused "
    # "when neither NTLM nor Negotiate auth is in progress. Closes #21203."
    "TODO: fill in your bug description here."
)

claude_config = ClaudeConfig(
    model="claude-opus-4-6",
    allowed_tools=["Read", "Write", "Bash"],
    perm_mode="acceptEdits",
    cwd="./bug-fix-output",
)

bug_fix_config = BugFixConfig(
    repo_path="/path/to/your/repo",
    build_dir="/path/to/your/repo/build",
    source_branch="main",           # branch that already has the fix
    target_branch="release-1.x",    # branch that needs the fix backported
    source_fix_commit="<full-sha>",
    bug_description=_BUG_DESCRIPTION,
    issue_id="ISSUE-000",
    disallowed_modules=[],
    port_tests=True,
    build_command="cmake --build /path/to/your/repo/build -j$(nproc)",
    test_command="ctest --test-dir /path/to/your/repo/build -R <test-name>",
    max_build_test_retries=3,
    output_dir="./bug-fix-output",
    fix_signatures=[
        # One or more code strings that are present ONLY after the fix is
        # applied. Used by the gateway check to skip branches already fixed.
        # Example: "GSS_AUTHNONE"
    ],
)

# ---------------------------------------------------------------------------
# MULTI_TARGET_CONFIGS — used by run_with_gateway.py for parallel / series
# runs across multiple target branches. Each key is a human-readable label.
# Fields override the corresponding fields in bug_fix_config above.
# ---------------------------------------------------------------------------
MULTI_TARGET_CONFIGS: dict = {
    # "branch-label": {
    #     "repo_path":   "/path/to/clone-for-that-branch",
    #     "build_dir":   "/path/to/clone-for-that-branch/build",
    #     "output_dir":  "./bug-fix-output-branch-label",
    # },
}
