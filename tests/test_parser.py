"""Tests for cldgen parser and renderer."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest

from cldgen.parser import (
    MarkdownRenderer,
    group_commits,
    normalize_type,
    parse_git_log,
    parse_tags,
    render_changelog,
)
from cldgen.types import ChangelogEntry, Commit, GroupHeader


def test_normalize_type_known_aliases():
    assert normalize_type("fix") == "Fixes"
    assert normalize_type("feat") == "Features"
    assert normalize_type("perf") == "Performance"
    assert normalize_type("chore") == "Chores"


def test_normalize_type_title_fallback():
    assert "style" in normalize_type("style").lower()
    assert "operations" in normalize_type("ops").lower()


def test_parse_tags_basic():
    tags = parse_tags(["Release-1.0", "Release-2.0@2025-08-01"])
    assert [t.label for t in tags] == ["Release-1.0", "Release-2.0"]
    assert tags[0].date is None
    assert tags[1].date == "2025-08-01"


def test_parse_tags_empty_rejected():
    with pytest.raises(ValueError):
        parse_tags([""])


def test_parse_git_log_positive_case():
    text = (
        "abc123 | 2025-08-01 | Ada | feat(auth): add login | feat(auth): add login\n"
        "def456 | 2025-08-02 | Bob | fix: handle null user | fix: handle null user\n"
    )
    entries = parse_git_log(text, [])
    assert len(entries) >= 1
    assert any("Features" in {c.type for c in e.commits} for e in entries)


def test_parse_git_log_negative_case():
    assert parse_git_log("", ["Anything"]) == []


def test_parse_git_log_edge_case_blank_lines_ignored():
    entries = parse_git_log("\n\nabc123 | 2025-08-01 | Ada | fix: edge case | fix: edge case\n\n", [])
    assert len(entries) >= 1
    assert entries[0].commits[0].type == "Fixes"


def test_markdown_renderer_empty():
    rendered = MarkdownRenderer().render([])
    assert "No changelog entries found" in rendered


def test_markdown_renderer_single_entry():
    date = datetime(2025, 8, 1)
    entry = ChangelogEntry(
        group=GroupHeader("Release-1.0", "Release-1.0", "2025-08-01"),
        commits=[
            Commit("abc123", "abc123", "Ada", date, "Features", "auth", "add login", False, "raw"),
        ],
    )
    rendered = MarkdownRenderer().render([entry])
    assert "## Release-1.0 - _2025-08-01_" in rendered
    assert "add login" in rendered


def test_markdown_renderer_breaking_prefix():
    date = datetime(2025, 8, 1)
    entry = ChangelogEntry(
        group=GroupHeader("Release-2.0", "Release-2.0", "2025-08-01"),
        commits=[
            Commit("abc123", "abc123", "Ada", date, "Breaking Changes", "binding", "remove legacy", True, "raw"),
        ],
    )
    rendered = MarkdownRenderer().render([entry])
    assert "**BREAKING**" in rendered


def test_render_changelog_helper():
    entries = [
        ChangelogEntry(
            GroupHeader("Release-1.0", "Release-1.0", "2025-08-01"),
            [
                Commit("abc123", "abc123", "Ada", datetime(2025, 8, 1), "Features", "auth", "add login", False, "raw"),
            ],
        )
    ]
    text = render_changelog(entries)
    assert text.startswith("# Changelog")


def test_commit_header_with_scope():
    commit = Commit("abc", "abc", "Ada", datetime(2025, 8, 5), "Features", "auth", "login added", False, "raw")
    assert commit.header == "**auth**: login added"
