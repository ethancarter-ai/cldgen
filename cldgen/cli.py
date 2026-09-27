"""CLI for cldgen: changelog generator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cldgen.generator import ChangelogGenerator


def _epilog() -> str:
    return (
        "examples:\n"
        "  cldgen generate /repo\n"
        "  cldgen generate /repo --output CHANGELOG.md\n"
        "  cldgen generate /repo --since v1.2.0 --format json\n"
        "  cldgen generate /repo --group Release-2025-09-01\n"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cldgen",
        description="Generate changelogs from git tags and messages.",
        epilog=_epilog(),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate changelog for a repository.")
    gen.add_argument("repo", type=str, help="Path to the repository.")
    gen.add_argument("--output", "-o", type=str, default=None, help="Write output to file.")
    gen.add_argument(
        "--format",
        "-f",
        choices=["md", "markdown", "json", "text"],
        default="md",
        help="Output format; JSON gives structured machine-readable output.",
    )
    gen.add_argument("--since", type=str, default=None, help="Start from an existing tag.")
    gen.add_argument("--group", dest="group", action="append", help="Group heading tag; repeatable.")
    gen.add_argument("--limit", type=int, default=50, help="Max commits to include.")
    gen.add_argument("--json", action="store_true", help="Alias for --format json.")
    return parser


def _resolve_format(args: argparse.Namespace) -> str:
    if args.json:
        return "json"
    return args.format.lower()


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = []
    parser = _build_parser()
    if not argv:
        parser.print_help()
        return 2
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 1

    if args.command != "generate":
        parser.print_help()
        return 2

    repo = Path(args.repo).expanduser().resolve()
    output = Path(args.output).expanduser().resolve() if args.output else None
    fmt = _resolve_format(args)
    generator = ChangelogGenerator(repo, tags=args.group)

    try:
        if fmt == "json":
            rendered = generator.to_json(since=args.since)
        else:
            rendered = generator.build(since=args.since)
    except Exception as exc:
        print(f"cldgen error: {exc}", file=sys.stderr)
        return 2

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0
