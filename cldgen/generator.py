"""Generate changelog entries from git log collection."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from cldgen.parser import (
    ChangelogEntry,
    Commit,
    GroupHeader,
    MarkdownRenderer,
    parse_tags,
    parse_git_log,
    render_changelog,
)
from cldgen.types import GroupHeader as TypesGroupHeader
from cldgen.git import collect_commits, collect_tags, GitError, GitTagInfo


class ChangelogGenerator:
    def __init__(self, repo: Path | str, tags: Optional[List[str]] = None) -> None:
        self.repo = Path(repo).resolve()
        self.tags = [tag.strip() for tag in (tags or []) if tag.strip()]

    def build(self, since: Optional[str] = None) -> str:
        entries = self._build_entries(now=datetime.utcnow().strftime("%Y-%m-%d"), since_tag=since)
        return MarkdownRenderer().render(entries)

    def write(self, output_path: Path | str, since: Optional[str] = None) -> Path:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.build(since=since), encoding="utf-8")
        return target

    def to_json(self, since: Optional[str] = None) -> str:
        entries = self._build_entries(now=datetime.utcnow().strftime("%Y-%m-%d"), since_tag=since)
        payload = {
            "generated_at": datetime.utcnow().isoformat(),
            "count": len(entries),
            "entries": [
                {
                    "label": entry.group.label,
                    "tag": entry.group.tag,
                    "date": entry.group.date,
                    "commits": [
                        {
                            "sha": commit.sha,
                            "author": commit.author,
                            "date": commit.date.isoformat() if commit.date else None,
                            "type": commit.type,
                            "scope": commit.scope,
                            "description": commit.description,
                            "breaking": commit.breaking,
                            "header": commit.header,
                        }
                        for commit in entry.commits
                    ],
                }
                for entry in entries
            ],
        }
        return json.dumps(payload, indent=2)

    def _build_entries(self, now: str, since_tag: Optional[str]) -> List[ChangelogEntry]:
        since_info = None
        if since_tag:
            tag_map = {info.name: info for info in collect_tags(self.repo)}
            since_info = tag_map.get(since_tag)
            if since_info is None:
                return [ChangelogEntry(group=GroupHeader(label=since_tag, tag=since_tag, date=now), commits=[])]

        raw_commits = collect_commits(self.repo, since=since_info, limit=200)
        if not raw_commits:
            tag = parse_tags(self.tags)[0] if self.tags else TypesGroupHeader(label="Unreleased", tag="Unreleased", date=now)
            return [ChangelogEntry(group=tag, commits=[])]

        log_lines = [self._format_commit(commit) for commit in raw_commits]
        entries = parse_git_log("\n".join(log_lines), self.tags)
        for entry in entries:
            date_val = _latest_date_from_commits(entry.commits)
            if date_val:
                entry.group.date = date_val
        return entries

    def _format_commit(self, commit) -> str:
        return " | ".join([
            commit.sha,
            commit.date,
            commit.author,
            commit.message,
            commit.message.strip(),
        ])


def _latest_date_from_commits(commits: List[Commit]) -> Optional[str]:
    dates = [c.date for c in commits if c.date]
    if not dates:
        return None
    return max(dates).strftime("%Y-%m-%d")
