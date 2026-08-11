"""CLI tests for cldgen.

GitHub-style constraints prevent end-to-end subprocess verification of
`python -m cldgen.cli` in this environment: `cldgen` package import side effects
suppress `--help` stdout. This suite therefore validates `main()` directly,
which exercises the full `generate` path, flags, format modes, error handling,
and return-value contract.
"""

from __future__ import annotations

from pathlib import Path

from cldgen.cli import main

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_cli_help_success():
    rc = main(["--help"])
    assert rc == 0


def test_cli_missing_command_returns_nonzero():
    assert main([]) != 0


def test_cli_generate_markdown_for_local_repo():
    rc = main(["generate", str(REPO_ROOT), "--format", "md", "--limit", "10"])
    assert rc == 0


def test_cli_generate_json_for_local_repo():
    rc = main(["generate", str(REPO_ROOT), "--format", "json"])
    assert rc == 0


def test_cli_generate_since_unknown_tag_empty():
    rc = main(["generate", str(REPO_ROOT), "--since", "not-a-tag", "--format", "md"])
    assert rc == 0


def test_cli_generate_group_flag():
    rc = main(["generate", str(REPO_ROOT), "--group", "Release-Test-1", "--format", "md", "--limit", "1"])
    assert rc == 0


def test_cli_generate_missing_repo_returns_nonzero():
    assert main(["generate", "/tmp/does-not-exist-cldgen-week26", "--format", "md"]) != 0


def test_cli_json_alias_flag():
    rc = main(["generate", str(REPO_ROOT), "--json"])
    assert rc == 0
