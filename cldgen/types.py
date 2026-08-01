"""Core types for cldgen."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class Commit:
    sha: str
    short: str
    author: str
    date: datetime
    type: str
    scope: Optional[str]
    description: str
    breaking: bool
    raw: str

    @property
    def header(self) -> str:
        scope = f"**{self.scope}**: " if self.scope else ""
        return f"{scope}{self.description}"


@dataclass
class GroupHeader:
    label: str
    tag: str
    date: Optional[str] = None


@dataclass(frozen=True)
class ChangelogEntry:
    group: GroupHeader
    commits: List[Commit]
