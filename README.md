# cldgen

Generate Markdown changelogs from **Git** tag history and commit message conventions.

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Status](https://img.shields.io/badge/status-stable-green)
![CLI](https://img.shields.io/badge/cli-changelog-green)

Source: https://github.com/ethancarter-ai/cldgen

## About

`cldgen` inspects a git repository, walks commit messages, and emits a compact Markdown changelog grouped by release tags. It supports conventional commits, custom group headings, JSON output for automation, and `--since` filtering from an existing tag.

## Features

- Generate changelogs from local git history.
- Group entries by tags or custom `--group` release headings.
- Supports **Conventional Commits**: `feat`, `fix`, `docs`, `refactor`, `perf`, `chore`, `breaking`, etc.
- Output formats: **Markdown** and **JSON**.
- Pure stdlib + one small optional dependency (`arrow`) for date handling.
- Local-first with no network calls by default.

## Installation

```bash
python -m pip install -e .
```

After installing, `cldgen` is on your PATH.

## Usage

```bash
# generate markdown changelog
cldgen generate /path/to/repo

# write to file
cldgen generate /path/to/repo --output CHANGELOG.md

# start from an existing tag
cldgen generate /path/to/repo --since v1.2.0

# JSON output for automation
cldgen generate /path/to/repo --format json

# custom group heading
cldgen generate /path/to/repo --group "Release-2025-09-01"
```

## Project Structure

```text
cldgen/
  cldgen/
    __init__.py
    cli.py
    generator.py
    git.py
    parser.py
    types.py
  tests/
    __init__.py
    test_parser.py
    test_generator.py
    test_cli.py
  docs/
    usage.md
  pyproject.toml
  README.md
  .gitignore
```

## Tags

`python`, `cli`, `changelog`, `git`, `developer-tools`, `conventional-commits`
