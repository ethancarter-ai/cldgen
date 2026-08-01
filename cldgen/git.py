"""Isolated git log fetching for deterministic tests."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class GitCommit:
    sha: str
    date: str
    author: str
    message: str


@dataclass(frozen=True)
class GitTagInfo:
    name: str
    sha: str
    date: str
    message: str


class GitError(Exception):
    pass


def collect_tags(path: Path | str) -> List[GitTagInfo]:
    cwd = str(Path(path).resolve())
    try:
        output = subprocess.check_output(
            ["git", "-C", cwd, "tag", "-l", "--sort=-version:refname"],
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise GitError(str(exc)) from exc

    tag_names = [line.strip() for line in output.splitlines() if line.strip()]
    infos: List[GitTagInfo] = []
    for name in tag_names:
        try:
            sha_out = subprocess.check_output(
                ["git", "-C", cwd, "rev-parse", name],
                text=True,
            )
            sha = sha_out.strip()
            message_raw = subprocess.check_output(
                ["git", "-C", cwd, "tag", "-l", "--format=%(contents)", name],
                text=True,
            )
            date_raw = subprocess.check_output(
                ["git", "-C", cwd, "tag", "-l", "--format=%(creatordate:iso8601)", name],
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            raise GitError(str(exc)) from exc
        infos.append(
            GitTagInfo(
                name=name,
                sha=sha[:12],
                date=date_raw.strip()[:10],
                message=message_raw.strip(),
            )
        )
    return infos


def collect_commits(path: Path | str, since: Optional[GitTagInfo] = None, limit: int = 20) -> List[GitCommit]:
    cwd = str(Path(path).resolve())
    cmd = [
        "git",
        "-C",
        cwd,
        "log",
        "--format=%H | %ai | %an | %s",
    ]
    if since:
        cmd.append(f"{since.sha}..HEAD")
    cmd.extend(["-n", str(max(limit, 1))])
    try:
        output = subprocess.check_output(cmd, text=True)
    except subprocess.CalledProcessError as exc:
        raise GitError(str(exc)) from exc
    commits: List[GitCommit] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        sha, date, author, message = line.split(" | ", 3)
        commits.append(GitCommit(sha=sha[:12], date=date[:10], author=author.strip(), message=message.strip()))
    return commits
