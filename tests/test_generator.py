"""Tests for cldgen generator."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from cldgen.generator import ChangelogGenerator
from cldgen.types import Commit, GroupHeader, ChangelogEntry
from cldgen.parser import group_commits


def test_generator_build_from_fake_commits(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "pyproject.toml").write_text("[project]\nname='demo'\n")
    originals = ChangelogGenerator.build
    def fake_build(self, since=None):
        if not Path(self.repo).exists():
            raise RuntimeError("missing")
        tag = GroupHeader(label="Unreleased", tag="Unreleased", date="2025-08-01")
        entry = ChangelogEntry(
            group=tag,
            commits=[
                Commit("abc123", "abc123", "Me", __import__("datetime").datetime(2025, 8, 1), "Fixes", None, "cleanup", False, "raw"),
            ],
        )
        from cldgen.parser import MarkdownRenderer

        return MarkdownRenderer().render([entry])

    import cldgen.generator as generator_mod

    generator_mod.ChangelogGenerator.build = fake_build  # type: ignore[assignment]
    try:
        gen = ChangelogGenerator(repo)
        out = gen.build()
        assert "Fixes" in out
        assert "cleanup" in out
    finally:
        generator_mod.ChangelogGenerator.build = originals  # type: ignore[assignment]


def test_generator_write_creates_file(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    target = tmp_path / "out.md"
    tag = GroupHeader(label="Unreleased", tag="Unreleased", date="2025-08-01")
    entry = ChangelogEntry(group=tag, commits=[])
    from cldgen.parser import MarkdownRenderer

    rendered = MarkdownRenderer().render([entry])

    class _Gen:
        repo_path = repo

        def build(self, since=None):
            return rendered

    originals = ChangelogGenerator.build
    import cldgen.generator as generator_mod

    generator_mod.ChangelogGenerator.build = lambda self, since=None: rendered  # type: ignore[assignment]
    try:
        gen = ChangelogGenerator(repo)
        path = gen.write(target)
        assert path.exists()
        assert path.read_text(encoding="utf-8") == rendered
    finally:
        generator_mod.ChangelogGenerator.build = originals  # type: ignore[assignment]


def test_group_commits_empty():
    assert group_commits([]) == []


def test_group_commits_single():
    date = __import__("datetime").datetime(2025, 8, 2)
    commits = [Commit("abc", "abc", "Ada", date, "Fixes", "ui", "button fix", False, "raw")]
    entries = group_commits(commits)
    assert len(entries) == 1
    assert entries[0].commits[0].type == "Fixes"
