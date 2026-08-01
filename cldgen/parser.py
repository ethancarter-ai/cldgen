"""Changelog generation package for git-backed releases."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Sequence

from cldgen.types import ChangelogEntry, Commit, GroupHeader

_TAG_RE = re.compile(r"(?i)^\s*\[([^\[\]]+)\]\s*")
_CONVENTIONAL_TYPE_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?:\((?P<scope>[^)]+)\))?(?P<break>!)?:\s*(?P<msg>.+)$"
)


def normalize_type(raw: str) -> str:
    value = raw.strip()
    if not value:
        return "misc"
    lowered = value.lower()
    mapping = {
        "feat": "Features",
        "feature": "Features",
        "fixed": "Fixes",
        "fix": "Fixes",
        "bugfix": "Fixes",
        "bug": "Fixes",
        "perf": "Performance",
        "performance": "Performance",
        "docs": "Docs",
        "doc": "Docs",
        "ci": "CI",
        "ops": "Operations",
        "chore": "Chores",
        "refactor": "Refactors",
        "refactoring": "Refactors",
        "style": "Styles",
        "test": "Tests",
        "tests": "Tests",
        "build": "Build",
        "revert": "Reverts",
        "breaking": "Breaking Changes",
        "breaking change": "Breaking Changes",
        "break": "Breaking Changes",
    }
    return mapping.get(lowered, value.title())


def parse_tags(tags: Sequence[str]) -> list[GroupHeader]:
    return [_header_for_tag(tag) for tag in tags]


def _header_for_tag(tag: str) -> GroupHeader:
    normalized = tag.strip()
    if not normalized:
        raise ValueError("Group tag cannot be empty")
    label, date_str = _split_tag(normalized)
    return GroupHeader(label=label, tag=normalized, date=date_str or None)


def _split_tag(tag: str) -> tuple[str, Optional[str]]:
    if "@" in tag:
        head, tail = tag.split("@", 1)
        return head.strip() or tag, tail.strip()
    if " " in tag:
        head, tail = tag.split(" ", 1)
        return head.strip() or tag, tail.strip()
    return tag, None


def _normalize_sha(sha: str) -> str:
    return sha.strip()[:12]


def _parse_type_scope(raw_message: str) -> tuple[str, Optional[str], str, bool]:
    raw = raw_message.strip()
    match = _CONVENTIONAL_TYPE_RE.match(raw)
    if not match:
        return "misc", None, raw, False
    msg = match.group("msg").strip() or raw
    return (
        match.group("type").strip() or "misc",
        match.group("scope"),
        msg,
        bool(match.group("break")),
    )


def _sort_commit(commit: Commit) -> tuple[int, str]:
    type_priority = {
        "Breaking Changes": 0,
        "Features": 1,
        "Fixes": 2,
        "Performance": 3,
        "Docs": 4,
        "Refactors": 5,
        "Chores": 6,
        "Tests": 7,
    }
    return (type_priority.get(commit.type, 99), commit.description.lower())


@dataclass
class _ParsedCommit:
    sha: str
    short: str
    author: str
    date: Optional[datetime]
    tag: Optional[str]
    type: str
    scope: Optional[str]
    message: str
    breaking: bool
    raw: str


def parse_git_log(text: str, tags: List[str]) -> List[ChangelogEntry]:
    parsed = [_parsed_from_line(line) for line in text.splitlines() if line.strip()]
    commits = [_as_commit(result) for result in parsed if result]
    return _results_to_entries(sorted(commits, key=lambda item: item.date or datetime.min, reverse=True))


def _as_commit(result: _ParsedCommit) -> _ParsedCommit:
    return result


def _parsed_from_line(raw_line: str) -> Optional[_ParsedCommit]:
    line = raw_line.strip()
    if not line:
        return None
    parts = [segment.strip() for segment in line.split(" | ")]
    if len(parts) < 5:
        return None
    sha, _date, author, message = parts[0], parts[1], parts[2], parts[3]
    formatted_date = None
    if _date:
        try:
            formatted_date = datetime.strptime(_date, "%Y-%m-%d")
        except ValueError:
            try:
                formatted_date = datetime.fromisoformat(_date)
            except ValueError:
                formatted_date = None
    raw_message = parts[4] if len(parts) > 4 else message
    type_, scope, description, breaking = _parse_type_scope(raw_message)
    return _ParsedCommit(
        sha=_normalize_sha(sha),
        short=_normalize_sha(sha),
        author=author,
        date=formatted_date,
        tag=None,
        type=normalize_type(type_),
        scope=scope,
        message=description,
        breaking=breaking,
        raw=line,
    )


def _results_to_entries(results: list[_ParsedCommit]) -> list[ChangelogEntry]:
    if not results:
        return []
    entries: list[ChangelogEntry] = []
    for group, group_results in _group_by_tag(results):
        if not group_results:
            continue
        group_header = GroupHeader(label=group, tag=group, date=_first_date(group_results))
        commits = [
            Commit(
                sha=r.sha,
                short=r.short,
                author=r.author,
                date=r.date,
                type=r.type,
                scope=r.scope,
                description=r.message,
                breaking=r.breaking,
                raw=r.raw,
            )
            for r in group_results
        ]
        entries.append(ChangelogEntry(group=group_header, commits=commits))
    return entries


def _group_by_tag(results: list[_ParsedCommit]) -> list[tuple[str, list[_ParsedCommit]]]:
    order: list[str] = []
    buckets: dict[str, list[_ParsedCommit]] = {}
    for item in results:
        tag = item.tag or "Unreleased"
        buckets.setdefault(tag, []).append(item)
        if tag not in order:
            order.append(tag)
    return [(tag, buckets[tag]) for tag in order]


def _first_date(commits: Iterable[_ParsedCommit]) -> Optional[str]:
    dates = [c.date for c in commits if c.date]
    if not dates:
        return None
    return min(dates).strftime("%Y-%m-%d")


class MarkdownRenderer:
    def render(self, entries: list[ChangelogEntry]) -> str:
        if not entries:
            return "# Changelog\n\nNo changelog entries found.\n"
        sections: list[str] = ["# Changelog"]
        for entry in entries:
            sections.append(self._render_entry(entry))
        return "\n\n".join(sections) + "\n"

    def _render_entry(self, entry: ChangelogEntry) -> str:
        group_parts = [entry.group.label]
        if entry.group.date:
            group_parts.append(f"_{entry.group.date}_")
        heading = " - ".join(group_parts)
        parts = [f"## {heading}"]
        for commit in sorted(entry.commits, key=_sort_commit):
            prefix = "**BREAKING** " if commit.breaking else ""
            parts.append(f"- [{commit.type}] {prefix}{commit.header} `{commit.short}` ({commit.author})")
        return "\n".join(parts)


def group_commits(commits: Sequence[Commit]) -> List[ChangelogEntry]:
    results = [
        _ParsedCommit(
            sha=c.sha,
            short=c.short,
            author=c.author,
            date=c.date,
            tag=c.type,
            type=c.type,
            scope=c.scope,
            message=c.description,
            breaking=c.breaking,
            raw=c.raw,
        )
        for c in commits
    ]
    return _results_to_entries(sorted(results, key=lambda r: r.date or datetime.min, reverse=True))


def render_changelog(entries: Iterable[ChangelogEntry]) -> str:
    return MarkdownRenderer().render(list(entries))
