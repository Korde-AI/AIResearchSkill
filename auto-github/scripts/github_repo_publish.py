#!/usr/bin/env python3
"""Create GitHub repos and push local projects safely."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=check,
    )


def git_root(source_dir: Path) -> Path | None:
    try:
        completed = run(["git", "rev-parse", "--show-toplevel"], source_dir)
    except subprocess.CalledProcessError:
        return None
    return Path(completed.stdout.strip())


def ensure_tools() -> None:
    missing = [name for name in ("git", "gh") if shutil.which(name) is None]
    if missing:
        raise SystemExit(f"Missing required tools: {', '.join(missing)}")


def current_branch(source_dir: Path) -> str | None:
    try:
        completed = run(["git", "branch", "--show-current"], source_dir)
    except subprocess.CalledProcessError:
        return None
    branch = completed.stdout.strip()
    return branch or None


def remotes(source_dir: Path) -> dict[str, str]:
    try:
        completed = run(["git", "remote", "-v"], source_dir)
    except subprocess.CalledProcessError:
        return {}
    mapping: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] not in mapping:
            mapping[parts[0]] = parts[1]
    return mapping


def worktree_status(source_dir: Path) -> list[str]:
    try:
        completed = run(["git", "status", "--short"], source_dir)
    except subprocess.CalledProcessError:
        return []
    return [line for line in completed.stdout.splitlines() if line.strip()]


def ensure_git_repo(source_dir: Path) -> None:
    if git_root(source_dir) is not None:
        return
    run(["git", "init", "-b", "main"], source_dir)


def ensure_gh_auth() -> None:
    try:
        run(["gh", "auth", "status"], Path.cwd())
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or "gh auth status failed"
        raise SystemExit(f"GitHub CLI is not authenticated: {message}") from exc


def cmd_inspect(args: argparse.Namespace) -> int:
    ensure_tools()
    source_dir = Path(args.source_dir).expanduser().resolve()
    repo_root = git_root(source_dir)
    gh_status = run(["gh", "auth", "status"], source_dir, check=False)
    payload = {
        "source_dir": str(source_dir),
        "git_repo": repo_root is not None,
        "git_root": str(repo_root) if repo_root else None,
        "branch": current_branch(source_dir) if repo_root else None,
        "remotes": remotes(source_dir) if repo_root else {},
        "worktree_status": worktree_status(source_dir) if repo_root else [],
        "gh_auth_ok": gh_status.returncode == 0,
        "gh_auth_output": (gh_status.stdout or gh_status.stderr).strip(),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_create_repo(args: argparse.Namespace) -> int:
    ensure_tools()
    ensure_gh_auth()
    source_dir = Path(args.source_dir).expanduser().resolve()
    source_dir.mkdir(parents=True, exist_ok=True)
    ensure_git_repo(source_dir)

    remote_map = remotes(source_dir)
    expected_https = f"https://github.com/{args.repo}.git"
    expected_ssh = f"git@github.com:{args.repo}.git"
    if "origin" in remote_map and remote_map["origin"] not in {expected_https, expected_ssh}:
        raise SystemExit(
            f"origin already points to {remote_map['origin']}, not {args.repo}. Stop instead of rewriting it."
        )

    visibility_flag = "--private" if args.private else "--public"

    if "origin" not in remote_map:
        cmd = [
            "gh",
            "repo",
            "create",
            args.repo,
            visibility_flag,
            "--source",
            ".",
            "--remote",
            "origin",
        ]
        run(cmd, source_dir)

    print(
        json.dumps(
            {
                "source_dir": str(source_dir),
                "repo": args.repo,
                "origin": remotes(source_dir).get("origin"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def has_commits(source_dir: Path) -> bool:
    completed = run(["git", "rev-parse", "--verify", "HEAD"], source_dir, check=False)
    return completed.returncode == 0


def cmd_push(args: argparse.Namespace) -> int:
    ensure_tools()
    ensure_gh_auth()
    source_dir = Path(args.source_dir).expanduser().resolve()
    if git_root(source_dir) is None:
        raise SystemExit("source-dir is not a git repository.")

    remote_map = remotes(source_dir)
    if "origin" not in remote_map:
        raise SystemExit("origin remote is missing. Run create-repo first.")

    branch = current_branch(source_dir) or "main"
    status_lines = worktree_status(source_dir)
    if status_lines:
        run(["git", "add", "-A"], source_dir)
        run(["git", "commit", "-m", args.message], source_dir)
    elif not has_commits(source_dir):
        raise SystemExit("Repository has no commits and no staged changes to commit.")

    push_cmd = ["git", "push", "-u", "origin", f"HEAD:{branch}"]
    run(push_cmd, source_dir)

    print(
        json.dumps(
            {
                "source_dir": str(source_dir),
                "branch": branch,
                "origin": remote_map["origin"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create GitHub repos and push local code.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("--source-dir", required=True)

    create_parser = subparsers.add_parser("create-repo")
    create_parser.add_argument("--source-dir", required=True)
    create_parser.add_argument("--repo", required=True, help="owner/name")
    visibility = create_parser.add_mutually_exclusive_group()
    visibility.add_argument("--public", action="store_true")
    visibility.add_argument("--private", action="store_true")

    push_parser = subparsers.add_parser("push")
    push_parser.add_argument("--source-dir", required=True)
    push_parser.add_argument("--message", required=True)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "inspect":
        return cmd_inspect(args)
    if args.command == "create-repo":
        return cmd_create_repo(args)
    if args.command == "push":
        return cmd_push(args)
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
